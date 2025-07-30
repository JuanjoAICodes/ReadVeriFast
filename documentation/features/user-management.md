# User Management Documentation

*Last Updated: July 21, 2025*
*Status: Current*

## Overview

The VeriFast User Management system provides comprehensive user authentication, profile management, and personalization features built on Django's robust authentication framework with custom extensions for speed reading and gamification.

## Core Components

### 1. Custom User Model
**Location:** `verifast_app/models.py`

**Extended User Features:**
```python
class CustomUser(AbstractUser):
    # Speed Reading Preferences
    current_wpm = models.PositiveIntegerField(default=250)
    max_wpm = models.PositiveIntegerField(default=250)
    preferred_chunk_size = models.PositiveIntegerField(default=2)
    
    # Gamification
    current_xp_points = models.PositiveIntegerField(default=0)
    total_xp_earned = models.PositiveIntegerField(default=0)
    
    # Personalization
    preferred_language = models.CharField(max_length=10, default='en')
    dark_mode_enabled = models.BooleanField(default=False)
    
    # Premium Features
    owned_features = models.JSONField(default=list)
    
    # Statistics
    articles_read = models.PositiveIntegerField(default=0)
    total_reading_time = models.PositiveIntegerField(default=0)  # in minutes
    quiz_attempts = models.PositiveIntegerField(default=0)
    average_quiz_score = models.FloatField(default=0.0)
```

### 2. Authentication System
**Location:** `verifast_app/views.py`, `templates/registration/`

**Authentication Features:**
- **Registration** - Custom registration with additional fields
- **Login/Logout** - Standard Django authentication
- **Password Reset** - Email-based password recovery
- **Profile Management** - User preference updates
- **Session Management** - Secure session handling

### 3. User Profile Interface
**Location:** `templates/user_profile.html`

**Profile Features:**
- **Reading Statistics** - Personal reading metrics
- **XP Dashboard** - Current points and transaction history
- **Preference Settings** - Speed, language, theme preferences
- **Achievement Display** - Reading milestones and badges
- **Premium Features** - Owned and available features

## User Registration

### Registration Form
**Location:** `verifast_app/forms.py`

```python
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    preferred_language = forms.ChoiceField(
        choices=[('en', 'English'), ('es', 'Español')],
        initial='en'
    )
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'preferred_language', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.preferred_language = self.cleaned_data['preferred_language']
        if commit:
            user.save()
        return user
```

### Registration Process
1. **Form Validation** - Email uniqueness, password strength
2. **User Creation** - Create CustomUser with defaults
3. **Welcome Email** - Optional welcome message
4. **Initial Setup** - Set default preferences
5. **Redirect** - Send to profile or onboarding

## User Authentication

### Login System
**Location:** `templates/registration/login.html`

**Login Features:**
- **Username/Email Login** - Flexible login options
- **Remember Me** - Extended session duration
- **Error Handling** - Clear error messages
- **Redirect Handling** - Return to intended page

### Security Features
- **CSRF Protection** - All forms protected
- **Session Security** - Secure session configuration
- **Password Validation** - Strong password requirements
- **Rate Limiting** - Login attempt protection

## User Profile Management

### Profile Dashboard
**Key Sections:**
- **Reading Statistics** - Articles read, time spent, average WPM
- **XP Information** - Current balance, total earned, recent transactions
- **Achievements** - Reading milestones and badges
- **Preferences** - Customizable settings
- **Premium Features** - Owned and purchasable features

### Preference Management
**Configurable Settings:**
```python
# Reading Preferences
current_wpm = 250          # Current reading speed
max_wpm = 300             # Maximum achieved speed
preferred_chunk_size = 2   # Words per chunk in speed reader

# Interface Preferences
preferred_language = 'en'  # UI language
dark_mode_enabled = False  # Theme preference

# Notification Preferences
email_notifications = True # Email updates
achievement_notifications = True # Achievement alerts
```

## User Statistics and Analytics

### Reading Metrics
**Tracked Statistics:**
- **Articles Read** - Total articles completed
- **Reading Time** - Total time spent reading
- **Average WPM** - Reading speed progression
- **Quiz Performance** - Average quiz scores
- **XP Progression** - Points earned over time

### Performance Analytics
**Location:** `verifast_app/views.py`

```python
def get_user_statistics(user):
    """Generate comprehensive user statistics"""
    return {
        'reading_stats': {
            'articles_read': user.articles_read,
            'total_reading_time': user.total_reading_time,
            'average_wpm': user.current_wpm,
            'wpm_improvement': user.max_wpm - 250,  # Improvement from default
        },
        'quiz_stats': {
            'attempts': user.quiz_attempts,
            'average_score': user.average_quiz_score,
            'perfect_scores': QuizAttempt.objects.filter(
                user=user, score=100
            ).count(),
        },
        'xp_stats': {
            'current_balance': user.current_xp_points,
            'total_earned': user.total_xp_earned,
            'total_spent': user.total_xp_earned - user.current_xp_points,
        }
    }
```

## Premium Features Integration

### Feature Ownership
**Location:** `verifast_app/models.py`

```python
def has_premium_feature(self, feature_key):
    """Check if user owns a premium feature"""
    return feature_key in self.owned_features

def purchase_feature(self, feature_key, cost):
    """Purchase a premium feature with XP"""
    if self.current_xp_points >= cost:
        self.current_xp_points -= cost
        if feature_key not in self.owned_features:
            self.owned_features.append(feature_key)
        self.save()
        return True
    return False
```

### Available Premium Features
- **Font Customization** - Custom fonts for reading
- **Advanced Analytics** - Detailed reading statistics
- **Theme Options** - Additional color schemes
- **Export Features** - Data export capabilities

## API Endpoints

### User Management API
**Location:** `verifast_app/api_views.py`

```python
# User profile endpoints
GET /api/user/                    # Get current user info
PUT /api/user/                    # Update user preferences
GET /api/user/statistics/         # Get user statistics
GET /api/user/achievements/       # Get user achievements

# Authentication endpoints
POST /api/auth/login/             # User login
POST /api/auth/logout/            # User logout
POST /api/auth/register/          # User registration
POST /api/auth/password-reset/    # Password reset request
```

### User Data Serialization
```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'preferred_language',
            'current_wpm', 'max_wpm', 'current_xp_points',
            'articles_read', 'total_reading_time', 'owned_features'
        ]
        read_only_fields = ['id', 'total_xp_earned']
```

## User Interface Components

### Profile Templates
**Location:** `verifast_app/templates/verifast_app/`

**Template Structure:**
- `user_profile.html` - Main profile dashboard
- `profile_edit.html` - Preference editing form
- `user_statistics.html` - Detailed statistics view
- `achievement_display.html` - Achievement showcase

### Navigation Integration
**User-Specific Navigation:**
- **Profile Link** - Access to user dashboard
- **XP Display** - Current XP balance in header
- **Achievement Notifications** - New achievement alerts
- **Premium Feature Access** - Feature-specific UI elements

## Security and Privacy

### Data Protection
- **Password Hashing** - Secure password storage
- **Personal Data Encryption** - Sensitive data protection
- **Session Security** - Secure session management
- **GDPR Compliance** - Data export and deletion options

### Privacy Controls
- **Data Visibility** - Control over public statistics
- **Email Preferences** - Notification management
- **Account Deletion** - Complete account removal option
- **Data Export** - User data download capability

## Testing

### User Management Tests
**Location:** `verifast_app/tests.py`

**Test Coverage:**
- **Registration Process** - Form validation and user creation
- **Authentication Flow** - Login, logout, password reset
- **Profile Updates** - Preference changes and validation
- **Premium Features** - Feature purchase and access
- **Statistics Calculation** - Metric accuracy

### Integration Tests
- **XP System Integration** - User XP balance updates
- **Reading Progress** - Statistics tracking accuracy
- **Premium Feature Access** - Feature availability checks
- **API Endpoints** - All user-related API functionality

## Configuration

### User Settings
```python
# settings.py
AUTH_USER_MODEL = 'verifast_app.CustomUser'

# Authentication settings
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/profile/'
LOGOUT_REDIRECT_URL = '/'

# Session settings
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8,}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

## Future Enhancements

### Planned Features
- **Social Features** - Friend connections and leaderboards
- **Achievement System** - Comprehensive badge system
- **Reading Goals** - Personal reading targets
- **Data Insights** - Advanced analytics dashboard

### Advanced Personalization
- **AI Recommendations** - Personalized article suggestions
- **Adaptive Interface** - UI that learns user preferences
- **Reading Habit Analysis** - Detailed behavior insights
- **Custom Themes** - User-created color schemes

## Related Documentation
- [XP System](xp-system.md) - Gamification integration
- [Speed Reader](speed-reader.md) - Reading preferences
- [Tag System](tag-system.md) - Content personalization
- [API Specification](../api/specification.md) - User API endpoints