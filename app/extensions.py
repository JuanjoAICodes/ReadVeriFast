from celery import Celery
from flask_login import LoginManager
from flask_babel import Babel
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# No necesitamos dotenv aquí. La configuración se centralizará.

# 1. Creamos la instancia de Celery SIN configuración.
celery = Celery(__name__, include=['app.tasks'])

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
babel = Babel()