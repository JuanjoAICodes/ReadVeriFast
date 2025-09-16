# VeriFast - Setup and Deployment Guide

## Prerequisites

### System Requirements
- Python 3.10 or higher
- PostgreSQL 12+ (for production) or SQLite (for development)
- Redis 6+ (for Celery task queue)
- Git

### Required API Keys
- **Google Gemini API Key** - Required for LLM-powered quiz generation
- **Wikipedia API** - No key required, but rate limits apply

## Development Setup

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd verifast

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install NLP Models

```bash
# Download spaCy language models
python -m spacy download en_core_web_sm
python -m spacy download es_core_news_sm
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=sqlite:///db.sqlite3  # For development
# DATABASE_URL=postgres://user:password@localhost:5432/verifast  # For production

# Django Settings
SECRET_KEY='your-secret-key-here'
DEBUG=True

# Celery Configuration
BROKER_URL=redis://localhost:6379/0

# API Keys
GEMINI_API_KEY=your-gemini-api-key-here
```

### 4. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic
```

### 5. Start Development Services

You have two options for running the development environment:

#### Option A: Using Honcho (Recommended)
```bash
# Install honcho if not already installed
pip install honcho

# Start all services
honcho start
```

This will start:
- Django development server on http://127.0.0.1:8000
- Celery worker for background tasks

#### Option B: Manual Process Management
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Django development server
python manage.py runserver

# Terminal 3: Start Celery worker
celery -A config.celery worker --loglevel=INFO
```

## Production Deployment

### 1. Environment Setup

```env
# Production environment variables
DATABASE_URL=postgres://user:password@localhost:5432/verifast
SECRET_KEY='secure-production-secret-key'
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Redis Configuration
BROKER_URL=redis://localhost:6379/0

# API Keys
GEMINI_API_KEY=your-production-gemini-api-key
```

### 2. Database Configuration

```bash
# Install PostgreSQL and create database
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres createdb verifast
sudo -u postgres createuser verifast_user

# Run migrations
python manage.py migrate
python manage.py collectstatic --noinput
```

### 3. Web Server Setup (Nginx + Gunicorn)

#### Gunicorn Configuration
```bash
# Install gunicorn (already in requirements.txt)
pip install gunicorn

# Test gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

#### Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location /static/ {
        alias /path/to/verifast/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. Process Management (Systemd)

#### Django Service
```ini
# /etc/systemd/system/verifast-web.service
[Unit]
Description=VeriFast Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/verifast
Environment=PATH=/path/to/verifast/venv/bin
ExecStart=/path/to/verifast/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 config.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Celery Worker Service
```ini
# /etc/systemd/system/verifast-worker.service
[Unit]
Description=VeriFast Celery Worker
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/verifast
Environment=PATH=/path/to/verifast/venv/bin
ExecStart=/path/to/verifast/venv/bin/celery -A config.celery worker --loglevel=INFO
Restart=always

[Install]
WantedBy=multi-user.target
```

## Configuration Details

### Django Settings

Key settings in `config/settings.py`:

```python
# Custom User Model
AUTH_USER_MODEL = 'verifast_app.CustomUser'

# Celery Configuration
CELERY_BROKER_URL = env('BROKER_URL')
CELERY_RESULT_BACKEND = env('BROKER_URL')
CELERY_IMPORTS = ('verifast_app.tasks',)

# Static Files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Templates
TEMPLATES = [{
    'DIRS': [BASE_DIR / 'templates'],
    'OPTIONS': {
        'context_processors': [
            # ... default processors ...
            'verifast_app.context_processors.user_xp_processor',
        ],
    },
}]
```

### Celery Configuration

The Celery configuration in `config/celery.py` handles:
- Task discovery from Django apps
- Redis broker connection
- Task routing and execution

### Database Models

The system uses a custom user model with gamification fields:
- `current_wpm`, `max_wpm` - Reading speed tracking
- `total_xp`, `current_xp_points` - Experience points
- `preferred_language`, `theme` - User preferences
- `llm_api_key_encrypted` - User's personal API keys

## API Integration

### Google Gemini API

The system integrates with Google Gemini for:
- Quiz question generation
- Entity co-reference resolution
- Dynamic model selection based on content complexity

Models used:
- `gemini-2.5-pro` - Complex content (reading level < 30)
- `gemini-2.5-flash` - Standard content (30-60)
- `gemini-2.5-flash-lite-preview-06-17` - Simple content (>60)

### Wikipedia API

Used for:
- Entity validation and canonical name resolution
- Tag creation and management
- Multi-language support (English/Spanish)

## Monitoring and Logging

### Application Logging

Django logging is configured to capture:
- Task execution logs
- API call logs
- Error tracking
- User activity logs

### Celery Monitoring

Monitor Celery tasks using:
```bash
# View active tasks
celery -A config.celery inspect active

# View task statistics
celery -A config.celery inspect stats

# Monitor task events
celery -A config.celery events
```

### Database Monitoring

Key metrics to monitor:
- Article processing queue length
- User engagement metrics
- Quiz completion rates
- Comment interaction patterns

## Troubleshooting

### Common Issues

1. **Celery Tasks Not Processing**
   - Check Redis connection
   - Verify Celery worker is running
   - Check task logs for errors

2. **LLM API Failures**
   - Verify API key configuration
   - Check API quota limits
   - Review retry logic in tasks

3. **Database Connection Issues**
   - Verify DATABASE_URL format
   - Check PostgreSQL service status
   - Ensure database user permissions

4. **Static Files Not Loading**
   - Run `python manage.py collectstatic`
   - Check STATIC_ROOT configuration
   - Verify web server static file serving

### Debug Mode

For development debugging:
```python
# In settings.py
DEBUG = True
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'verifast_app': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Security Considerations

### Production Security

1. **Environment Variables**
   - Never commit `.env` files
   - Use secure secret key generation
   - Rotate API keys regularly

2. **Database Security**
   - Use strong database passwords
   - Limit database user permissions
   - Enable SSL connections

3. **Web Server Security**
   - Configure HTTPS with SSL certificates
   - Set appropriate security headers
   - Implement rate limiting

### API Security

1. **Rate Limiting**
   - Implement API call rate limiting
   - Monitor API usage patterns
   - Set up alerts for quota limits

2. **Data Validation**
   - Validate all user inputs
   - Sanitize scraped content
   - Implement CSRF protection

## Backup and Recovery

### Database Backups

```bash
# PostgreSQL backup
pg_dump verifast > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
psql verifast < backup_file.sql
```

### File Backups

- Static files and media uploads
- Configuration files
- Log files

## Performance Optimization

### Database Optimization

1. **Indexing**
   - Add indexes on frequently queried fields
   - Monitor slow query logs
   - Use database query optimization

2. **Connection Pooling**
   - Configure PostgreSQL connection pooling
   - Use pgbouncer for production

### Caching

1. **Redis Caching**
   - Cache expensive database queries
   - Store session data in Redis
   - Cache API responses

2. **Static File Caching**
   - Configure browser caching headers
   - Use CDN for static file delivery
   - Implement template fragment caching

---

*This setup guide covers development and production deployment for VeriFast as of July 2025.*