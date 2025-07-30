# VeriFast Project Structure

## Directory Organization

```
verifast/
├── config/                 # Django project configuration
│   ├── settings.py        # Main settings with environment variables
│   ├── urls.py           # Root URL configuration
│   ├── wsgi.py           # WSGI application entry point
│   ├── asgi.py           # ASGI application entry point
│   └── celery.py         # Celery configuration
├── verifast_app/          # Main application (primary business logic)
│   ├── models.py         # Database models (CustomUser, Article, Tag, etc.)
│   ├── views.py          # View controllers (class-based and function-based)
│   ├── urls.py           # App URL patterns with app_name namespace
│   ├── admin.py          # Django admin configuration
│   ├── forms.py          # Django forms for user input
│   ├── tasks.py          # Celery background tasks
│   ├── services.py       # Business logic services
│   ├── xp_system.py      # Gamification and XP management
│   ├── tag_analytics.py  # Tag analysis and statistics
│   ├── serializers.py    # DRF serializers for API endpoints
│   ├── api_views.py      # API view controllers
│   ├── api_urls.py       # API URL patterns
│   ├── context_processors.py # Template context processors
│   ├── migrations/       # Database migration files
│   ├── templates/        # HTML templates
│   ├── static/           # App-specific static files
│   ├── templatetags/     # Custom template tags
│   └── test_*.py         # Test files (test_xp_system.py, etc.)
├── core/                  # Secondary app (minimal usage)
├── templates/            # Global templates (registration, etc.)
├── static/               # Global static files
├── staticfiles/          # Collected static files (production)
├── documentation/        # Comprehensive project documentation
├── .kiro/               # Kiro IDE specifications and steering
└── manage.py            # Django management script
```

## Code Organization Patterns

### Models (models.py)
- **CustomUser**: Extended Django user with XP, premium features, and stats
- **Article**: Content model with processing status and metadata
- **Tag**: Wikipedia-validated tags with analytics annotations
- **Comment**: Hierarchical comment system with interactions
- **QuizAttempt**: Quiz results and XP tracking
- **XPTransaction**: Detailed XP earning/spending history
- **FeaturePurchase**: Premium feature purchase tracking

### Views Architecture
- **Class-based views**: Inherit from Django generic views (DetailView, ListView, etc.)
- **Function-based views**: For simple operations and form handling
- **API views**: Separate api_views.py for AJAX endpoints
- **Mixins**: LoginRequiredMixin for authentication

### Speed Reader Architecture (CRITICAL)
- **SINGLE-MODE DESIGN**: Immersive mode is the ONLY speed reading interface
- **NO DUAL-MODE**: Regular inline speed reader has been permanently removed
- **FULL-WIDTH DISPLAY**: Text strip spans entire screen width (side to side)
- **SIMPLIFIED UX**: Single "Start Reading" button launches immersive mode directly
- **HTMX HYBRID**: Server-side processing with minimal Alpine.js (max 30 lines)
- **Reference**: See `documentation/architecture/speed-reader-single-mode-spec.md` for complete specification

### Article Detail Page Architecture (CRITICAL)
- **COMPLETE FEATURE SET**: Must include image, metadata, tags, comments, related articles
- **HTMX INTEGRATION**: Speed reader and quiz use HTMX endpoints with progressive enhancement
- **DATA CALCULATIONS**: Word count and reading level calculated automatically
- **MOBILE RESPONSIVE**: All sections work properly on mobile devices
- **Reference**: See `documentation/architecture/article-detail-complete-spec.md` for complete specification

### URL Patterns
- **Namespaced URLs**: Use `app_name = 'verifast_app'` in urls.py
- **RESTful patterns**: `/articles/<int:pk>/` for detail views
- **API endpoints**: Separate `/api/v1/` prefix for API routes

### Template Organization
```
templates/
├── verifast_app/
│   ├── base.html         # Base template with PicoCSS
│   ├── index.html        # Homepage
│   ├── article_list.html # Article listing
│   ├── article_detail.html # Article reading interface
│   ├── user_profile.html # User dashboard
│   └── components/       # Reusable template components
└── registration/         # Auth templates
```

### Static Files Structure
```
static/
├── css/
│   └── custom.css        # Custom styles extending PicoCSS
├── js/
│   ├── speed-reader.js   # Speed reading functionality
│   ├── quiz-handler.js   # Quiz interaction logic
│   └── immersive-mode.js # Full-screen reading mode
└── images/               # Static images and icons
```

## Naming Conventions

### Python Code
- **Models**: PascalCase (CustomUser, QuizAttempt)
- **Functions/Methods**: snake_case (get_valid_tags, process_quiz)
- **Variables**: snake_case (user_xp, quiz_attempts)
- **Constants**: UPPER_SNAKE_CASE (TRANSACTION_TYPES)

### Templates
- **Files**: snake_case.html (article_detail.html)
- **Template variables**: snake_case (user_profile, quiz_attempts)
- **CSS classes**: kebab-case following PicoCSS conventions

### URLs
- **URL patterns**: kebab-case (article-list, user-profile)
- **URL names**: snake_case (article_list, user_profile)

## Database Conventions

### Model Fields
- Use descriptive help_text for all fields
- Include null=True, blank=True appropriately
- Use choices for constrained values (TRANSACTION_TYPES)
- Add database indexes for frequently queried fields

### Relationships
- Use related_name for reverse relationships
- CASCADE for dependent data, SET_NULL for optional references
- Many-to-many through intermediate models when metadata needed

## Testing Structure
- **Test files**: Prefix with `test_` (test_xp_system.py)
- **Test classes**: Suffix with `TestCase` or `Test`
- **Test methods**: Prefix with `test_`
- Use Django's TestCase for database tests

## Documentation Location
- **API docs**: `documentation/api/`
- **Architecture**: `documentation/architecture/`
- **Features**: `documentation/features/`
- **Setup guides**: `documentation/setup/`