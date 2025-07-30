# Core Functionality Fixes - Design Document

## Overview

This design document outlines the technical approach to fix critical functionality issues in the VeriFast application. The problems stem from template errors, missing JavaScript functionality, incomplete view context data, and broken frontend-backend integration. The solution involves systematic debugging and repair of each component layer.

## Architecture

### Problem Analysis

Based on the current status (profile page working, template filters fixed), the remaining issues are:

1. **Premium Feature Store**: Purchase buttons not working, features not showing properly
2. **Speed Reader System**: JavaScript not initializing, content not loading into reader
3. **Quiz System**: Quiz interface not working, XP not being awarded
4. **Article Content Display**: Content not showing in article detail view
5. **Comment System**: Comment posting and interaction buttons not functioning
6. **Tag Display**: Article tags not appearing on article pages

### Solution Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   Templates     │◄──►│   Views         │◄──►│   Models        │
│   JavaScript    │    │   Context       │    │   Transactions  │
│   CSS Styles    │    │   API Endpoints │    │   Integrity     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Template Fixes  │    │ View Context    │    │ Model Validation│
│ Filter Registry │    │ Data Passing    │    │ XP Transactions │
│ Component Load  │    │ Error Handling  │    │ Feature Unlocks │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components and Interfaces

### 1. Template System Repair

**Template Filter Registry**
```python
# verifast_app/templatetags/xp_filters.py
from django import template

register = template.Library()

@register.filter
def floatdiv(value, divisor):
    """Divide value by divisor, return float"""
    try:
        return float(value) / float(divisor)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter  
def modulo(value, divisor):
    """Return remainder of division"""
    try:
        return int(value) % int(divisor)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def multiply(value, multiplier):
    """Multiply value by multiplier"""
    try:
        return float(value) * float(multiplier)
    except (ValueError, TypeError):
        return 0
```

**Template Component Loading**
```html
<!-- Ensure all components load custom filters -->
{% load xp_filters %}
{% load static %}

<!-- Verify component file paths -->
{% include 'verifast_app/components/xp_balance_widget.html' with user=user_profile %}
{% include 'verifast_app/components/xp_notifications.html' %}
{% include 'verifast_app/components/xp_transaction_history.html' %}
```

### 2. Article Content Display Fix

**View Context Enhancement**
```python
class ArticleDetailView(DetailView):
    model = Article
    template_name = 'verifast_app/article_detail.html'
    context_object_name = 'article'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ensure article content is available
        if not self.object.content:
            context['content_error'] = "Article content is not available"
        
        # Add user context for authenticated users
        if self.request.user.is_authenticated:
            context.update({
                'user_has_completed_quiz': self._check_quiz_completion(),
                'user_xp': self.request.user.total_xp,
                'user_wpm': self.request.user.current_wpm,
                'user_spendable_xp': self.request.user.current_xp_points,
            })
        else:
            # Handle anonymous users with session data
            context.update({
                'user_has_completed_quiz': self._check_session_quiz(),
                'user_xp': self.request.session.get('total_xp', 0),
                'user_wpm': self.request.session.get('current_wpm', 250),
                'user_spendable_xp': 0,
            })
        
        return context
```

**Template Content Display**
```html
<!-- Article content section -->
<section class="article-content">
    <h3>Article Content</h3>
    {% if article.content %}
        <div class="content-text">
            {{ article.content|linebreaks }}
        </div>
    {% else %}
        <div class="content-error">
            <p>Article content is not available. Please try refreshing the page.</p>
        </div>
    {% endif %}
</section>
```

### 3. Speed Reader JavaScript Repair

**Speed Reader Initialization**
```javascript
document.addEventListener('DOMContentLoaded', () => {
    const speedReaderSection = document.getElementById('speed-reader-section');
    
    // Verify article content exists
    if (!speedReaderSection) {
        console.error('Speed reader section not found');
        return;
    }
    
    const articleContent = speedReaderSection.dataset.content;
    
    if (!articleContent || articleContent.trim() === '') {
        console.error('No article content available for speed reader');
        displaySpeedReaderError('No content available for speed reading');
        return;
    }
    
    // Initialize speed reader with content
    initializeSpeedReader(articleContent);
});

function displaySpeedReaderError(message) {
    const wordDisplay = document.getElementById('word-display');
    if (wordDisplay) {
        wordDisplay.textContent = message;
        wordDisplay.style.color = 'red';
    }
}

function initializeSpeedReader(content) {
    // Clean and split words
    const words = cleanAndSplitWords(content);
    
    if (words.length === 0) {
        displaySpeedReaderError('Unable to process article content');
        return;
    }
    
    // Initialize speed reader controls
    setupSpeedReaderControls(words);
}
```

### 4. Quiz System Repair

**Quiz JavaScript Integration**
```javascript
class QuizSystem {
    constructor(quizData) {
        this.quizData = quizData;
        this.currentQuestion = 0;
        this.userAnswers = [];
        this.startTime = null;
    }
    
    initialize() {
        if (!this.quizData || !this.quizData.questions) {
            this.displayError('Quiz data is not available');
            return false;
        }
        
        this.setupQuizInterface();
        return true;
    }
    
    displayError(message) {
        const quizContainer = document.getElementById('quiz-container');
        if (quizContainer) {
            quizContainer.innerHTML = `
                <div class="quiz-error">
                    <p>${message}</p>
                    <button onclick="location.reload()">Refresh Page</button>
                </div>
            `;
        }
    }
    
    submitQuiz() {
        const score = this.calculateScore();
        const wpm = this.getCurrentWPM();
        const timeSpent = Date.now() - this.startTime;
        
        // Submit to backend
        this.sendQuizResults(score, wpm, timeSpent);
    }
}
```

### 5. Comment System Integration

**Comment Form Handling**
```python
def post(self, request, *args, **kwargs):
    self.object = self.get_object()
    user = request.user
    
    if 'post_comment' in request.POST:
        if not user.is_authenticated:
            messages.error(request, "Please register or login to post comments.")
            return redirect(self.object.get_absolute_url())
        
        # Check quiz completion
        if not self._user_has_completed_quiz(user):
            messages.error(request, "Complete the quiz with 60%+ score to unlock commenting.")
            return redirect(self.object.get_absolute_url())
        
        # Check XP balance
        comment_cost = 10  # XP cost for new comment
        if user.current_xp_points < comment_cost:
            messages.error(request, f"You need {comment_cost} XP to post a comment. You have {user.current_xp_points} XP.")
            return redirect(self.object.get_absolute_url())
        
        # Process comment
        content = request.POST.get('comment_content', '').strip()
        if content:
            success = self._create_comment(user, content, comment_cost)
            if success:
                messages.success(request, "Your comment has been posted.")
            else:
                messages.error(request, "Failed to post comment. Please try again.")
        
    return redirect(self.object.get_absolute_url())
```

### 6. Premium Feature Purchase System

**Purchase API Endpoint**
```python
class PurchaseFeatureView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            feature_key = data.get('feature_key')
            
            if not feature_key:
                return JsonResponse({
                    'success': False,
                    'error': 'Feature key is required'
                }, status=400)
            
            # Validate feature exists and get cost
            feature_info = self._get_feature_info(feature_key)
            if not feature_info:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid feature'
                }, status=400)
            
            # Check if user already owns feature
            if self._user_owns_feature(request.user, feature_key):
                return JsonResponse({
                    'success': False,
                    'error': 'Feature already owned'
                }, status=400)
            
            # Check XP balance
            if request.user.current_xp_points < feature_info['cost']:
                return JsonResponse({
                    'success': False,
                    'error': f'Insufficient XP. Need {feature_info["cost"]}, have {request.user.current_xp_points}'
                }, status=400)
            
            # Process purchase
            with transaction.atomic():
                success = self._process_purchase(request.user, feature_key, feature_info)
                
                if success:
                    return JsonResponse({
                        'success': True,
                        'message': f'Successfully purchased {feature_info["name"]}!',
                        'new_balance': request.user.current_xp_points
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Purchase failed. Please try again.'
                    }, status=500)
                    
        except Exception as e:
            logger.error(f"Purchase error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An unexpected error occurred'
            }, status=500)
```

**Frontend Purchase Integration**
```javascript
function purchaseFeature(featureKey, cost, featureName) {
    // Show loading state
    const modal = document.getElementById('purchase-modal');
    const confirmBtn = document.getElementById('confirm-purchase');
    
    if (!confirmBtn) {
        alert('Purchase interface not available');
        return;
    }
    
    confirmBtn.textContent = 'Processing...';
    confirmBtn.disabled = true;

    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken) {
        alert('Security token not found. Please refresh the page.');
        return;
    }

    // Make purchase request
    fetch('/purchase-feature/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken.value
        },
        body: JSON.stringify({
            feature_key: featureKey
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert(`Successfully purchased ${featureName}!`);
            window.location.reload();
        } else {
            alert(`Error: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Purchase error:', error);
        alert('An error occurred while processing your purchase. Please try again.');
    })
    .finally(() => {
        if (modal && modal.close) {
            modal.close();
        }
        confirmBtn.textContent = 'Confirm Purchase';
        confirmBtn.disabled = false;
    });
}
```

## Data Models

### Model Validation and Integrity

**User Model Validation**
```python
class CustomUser(AbstractUser):
    # Existing fields...
    
    def clean(self):
        super().clean()
        # Validate XP fields
        if self.current_xp_points < 0:
            raise ValidationError('Spendable XP cannot be negative')
        if self.total_xp < 0:
            raise ValidationError('Total XP cannot be negative')
    
    def has_sufficient_xp(self, amount):
        """Check if user has enough spendable XP"""
        return self.current_xp_points >= amount
    
    def spend_xp(self, amount, description):
        """Safely spend XP with transaction logging"""
        if not self.has_sufficient_xp(amount):
            raise InsufficientXPError(f'Need {amount} XP, have {self.current_xp_points}')
        
        with transaction.atomic():
            self.current_xp_points -= amount
            self.save()
            
            # Log transaction
            XPTransaction.objects.create(
                user=self,
                transaction_type='SPEND',
                amount=-amount,
                description=description,
                balance_after=self.current_xp_points
            )
```

## Error Handling

### Comprehensive Error Management

**Template Error Handling**
```python
# Custom template context processor
def error_context_processor(request):
    """Add error handling context to all templates"""
    return {
        'debug_mode': settings.DEBUG,
        'user_authenticated': request.user.is_authenticated,
        'has_errors': bool(messages.get_messages(request)),
    }
```

**JavaScript Error Handling**
```javascript
// Global error handler
window.addEventListener('error', function(event) {
    console.error('JavaScript error:', event.error);
    
    // Show user-friendly message for critical errors
    if (event.error.message.includes('speed-reader') || 
        event.error.message.includes('quiz')) {
        showErrorNotification('A feature is temporarily unavailable. Please refresh the page.');
    }
});

function showErrorNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'error-notification';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #ff4444;
        color: white;
        padding: 15px;
        border-radius: 5px;
        z-index: 10000;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}
```

## Testing Strategy

### Component Testing Approach

1. **Template Rendering Tests**
   - Verify all custom filters work correctly
   - Test template component loading
   - Validate context data passing

2. **JavaScript Functionality Tests**
   - Test speed reader initialization with various content types
   - Verify quiz system handles missing data gracefully
   - Test purchase flow with different user states

3. **Backend Integration Tests**
   - Test view context data completeness
   - Verify XP transaction atomicity
   - Test error handling for edge cases

4. **End-to-End User Flow Tests**
   - Complete article reading and quiz flow
   - Test comment posting with XP deduction
   - Verify premium feature purchase and activation

---

*This design provides a systematic approach to fixing all identified functionality issues while maintaining data integrity and user experience.*