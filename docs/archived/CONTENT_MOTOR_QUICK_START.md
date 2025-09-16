# VeriFast Content Motor - Quick Start Guide

The Content Motor is your automated article acquisition system that finds and processes articles from various sources like RSS feeds and news APIs.

## 🚀 Quick Start (3 Steps)

### Step 1: Setup Content Sources
```bash
# Create sample RSS sources (free, no API key needed)
python manage.py setup_content_sources --create-sample-rss

# OR with NewsData.io API (more articles, requires API key)
python manage.py setup_content_sources --create-sample-rss --newsdata-api-key YOUR_API_KEY
```

### Step 2: Start the Content Motor
```bash
# Test what would happen (dry run)
python manage.py start_content_motor --dry-run

# Start content acquisition
python manage.py start_content_motor --orchestrate
```

### Step 3: Monitor Progress
- **Django Admin**: Go to `/admin/verifast_app/contentacquisitionjob/`
- **Article List**: Check `/admin/verifast_app/article/` for new articles
- **Logs**: `tail -f celery.log` to see real-time processing

## 🎯 Using the Admin Interface

### Method 1: Admin Action Button
1. Go to **Django Admin** → **Articles**
2. Select any article (or none)
3. Choose **Actions** → **🚀 Start Content Motor - Find New Articles**
4. Click **Go**

### Method 2: Content Sources Admin
1. Go to **Django Admin** → **Content Sources**
2. View/edit your configured sources
3. Use **Actions** → **Trigger manual acquisition**
4. Or click individual **Acquire** buttons

### Method 3: Content Acquisition Dashboard
1. Go to `/admin/verifast_app/contentsource/dashboard/`
2. View overall statistics and health
3. Use the **Manual Orchestration** interface

## 📊 Understanding the System

### Content Sources
- **RSS Feeds**: Free, reliable, but limited articles
- **NewsData.io API**: More articles, requires API key (200 free requests/day)
- **Web Scrapers**: Custom scrapers for specific sites

### Processing Pipeline
1. **Acquisition**: Fetch articles from sources
2. **Deduplication**: Skip articles we already have
3. **Quality Filtering**: Ensure articles meet minimum standards
4. **Content Processing**: Extract text, analyze reading level
5. **AI Processing**: Generate quizzes using Gemini API
6. **Storage**: Save to database with tags and metadata

### Rate Limiting
- Sources have built-in rate limiting to respect API limits
- Failed sources are temporarily disabled
- Health monitoring prevents overuse

## 🛠️ Configuration

### Environment Variables (.env)
```bash
# NewsData.io API (optional but recommended)
NEWSDATA_API_KEY=your_api_key_here

# Content acquisition settings
MAX_ARTICLES_PER_SOURCE=20
CONTENT_QUALITY_THRESHOLD=0.7
ENABLE_CONTENT_ACQUISITION=true
```

### Content Source Configuration
Each source has:
- **Rate Limits**: Requests per hour/day
- **Priority**: High/Normal/Low processing priority
- **Language**: English, Spanish, or both
- **Status**: Active/Inactive/Error/Maintenance

## 📈 Monitoring & Troubleshooting

### Check Source Health
```bash
# View source status
python manage.py start_content_motor --dry-run

# Test specific sources
python manage.py start_content_motor --sources "BBC News RSS" --dry-run
```

### Common Issues

**No articles found:**
- Check if sources are active: Admin → Content Sources
- Verify API keys in source configuration
- Check rate limits haven't been exceeded

**Processing failures:**
- Ensure Celery worker is running: `celery -A config.celery worker`
- Check Gemini API key is configured
- Monitor logs: `tail -f celery.log`

**Duplicate articles:**
- System automatically detects and skips duplicates
- Check Content Fingerprints in admin for duplicate tracking

### Health Monitoring
- **Health Score**: 0-100 score based on recent success rate
- **Consecutive Failures**: Automatic disabling after 5 failures
- **Last Successful Fetch**: Shows when source last worked

## 🔧 Advanced Usage

### Custom Acquisition
```bash
# Specific languages only
python manage.py start_content_motor --languages en --max-articles 10

# Specific sources only
python manage.py start_content_motor --sources "BBC News RSS" "Reuters World News"

# Force acquisition (ignore health checks)
python manage.py start_content_motor --force
```

### Scheduled Acquisition
Add to your crontab or task scheduler:
```bash
# Every 2 hours
0 */2 * * * cd /path/to/verifast && python manage.py start_content_motor --orchestrate

# Daily at 6 AM
0 6 * * * cd /path/to/verifast && python manage.py start_content_motor --orchestrate --max-articles 50
```

### API Integration
You can also trigger acquisition programmatically:
```python
from verifast_app.tasks_content_acquisition import acquire_content_from_source
from verifast_app.models_content_acquisition import ContentSource

# Trigger specific source
source = ContentSource.objects.get(name="BBC News RSS")
task = acquire_content_from_source.delay(source.id, 'api', 15)
```

## 📚 Getting External API Keys (Optional but Recommended)

### NewsData.io API (200 requests/day free)
1. Go to [NewsData.io](https://newsdata.io/)
2. Sign up for free account
3. Get your API key from dashboard
4. Add to `.env`: `NEWSDATA_API_KEY=your_key_here`

### GNews API (100 requests/day free)
1. Go to [GNews.io](https://gnews.io/)
2. Sign up for free account
3. Get your API key from dashboard
4. Add to `.env`: `GNEWS_API_KEY=your_key_here`

### NewsAPI.org (1000 requests/day free)
1. Go to [NewsAPI.org](https://newsapi.org/)
2. Sign up for free account
3. Get your API key from dashboard
4. Add to `.env`: `NEWSAPI_KEY=your_key_here`

### Setup All APIs at Once
```bash
python manage.py setup_content_sources \
  --create-sample-rss \
  --newsdata-api-key YOUR_NEWSDATA_KEY \
  --gnews-api-key YOUR_GNEWS_KEY \
  --newsapi-key YOUR_NEWSAPI_KEY
```

## 🎯 Best Practices

1. **Start Small**: Begin with RSS sources, add API sources later
2. **Monitor Health**: Check source health scores regularly
3. **Respect Limits**: Don't exceed API rate limits
4. **Quality First**: Better to have fewer high-quality articles
5. **Regular Maintenance**: Clean up old fingerprints and failed jobs

## 📞 Support

If you encounter issues:
1. Check the logs: `tail -f celery.log django.log`
2. Verify all services are running: `./quick_start.sh status`
3. Test individual components: `python manage.py start_content_motor --dry-run`
4. Check admin interfaces for detailed error messages

---

**Happy content acquisition! 🚀📰**