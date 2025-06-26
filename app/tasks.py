import json
import random
import secrets
from datetime import datetime, timedelta, timezone
import newspaper
import requests
from requests.exceptions import RequestException
from urllib3.exceptions import ProtocolError
from newspaper import Config
from flask import current_app
from sqlalchemy import func, select

import feedparser
from app.extensions import celery, db
from app.models import Article, QuizAttempt, Tag, User, article_tags
from app.llm_services import generate_quiz_from_text

@celery.task(bind=True, max_retries=2)
def process_article_task(self, article_id): # <-- Añade self como primer argumento
    """
    Tarea asíncrona para procesar un artículo.
    """
    from app import create_app
    app = create_app()
    with app.app_context():
        # Usa el logger de la app para más visibilidad
        logger = current_app.logger
        
        logger.info(f"--- INICIANDO TAREA para Artículo ID: {article_id} ---")
        
        article = Article.query.get(article_id)
        if not article:
            logger.error(f"Error: No se encontró el artículo con ID {article_id} en la BD.")
            return

        try:
            # --- Configuración para simular un navegador y evitar bloqueos ---
            config = Config()
            config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0'
            config.request_timeout = 15 # También es buena idea poner el timeout aquí

            logger.info(f"Descargando URL: {article.url}")
            # Pasamos la configuración al crear el objeto Article de newspaper
            n_article = newspaper.Article(article.url, config=config)
            n_article.download()
            n_article.parse()
            logger.info("URL descargada y parseada con éxito.")

            # --- Detección de Muro de Pago (Paywall) y Contenido Insuficiente ---
            extracted_text = n_article.text
            paywall_keywords = [
                'subscribe', 'monthly limit', 'premium content',
                'log in to continue', 'create an account to read'
            ]
            lower_text = extracted_text.lower() if extracted_text else ""

            if (not extracted_text or len(extracted_text) < 250) or any(keyword in lower_text for keyword in paywall_keywords):
                raise ValueError("Contenido bloqueado por un muro de pago o insuficiente.")

            # Si pasa la validación, guardamos el contenido y continuamos
            article.image_url = n_article.top_image
            article.title = n_article.title or "Título no encontrado"
            # Prioriza el idioma ya existente, luego intenta detectar, y finalmente usa 'en' como fallback.
            article.language = article.language or n_article.meta_lang or 'en'
            article.raw_content = extracted_text
            article.clean_content = extracted_text

            logger.info(f"Generando cuestionario con IA en '{article.language}'...")
            # --- LÓGICA REAL DE LLAMADA A IA ---
            quiz_data = generate_quiz_from_text(article)

            # Comprueba el resultado de la API
            if not quiz_data or "questions" not in quiz_data or "tags" not in quiz_data:
                 raise ValueError("La respuesta de la API de IA no tiene el formato esperado o está vacía.")

            # --- Lógica Unificada de Tags ---
            # 1. Obtener tags de la IA
            tag_names = quiz_data.get('tags', [])

            # 2. Añadir el tag de idioma a la lista
            language_tag_map = {'es': 'español', 'en': 'english'}
            language_tag_name = language_tag_map.get(article.language)
            if language_tag_name and language_tag_name not in tag_names:
                tag_names.append(language_tag_name)

            # 3. Iterar sobre la lista combinada y asociar los tags
            for tag_name in tag_names: # Bucle unificado
                if not isinstance(tag_name, str) or not tag_name.strip():
                    continue
                # Busca el tag ignorando mayúsculas/minúsculas
                tag = Tag.query.filter(db.func.lower(Tag.name) == db.func.lower(tag_name.strip())).first()
                if not tag:
                    tag = Tag(name=tag_name.strip())
                    db.session.add(tag)
                if tag not in article.tags:
                    article.tags.append(tag)

            article.quiz_data = json.dumps(quiz_data) # Guardar los datos del cuestionario
            article.processing_status = 'complete'
            logger.info(f"Artículo {article.id} procesado con ÉXITO.")

        except Exception as e:
            logger.error(f"!!! EXCEPCIÓN al procesar artículo {article.id}: {type(e).__name__} - {e}", exc_info=True)

            # Lista de errores que merecen un reintento (errores de red/temporales)
            RETRYABLE_EXCEPTIONS = (RequestException, ProtocolError, ConnectionError)

            if isinstance(e, RETRYABLE_EXCEPTIONS):
                logger.info(f"Error temporal de red detectado. Reintentando la tarea para el artículo {article.id}...")
                try:
                    # Aumentamos el countdown para dar tiempo a que se resuelvan problemas de red.
                    # self.retry() lanza una excepción para detener la ejecución y que Celery la reintente más tarde.
                    # El número máximo de reintentos se define en el decorador @celery.task.
                    self.retry(exc=e, countdown=60 * 5)
                except self.MaxRetriesExceededError:
                    # Si se ha alcanzado el límite de reintentos, el fallo es definitivo.
                    logger.error(f"La tarea para el artículo {article.id} ha fallado definitivamente después de varios reintentos de red.")
                    article.processing_status = 'failed'
            else:
                # Si es un error de paywall, de newspaper, o cualquier otro, es un fallo permanente y no se reintenta.
                logger.warning(f"Fallo permanente detectado. Marcando el artículo {article.id} como 'failed' sin reintentos.")
                article.processing_status = 'failed'

        finally:
            # Este bloque se ejecuta siempre, haya error o no.
            # Nos aseguramos de guardar el estado (complete o failed).
            db.session.commit()
            logger.info(f"--- TAREA FINALIZADA para Artículo ID: {article_id} ---")


@celery.task
def analyze_trending_tags_task():
    """
    Tarea periódica para analizar los tags más leídos y el ratio de idiomas,
    guardando los resultados en Redis para un acceso rápido.
    """
    from app import create_app
    app = create_app()
    with app.app_context():
        logger = current_app.logger
        logger.info("--- INICIANDO TAREA de análisis de tendencias ---")

        try:
            # 1. Obtener el cliente de Redis desde la instancia de Celery
            redis_client = celery.backend.client

            # 2. Calcular el rango de fechas (últimos 2 días)
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=2)
            logger.info(f"Analizando actividad desde {start_date} hasta {end_date}")

            # 3. Consulta de los 5 tags más populares
            trending_tags_query = (
                db.session.query(Tag.name, func.count(QuizAttempt.id).label('attempt_count'))
                .join(article_tags, Tag.id == article_tags.c.tag_id)
                .join(Article, Article.id == article_tags.c.article_id)
                .join(QuizAttempt, QuizAttempt.article_id == Article.id)
                .filter(QuizAttempt.timestamp >= start_date)
                .group_by(Tag.name)
                .order_by(func.count(QuizAttempt.id).desc())
                .limit(5)
                .all()
            )
            trending_tags = [row[0] for row in trending_tags_query]
            logger.info(f"Top 5 tags encontrados: {trending_tags}")

            # 4. Guardar los tags en Redis
            redis_client.set('trending_tags', json.dumps(trending_tags))
            logger.info("Tags populares guardados en Redis en la clave 'trending_tags'.")

            # 5. Consulta para determinar el ratio de idiomas
            total_attempts = QuizAttempt.query.filter(QuizAttempt.timestamp >= start_date).count()
            language_ratio = {'en': 0.0, 'es': 0.0}
            if total_attempts > 0:
                en_attempts = QuizAttempt.query.join(Article).filter(QuizAttempt.timestamp >= start_date, Article.language == 'en').count()
                es_attempts = QuizAttempt.query.join(Article).filter(QuizAttempt.timestamp >= start_date, Article.language == 'es').count()
                language_ratio['en'] = round(en_attempts / total_attempts, 2)
                language_ratio['es'] = round(es_attempts / total_attempts, 2)
            
            logger.info(f"Ratio de idiomas calculado: {language_ratio}")

            # 6. Guardar el ratio en Redis
            redis_client.set('language_ratio', json.dumps(language_ratio))
            logger.info("Ratio de idiomas guardado en Redis en la clave 'language_ratio'.")

        except Exception as e:
            logger.error(f"!!! EXCEPCIÓN en la tarea de análisis de tendencias: {e}", exc_info=True)
        
        finally:
            logger.info("--- TAREA de análisis de tendencias FINALIZADA ---")


@celery.task
def fetch_new_articles_task():
    """
    Tarea periódica para buscar nuevos artículos basados en las tendencias
    de los usuarios (tags e idiomas) y los añade a la base de datos para procesar.
    """
    # Importación local para evitar problemas de importación circular
    from app import create_app
    app = create_app()
    with app.app_context():
        logger = current_app.logger
        logger.info("--- INICIANDO TAREA de búsqueda de nuevos artículos ---")

        # --- LÓGICA ROBUSTA PARA OBTENER/CREAR USUARIO SISTEMA ---
        # Intenta obtener el usuario del sistema por su email único.
        system_user = db.session.scalar(
            select(User).where(User.email == 'system@verifast.com')
        )
        if system_user is None:
            # Si no existe, lo crea, le asigna una contraseña segura y lo guarda.
            logger.warning("Usuario 'system@verifast.com' no encontrado. Creándolo ahora...")
            system_user = User(
                email='system@verifast.com',
                is_admin=True
            )
            # Generamos una contraseña muy larga y aleatoria que no necesitamos recordar
            system_user.set_password(secrets.token_hex(24))
            db.session.add(system_user)
            db.session.commit() # Commit inmediato para asegurar que el usuario exista
            logger.info("Usuario 'system@verifast.com' creado con éxito.")

        # --- Configuración Inicial para la Ingesta ---
        MAX_ARTICLES_PER_RUN = 15
        total_new_articles_enqueued = 0 # Inicialización del contador principal
        new_article_ids_to_enqueue = [] # Lista para recolectar IDs para procesamiento posterior

        ENGLISH_RSS_FEEDS = [
            'http://feeds.bbci.co.uk/news/rss.xml',
            'http://feeds.reuters.com/reuters/topNews'
        ]
        SPANISH_RSS_FEEDS = [
            'https://www.europapress.es/rss/rss.aspx',
            'https://www.publico.es/rss/'
        ]

        # --- Helper function para el procesamiento de Feeds RSS (Capa 1) ---
        def _process_rss_feeds(feed_urls, lang, system_user, total_enqueued_count_param, max_articles, article_ids_list):
            """
            Procesa una lista de URLs de feeds RSS, añade artículos a la sesión
            y recolecta sus IDs.
            """
            logger.info(f"Procesando feeds RSS en {lang.upper()}...")
            for feed_url in feed_urls:
                if total_enqueued_count_param >= max_articles:
                    logger.info(f"Límite de artículos ({max_articles}) alcanzado. Deteniendo procesamiento RSS.")
                    return total_enqueued_count_param # Retorna el conteo actual a la tarea principal

                logger.info(f"Obteniendo feed RSS: {feed_url}")
                try:
                    feed = feedparser.parse(feed_url)
                    if feed.bozo: # Comprobar errores de parseo
                        logger.warning(f"Error al parsear feed RSS {feed_url}: {feed.bozo_exception}")
                        continue

                    articles_from_feed = 0
                    for entry in feed.entries:
                        if hasattr(entry, 'link') and hasattr(entry, 'title'): # Asegurarse de que la entrada tiene los atributos básicos
                            if total_enqueued_count_param >= max_articles:
                                logger.info(f"Límite de artículos ({max_articles}) alcanzado durante el procesamiento de {feed_url}. Deteniendo.")
                                return total_enqueued_count_param

                            url = entry.link
                            if not url:
                                continue

                            # Comprobar duplicados
                            exists = db.session.query(Article.id).filter_by(url=url).first()
                            if not exists:
                                title = entry.title if hasattr(entry, 'title') else 'No Title'
                                # Usar summary o description, preferir summary
                                content = entry.summary if hasattr(entry, 'summary') else (entry.description if hasattr(entry, 'description') else None)
                                
                                if not content: # Saltar si no hay contenido para procesar
                                    logger.warning(f"Saltando artículo de {feed_url} por falta de contenido: {title}")
                                    continue

                                new_article = Article(
                                    url=url,
                                    title=title,
                                    raw_content=content, # Almacenar summary/description como raw content
                                    clean_content=content, # Para RSS, el clean content inicial puede ser summary/description
                                    language=lang,
                                    is_user_submitted=False,
                                    author=system_user,
                                    processing_status='pending'
                                )
                                db.session.add(new_article)
                                db.session.flush()
                                article_ids_list.append(new_article.id)
                                total_enqueued_count_param += 1
                                articles_from_feed += 1
                    logger.info(f"Añadidos {articles_from_feed} artículos del feed: {feed_url}.")
                except Exception as e:
                    logger.error(f"Error al procesar feed RSS {feed_url}: {e}", exc_info=True)
            return total_enqueued_count_param

        # --- Nueva Helper function para el procesamiento de artículos de GNews (Capas 2 y 3) ---
        def _process_gnews_articles(articles_data, lang, system_user, total_enqueued_count_param, max_articles, article_ids_list):
            """
            Procesa una lista de artículos obtenidos de la API de GNews,
            añade artículos a la sesión y recolecta sus IDs.
            Retorna el conteo total actualizado y cuántos artículos se añadieron en esta llamada.
            """
            articles_added_in_this_call = 0
            for api_article in articles_data:
                if total_enqueued_count_param >= max_articles:
                    break # Detener si se alcanza el límite general

                url = api_article.get('url')
                if not url:
                    continue

                exists = db.session.query(Article.id).filter_by(url=url).first()
                if not exists:
                    title = api_article.get('title', 'No Title')
                    image_url = api_article.get('image')
                    # GNews 'content' a menudo está truncado, 'description' puede ser más completa.
                    # Usamos 'content' si está disponible, de lo contrario 'description'.
                    raw_content = api_article.get('content') or api_article.get('description')
                    
                    if not raw_content: # Saltar si no hay contenido para procesar
                        logger.warning(f"Saltando artículo de GNews por falta de contenido: {title}")
                        continue

                    new_article = Article(
                        url=url,
                        title=title,
                        image_url=image_url,
                        language=lang,
                        raw_content=raw_content,
                        clean_content=raw_content, # El contenido limpio inicial es el contenido raw
                        is_user_submitted=False,
                        author=system_user,
                        processing_status='pending'
                    )
                    db.session.add(new_article)
                    db.session.flush() # Obtener ID
                    article_ids_list.append(new_article.id)
                    total_enqueued_count_param += 1
                    articles_added_in_this_call += 1
            return total_enqueued_count_param, articles_added_in_this_call

        try:
            # Obtener API key y cliente de Redis
            redis_client = celery.backend.client
            api_key = current_app.config.get('GNEWS_API_KEY')
            if not api_key:
                logger.error("GNEWS_API_KEY no encontrada en la configuración. Abortando tarea.")
                return

            # --- Capa 1: Procesamiento de Feeds RSS ---
            logger.info("--- INICIANDO Capa 1: Procesamiento de Feeds RSS ---")
            
            # Procesar feeds en inglés
            total_new_articles_enqueued = _process_rss_feeds(
                ENGLISH_RSS_FEEDS, 'en', system_user, total_new_articles_enqueued, MAX_ARTICLES_PER_RUN, new_article_ids_to_enqueue
            )
            
            # Procesar feeds en español (solo si no se ha alcanzado el límite)
            if total_new_articles_enqueued < MAX_ARTICLES_PER_RUN:
                total_new_articles_enqueued = _process_rss_feeds(
                    SPANISH_RSS_FEEDS, 'es', system_user, total_new_articles_enqueued, MAX_ARTICLES_PER_RUN, new_article_ids_to_enqueue
                )
            
            logger.info(f"--- Capa 1 FINALIZADA. Artículos encolados hasta ahora: {total_new_articles_enqueued} ---")

            # --- Capa 2: Descubrimiento Curado (GNews /top-headlines con dominio específico) ---
            if total_new_articles_enqueued < MAX_ARTICLES_PER_RUN:
                logger.info("--- INICIANDO Capa 2: Descubrimiento Curado (GNews) ---")
                curated_domains = ['theguardian.com', 'npr.org', 'nytimes.com', 'bbc.com'] # Puedes añadir más dominios de alta calidad
                selected_domain = random.choice(curated_domains)
                logger.info(f"Buscando artículos curados en el dominio: {selected_domain}")

                try:
                    params = {'domain': selected_domain, 'token': api_key, 'max': 10} # Máximo 10 artículos de este dominio
                    response = requests.get("https://gnews.io/api/v4/top-headlines", params=params, timeout=15)
                    response.raise_for_status()
                    data = response.json()
                    
                    total_new_articles_enqueued, added_count = _process_gnews_articles(
                        data.get('articles', []), 'en', system_user, total_new_articles_enqueued, MAX_ARTICLES_PER_RUN, new_article_ids_to_enqueue
                    )
                    logger.info(f"Añadidos {added_count} artículos de la Capa 2. Total: {total_new_articles_enqueued}")

                except requests.exceptions.RequestException as e:
                    logger.error(f"!!! EXCEPCIÓN en Capa 2 (GNews top-headlines - {selected_domain}): {e}", exc_info=True)
                logger.info(f"--- Capa 2 FINALIZADA. Artículos encolados hasta ahora: {total_new_articles_enqueued} ---")

            # --- Capa 3: Exploración Oportunista (GNews /search o /top-headlines por categoría) ---
            if total_new_articles_enqueued < MAX_ARTICLES_PER_RUN:
                logger.info("--- INICIANDO Capa 3: Exploración Oportunista (GNews) ---")
                exploration_factor = random.randint(1, 10)
                gnews_articles_data = []
                selected_lang = random.choice(['en', 'es']) # Idioma aleatorio para la búsqueda oportunista

                if exploration_factor <= 8: # 80% de las veces: búsqueda por trending tags
                    logger.info("Factor de exploración: Búsqueda por trending tags.")
                    trending_tags = []
                    try:
                        tags_json = redis_client.get('trending_tags')
                        if tags_json: trending_tags = json.loads(tags_json)
                    except (json.JSONDecodeError, TypeError):
                        logger.warning("No se pudieron leer los 'trending_tags' de Redis para Capa 3.")

                    if trending_tags and isinstance(trending_tags, list):
                        search_term = " OR ".join(f'"{tag}"' for tag in trending_tags)
                        logger.info(f"Usando tags de tendencia para la búsqueda oportunista: {search_term} en {selected_lang}")
                        params = {'q': search_term, 'lang': selected_lang, 'token': api_key, 'max': 10}
                        try:
                            response = requests.get("https://gnews.io/api/v4/search", params=params, timeout=15)
                            response.raise_for_status()
                            gnews_articles_data = response.json().get('articles', [])
                        except requests.exceptions.RequestException as e:
                            logger.error(f"!!! EXCEPCIÓN en Capa 3 (GNews search - trending tags): {e}", exc_info=True)
                    else:
                        logger.info("No hay trending tags disponibles para la búsqueda oportunista.")

                else: # 20% de las veces: búsqueda por categoría aleatoria
                    logger.info("Factor de exploración: Búsqueda por categoría aleatoria.")
                    fallback_categories = ['world', 'technology', 'science', 'business', 'health', 'sports', 'entertainment']
                    selected_category = random.choice(fallback_categories)
                    logger.info(f"Usando categoría de fallback: '{selected_category}' en {selected_lang}")
                    params = {'category': selected_category, 'lang': selected_lang, 'token': api_key, 'max': 10}
                    try:
                        response = requests.get("https://gnews.io/api/v4/top-headlines", params=params, timeout=15)
                        response.raise_for_status()
                        gnews_articles_data = response.json().get('articles', [])
                    except requests.exceptions.RequestException as e:
                        logger.error(f"!!! EXCEPCIÓN en Capa 3 (GNews top-headlines - category): {e}", exc_info=True)
                
                if gnews_articles_data:
                    total_new_articles_enqueued, added_count = _process_gnews_articles(
                        gnews_articles_data, selected_lang, system_user, total_new_articles_enqueued, MAX_ARTICLES_PER_RUN, new_article_ids_to_enqueue
                    )
                    logger.info(f"Añadidos {added_count} artículos de la Capa 3. Total: {total_new_articles_enqueued}")
                else:
                    logger.info("No se encontraron artículos en la Capa 3.")
                logger.info(f"--- Capa 3 FINALIZADA. Artículos encolados hasta ahora: {total_new_articles_enqueued} ---")

            # --- Commit final de todos los artículos añadidos en esta ejecución ---
            db.session.commit()
            logger.info(f"Se han guardado {len(new_article_ids_to_enqueue)} artículos nuevos en la base de datos.")

            # --- Encolar tareas de procesamiento DESPUÉS del commit ---
            for article_id in new_article_ids_to_enqueue:
                process_article_task.delay(article_id)
                logger.info(f"Tarea de procesamiento encolada para el artículo ID: {article_id}")

            logger.info(f"Tarea de búsqueda completada. Se encontraron y encolaron {total_new_articles_enqueued} artículos nuevos en total.")

        except Exception as e:
            logger.error(f"!!! EXCEPCIÓN en la tarea de búsqueda de artículos: {e}", exc_info=True)
            db.session.rollback() # Asegurar rollback en caso de excepción
        finally:
            logger.info("--- TAREA de búsqueda de nuevos artículos FINALIZADA ---")