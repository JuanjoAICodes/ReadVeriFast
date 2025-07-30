# VeriFast Technology Stack

## Backend Framework
- **Django 5.2.4**: Main web framework with built-in ORM, admin, and authentication
- **Python 3.10+**: Programming language
- **PostgreSQL**: Production database (SQLite for development)
- **Django REST Framework**: API endpoints for AJAX functionality

## Asynchronous Processing
- **Celery**: Background task processing for article scraping and AI analysis
- **Redis**: Message broker and result backend for Celery
- **Gunicorn**: WSGI server for production deployment

## AI & External APIs
- **Google Gemini API**: Quiz generation and content analysis
- **Wikipedia API**: Tag validation and content enrichment
- **newspaper3k**: Web scraping for article content
- **spaCy**: Natural language processing

## Frontend
- **Django Templates**: Server-side rendering with DTL
- **HTMX**: Server-driven interactivity with minimal JavaScript
- **Alpine.js**: Minimal client-side reactivity (30 lines total)
- **PicoCSS**: Lightweight, semantic CSS framework
- **WhiteNoise**: Static file serving

## Development Tools
- **ruff**: Code formatting and linting
- **mypy**: Static type checking with mypy.ini configuration
- **django-environ**: Environment variable management

## Common Commands

### Development Setup
```bash
# Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Database setup
python manage.py migrate
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Background Tasks
```bash
# Start Celery worker (separate terminal)
celery -A config.celery worker --loglevel=INFO

# Start Redis (if not running as service)
redis-server
```

### Code Quality
```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy .

# Run tests
python manage.py test
```

### Database Operations
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Database shell
python manage.py dbshell

# Django shell
python manage.py shell
```

### Production Deployment
```bash
# Collect static files
python manage.py collectstatic

# Run with Gunicorn (as defined in Procfile)
gunicorn config.wsgi --bind 0.0.0.0:8000
```

## Environment Variables
Required in `.env` file:
- `SECRET_KEY`: Django secret key
- `DEBUG`: Boolean for debug mode
- `DATABASE_URL`: Database connection string
- `BROKER_URL`: Redis URL for Celery
- `GEMINI_API_KEY`: Google Gemini API key