# VeriFast Project Architecture Guide

## Overview
VeriFast is a Django-based web application that provides speed reading functionality with gamification elements. Users can read articles at configurable speeds, take comprehension quizzes, earn XP points, and interact with a community through comments and social features.

## Technology Stack

### Backend
- **Framework**: Django 4.x (Python web framework)
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Task Queue**: Celery with Redis/RabbitMQ
- **Authentication**: Django's built-in authentication system
- **API**: Django REST Framework (for AJAX endpoints)

### Frontend
- **Template Engine**: Django Templates with Jinja2-like syntax
- **CSS Framework**: PicoCSS (lightweight, semantic CSS framework)
- **JavaScript**: Vanilla ES6+ (no external frameworks)
- **Icons**: Unicode emojis and symbols
- **Responsive Design**: CSS Grid and Flexbox

### Database Schema
- **User Management**: Extended Django User model (CustomUser)
- **Content**: Articles, Tags, Comments with relationships
- **Gamification**: XP transactions, quiz attempts, feature purchases
- **Social**: Comment interactions, user profiles

## Project Structure

```
VeriFast/
├── config/                     # Django project settings
│   ├── settings.py            # Main configuration
│   ├── urls.py               # Root URL configuration
│   ├── wsgi.py               # WSGI application
│   └── asgi.py               # ASGI application
├── verifast_app/             # Main application
│   ├── models.py             # Database models
│   ├── views.py              # View controllers
│   ├── urls.py               # App URL patterns
│   ├── forms.py              # Django forms
│   ├── admin.py              # Django admin configuration
│   ├── tasks.py              # Celery background tasks
│   ├── services.py           # Business logic services
│   ├── xp_system.py          # Gamification system
│   ├── tag_analytics.py      # Tag analysis utilities
│   ├── serializers.py        # DRF serializers
│   ├── api_views.py          # API endpoints
│   ├── templatetags/         # Custom template tags
│   ├── templates/            # HTML templates
│   ├── static/               # Static files (CSS, JS, images)
│   └── migrations/           # Database migrations
├── templates/                # Global templates
├── static/                   # Global static files
├── staticfiles/              # Collected static files
├── documentation/            # Project documentation
├── .kiro/                    # Kiro IDE specifications
└── manage.py                 # Django management script
```

## Database Architecture

### Core Models

#### CustomUser (Extended Django User)
```python
class CustomUser(AbstractUser):
    # Gamification
    current_wpm = PositiveIntegerField(default=250)
    max_wpm = PositiveIntegerField(default=250)
    total_xp = PositiveIntegerField(default=0)
    current_xp_points = PositiveIntegerField(default=0)
    
    # Premium Features (Boolean flags)
    has_font_opensans = BooleanField(default=False)
    has_2word_chunking = BooleanField(default=False)
    has_smart_connector_grouping = BooleanField(default=False)
    # ... more premium features
    
    # Statistics
    perfect_quiz_count = PositiveIntegerField(default=0)
    quiz_attempts_count = PositiveIntegerField(default=0)
    
    # Personalization
    preferred_language = CharField(max_length=10, default='en')
    theme = CharField(max_length=20, default='light')
```

#### Article
```python
class Article(models.Model):
    title = CharField(max_length=200)
    content = TextField()
    url = URLField(unique=True, null=True)
    image_url = URLField(blank=True, null=True)
    
    # Content Analysis
    word_count = PositiveIntegerField(null=True, blank=True)
    reading_level = FloatField(null=True, blank=True)
    
    # Processing
    processing_status = CharField(max_length=20, default='pending')
    quiz_data = JSONField(null=True, blank=True)
    
    # Relationships
    user = ForeignKey(CustomUser, on_delete=SET_NULL, null=True)
    tags = ManyToManyField(Tag, blank=True)
    
    # Article Types
    ARTICLE_TYPE_CHOICES = [
        ('regular', 'Regular Article'),
        ('wikipedia', 'Wikipedia Article'),
    ]
    article_type = CharField(max_length=20, choices=ARTICLE_TYPE_CHOICES)
```

#### Tag System
```python
class Tag(models.Model):
    name = CharField(max_length=50, unique=True)
    slug = SlugField(max_length=50, unique=True)
    description = TextField(null=True, blank=True)
    
    # Wikipedia Integration
    wikipedia_url = URLField(null=True, blank=True)
    wikipedia_content = TextField(null=True, blank=True)
    is_validated = BooleanField(default=False)
    
    # Statistics
    article_count = PositiveIntegerField(default=0)
```

#### Gamification Models
```python
class QuizAttempt(models.Model):
    user = ForeignKey(CustomUser, on_delete=CASCADE)
    article = ForeignKey(Article, on_delete=CASCADE)
    score = FloatField()
    wpm_used = IntegerField()
    xp_awarded = IntegerField()
    result = JSONField(null=True, blank=True)
    
class XPTransaction(models.Model):
    user = ForeignKey(CustomUser, on_delete=CASCADE)
    transaction_type = CharField(max_length=5, choices=TRANSACTION_TYPES)
    amount = IntegerField()
    source = CharField(max_length=20, choices=SOURCES)
    description = TextField()
    balance_after = PositiveIntegerField()
```

## Backend Architecture

### View Layer Structure

#### Class-Based Views
```python
# Main article views
class ArticleDetailView(DetailView):
    model = Article
    template_name = 'verifast_app/article_detail.html'
    
    def get_context_data(self, **kwargs):
        # Add user-specific context
        # Handle authentication states
        # Add owned features for premium users
        
class ArticleListView(ListView):
    model = Article
    
    def get_queryset(self):
        # Sort by read/unread status for authenticated users
        # Filter by processing status
```

#### API Views (Django REST Framework)
```python
class QuizSubmissionAPIView(LoginRequiredMixin, View):
    def post(self, request):
        # Process quiz submissions via AJAX
        # Calculate scores and XP rewards
        # Return JSON response
```

### Service Layer

#### XP System (`xp_system.py`)
```python
class QuizResultProcessor:
    @staticmethod
    def process_quiz_completion(quiz_attempt, article, user):
        # Calculate XP based on score, WPM, reading level
        # Handle perfect score bonuses
        # Update user statistics
        
class PremiumFeatureStore:
    @staticmethod
    def purchase_feature(user, feature_key):
        # Validate XP balance
        # Unlock premium features
        # Record transactions
```

#### Content Processing (`tasks.py`)
```python
@shared_task
def scrape_and_save_article(url):
    # Background task for article processing
    # Extract content, generate summaries
    # Create quiz questions using LLM
    # Update processing status
```

### URL Configuration

#### Main URLs (`config/urls.py`)
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('verifast_app.urls')),
    path('api/', include('verifast_app.api_urls')),
]
```

#### App URLs (`verifast_app/urls.py`)
```python
urlpatterns = [
    path('', views.index, name='index'),
    path('articles/', views.ArticleListView.as_view(), name='article_list'),
    path('article/<int:pk>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('tags/<str:tag_name>/', views.TagDetailView.as_view(), name='tag_detail'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    # ... more URL patterns
]
```

## Frontend Architecture

### Template Hierarchy

#### Base Template (`base.html`)
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <!-- PicoCSS framework -->
    <!-- Custom CSS variables -->
    <!-- Meta tags for responsive design -->
</head>
<body>
    <nav><!-- Global navigation --></nav>
    <main>
        {% block content %}{% endblock %}
    </main>
    <footer><!-- Global footer --></footer>
    
    <!-- JavaScript blocks -->
    {% block extra_js %}{% endblock %}
</body>
</html>
```

#### Article Detail Template Structure
```html
{% extends 'verifast_app/base.html' %}

{% block content %}
<main class="article-detail" role="main">
    <!-- Article Header -->
    <header class="article-header">
        <!-- Title, image, tags, metadata -->
    </header>
    
    <!-- Speed Reader Section -->
    <section class="speed-reader-section" data-content="{{ article.content|escape }}">
        <!-- Word display, controls, progress -->
    </section>
    
    <!-- Quiz Modal -->
    <div id="quiz-modal" class="quiz-modal">
        <!-- Quiz interface -->
    </div>
    
    <!-- Comments Section -->
    <section class="comments-section">
        <!-- Comment forms and display -->
    </section>
</main>
{% endblock %}
```

### JavaScript Architecture

#### Speed Reader Class
```javascript
class SpeedReader {
    constructor() {
        this.words = [];
        this.currentIndex = 0;
        this.isPlaying = false;
        this.wpm = 250;
        this.interval = null;
        this.isImmersive = false;
    }
    
    // Content parsing and display methods
    parseContent(content) { /* Parse article content */ }
    updateDisplay() { /* Update word display and progress */ }
    
    // Playback control methods
    play() { /* Start reading */ }
    pause() { /* Pause reading */ }
    reset() { /* Reset to beginning */ }
    
    // User interaction methods
    adjustSpeed(delta) { /* Change WPM */ }
    toggleImmersive() { /* Enter/exit fullscreen */ }
    
    // Event handling
    bindEvents() { /* Keyboard shortcuts, button clicks */ }
}
```

### CSS Architecture

#### Design System
```css
:root {
    /* Color scheme */
    --primary: #007bff;
    --secondary: #6c757d;
    --success: #28a745;
    --danger: #dc3545;
    
    /* Typography */
    --font-family: system-ui, sans-serif;
    --font-size-base: 1rem;
    --line-height-base: 1.5;
    
    /* Spacing */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 2rem;
    
    /* Layout */
    --border-radius: 0.375rem;
    --border-width: 1px;
    --container-max-width: 1200px;
}
```

#### Component Styles
```css
/* Speed Reader Component */
.speed-reader-section {
    background: var(--card-background-color);
    padding: 2rem;
    border-radius: var(--border-radius);
    margin-bottom: 2rem;
}

.word-display {
    font-size: 3rem;
    text-align: center;
    padding: 2rem;
    min-height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Responsive Design */
@media (max-width: 768px) {
    .word-display {
        font-size: 2rem;
        padding: 1rem;
    }
}
```

## Development Workflow

### Setting Up Development Environment

1. **Clone Repository**
```bash
git clone <repository-url>
cd verifast
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Database Setup**
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

5. **Run Development Server**
```bash
python manage.py runserver
```

### Key Development Commands

```bash
# Database operations
python manage.py makemigrations
python manage.py migrate
python manage.py shell

# Static files
python manage.py collectstatic
python manage.py findstatic <filename>

# Testing
python manage.py test
python manage.py test verifast_app.tests.TestSpeedReader

# Background tasks (if using Celery)
celery -A config worker --loglevel=info
```

### File Modification Guidelines

#### When Adding New Features:

1. **Models**: Add to `verifast_app/models.py`
   - Create migration: `python manage.py makemigrations`
   - Apply migration: `python manage.py migrate`

2. **Views**: Add to `verifast_app/views.py`
   - Follow class-based view patterns
   - Add proper error handling
   - Include authentication checks

3. **Templates**: Add to `verifast_app/templates/verifast_app/`
   - Extend base template
   - Use semantic HTML
   - Include accessibility features

4. **URLs**: Update `verifast_app/urls.py`
   - Follow RESTful patterns
   - Use descriptive names

5. **Static Files**: Add to `verifast_app/static/verifast_app/`
   - CSS in `css/` subdirectory
   - JavaScript in `js/` subdirectory
   - Images in `images/` subdirectory

### Testing Strategy

#### Template Testing
```python
from django.test import TestCase
from django.template.loader import render_to_string

class TemplateTests(TestCase):
    def test_article_detail_renders(self):
        html = render_to_string('verifast_app/article_detail.html', context)
        self.assertIn('SpeedReader', html)
```

#### View Testing
```python
class ArticleDetailViewTests(TestCase):
    def test_article_detail_view(self):
        response = self.client.get(f'/article/{self.article.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)
```

#### JavaScript Testing
- Use browser developer tools for debugging
- Test keyboard shortcuts in immersive mode
- Verify responsive design on different screen sizes

## Deployment Architecture

### Production Settings
```python
# config/settings.py
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'verifast_db',
        'USER': 'verifast_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Static files
STATIC_ROOT = '/var/www/verifast/static/'
MEDIA_ROOT = '/var/www/verifast/media/'
```

### Server Configuration
- **Web Server**: Nginx (reverse proxy, static files)
- **Application Server**: Gunicorn (WSGI server)
- **Database**: PostgreSQL
- **Cache**: Redis (for sessions, Celery broker)
- **Background Tasks**: Celery workers

### Security Considerations
- CSRF protection enabled
- XSS prevention with template escaping
- SQL injection protection via Django ORM
- User input validation
- Rate limiting for API endpoints

## Integration Points

### External Services
- **LLM Integration**: For quiz generation and content analysis
- **Wikipedia API**: For tag-based article fetching
- **Email Service**: For user notifications (optional)

### API Endpoints
```python
# Quiz submission
POST /api/quiz/submit/
{
    "article_id": 123,
    "user_answers": {...},
    "wpm_used": 300,
    "quiz_time_seconds": 120
}

# Feature purchase
POST /api/features/purchase/
{
    "feature_key": "has_2word_chunking"
}
```

## Performance Considerations

### Database Optimization
- Indexes on frequently queried fields
- Select_related and prefetch_related for relationships
- Database connection pooling

### Frontend Optimization
- Lazy loading for images
- Minified CSS and JavaScript
- Progressive enhancement
- Responsive images

### Caching Strategy
- Template fragment caching
- Database query caching
- Static file caching with proper headers

## Troubleshooting Guide

### Common Issues

1. **Template Syntax Errors**
   - Check for missing `{% endif %}` tags
   - Verify proper nesting of conditional blocks
   - Use `python manage.py check` for validation

2. **JavaScript Errors**
   - Check browser console for errors
   - Verify DOM elements exist before binding events
   - Test with different browsers

3. **Database Issues**
   - Run `python manage.py migrate` after model changes
   - Check for migration conflicts
   - Verify database permissions

4. **Static Files Not Loading**
   - Run `python manage.py collectstatic`
   - Check STATIC_URL and STATIC_ROOT settings
   - Verify web server configuration

### Debug Mode
```python
# Enable debug mode for development
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
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
```

This architecture guide provides a comprehensive foundation for understanding and building upon the VeriFast project. Follow these patterns and conventions to maintain consistency and ensure the application scales properly.