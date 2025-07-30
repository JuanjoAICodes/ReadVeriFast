# VeriFast - Consolidated Development Guide
*Unified Development Standards & Best Practices*  
*Last Updated: July 27, 2025*

## Overview

This consolidated guide combines all development standards, architectural patterns, and best practices for VeriFast development. It serves as the single source of truth for all development activities, whether using Kiro IDE, Gemini CLI, or other development tools.

## 1. Technology Stack & Architecture

### Core Technologies
- **Backend**: Django 5.2.4 with Python 3.10+
- **Database**: PostgreSQL (production), SQLite (development)
- **Frontend**: Django Templates + PicoCSS + HTMX + Alpine.js (minimal)
- **Background Processing**: Celery with Redis broker
- **AI Integration**: Google Gemini API
- **External APIs**: Wikipedia API, newspaper3k
- **Development Tools**: ruff, mypy, django-environ

### Architecture Principles
1. **Django Apps Pattern**: Modular application structure
2. **Service Layer**: Business logic separated from views
3. **Component-Based Frontend**: Reusable JavaScript classes
4. **API-First Design**: REST endpoints for all interactions
5. **Background Processing**: Asynchronous task handling
6. **Caching Strategy**: Redis for performance optimization

## 2. Project Structure Standards

### Directory Organization
```
verifast/
├── config/                 # Django project configuration
│   ├── settings.py        # Environment-based settings
│   ├── urls.py           # Root URL routing
│   ├── celery.py         # Background task config
│   └── wsgi.py/asgi.py   # Server interfaces
├── verifast_app/          # Main application
│   ├── models.py         # Database models
│   ├── views.py          # View controllers
│   ├── services.py       # Business logic
│   ├── xp_system.py      # Gamification engine
│   ├── tasks.py          # Celery background tasks
│   ├── api_views.py      # REST API endpoints
│   ├── templates/        # HTML templates
│   ├── static/           # CSS, JavaScript, images
│   └── migrations/       # Database migrations
├── documentation/        # Consolidated documentation
├── .kiro/               # Kiro IDE specifications
└── requirements.txt     # Python dependencies
```

### File Naming Conventions
- **Python Files**: snake_case.py
- **Templates**: snake_case.html
- **Static Files**: kebab-case.css, kebab-case.js
- **URLs**: kebab-case patterns, snake_case names
- **Classes**: PascalCase
- **Functions/Variables**: snake_case
- **Constants**: UPPER_SNAKE_CASE

## 3. Development Workflow

### Spec-Based Development Process
1. **Requirements Phase**: Create requirements.md with EARS format
2. **Design Phase**: Create design.md with technical architecture
3. **Implementation Phase**: Create tasks.md with Kiro checkbox format
4. **Execution Phase**: Implement tasks one at a time
5. **Review Phase**: Code review and quality assurance
6. **Documentation Phase**: Update relevant documentation

### Task Format Standards
```markdown
- [ ] 1. Create authentication models
  - Implement CustomUser model with required fields
  - Add authentication middleware configuration
  - Create user registration and login views
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 2. Implement XP system integration
  - [ ] 2.1 Create XPTransaction model
    - Define transaction types and sources
    - Add balance validation logic
    - _Requirements: 2.1_
  - [ ] 2.2 Integrate with quiz system
    - Calculate XP rewards based on performance
    - Update user statistics
    - _Requirements: 2.2_
```

### Git Workflow
- **Feature Branches**: `feature/feature-name`
- **Bug Fixes**: `fix/bug-description`
- **Documentation**: `docs/update-description`
- **Commit Messages**: Conventional commits format
- **Pull Requests**: Required for all changes
- **Code Review**: Mandatory before merging

## 4. Code Quality Standards

### Python Code Standards
```python
# Model example with proper documentation
class CustomUser(AbstractUser):
    """Extended user model with gamification features.
    
    Attributes:
        current_wpm: User's current reading speed
        total_xp: Accumulated experience points
        current_xp_points: Spendable experience points
    """
    current_wpm: models.PositiveIntegerField = models.PositiveIntegerField(
        default=250,
        help_text=_("User's current words-per-minute reading speed."),
        verbose_name=_("Current WPM")
    )
    
    def can_afford(self, cost: int) -> bool:
        """Check if user has sufficient XP for purchase.
        
        Args:
            cost: XP cost of the item
            
        Returns:
            True if user can afford the cost
        """
        return self.current_xp_points >= cost
```

### JavaScript Code Standards
```javascript
/**
 * Speed Reader class for word-by-word reading functionality
 */
class SpeedReader {
    /**
     * Initialize speed reader with section ID
     * @param {string} sectionId - DOM element ID containing the reader
     */
    constructor(sectionId) {
        this.section = document.getElementById(sectionId);
        this.words = [];
        this.currentIndex = 0;
        this.isRunning = false;
        this.wpm = 250;
        
        this.init();
    }
    
    /**
     * Initialize the speed reader components
     * @private
     */
    init() {
        if (!this.validateElements()) {
            console.error('Speed Reader: Essential elements missing');
            return;
        }
        
        this.loadContent();
        this.attachEventListeners();
        console.log('Speed Reader: Initialized successfully');
    }
}
```

### CSS Code Standards
```css
/* Component-based CSS with BEM-like naming */
.speed-reader-section {
    margin: var(--spacing-lg) 0;
    padding: var(--spacing-lg);
    border: 1px solid var(--muted-border-color);
    border-radius: var(--border-radius);
    background-color: var(--card-background-color);
}

.speed-reader__word-display {
    min-height: 4rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    text-align: center;
    padding: var(--spacing-md);
    border: 2px solid var(--primary);
    border-radius: var(--border-radius);
    background-color: var(--background-color);
}

.speed-reader__word-display--immersive {
    font-size: 4rem;
    color: #ffffff;
    background-color: transparent;
    border: none;
}
```

## 5. Database Design Standards

### Model Design Principles
1. **Descriptive Field Names**: Clear, unambiguous field names
2. **Help Text**: All fields must have descriptive help_text
3. **Proper Relationships**: Use appropriate ForeignKey/ManyToMany
4. **Indexes**: Add indexes for frequently queried fields
5. **Constraints**: Use database constraints for data integrity

### Migration Best Practices
```python
# Example migration with proper structure
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('verifast_app', '0004_previous_migration'),
    ]
    
    operations = [
        migrations.AddField(
            model_name='customuser',
            name='has_premium_feature',
            field=models.BooleanField(
                default=False,
                help_text='User has purchased premium feature access'
            ),
        ),
        migrations.AddIndex(
            model_name='customuser',
            index=models.Index(
                fields=['has_premium_feature'],
                name='idx_user_premium_feature'
            ),
        ),
    ]
```

## 6. Frontend Development Standards

### Template Structure
```html
{% extends 'verifast_app/base.html' %}
{% load static %}
{% load i18n %}

{% block title %}{{ article.title }} - {{ block.super }}{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'verifast_app/css/article-detail.css' %}">
{% endblock %}

{% block content %}
<main class="container" role="main">
    <article class="article-detail">
        <header class="article-detail__header">
            <h1>{{ article.title }}</h1>
        </header>
        
        <section class="speed-reader-section" 
                 data-content="{{ article.content|escape }}"
                 data-user-wpm="{{ user_wpm|default:250 }}">
            <!-- Speed reader interface -->
        </section>
    </article>
</main>
{% endblock %}

{% block extra_js %}
<script src="{% static 'verifast_app/js/speed-reader.js' %}"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    const speedReader = new SpeedReader('speed-reader-section');
});
</script>
{% endblock %}
```

### Internationalization Standards
```html
<!-- Static text translation -->
<h1>{% trans "Speed Reader" %}</h1>

<!-- Dynamic content translation -->
<p>{% blocktrans with speed=user_wpm %}Reading at {{ speed }} WPM{% endblocktrans %}</p>

<!-- Context for translators -->
<button aria-label="{% trans 'Start reading this article' context 'speed reader button' %}">
    {% trans "Start" %}
</button>
```

### JavaScript Internationalization
```javascript
// Global translation function
function _(key, params = {}) {
    return window.i18n ? window.i18n._(key, params) : key;
}

// Usage in components
class SpeedReader {
    showError(message) {
        this.wordDisplay.textContent = _(message);
    }
    
    updateButton() {
        this.startPauseBtn.textContent = this.isRunning ? 
            _('pause_reading') : _('start_reading');
    }
}
```

## 7. API Development Standards

### REST API Design
```python
# API view example with proper structure
class QuizSubmissionAPIView(LoginRequiredMixin, View):
    """Handle quiz submission and scoring."""
    
    def post(self, request):
        """Submit quiz answers and calculate score.
        
        Request Format:
            {
                "article_id": 123,
                "user_answers": [0, 2, 1, 3, 0],
                "wpm_used": 300,
                "quiz_time_seconds": 120
            }
            
        Response Format:
            {
                "success": true,
                "score": 80,
                "xp_awarded": 150,
                "feedback": {...}
            }
        """
        try:
            data = json.loads(request.body)
            
            # Validate input data
            article = get_object_or_404(Article, id=data.get('article_id'))
            user_answers = data.get('user_answers', [])
            wpm_used = int(data.get('wpm_used', 0))
            
            # Process quiz submission
            result = QuizResultProcessor.process_submission(
                user=request.user,
                article=article,
                answers=user_answers,
                wpm_used=wpm_used
            )
            
            return JsonResponse({
                'success': True,
                'score': result['score'],
                'xp_awarded': result['xp_awarded'],
                'feedback': result['feedback']
            })
            
        except Exception as e:
            logger.error(f"Quiz submission error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
```

### API Response Standards
```python
# Standardized API response format
def api_response(success=True, data=None, message=None, errors=None, status=200):
    """Create standardized API response."""
    response_data = {
        'success': success,
        'timestamp': timezone.now().isoformat(),
    }
    
    if data is not None:
        response_data['data'] = data
    if message:
        response_data['message'] = message
    if errors:
        response_data['errors'] = errors
        
    return JsonResponse(response_data, status=status)
```

## 8. Testing Standards

### Test Structure
```python
# Model testing example
class CustomUserModelTest(TestCase):
    """Test CustomUser model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_creation_defaults(self):
        """Test user is created with correct defaults."""
        self.assertEqual(self.user.current_wpm, 250)
        self.assertEqual(self.user.total_xp, 0)
        self.assertFalse(self.user.has_2word_chunking)
    
    def test_xp_award_calculation(self):
        """Test XP award calculation logic."""
        initial_xp = self.user.total_xp
        awarded_xp = 100
        
        self.user.total_xp += awarded_xp
        self.user.current_xp_points += awarded_xp
        self.user.save()
        
        self.assertEqual(self.user.total_xp, initial_xp + awarded_xp)
        self.assertEqual(self.user.current_xp_points, awarded_xp)
```

### View Testing
```python
class ArticleViewTest(TestCase):
    """Test article-related views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.article = Article.objects.create(
            title='Test Article',
            content='Test content for reading.',
            processing_status='complete'
        )
    
    def test_article_detail_view_anonymous(self):
        """Test article detail view for anonymous users."""
        url = reverse('verifast_app:article_detail', kwargs={'pk': self.article.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)
        self.assertContains(response, 'speed-reader-section')
    
    def test_article_detail_view_authenticated(self):
        """Test article detail view for authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('verifast_app:article_detail', kwargs={'pk': self.article.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'data-user-wpm="{self.user.current_wpm}"')
```

## 9. Performance Standards

### Database Optimization
```python
# Optimized queryset examples
def get_article_list_optimized(user=None):
    """Get optimized article list with minimal queries."""
    queryset = Article.objects.filter(
        processing_status='complete'
    ).select_related('user').prefetch_related('tags')
    
    if user and user.is_authenticated:
        # Annotate with read status
        queryset = queryset.annotate(
            is_read_by_user=Exists(
                QuizAttempt.objects.filter(
                    user=user,
                    article=OuterRef('pk')
                )
            )
        ).order_by('is_read_by_user', '-timestamp')
    
    return queryset

# Use select_related for ForeignKey relationships
user_stats = CustomUser.objects.select_related('profile').get(id=user_id)

# Use prefetch_related for ManyToMany relationships
articles = Article.objects.prefetch_related('tags', 'comments').all()
```

### Caching Strategy
```python
from django.core.cache import cache
from django.views.decorators.cache import cache_page

# View-level caching
@cache_page(60 * 15)  # Cache for 15 minutes
def article_list_view(request):
    return render(request, 'article_list.html', context)

# Template fragment caching
{% load cache %}
{% cache 500 article_sidebar article.id %}
    <!-- Expensive sidebar content -->
{% endcache %}

# Low-level caching
def get_popular_tags():
    cache_key = 'popular_tags'
    tags = cache.get(cache_key)
    
    if tags is None:
        tags = Tag.objects.annotate(
            article_count=Count('article')
        ).order_by('-article_count')[:10]
        cache.set(cache_key, tags, 60 * 60)  # Cache for 1 hour
    
    return tags
```

## 10. Security Standards

### Input Validation
```python
from django.core.exceptions import ValidationError
from django.utils.html import escape

def validate_quiz_submission(data):
    """Validate quiz submission data."""
    required_fields = ['article_id', 'user_answers', 'wpm_used']
    
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")
    
    # Validate article exists
    try:
        article = Article.objects.get(id=data['article_id'])
    except Article.DoesNotExist:
        raise ValidationError("Invalid article ID")
    
    # Validate WPM range
    wpm = int(data['wpm_used'])
    if not (50 <= wpm <= 1000):
        raise ValidationError("WPM must be between 50 and 1000")
    
    return True
```

### XSS Prevention
```html
<!-- Always escape user content -->
<div class="comment-content">
    {{ comment.content|escape }}
</div>

<!-- Use safe filter only for trusted content -->
<div class="article-content">
    {{ article.content|safe }}
</div>
```

### CSRF Protection
```javascript
// Include CSRF token in AJAX requests
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

fetch('/api/quiz/submit/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify(data)
});
```

## 11. Deployment Standards

### Environment Configuration
```python
# settings.py - Environment-based configuration
import os
from pathlib import Path

def get_env(key, default=None, cast_type=str):
    """Get environment variable with type casting."""
    value = os.environ.get(key, default)
    if cast_type is bool and isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return cast_type(value) if value is not None else default

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': get_env('DB_NAME', 'verifast_db'),
        'USER': get_env('DB_USER', 'verifast_user'),
        'PASSWORD': get_env('DB_PASSWORD'),
        'HOST': get_env('DB_HOST', 'localhost'),
        'PORT': get_env('DB_PORT', '5432'),
    }
}

# Security settings for production
if not get_env('DEBUG', True, bool):
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

### Production Checklist
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] SSL certificates installed
- [ ] Backup procedures tested
- [ ] Monitoring configured
- [ ] Log rotation setup
- [ ] Security headers configured
- [ ] Error tracking enabled
- [ ] Performance monitoring active

## 12. Multi-Developer Coordination

### Conflict Prevention
1. **Spec Assignment**: Check active specs before starting work
2. **Feature Branches**: Use separate branches for each feature
3. **Communication**: Document decisions in specs and code comments
4. **Integration Points**: Coordinate changes to shared components

### Code Review Process
1. **Self Review**: Review your own code before submitting
2. **Automated Checks**: Ensure all tests pass and code is formatted
3. **Peer Review**: At least one other developer must review
4. **Documentation**: Update relevant documentation with changes
5. **Testing**: Verify changes work in staging environment

### Integration Guidelines
- **XP System**: Use `XPTransactionManager` for all XP operations
- **Tag System**: Validate tags through Wikipedia API integration
- **Quiz System**: Follow existing Gemini API patterns
- **User System**: Extend `CustomUser` model appropriately
- **Frontend**: Maintain PicoCSS compatibility and accessibility

## 13. Monitoring & Maintenance

### Logging Standards
```python
import logging

logger = logging.getLogger(__name__)

# Log levels and usage
logger.debug("Detailed information for debugging")
logger.info("General information about system operation")
logger.warning("Something unexpected happened but system continues")
logger.error("Serious problem occurred")
logger.critical("Very serious error occurred")

# Structured logging
logger.info("User quiz completed", extra={
    'user_id': user.id,
    'article_id': article.id,
    'score': score,
    'xp_awarded': xp_awarded
})
```

### Health Monitoring
```python
# Health check endpoint
def health_check(request):
    """System health check endpoint."""
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'services': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['services']['database'] = 'healthy'
    except Exception as e:
        health_status['services']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Redis check
    try:
        cache.set('health_check', 'ok', 10)
        health_status['services']['redis'] = 'healthy'
    except Exception as e:
        health_status['services']['redis'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)
```

## 14. Common Development Commands

### Setup Commands
```bash
# Environment setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Database operations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic

# Development server
python manage.py runserver

# Background tasks
celery -A config worker --loglevel=info
redis-server
```

### Code Quality Commands
```bash
# Format and lint
ruff format .
ruff check .
mypy .

# Testing
python manage.py test
coverage run --source='.' manage.py test
coverage report

# Database
python manage.py makemigrations
python manage.py migrate
python manage.py shell
```

This consolidated development guide serves as the definitive reference for all VeriFast development activities, ensuring consistency and quality across all contributions.

---

*This guide is maintained by the VeriFast development team and updated regularly to reflect current best practices and standards.*