import os
from flask import Flask, g, request, session, current_app
from flask_login import current_user
from celery.schedules import crontab
from flask_babel import get_locale as babel_get_locale
from flask_wtf.csrf import CSRFProtect

from config import Config  # <-- 'config' ahora es nuestra única fuente de verdad

# Importa tus herramientas desde la caja de herramientas
from app.extensions import celery, db, login_manager, migrate, babel
from app.core import bp as core_bp
from app.auth import auth_bp
from app.cli import register_commands
from app.models import User


def create_app(config_class=Config):
    """
    Application factory function.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- INICIALIZACIÓN DE EXTENSIONES ---
    # Habilita la protección CSRF globalmente para la aplicación.
    # Esto hace que la función csrf_token() esté disponible en todas las plantillas.
    CSRFProtect(app)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    # Apunta a la vista de login de tu blueprint de autenticación.
    # Es necesario para que @login_required funcione.
    login_manager.login_view = 'auth.login'

    # --- CONFIGURACIÓN CENTRALIZADA DE CELERY ---
    # Usamos celery.conf.update para pasarle TODA la configuración de la app
    # Flask y Celery ahora compartirán exactamente la misma configuración.
    celery.conf.update(app.config)

    # --- CONFIGURACIÓN DE CELERY BEAT (TAREAS PERIÓDICAS) ---
    celery.conf.beat_schedule = {
        'analyze-daily-trends': {
            'task': 'app.tasks.analyze_trending_tags_task',
            'schedule': crontab(minute=0, hour=0),  # Todos los días a medianoche
        },
        'fetch-hourly-articles': {
            'task': 'app.tasks.fetch_new_articles_task',
            # Se ejecuta cada hora, al inicio de la hora (ej: 1:00, 2:00, etc.)
            'schedule': crontab(minute=0),
        }
    }

    celery.conf.broker_connection_retry_on_startup = (
        True  # Silenciamos la advertencia
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    # Register blueprints here
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(core_bp)

    # Register CLI commands
    register_commands(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    def get_locale():
        # --- Depuración de la selección de idioma ---
        current_app.logger.info(f"--- Locale Debug ---")
        current_app.logger.info(f"1. Session language: {session.get('language')}")

        # Prioridad 1: Idioma explícitamente guardado en la sesión (p.ej. por el selector de idioma)
        if 'language' in session:
            lang = session['language']
            current_app.logger.info(f"-> Returning from session: {lang}")
            return lang
        # Prioridad 2: Preferencia guardada en el perfil del usuario autenticado
        if current_user.is_authenticated and getattr(current_user, 'preferred_language', None):
            lang = current_user.preferred_language
            current_app.logger.info(f"-> Returning from user profile: {lang}")
            return lang
        # Prioridad 3: El mejor idioma según la cabecera 'Accept-Language' del navegador
        browser_match = request.accept_languages.best_match(app.config['LANGUAGES'])
        current_app.logger.info(f"2. Browser language match: {browser_match}")
        current_app.logger.info(f"-> Returning from browser match (or default if None): {browser_match}")
        return browser_match
        # Prioridad 4 (implícita): Si todo lo anterior falla, Flask-Babel usará BABEL_DEFAULT_LOCALE.

    # La inicialización de Babel ahora se hace pasando la función `locale_selector`.
    # El decorador @babel.localeselector fue eliminado en Flask-Babel 4.0.
    babel.init_app(app, locale_selector=get_locale)

    # Configura explícitamente el directorio de traducciones para mayor robustez.
    # app.root_path apunta al directorio del paquete 'app', que es donde se encuentra la carpeta 'translations'.
    app.config.setdefault('BABEL_TRANSLATION_DIRECTORIES', os.path.join(app.root_path, 'translations'))


    @app.context_processor
    def inject_context():
        return dict(
            get_locale=babel_get_locale,
            config=app.config
        )

    @app.before_request
    def before_request():
        """
        Sets the current locale on the Flask global `g` object before each request.
        """
        g.locale = str(babel_get_locale())

    return app