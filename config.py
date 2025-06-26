import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))  # Esta línea es crucial


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Idiomas para Babel ---
    LANGUAGES = ['en', 'es']
    BABEL_DEFAULT_LOCALE = 'en'

    # --- Claves para Celery ---
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    RESULT_BACKEND = os.environ.get('RESULT_BACKEND', 'redis://localhost:6379/0')

    # --- Clave para la IA ---
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

    # --- Clave para GNews ---
    GNEWS_API_KEY = os.environ.get('GNEWS_API_KEY')

class TestConfig(Config):
    """Configuración específica para las pruebas."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False  # Desactiva la protección CSRF para las pruebas
    # Ejecuta las tareas de Celery de forma síncrona para facilitar las pruebas
    CELERY_TASK_ALWAYS_EAGER = True