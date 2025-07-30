# VeriFast - Technical Specification

## Architecture Overview

VeriFast is built using Django with a modular architecture designed for scalability and maintainability. The system uses asynchronous task processing for content ingestion and AI-powered analysis.

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Django App    │    │   PostgreSQL    │
│                 │◄──►│                 │◄──►│    Database     │
│  (Pico.css UI)  │    │  (Views/Models) │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Celery Worker  │◄──►│  Redis Broker   │
                       │                 │    │                 │
                       │ (Async Tasks)   │    │ (Message Queue) │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  External APIs  │
                       │                 │
                       │ • Gemini API    │
                       │ • Wikipedia API │
                       │ • News APIs     │
                       └─────────────────┘
```

## Technology Stack

### Backend Framework
- **Django 5.2.4**: Web framework with built-in ORM, admin, and authentication
- **Python 3.10**: Programming language
- **PostgreSQL**: Primary database for production
- **SQLite**: Development database

### Asynchronous Processing
- **Celery**: Distributed task queue for background processing
- **Redis**: Message broker and result backend
- **Gunicorn**: WSGI HTTP Server for production

### AI and NLP Integration
- **Google Gemini API**: Large Language Model for quiz generation and text analysis
- **spaCy 3.7.2**: Natural Language Processing library
  - `en_core_web_sm`: English language model
  - `es_core_news_sm`: Spanish language model
- **textstat**: Reading level analysis
- **Wikipedia API 0.6.0**: Entity validation and canonical name resolution

### Frontend
- **Pico.css**: Classless CSS framework for clean, semantic styling
- **Django Template Language (DTL)**: Server-side templating
- **WhiteNoise**: Static file serving
- **Vanilla JavaScript**: Client-side interactivity for speed reader and immersive mode
- **CSS3 Animations**: Smooth transitions and GPU-accelerated animations

### Content Processing
- **newspaper3k**: Web scraping for article content
- **BeautifulSoup4**: HTML parsing and cleaning

### Development Tools
- **django-environ**: Environment variable management
- **ruff**: Code linting and formatting
- **mypy**: Static type checking
- **honcho**: Process management for development

## Project Structure

```
verifast/
├── config/                 # Django project configuration
│   ├── settings.py        # Main settings file
│   ├── urls.py           # Root URL configuration
│   ├── wsgi.py           # WSGI application
│   └── celery.py         # Celery configuration
├── verifast_app/          # Main application
│   ├── models.py         # Data models
│   ├── views.py          # View controllers
│   ├── urls.py           # App URL patterns
│   ├── admin.py          # Admin interface configuration
│   ├── tasks.py          # Celery tasks
│   ├── services.py       # Business logic services
│   ├── gamification.py   # XP and gamification logic
│   ├── forms.py          # Django forms
│   ├── migrations/       # Database migrations
│   └── templates/        # HTML templates
├── core/                  # Secondary app (minimal usage)
├── static/               # Static files (CSS, JS, images)
├── templates/            # Global templates
├── documentation/        # Project documentation
└── requirements.txt      # Python dependencies
```

## Data Models

### CustomUser Model
Extends Django's AbstractUser with gamification and personalization fields:

```python
class CustomUser(AbstractUser):
    # Gamification fields
    current_wpm = PositiveIntegerField(default=250)
    max_wpm = PositiveIntegerField(default=250)
    total_xp = PositiveIntegerField(default=0)
    current_xp_points = PositiveIntegerField(default=0)
    negative_xp_points = PositiveIntegerField(default=0)
    last_successful_wpm_used = PositiveIntegerField(default=250)
    ad_free_articles_count = PositiveIntegerField(default=0)
    
    # Personalization fields
    preferred_language = CharField(max_length=10, default='en')
    theme = CharField(max_length=20, default='light')
    
    # LLM integration fields
    llm_api_key_encrypted = CharField(max_length=255, blank=True, null=True)
    preferred_llm_model = CharField(max_length=100, blank=True, null=True)
```

### Article Model
Stores article content and processing metadata:

```python
class Article(Model):
    url = URLField(max_length=500, unique=True, null=True)
    title = CharField(max_length=200)
    content = TextField()  # Processed content
    raw_content = TextField(blank=True, null=True)  # Original scraped content
    image_url = URLField(max_length=500, blank=True, null=True)
    
    # Processing metadata
    processing_status = CharField(max_length=20, default='pending')
    llm_model_used = CharField(max_length=100, blank=True, null=True)
    reading_level = FloatField(null=True, blank=True)  # Flesch-Kincaid grade
    
    # Content metadata
    language = CharField(max_length=10, default='en')
    source = CharField(max_length=100, default='user_submission')
    publication_date = DateTimeField(null=True, blank=True)
    timestamp = DateTimeField(auto_now_add=True)
    
    # Relationships
    user = ForeignKey(CustomUser, on_delete=SET_NULL, null=True, blank=True)
    tags = ManyToManyField(Tag, blank=True)
    quiz_data = JSONField(null=True, blank=True)  # Generated quiz questions
```

### Comment System Models

```python
class Comment(Model):
    article = ForeignKey(Article, on_delete=CASCADE, related_name='comments')
    user = ForeignKey(CustomUser, on_delete=CASCADE)
    content = TextField()
    timestamp = DateTimeField(auto_now_add=True)
    parent_comment = ForeignKey('self', null=True, blank=True, 
                               on_delete=CASCADE, related_name='replies')

class CommentInteraction(Model):
    class InteractionType(TextChoices):
        BRONZE = 'BRONZE', 'Bronze'
        SILVER = 'SILVER', 'Silver'
        GOLD = 'GOLD', 'Gold'
        REPORT = 'REPORT', 'Report'
    
    user = ForeignKey(CustomUser, on_delete=CASCADE)
    comment = ForeignKey(Comment, on_delete=CASCADE)
    interaction_type = CharField(max_length=10, choices=InteractionType.choices)
    timestamp = DateTimeField(auto_now_add=True)
    xp_cost = PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('user', 'comment')
```

### Quiz and Progress Tracking

```python
class QuizAttempt(Model):
    user = ForeignKey(CustomUser, on_delete=CASCADE)
    article = ForeignKey(Article, on_delete=CASCADE)
    score = FloatField()  # Percentage score
    wpm_used = IntegerField()  # WPM setting used
    xp_awarded = IntegerField()  # XP earned
    result = JSONField(null=True, blank=True)  # Detailed results
    timestamp = DateTimeField(auto_now_add=True)
    
    # Optional timing and feedback fields
    reading_time_seconds = PositiveIntegerField(null=True, blank=True)
    quiz_time_seconds = PositiveIntegerField(null=True, blank=True)
    quiz_rating = PositiveSmallIntegerField(null=True, blank=True)
    quiz_feedback = TextField(blank=True, null=True)
```

## Frontend Features

### Immersive Speed Reader

The immersive speed reader is a full-screen reading experience that provides distraction-free speed reading with advanced UI animations and accessibility features.

#### Key Features

1. **Current/Max WPM Display**
   - Format: "200/400 WPM" showing current speed and user's maximum
   - Real-time updates when WPM slider changes
   - Dynamic max speed based on user authentication status

2. **Immersive Full-Screen Mode**
   - Dark overlay (90% opacity) covering entire viewport
   - Background content fades to secondary focus
   - Centered word display with enhanced typography
   - Single stop button for simplified control

3. **Smooth Animations**
   - "Jump forward" effect when entering immersive mode
   - Speed reader rectangle scales and transitions to full-screen
   - GPU-accelerated animations with cubic-bezier easing
   - Staggered element animations for professional feel

4. **Responsive Design**
   - Mobile-optimized layouts for all screen sizes
   - Orientation change handling (portrait/landscape)
   - Font size scaling from 1.8rem to 5rem based on device
   - Safe area handling for modern mobile devices

5. **Accessibility Features**
   - Full keyboard navigation support
   - ARIA labels and screen reader compatibility
   - Focus management in immersive mode
   - High contrast mode support
   - Reduced motion support for accessibility preferences

#### Technical Implementation

**CSS Architecture:**
```css
.immersive-overlay {
    position: fixed;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.9);
    z-index: 9999;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    /* GPU acceleration */
    will-change: opacity, transform;
    backface-visibility: hidden;
}

.immersive-word-display {
    font-size: 4rem;
    color: white;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(10px);
    /* Optimized text rendering */
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
```

**JavaScript Architecture:**
```javascript
// State management
let isImmersiveMode = false;
let currentIndex = 0;
let wpm = 250;

// Overlay management with error handling
function showImmersiveOverlay() {
    try {
        // Animation sequence with proper timing
        speedReaderSection.classList.add('preparing-immersive');
        setTimeout(() => {
            immersiveOverlay.classList.add('active');
            // Focus management and accessibility
            manageFocus();
        }, 150);
    } catch (error) {
        console.error('Error showing overlay:', error);
        // Graceful fallback
    }
}
```

**Keyboard Shortcuts:**
- `Space`: Start/Pause reading
- `Escape`: Exit immersive mode
- `F`: Enter fullscreen immersive mode
- `R`: Reset reading progress
- `Arrow Up/Down`: Adjust WPM speed

#### Performance Optimizations

1. **GPU Acceleration**
   - `will-change` properties for animated elements
   - `transform: translateZ(0)` for hardware acceleration
   - Optimized CSS transitions and transforms

2. **Efficient DOM Manipulation**
   - Minimal reflows and repaints
   - Batch DOM updates
   - Event delegation for better performance

3. **Memory Management**
   - Proper event listener cleanup
   - Timeout and interval management
   - Error boundary implementation

4. **Browser Compatibility**
   - Graceful degradation for older browsers
   - Feature detection before using advanced CSS
   - Fallback animations for unsupported features

## Business Logic Services

### Article Processing Pipeline

The article processing system uses a multi-stage pipeline:

1. **Content Scraping** (`scrape_and_save_article` task)
   - Uses newspaper3k to extract article content
   - Stores raw content and metadata
   - Sets status to 'pending' for processing

2. **NLP Analysis** (`analyze_text_content` service)
   - Calculates reading level using textstat
   - Extracts named entities (people, organizations, money) using spaCy
   - Returns structured analysis data

3. **LLM Processing** (`generate_master_analysis` service)
   - Sends article content to Google Gemini API
   - Generates 5 multiple-choice quiz questions
   - Performs co-reference resolution on entities
   - Returns quiz data and canonical tags

4. **Tag Validation** (`get_valid_wikipedia_tags` service)
   - Validates entities against Wikipedia API
   - Resolves canonical names for entities
   - Creates Tag objects for valid entities

### Gamification System

The gamification system is implemented in `xp_system.py`:

```python
def calculate_xp_reward(score_percentage: float, wpm: int, article: Article) -> int:
    """Calculate XP based on performance and article complexity"""
    complexity_factor = article.reading_level or 1.0
    xp = int((score_percentage * 50) + (wpm * 2 * complexity_factor))
    return max(0, xp)

def post_comment(user: User, article: Article, content: str, 
                parent_comment: Comment = None) -> bool:
    """Handle comment posting with XP deduction"""
    xp_cost = 5 if parent_comment else 10  # Reply vs new comment
    if user.total_xp >= xp_cost:
        user.total_xp -= xp_cost
        user.save()
        Comment.objects.create(...)
        return True
    return False
```

## API Integration

### Google Gemini API Integration

The system integrates with Google Gemini API for intelligent content analysis:

```python
def generate_master_analysis(model_name: str, entity_list: list, 
                           article_text: str) -> dict:
    """Generate quiz and perform entity resolution using Gemini API"""
    
    # Dynamic model selection based on content complexity
    if article.reading_level < 30:  # Very difficult
        model_name = 'models/gemini-2.5-pro'
    elif 30 <= article.reading_level < 60:  # Standard
        model_name = 'models/gemini-2.5-flash'
    else:  # Easy content
        model_name = 'models/gemini-2.5-flash-lite-preview-06-17'
    
    # API call with retry logic and error handling
    # Returns structured JSON with quiz questions and canonical tags
```

### Wikipedia API Integration

Entity validation and canonical name resolution:

```python
def get_valid_wikipedia_tags(entities: list, language: str = 'en') -> list:
    """Validate entities against Wikipedia and return Tag objects"""
    
    # Step 1: Resolve canonical names
    for entity_name in entities:
        page_obj = wiki.page(entity_name)
        if page_obj.exists():
            canonical_name = page_obj.title
            # Store mapping for deduplication
    
    # Step 2: Create Tag objects for unique canonical names
    # Returns list of validated Tag model instances
```

## Asynchronous Task Processing

### Celery Configuration

```python
# config/celery.py
app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Settings
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

### Task Definitions

```python
@shared_task(bind=True)
def process_article(self, article_id):
    """Main article processing task with retry logic"""
    try:
        article = Article.objects.get(id=article_id, processing_status='pending')
        
        # NLP analysis
        analysis_data = analyze_text_content(article.content, article.language)
        
        # LLM processing with retry logic
        llm_data = generate_master_analysis(...)
        
        # Tag validation and assignment
        validated_tags = get_valid_wikipedia_tags(...)
        
        # Update article status
        article.processing_status = 'complete'
        article.save()
        
    except Exception as e:
        # Retry logic with exponential backoff
        self.retry(countdown=60 * (2 ** self.request.retries))
```

## Security Implementation

### Authentication and Authorization
- Django's built-in authentication system
- Custom user model with additional fields
- Session-based authentication for web interface
- CSRF protection on all forms

### Data Security
- Environment variables for sensitive configuration
- Encrypted storage of user API keys
- Parameterized database queries via Django ORM
- Input validation through Django forms

### API Security
- Rate limiting on external API calls
- Error handling to prevent information leakage
- Secure headers configuration

## Performance Considerations

### Database Optimization
- Proper indexing on frequently queried fields
- Use of `select_related` and `prefetch_related` for relationship queries
- Database connection pooling in production

### Caching Strategy
- Redis for Celery message brokering
- Static file caching with WhiteNoise
- Template fragment caching for expensive operations

### Scalability
- Horizontal scaling support through stateless design
- Asynchronous processing for CPU-intensive tasks
- CDN-ready static file serving

## Deployment Architecture

### Development Environment
```bash
# Process management with honcho
web: gunicorn config.wsgi --bind 0.0.0.0:8000 --reload
worker: celery -A config.celery worker --loglevel=INFO
```

### Production Considerations
- PostgreSQL database with connection pooling
- Redis cluster for high availability
- Load balancer for multiple Django instances
- Separate Celery workers for different task types
- Monitoring and logging infrastructure

---

*This technical specification reflects the current implementation as of July 2025.*