# VeriFast Content Motor

The Content Motor is VeriFast's background processing system that handles article scraping, AI analysis, quiz generation, and content processing using Celery and Redis.

## Quick Start

### Option 1: Interactive Quick Start (Recommended)
```bash
./quick_start.sh
```
This script will guide you through different startup options and handle prerequisites automatically.

### Option 2: Advanced Management
```bash
python start_content_motor.py --prod    # Production mode with honcho
python start_content_motor.py --dev     # Development instructions
python start_content_motor.py --status  # Check service status
```

## Available Commands

### Quick Start Script
```bash
./quick_start.sh           # Interactive startup
./quick_start.sh status    # Check service status
./quick_start.sh stop      # Stop background services
```

### Advanced Management Script
```bash
python start_content_motor.py --prod        # Production mode (honcho)
python start_content_motor.py --background  # Background/daemon mode
python start_content_motor.py --dev         # Development instructions
python start_content_motor.py --status      # Service status
python start_content_motor.py --stop        # Stop background services
python start_content_motor.py --test        # Test content processing
```

## Startup Modes

### 1. Development Mode
Best for development and debugging. Requires multiple terminals:

**Terminal 1 - Django:**
```bash
python manage.py runserver
```

**Terminal 2 - Celery Worker:**
```bash
celery -A config.celery worker --loglevel=INFO
```

**Terminal 3 - Celery Flower (optional monitoring):**
```bash
celery -A config.celery flower
```

### 2. Production Mode (Honcho)
Single terminal, production-like setup:
```bash
honcho start
```
or
```bash
./quick_start.sh  # Choose option 2
```

### 3. Background Mode
Daemonized processes for server deployment:
```bash
./quick_start.sh  # Choose option 3
```

## Content Processing Tasks

The content motor handles several types of background tasks:

### Article Processing
- **`process_article(article_id)`**: Full article analysis pipeline
- **`process_wikipedia_article(article_id)`**: Wikipedia-specific processing
- **`scrape_and_save_article(url)`**: Scrape and process web articles

### Content Analysis
- NLP analysis using spaCy
- Reading level calculation
- Entity extraction (people, organizations)
- Tag validation via Wikipedia API

### AI Integration
- Quiz generation using Google Gemini API
- Dynamic model selection based on content complexity
- Fallback handling for API failures

### XP System Integration
- **`process_xp_transaction(transaction_data)`**: Handle XP awards/spending
- Automatic XP calculation based on quiz performance
- Transaction validation and logging

## Testing Content Processing

### Test Basic Functionality
```bash
python manage.py shell
```
```python
# Test debug task
from verifast_app.tasks import debug_task
result = debug_task.delay()
print(f"Task ID: {result.id}")

# Test article scraping
from verifast_app.tasks import scrape_and_save_article
result = scrape_and_save_article.delay('https://example.com/article')
print(f"Scraping task ID: {result.id}")
```

### Monitor Task Execution
```bash
# View Celery logs
tail -f celery.log

# View Django logs
tail -f django_access.log

# Use Celery Flower (if running)
# Visit: http://localhost:5555
```

## Prerequisites

### Required Services
- **Redis**: Message broker and result backend
- **Python 3.10+**: Runtime environment
- **Virtual Environment**: Isolated Python environment

### Required Python Packages
All dependencies are in `requirements.txt`:
- Django 5.2.4
- Celery 5.5.3
- Redis 6.2.0
- Google Generative AI 0.8.5
- spaCy 3.7.2
- newspaper3k 0.2.8

### Environment Variables
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

Key variables:
- `GEMINI_API_KEY`: Google Gemini API key for quiz generation
- `REDIS_URL`: Redis connection URL
- `CELERY_BROKER_URL`: Celery broker URL
- `DEBUG`: Set to False for production

## Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Django Web    │    │  Celery Worker  │    │   Redis Broker  │
│   Application   │◄──►│   Background    │◄──►│   Message       │
│   (Port 8000)   │    │   Processing    │    │   Queue         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   Google        │    │   Wikipedia     │
│   Database      │    │   Gemini API    │    │   API           │
│   (Articles)    │    │   (Quiz Gen)    │    │   (Tag Valid)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Troubleshooting

### Common Issues

**Redis Connection Error:**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis if needed
redis-server --daemonize yes
```

**Celery Worker Not Processing:**
```bash
# Check worker status
celery -A config.celery inspect active

# Restart worker
./quick_start.sh stop
./quick_start.sh  # Choose background mode
```

**Django Configuration Issues:**
```bash
# Check Django configuration
python manage.py check

# Apply migrations
python manage.py migrate
```

**API Quota Exceeded:**
- Check `django.log` for API errors
- Verify `GEMINI_API_KEY` in `.env`
- Monitor API usage in Google Cloud Console

### Log Files
- `celery.log`: Celery worker logs
- `django_access.log`: Django access logs
- `django_error.log`: Django error logs
- `honcho.log`: Honcho process management logs

### Performance Monitoring
```bash
# Monitor system resources
htop

# Monitor Redis
redis-cli monitor

# Monitor Celery with Flower
celery -A config.celery flower
# Visit: http://localhost:5555
```

## Production Deployment

For production deployment:

1. Use `gunicorn` instead of Django dev server
2. Configure proper logging
3. Set up process monitoring (systemd, supervisor)
4. Use Redis as a service
5. Configure proper security settings
6. Set up SSL/TLS certificates

Example systemd service files are available in the `docs/` directory.

## Development Tips

- Use development mode for debugging
- Monitor logs in real-time during development
- Test individual tasks in Django shell
- Use Celery Flower for task monitoring
- Keep Redis running as a service for convenience

## Support

For issues or questions:
1. Check the logs first
2. Verify all prerequisites are met
3. Test with the debug task
4. Check the Django admin for article processing status
5. Review the comprehensive documentation in `documentation/`