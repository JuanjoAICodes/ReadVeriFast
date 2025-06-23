import json
import newspaper
from flask import current_app

from app.extensions import celery, db
from app.models import Article, Tag
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