web: gunicorn config.wsgi --bind 0.0.0.0:8000 --reload
worker: celery -A config.celery worker --loglevel=INFO