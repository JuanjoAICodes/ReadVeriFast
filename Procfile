web: gunicorn config.wsgi:application
worker: celery -A config.celery worker -Q acquisition --loglevel=info
