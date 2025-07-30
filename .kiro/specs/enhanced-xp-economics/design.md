# Enhanced XP Economics System - Design Document

## Overview

This design document outlines the implementation of a sophisticated XP (Experience Points) economics system that creates a virtual currency economy within VeriFast. The system separates accumulated XP (permanent achievement record) from spendable XP (virtual currency), enabling users to purchase premium features and enhanced social interactions while maintaining their progress history.

## Architecture

### XP Economics Flow Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Actions  │    │   XP Engine     │    │   XP Storage    │
│                 │    │                 │    │                 │
│ • Complete Quiz │───►│ • Calculate XP  │───►│ • total_xp      │
│ • Read Articles │    │ • Apply Bonuses │    │ • current_xp    │
│ • Achieve Goals │    │ • Validate Earn │    │ • Transactions  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  XP Spending    │    │  Feature Store  │    │  Social Economy │
│                 │    │                 │    │                 │
│ • Validate Bal. │◄───│ • Premium Fonts │    │ • Comments      │
│ • Process Trans │    │ • Adv. Chunking │    │ • Interactions  │
│ • Update Balance│    │ • Themes        │    │ • Rewards       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### System Components

#### 1. XP Calculation Engine
Handles all XP earning calculations with multiple factors:

```python
class XPCalculationEngine:
    @staticmethod
    def calculate_quiz_xp(quiz_attempt, article, use_letters=False):
        """Calculate XP using complex formula with word/letter count"""
        # Only award XP if quiz score >= 60%
        if quiz_attempt.score < 60:
            return 0
        
        # Choose between word count or letter count (configurable)
        if use_letters:
            base_count = len(article.content.replace(' ', ''))  # Letter count
        else:
            base_count = len(article.content.split())  # Word count
        
        # Speed multiplier based on WPM and complexity
        complexity_factor = (article.reading_level or 10) / 10
        speed_multiplier = (quiz_attempt.wpm_used / 250) * complexity_factor
        
        # Accuracy bonus (quiz score percentage)
        accuracy_bonus = quiz_attempt.score / 100
        
        # Calculate final XP
        total_xp = int(base_count * speed_multiplier * accuracy_bonus)
        
        return max(total_xp, 1)  # Minimum 1 XP
    
    @staticmethod
    def has_perfect_score_privilege(quiz_attempt):
        """Check if user gets free comment for perfect score"""
        return quiz_attempt.score >= 100
    
    @staticmethod
    def get_recommended_wpm(user, failed_attempts=0):
        """Get recommended WPM after quiz failure"""
        last_successful_wpm = user.last_successful_wpm_used or 200
        
        # Progressively slower recommendations
        reduction = min(failed_attempts * 25, 100)  # Max 100 WPM reduction
        recommended_wpm = max(last_successful_wpm - reduction, 100)
        
        return recommended_wpm
    
    @staticmethod
    def get_next_recommended_articles(user, current_article, limit=2):
        """Get recommended articles based on tags and reading status"""
        # Find unread articles with most common tags
        user_read_articles = QuizAttempt.objects.filter(
            user=user, score__gte=60
        ).values_list('article_id', flat=True)
        
        unread_articles = Article.objects.exclude(
            id__in=user_read_articles
        ).filter(processing_status='complete')
        
        # Find articles with common tags
        current_tags = current_article.tags.all()
        if current_tags.exists():
            tagged_articles = unread_articles.filter(
                tags__in=current_tags
            ).annotate(
                common_tags=Count('tags')
            ).order_by('-common_tags')[:1]
        else:
            tagged_articles = []
        
        # Get random unread article
        random_article = unread_articles.order_by('?')[:1]
        
        return {
            'next_similar': tagged_articles[0] if tagged_articles else None,
            'random_unread': random_article[0] if random_article else None
        }
```

#### 2. XP Transaction Manager
Handles all XP transactions with atomic operations:

```python
class XPTransactionManager:
    @staticmethod
    @transaction.atomic
    def earn_xp(user, amount, source, description, reference_obj=None):
        """Award XP to user with transaction logging"""
        # Update both total and spendable XP
        user.total_xp += amount
        user.current_xp_points += amount
        user.save()
        
        # Log transaction
        XPTransaction.objects.create(
            user=user,
            transaction_type='EARN',
            amount=amount,
            source=source,
            description=description,
            balance_after=user.current_xp_points,
            quiz_attempt=reference_obj if isinstance(reference_obj, QuizAttempt) else None
        )
        
        return True
    
    @staticmethod
    @transaction.atomic
    def spend_xp(user, amount, purpose, description, reference_obj=None):
        """Spend user's XP with validation"""
        if user.current_xp_points < amount:
            raise InsufficientXPError(f"User has {user.current_xp_points} XP, needs {amount}")
        
        # Deduct only from spendable XP
        user.current_xp_points -= amount
        user.save()
        
        # Log transaction
        XPTransaction.objects.create(
            user=user,
            transaction_type='SPEND',
            amount=-amount,  # Negative for spending
            source=purpose,
            description=description,
            balance_after=user.current_xp_points,
            comment=reference_obj if isinstance(reference_obj, Comment) else None
        )
        
        return True
```

#### 3. Premium Feature Store
Manages feature purchases and unlocks:

```python
class PremiumFeatureStore:
    FEATURES = {
        'opendyslexic_font': {
            'name': 'OpenDyslexic Font',
            'description': 'Dyslexia-friendly font for easier reading',
            'cost': 50,
            'category': 'accessibility'
        },
        'advanced_chunking': {
            'name': 'Advanced Word Chunking',
            'description': '2-3 words per chunk for faster reading',
            'cost': 100,
            'category': 'speed_reading'
        },
        'connector_grouping': {
            'name': 'Smart Connector Grouping',
            'description': 'Intelligent grouping of connecting words',
            'cost': 75,
            'category': 'speed_reading'
        },
        'symbol_removal': {
            'name': 'Symbol Removal',
            'description': 'Remove distracting punctuation marks',
            'cost': 25,
            'category': 'readability'
        },
        'premium_themes': {
            'name': 'Premium Themes',
            'description': 'Dark mode and custom color schemes',
            'cost': 150,
            'category': 'customization'
        }
    }
    
    @staticmethod
    def purchase_feature(user, feature_key):
        """Purchase a premium feature for user"""
        if feature_key not in PremiumFeatureStore.FEATURES:
            raise InvalidFeatureError(f"Feature {feature_key} does not exist")
        
        feature = PremiumFeatureStore.FEATURES[feature_key]
        
        # Check if already owned
        if PremiumFeatureStore.user_owns_feature(user, feature_key):
            raise FeatureAlreadyOwnedError(f"User already owns {feature['name']}")
        
        # Process XP transaction
        XPTransactionManager.spend_xp(
            user=user,
            amount=feature['cost'],
            purpose='feature_purchase',
            description=f"Purchased {feature['name']}"
        )
        
        # Unlock feature
        setattr(user, f"has_{feature_key}", True)
        user.save()
        
        # Record purchase
        FeaturePurchase.objects.create(
            user=user,
            feature_name=feature_key,
            xp_cost=feature['cost']
        )
        
        return True
    
    @staticmethod
    def user_owns_feature(user, feature_key):
        """Check if user owns a specific feature"""
        return getattr(user, f"has_{feature_key}", False)
```

## Components and Interfaces

### 1. User Interface Components

#### XP Balance Display
```html
<!-- XP Balance Widget -->
<div class="xp-balance-widget">
    <div class="xp-total">
        <span class="xp-icon">🏆</span>
        <span class="xp-amount">{{ user.total_xp }}</span>
        <span class="xp-label">Total XP</span>
    </div>
    <div class="xp-spendable">
        <span class="xp-icon">💰</span>
        <span class="xp-amount">{{ user.current_xp_points }}</span>
        <span class="xp-label">Spendable</span>
    </div>
</div>
```

#### Premium Feature Store
The premium feature store is accessible from the user profile page, providing a dedicated section for purchasing and managing premium features.

```html
<!-- Feature Store Interface (accessible from user profile) -->
<div class="feature-store">
    <h3>Premium Features</h3>
    {% for feature_key, feature in features.items %}
    <div class="feature-card {% if user_owns_feature %}owned{% endif %}">
        <div class="feature-info">
            <h4>{{ feature.name }}</h4>
            <p>{{ feature.description }}</p>
        </div>
        <div class="feature-purchase">
            {% if user_owns_feature %}
                <span class="owned-badge">✓ Owned</span>
            {% else %}
                <button class="purchase-btn" 
                        data-feature="{{ feature_key }}"
                        data-cost="{{ feature.cost }}"
                        {% if user.current_xp_points < feature.cost %}disabled{% endif %}>
                    Buy for {{ feature.cost }} XP
                </button>
            {% endif %}
        </div>
    </div>
    {% endfor %}
</div>
```

#### Advanced Quiz Results Interface
```html
<!-- Perfect Score (100%) Result -->
<div class="quiz-result perfect-score">
    <div class="result-header">
        <h2>🎉 Perfect Quiz!</h2>
        <div class="score-display">100%</div>
    </div>
    
    <div class="perfect-bonus-message">
        <h3>You can comment on this article for free!</h3>
        <p>What do you think about this news/event?</p>
        <small>Writing about news you understood 100% improves retention and helps you remember the content better.</small>
    </div>
    
    <div class="xp-earned">
        <span class="xp-amount">+{{ xp_earned }} XP</span>
        <span class="xp-breakdown">{{ word_count }} words × {{ speed_multiplier }}× speed × 100% accuracy</span>
    </div>
    
    <div class="navigation-links">
        <a href="{{ next_similar_article.url }}" class="nav-btn primary">
            📖 Next: {{ next_similar_article.title|truncatechars:40 }}
            <small>Similar topics</small>
        </a>
        <a href="{{ random_article.url }}" class="nav-btn secondary">
            🎲 Random Article
            <small>Discover something new</small>
        </a>
        <a href="#comments" class="nav-btn accent">
            💬 Comment Section
            <small>Share your thoughts (FREE)</small>
        </a>
    </div>
</div>

<!-- Passed Quiz (60-99%) Result -->
<div class="quiz-result passed">
    <div class="result-header">
        <h2>✅ Quiz Passed!</h2>
        <div class="score-display">{{ quiz_score }}%</div>
    </div>
    
    <div class="feedback-section">
        <h3>Review Your Mistakes</h3>
        {% for question in incorrect_questions %}
        <div class="question-feedback">
            <div class="question-text">{{ question.question }}</div>
            <div class="answer-comparison">
                <div class="correct-answer">
                    <span class="answer-label">Correct:</span>
                    <span class="answer-text correct">{{ question.correct_answer }}</span>
                </div>
                <div class="wrong-answer">
                    <span class="answer-label">Your answer:</span>
                    <span class="answer-text incorrect">{{ question.user_answer }}</span>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    
    <div class="xp-earned">
        <span class="xp-amount">+{{ xp_earned }} XP</span>
        <span class="xp-breakdown">{{ word_count }} words × {{ speed_multiplier }}× speed × {{ quiz_score }}% accuracy</span>
    </div>
    
    <div class="navigation-links">
        <a href="{{ next_similar_article.url }}" class="nav-btn primary">
            📖 Next: {{ next_similar_article.title|truncatechars:40 }}
        </a>
        <a href="{{ random_article.url }}" class="nav-btn secondary">
            🎲 Random Article
        </a>
        <a href="#comments" class="nav-btn accent">
            💬 Comment Section (10 XP)
        </a>
    </div>
</div>

<!-- Failed Quiz (<60%) Result -->
<div class="quiz-result failed">
    <div class="result-header">
        <h2>📚 Keep Learning!</h2>
        <div class="score-display failed">{{ quiz_score }}%</div>
    </div>
    
    <div class="failure-message">
        <p>Don't worry! Reading comprehension improves with practice.</p>
        <div class="speed-recommendation">
            <h4>💡 Recommendation:</h4>
            <p>Try reading at <strong>{{ recommended_wpm }} WPM</strong> for better comprehension.</p>
            <small>Your last successful speed was {{ last_successful_wpm }} WPM</small>
        </div>
    </div>
    
    <div class="no-xp-message">
        <span class="xp-amount">0 XP</span>
        <span class="xp-note">Score 60% or higher to earn XP</span>
    </div>
    
    <div class="navigation-links">
        <a href="{{ current_article.url }}" class="nav-btn primary">
            📖 Re-read Article
            <small>Take your time</small>
        </a>
        <a href="{{ quiz_url }}" class="nav-btn secondary">
            🔄 Try Quiz Again
            <small>You can do it!</small>
        </a>
    </div>
</div>
```

#### XP Transaction History
```html
<!-- Transaction History -->
<div class="xp-history">
    <h3>XP Transaction History</h3>
    <div class="transaction-filters">
        <button class="filter-btn active" data-filter="all">All</button>
        <button class="filter-btn" data-filter="earned">Earned</button>
        <button class="filter-btn" data-filter="spent">Spent</button>
    </div>
    <div class="transaction-list">
        {% for transaction in transactions %}
        <div class="transaction-item {{ transaction.transaction_type|lower }}">
            <div class="transaction-info">
                <span class="transaction-description">{{ transaction.description }}</span>
                <span class="transaction-date">{{ transaction.timestamp|date:"M d, H:i" }}</span>
            </div>
            <div class="transaction-amount {% if transaction.amount > 0 %}positive{% else %}negative{% endif %}">
                {% if transaction.amount > 0 %}+{% endif %}{{ transaction.amount }} XP
            </div>
        </div>
        {% endfor %}
    </div>
</div>
```

### 2. Backend API Endpoints

#### XP Management API
```python
# API Views for XP system
class XPBalanceView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            'total_xp': user.total_xp,
            'current_xp_points': user.current_xp_points,
            'recent_transactions': XPTransactionSerializer(
                XPTransaction.objects.filter(user=user).order_by('-timestamp')[:5],
                many=True
            ).data
        })

class FeatureStoreView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        features = []
        
        for key, feature in PremiumFeatureStore.FEATURES.items():
            features.append({
                'key': key,
                'name': feature['name'],
                'description': feature['description'],
                'cost': feature['cost'],
                'category': feature['category'],
                'owned': PremiumFeatureStore.user_owns_feature(user, key)
            })
        
        return Response({'features': features})
    
    def post(self, request):
        feature_key = request.data.get('feature_key')
        
        try:
            PremiumFeatureStore.purchase_feature(request.user, feature_key)
            return Response({'success': True, 'message': 'Feature purchased successfully'})
        except (InsufficientXPError, InvalidFeatureError, FeatureAlreadyOwnedError) as e:
            return Response({'success': False, 'error': str(e)}, status=400)
```

### 3. Enhanced Speed Reader Integration

#### Feature-Gated Controls
```javascript
// Enhanced Speed Reader with Premium Features
class EnhancedSpeedReader {
    constructor(user_features) {
        this.userFeatures = user_features;
        this.initializeControls();
    }
    
    initializeControls() {
        // Show only purchased features
        if (this.userFeatures.has_advanced_chunking) {
            this.enableAdvancedChunking();
        }
        
        if (this.userFeatures.has_connector_grouping) {
            this.enableConnectorGrouping();
        }
        
        if (this.userFeatures.has_symbol_removal) {
            this.enableSymbolRemoval();
        }
        
        if (this.userFeatures.has_opendyslexic_font) {
            this.addFontOption('OpenDyslexic');
        }
        
        if (this.userFeatures.has_premium_themes) {
            this.enablePremiumThemes();
        }
    }
    
    enableAdvancedChunking() {
        // Add 2-3 word chunking options
        const chunkSelect = document.getElementById('chunk-size');
        if (chunkSelect) {
            chunkSelect.innerHTML += `
                <option value="2">2 words (Premium)</option>
                <option value="3">3 words (Premium)</option>
            `;
        }
    }
    
    enableConnectorGrouping() {
        // Enable smart connector grouping
        const connectorCheckbox = document.getElementById('group-connectors');
        if (connectorCheckbox) {
            connectorCheckbox.disabled = false;
            connectorCheckbox.parentElement.classList.remove('disabled');
        }
    }
}
```

## Data Models

### Enhanced User Model
```python
class CustomUser(AbstractUser):
    # Existing fields...
    total_xp = PositiveIntegerField(default=0)
    current_xp_points = PositiveIntegerField(default=0)
    
    # Premium feature flags
    has_opendyslexic_font = BooleanField(default=False)
    has_advanced_chunking = BooleanField(default=False)
    has_connector_grouping = BooleanField(default=False)
    has_symbol_removal = BooleanField(default=False)
    has_premium_themes = BooleanField(default=False)
    
    # XP tracking
    last_xp_earned = DateTimeField(null=True, blank=True)
    xp_earning_streak = PositiveIntegerField(default=0)
    lifetime_xp_earned = PositiveIntegerField(default=0)
    lifetime_xp_spent = PositiveIntegerField(default=0)
    
    def get_xp_level(self):
        """Calculate user level based on total XP"""
        return min(self.total_xp // 1000, 100)  # Level 1-100
    
    def can_afford(self, cost):
        """Check if user can afford XP cost"""
        return self.current_xp_points >= cost
```

### XP Transaction Model
```python
class XPTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('EARN', 'Earned'),
        ('SPEND', 'Spent'),
    ]
    
    SOURCES = [
        ('quiz_completion', 'Quiz Completion'),
        ('perfect_score_bonus', 'Perfect Score Bonus'),
        ('wpm_improvement', 'WPM Improvement'),
        ('reading_streak', 'Reading Streak'),
        ('comment_post', 'Comment Posted'),
        ('comment_reply', 'Comment Reply'),
        ('interaction_bronze', 'Bronze Interaction'),
        ('interaction_silver', 'Silver Interaction'),
        ('interaction_gold', 'Gold Interaction'),
        ('feature_purchase', 'Feature Purchase'),
        ('admin_adjustment', 'Admin Adjustment'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='xp_transactions')
    transaction_type = models.CharField(max_length=5, choices=TRANSACTION_TYPES)
    amount = models.IntegerField()  # Positive for earn, negative for spend
    source = models.CharField(max_length=20, choices=SOURCES)
    description = models.TextField()
    balance_after = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Optional references
    quiz_attempt = models.ForeignKey('QuizAttempt', null=True, blank=True, on_delete=models.SET_NULL)
    comment = models.ForeignKey('Comment', null=True, blank=True, on_delete=models.SET_NULL)
    feature_purchased = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['transaction_type', '-timestamp']),
        ]
```

## Error Handling

### Custom Exceptions
```python
class XPSystemError(Exception):
    """Base exception for XP system errors"""
    pass

class InsufficientXPError(XPSystemError):
    """Raised when user doesn't have enough XP for transaction"""
    pass

class InvalidFeatureError(XPSystemError):
    """Raised when trying to purchase non-existent feature"""
    pass

class FeatureAlreadyOwnedError(XPSystemError):
    """Raised when trying to purchase already owned feature"""
    pass

class XPTransactionError(XPSystemError):
    """Raised when XP transaction fails"""
    pass
```

### Error Handling Middleware
```python
def handle_xp_errors(view_func):
    """Decorator to handle XP-related errors gracefully"""
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except InsufficientXPError as e:
            messages.error(request, f"Insufficient XP: {str(e)}")
            return redirect('user_profile')
        except FeatureAlreadyOwnedError as e:
            messages.info(request, f"Feature already owned: {str(e)}")
            return redirect('feature_store')
        except XPSystemError as e:
            messages.error(request, f"XP System Error: {str(e)}")
            logger.error(f"XP System Error: {str(e)}", exc_info=True)
            return redirect('home')
    return wrapper
```

## Testing Strategy

### Unit Tests
```python
class XPSystemTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.article = Article.objects.create(
            title='Test Article',
            reading_level=10.0
        )
    
    def test_xp_earning(self):
        """Test XP earning from quiz completion"""
        initial_total = self.user.total_xp
        initial_spendable = self.user.current_xp_points
        
        # Simulate quiz completion
        quiz_attempt = QuizAttempt.objects.create(
            user=self.user,
            article=self.article,
            score=85.0,
            wpm_used=300
        )
        
        xp_earned = XPCalculationEngine.calculate_quiz_xp(quiz_attempt, self.article)
        XPTransactionManager.earn_xp(
            self.user, xp_earned, 'quiz_completion', 
            f'Quiz completed with {quiz_attempt.score}%'
        )
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.total_xp, initial_total + xp_earned)
        self.assertEqual(self.user.current_xp_points, initial_spendable + xp_earned)
    
    def test_feature_purchase(self):
        """Test premium feature purchase"""
        # Give user enough XP
        self.user.current_xp_points = 100
        self.user.save()
        
        # Purchase feature
        PremiumFeatureStore.purchase_feature(self.user, 'advanced_chunking')
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.has_advanced_chunking)
        self.assertEqual(self.user.current_xp_points, 0)  # 100 XP spent
    
    def test_insufficient_xp_error(self):
        """Test error handling for insufficient XP"""
        self.user.current_xp_points = 10
        self.user.save()
        
        with self.assertRaises(InsufficientXPError):
            PremiumFeatureStore.purchase_feature(self.user, 'advanced_chunking')
```

## Performance Considerations

### Database Optimization
- Index on user XP transactions for fast history retrieval
- Cache user feature ownership status
- Batch XP calculations for multiple users
- Use database transactions for XP operations

### Caching Strategy
```python
from django.core.cache import cache

class XPCacheManager:
    @staticmethod
    def get_user_features(user_id):
        """Get cached user feature ownership"""
        cache_key = f"user_features_{user_id}"
        features = cache.get(cache_key)
        
        if features is None:
            user = CustomUser.objects.get(id=user_id)
            features = {
                'has_opendyslexic_font': user.has_opendyslexic_font,
                'has_advanced_chunking': user.has_advanced_chunking,
                'has_connector_grouping': user.has_connector_grouping,
                'has_symbol_removal': user.has_symbol_removal,
                'has_premium_themes': user.has_premium_themes,
            }
            cache.set(cache_key, features, 3600)  # Cache for 1 hour
        
        return features
    
    @staticmethod
    def invalidate_user_features(user_id):
        """Invalidate user features cache after purchase"""
        cache_key = f"user_features_{user_id}"
        cache.delete(cache_key)
```

---

*This design document provides a comprehensive architecture for implementing an advanced XP economics system that gamifies VeriFast while creating opportunities for user engagement and monetization.*