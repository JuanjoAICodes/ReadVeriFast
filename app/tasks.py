import json
import random
from datetime import datetime, timedelta, timezone
import newspaper
import requests
from flask import current_app
from sqlalchemy import func

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
            logger.info(f"Descargando URL: {article.url}")
            n_article = newspaper.Article(article.url)
            n_article.download()
            n_article.parse()
            logger.info("URL descargada y parseada con éxito.")

            # Guardamos el idioma detectado y el contenido
            article.image_url = n_article.top_image
            article.title = n_article.title or "Título no encontrado"
            article.language = n_article.meta_lang or 'en'
            article.raw_content = n_article.text
            article.clean_content = n_article.text # Asignamos el contenido para la lectura rápida

            if not article.raw_content or len(article.raw_content) < 100: # Evita procesar artículos vacíos
                raise ValueError("El contenido extraído es demasiado corto o está vacío.")

            logger.info(f"Generando cuestionario con IA en '{article.language}'...")
            # --- LÓGICA REAL DE LLAMADA A IA ---
            quiz_data = generate_quiz_from_text(article)

            # Comprueba el resultado de la API
            if not quiz_data or "questions" not in quiz_data or "tags" not in quiz_data:
                 raise ValueError("La respuesta de la API de IA no tiene el formato esperado o está vacía.")

            # Procesa y asocia los tags generados
            tag_names = quiz_data.get('tags', [])
            for tag_name in tag_names:
                if not isinstance(tag_name, str) or not tag_name.strip():
                    continue
                # Busca el tag ignorando mayúsculas/minúsculas
                tag = Tag.query.filter(db.func.lower(Tag.name) == db.func.lower(tag_name.strip())).first()
                if not tag:
                    tag = Tag(name=tag_name.strip())
                    db.session.add(tag)
                if tag not in article.tags:
                    article.tags.append(tag)

            article.quiz_data = json.dumps(quiz_data)
            article.processing_status = 'complete'
            logger.info(f"Artículo {article.id} procesado con ÉXITO.")

        except Exception as e:
            logger.error(f"!!! EXCEPCIÓN al procesar artículo {article.id}: {e}", exc_info=True)
            article.processing_status = 'failed'
            # Esta es una función de reintento de Celery.
            # Intentará ejecutar la tarea de nuevo 2 veces más, con un retraso.
            try:
                self.retry(exc=e, countdown=60)
            except self.MaxRetriesExceededError:
                logger.error(f"La tarea para el artículo {article.id} ha fallado definitivamente después de varios reintentos.")
        
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
    from app import create_app
    app = create_app()
    with app.app_context():
        logger = current_app.logger
        logger.info("--- INICIANDO TAREA de búsqueda de nuevos artículos ---")

        try:
            # 1. Obtener dependencias
            redis_client = celery.backend.client
            api_key = current_app.config.get('GNEWS_API_KEY')
            if not api_key:
                logger.error("GNEWS_API_KEY no encontrada en la configuración. Abortando tarea.")
                return

            # 2. Leer Tendencias desde Redis
            trending_tags = []
            try:
                tags_json = redis_client.get('trending_tags')
                if tags_json: trending_tags = json.loads(tags_json)
            except (json.JSONDecodeError, TypeError):
                logger.warning("No se pudieron leer los 'trending_tags' de Redis.")

            language_ratio = {}
            try:
                ratio_json = redis_client.get('language_ratio')
                if ratio_json: language_ratio = json.loads(ratio_json)
            except (json.JSONDecodeError, TypeError):
                logger.warning("No se pudo leer el 'language_ratio' de Redis.")

            # 3. Preparar la Búsqueda
            if trending_tags and isinstance(trending_tags, list):
                search_term = " OR ".join(f'"{tag}"' for tag in trending_tags)
                logger.info(f"Usando tags de tendencia para la búsqueda: {search_term}")
            else:
                fallback_categories = ['world', 'technology', 'science', 'business', 'health']
                search_term = random.choice(fallback_categories)
                logger.info(f"No se encontraron tags. Usando categoría de fallback: '{search_term}'")

            if language_ratio and 'en' in language_ratio and 'es' in language_ratio:
                langs = list(language_ratio.keys())
                weights = list(language_ratio.values())
                selected_lang = random.choices(langs, weights=weights, k=1)[0]
                logger.info(f"Idioma seleccionado basado en ratio ({language_ratio}): '{selected_lang}'")
            else:
                selected_lang = random.choice(['en', 'es'])
                logger.info(f"No se encontró ratio de idiomas. Usando idioma al azar: '{selected_lang}'")

            # 4. Ejecutar la Petición a la API (GNews.io)
            params = {'q': search_term, 'lang': selected_lang, 'token': api_key, 'max': 10}
            response = requests.get("https://gnews.io/api/v4/search", params=params)
            response.raise_for_status()
            data = response.json()

            # 5. Procesar los Resultados
            new_articles_count = 0
            system_user = User.query.get(1)
            if not system_user:
                logger.error("Usuario sistema (ID=1) no encontrado. No se pueden asignar autores. Abortando.")
                return

            for api_article in data.get('articles', []):
                url = api_article.get('url')
                if not url: continue

                exists = db.session.query(Article.id).filter_by(url=url).first()
                if not exists:
                    new_article = Article(
                        url=url,
                        title=api_article.get('title', 'Sin Título'),
                        is_user_submitted=False,
                        author_id=system_user.id,
                        processing_status='pending'
                    )
                    db.session.add(new_article)
                    db.session.commit()

                    process_article_task.delay(new_article.id)
                    new_articles_count += 1
            
            logger.info(f"Tarea de búsqueda completada. Se encontraron y encolaron {new_articles_count} artículos nuevos.")

        except requests.exceptions.RequestException as e:
            logger.error(f"!!! EXCEPCIÓN durante la petición a la API de GNews: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"!!! EXCEPCIÓN en la tarea de búsqueda de artículos: {e}", exc_info=True)
        finally:
            logger.info("--- TAREA de búsqueda de nuevos artículos FINALIZADA ---")