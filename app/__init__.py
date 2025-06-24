from flask import Flask, request, session
from flask_login import current_user
from flask_babel import get_locale as babel_get_locale

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
        # 1. Mira si el usuario ha guardado una preferencia en su perfil
        if current_user.is_authenticated and getattr(current_user, 'preferred_language', None):
            return current_user.preferred_language
        # 2. Mira si el usuario ha guardado una preferencia en la sesión
        if 'language' in session:
            return session['language']
        # 3. Usa la que pide el navegador
        return request.accept_languages.best_match(app.config['LANGUAGES'])

    # La inicialización de Babel ahora se hace pasando la función `locale_selector`.
    # El decorador @babel.localeselector fue eliminado en Flask-Babel 4.0.
    babel.init_app(app, locale_selector=get_locale)

    @app.context_processor
    def inject_locale():
        return dict(get_locale=babel_get_locale)

    return app