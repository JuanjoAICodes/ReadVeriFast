# API Setup and Configuration Guide

This guide covers how to set up and configure all external services required for VeriFast to function properly.

## Required API Keys

### Google Gemini API

The Google Gemini API is used for AI-powered quiz generation and content analysis.

#### Setup Steps:

1. **Visit Google AI Studio**
   - Go to [https://ai.google.dev/](https://ai.google.dev/)
   - Sign in with your Google account

2. **Create an API Key**
   - Click on "Get API key" or "Create API key"
   - Choose "Create API key in new project" or select an existing project
   - Copy the generated API key

3. **Configure in VeriFast**
   - Add the API key to your `.env` file:
     ```
     GEMINI_API_KEY=your-actual-api-key-here
     ```

4. **Test the Configuration**
   - Run the health check: `curl http://localhost:8000/health/`
   - Verify that `google_ai` service shows as "healthy"

#### Usage Limits:
- Free tier: 15 requests per minute, 1,500 requests per day
- For production use, consider upgrading to a paid plan

## Service Configuration

### NLP Services (spaCy)

VeriFast uses spaCy for natural language processing and entity extraction.

#### Required Models:
```bash
# Install English model
python -m spacy download en_core_web_sm

# Install Spanish model  
python -m spacy download es_core_news_sm
```

#### Configuration Options:
```env
SPACY_MODEL_EN=en_core_web_sm
SPACY_MODEL_ES=es_core_news_sm
ENABLE_NLP_FEATURES=true
```

### Wikipedia API

Used for tag validation and content enrichment.

#### Configuration:
```env
WIKIPEDIA_USER_AGENT=VeriFastApp/1.0
WIKIPEDIA_RATE_LIMIT=10
ENABLE_WIKIPEDIA_VALIDATION=true
```

#### Rate Limiting:
- Default: 10 requests per second
- Adjust `WIKIPEDIA_RATE_LIMIT` based on your needs
- Be respectful of Wikipedia's servers

### Article Scraping (newspaper3k)

For extracting content from web articles.

#### Configuration:
```env
ENABLE_ARTICLE_SCRAPING=true
```

#### Dependencies:
- Automatically installs with requirements.txt
- Requires `lxml_html_clean` for HTML processing

## Feature Flags

Control which services are enabled:

```env
# AI Features
ENABLE_AI_FEATURES=true
AI_FALLBACK_MODE=graceful

# NLP Features  
ENABLE_NLP_FEATURES=true

# External APIs
ENABLE_WIKIPEDIA_VALIDATION=true
ENABLE_ARTICLE_SCRAPING=true
```

### Graceful Degradation

When `AI_FALLBACK_MODE=graceful`, the system will:
- Continue functioning even if external APIs fail
- Log errors but not crash the application
- Return empty results instead of throwing exceptions

## Performance Configuration

### Processing Limits:
```env
MAX_ARTICLE_LENGTH=100000
PROCESSING_TIMEOUT=300
CONCURRENT_WORKERS=4
```

### Redis/Celery:
```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Health Monitoring

### Health Check Endpoint:
- URL: `http://localhost:8000/health/`
- Returns status of all services
- Use for monitoring and alerting

### Configuration:
```env
HEALTH_CHECK_INTERVAL=300
LOG_SERVICE_ERRORS=true
```

## Troubleshooting

### Common Issues:

1. **Google AI API Errors**
   - Verify API key is correct
   - Check quota limits in Google Cloud Console
   - Ensure billing is enabled for paid features

2. **spaCy Model Errors**
   - Run: `python -m spacy download en_core_web_sm`
   - Check virtual environment is activated
   - Verify model compatibility with spaCy version

3. **Wikipedia API Timeouts**
   - Reduce `WIKIPEDIA_RATE_LIMIT`
   - Check internet connectivity
   - Consider caching frequently accessed pages

4. **Article Scraping Failures**
   - Install missing dependencies: `pip install lxml_html_clean`
   - Check if target websites block scraping
   - Verify newspaper3k compatibility

### Validation Script:

Run the dependency validation script to check all services:
```bash
python scripts/validate_dependencies.py
```

### Health Check:

Monitor service health:
```bash
curl http://localhost:8000/health/ | python -m json.tool
```

## Production Considerations

### Security:
- Never commit API keys to version control
- Use environment variables or secret management
- Rotate API keys regularly

### Performance:
- Monitor API usage and costs
- Implement caching for frequently accessed data
- Scale Celery workers based on load

### Monitoring:
- Set up alerts for service failures
- Monitor API quota usage
- Track processing times and success rates

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | None | Yes |
| `ENABLE_AI_FEATURES` | Enable AI processing | true | No |
| `ENABLE_NLP_FEATURES` | Enable NLP processing | true | No |
| `ENABLE_WIKIPEDIA_VALIDATION` | Enable Wikipedia tag validation | true | No |
| `ENABLE_ARTICLE_SCRAPING` | Enable article scraping | true | No |
| `SPACY_MODEL_EN` | English spaCy model | en_core_web_sm | No |
| `SPACY_MODEL_ES` | Spanish spaCy model | es_core_news_sm | No |
| `WIKIPEDIA_USER_AGENT` | User agent for Wikipedia API | VeriFastApp/1.0 | No |
| `WIKIPEDIA_RATE_LIMIT` | Wikipedia API rate limit | 10 | No |
| `MAX_ARTICLE_LENGTH` | Maximum article length | 100000 | No |
| `PROCESSING_TIMEOUT` | Processing timeout (seconds) | 300 | No |
| `CONCURRENT_WORKERS` | Celery worker count | 4 | No |