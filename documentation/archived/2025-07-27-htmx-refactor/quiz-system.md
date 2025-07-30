# Quiz System Documentation

## Overview

The VeriFast Quiz System is a pure HTMX + Django implementation that provides interactive comprehension quizzes with gamification integration. The system is designed for reliability, security, and seamless integration with the speed reader.

## Core Features

### 1. Quiz Interface
- **Progressive Questions**: One question at a time with navigation
- **Multiple Choice**: 4-option questions with single selection
- **Answer Tracking**: Client-side answer storage with server validation
- **Progress Indication**: Current question / total questions display

### 2. Scoring System
- **Server-Side Calculation**: All scoring done securely on Django backend
- **Immediate Feedback**: Results displayed upon submission
- **Passing Threshold**: 60% required to pass and earn XP
- **Detailed Results**: Question-by-question breakdown for passing scores

### 3. XP Integration
- **Dynamic XP Calculation**: Based on score, speed, and article difficulty
- **Bonus Multipliers**: Speed bonuses and perfect score rewards
- **User Progression**: Automatic level updates and feature unlocks
- **Transaction Logging**: Complete audit trail of XP awards

## Technical Architecture

### Backend Components

#### Views
```python
# verifast_app/views/quiz.py
def quiz_init(request, article_id):
    """Initialize quiz with complete question data"""
    article = get_object_or_404(Article, id=article_id)
    
    if not article.quiz_data:
        return render(request, 'partials/no_quiz_available.html')
    
    # Initialize quiz session for tracking
    request.session[f'quiz_{article_id}'] = {
        'start_time': time.time(),
        'article_id': article_id,
        'user_id': request.user.id if request.user.is_authenticated else None
    }
    
    return render(request, 'partials/quiz_interface.html', {
        'quiz_data_json': json.dumps(article.quiz_data),
        'article_id': article_id,
        'total_questions': len(article.quiz_data),
        'user_authenticated': request.user.is_authenticated
    })

def quiz_submit(request, article_id):
    """Process quiz submission and award XP"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Parse submission data
        answers = json.loads(request.POST.get('answers', '[]'))
        wpm_used = int(request.POST.get('wpm_used', 250))
        quiz_time = int(request.POST.get('quiz_time', 0))
        
        # Validate submission
        article = get_object_or_404(Article, id=article_id)
        if not article.quiz_data or len(answers) != len(article.quiz_data):
            return JsonResponse({'error': 'Invalid submission'}, status=400)
        
        # Calculate score server-side for security
        score_data = calculate_quiz_score(article.quiz_data, answers)
        
        # Save quiz attempt and award XP
        xp_awarded = 0
        if request.user.is_authenticated:
            quiz_attempt = QuizAttempt.objects.create(
                user=request.user,
                article=article,
                score=score_data['percentage'],
                wpm_used=wpm_used,
                quiz_time_seconds=quiz_time,
                result={
                    'answers': answers,
                    'correct_answers': score_data['correct_answers'],
                    'feedback': score_data['feedback']
                }
            )
            
            # Award XP using the centralized processor
            if score_data['percentage'] >= 60:  # Passing score
                xp_awarded = QuizResultProcessor.process_quiz_completion(
                    quiz_attempt, article, request.user
                )
        else:
            # Handle anonymous users with session storage
            handle_anonymous_quiz_completion(request, article_id, score_data, wpm_used)
        
        return render(request, 'partials/quiz_results.html', {
            'score': score_data['percentage'],
            'correct_count': score_data['correct_count'],
            'total_questions': len(article.quiz_data),
            'xp_awarded': xp_awarded,
            'passed': score_data['percentage'] >= 60,
            'feedback': score_data['feedback'] if score_data['percentage'] >= 60 else None,
            'user_authenticated': request.user.is_authenticated
        })
        
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.error(f"Quiz submission error: {e}")
        return JsonResponse({'error': 'Invalid submission data'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected quiz error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

def calculate_quiz_score(quiz_data, user_answers):
    """Calculate quiz score with detailed feedback"""
    correct_count = 0
    feedback = []
    
    for i, (question, user_answer) in enumerate(zip(quiz_data, user_answers)):
        # Find correct answer index
        correct_answer = question.get('correct_answer', question.get('answer'))
        
        # Handle different answer formats
        if isinstance(correct_answer, str):
            # Answer is the text of the correct option
            correct_index = question['options'].index(correct_answer)
        else:
            # Answer is already an index
            correct_index = correct_answer
        
        is_correct = user_answer == correct_index
        if is_correct:
            correct_count += 1
        
        feedback.append({
            'question_index': i,
            'question': question['question'],
            'user_answer': question['options'][user_answer] if 0 <= user_answer < len(question['options']) else 'No answer',
            'correct_answer': question['options'][correct_index],
            'is_correct': is_correct,
            'explanation': question.get('explanation', '')
        })
    
    percentage = (correct_count / len(quiz_data)) * 100
    
    return {
        'correct_count': correct_count,
        'percentage': round(percentage, 1),
        'feedback': feedback,
        'correct_answers': [f['correct_answer'] for f in feedback]
    }
```

#### XP Processing
```python
# verifast_app/xp_system.py
class QuizResultProcessor:
    @staticmethod
    def process_quiz_completion(quiz_attempt, article, user):
        """Process quiz completion and award XP with bonuses"""
        
        # Base XP calculation
        base_xp = quiz_attempt.score * 10  # 10 XP per percentage point
        
        # Speed bonus (up to 2x multiplier)
        speed_multiplier = min(quiz_attempt.wpm_used / 250, 2.0)
        speed_bonus = base_xp * (speed_multiplier - 1) * 0.5
        
        # Difficulty bonus based on article reading level
        difficulty_bonus = (article.reading_level or 1.0) * 25
        
        # Perfect score bonus
        perfect_bonus = 100 if quiz_attempt.score >= 100 else 0
        
        # First attempt bonus
        first_attempt_bonus = 0
        if not QuizAttempt.objects.filter(
            user=user, 
            article=article
        ).exclude(id=quiz_attempt.id).exists():
            first_attempt_bonus = 50
        
        # Calculate total XP
        total_xp = int(base_xp + speed_bonus + difficulty_bonus + perfect_bonus + first_attempt_bonus)
        
        # Award XP to user
        with transaction.atomic():
            user.total_xp += total_xp
            user.current_xp_points += total_xp
            user.save()
            
            # Create XP transaction record
            XPTransaction.objects.create(
                user=user,
                transaction_type='EARN',
                amount=total_xp,
                source='quiz_completion',
                description=f'Quiz completed: "{article.title}" ({quiz_attempt.score}%)',
                balance_after=user.current_xp_points,
                quiz_attempt=quiz_attempt,
                metadata={
                    'base_xp': base_xp,
                    'speed_bonus': speed_bonus,
                    'difficulty_bonus': difficulty_bonus,
                    'perfect_bonus': perfect_bonus,
                    'first_attempt_bonus': first_attempt_bonus
                }
            )
            
            # Update quiz attempt with XP awarded
            quiz_attempt.xp_awarded = total_xp
            quiz_attempt.save()
        
        return total_xp

def handle_anonymous_quiz_completion(request, article_id, score_data, wpm_used):
    """Handle quiz completion for anonymous users using sessions"""
    if 'quiz_attempts' not in request.session:
        request.session['quiz_attempts'] = {}
    if 'total_xp' not in request.session:
        request.session['total_xp'] = 0
    
    # Calculate XP for anonymous user (simplified)
    base_xp = score_data['percentage'] * 5  # Reduced XP for anonymous users
    speed_bonus = max(0, (wpm_used - 250) / 10)  # Small speed bonus
    total_xp = int(base_xp + speed_bonus)
    
    # Store in session
    article_key = str(article_id)
    request.session['quiz_attempts'][article_key] = {
        'score': score_data['percentage'],
        'wmp_used': wpm_used,
        'xp_awarded': total_xp,
        'timestamp': time.time(),
        'correct_count': score_data['correct_count']
    }
    
    request.session['total_xp'] += total_xp
    request.session['current_wpm'] = wpm_used
    request.session.modified = True
    
    return total_xp
```

### Frontend Components

#### Pure HTMX Quiz Interface
```html
<!-- templates/partials/quiz_interface.html -->
<div id="quiz-container" class="quiz-interface">
    <!-- Quiz Header -->
    <div class="quiz-header">
        <h2>{% trans "Comprehension Quiz" %}</h2>
        <div class="quiz-progress">
            <span class="progress-text">
                Question <span id="current-question-num">1</span> of {{ total_questions }}
            </span>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {{ 100|div:total_questions }}%"></div>
            </div>
        </div>
    </div>
    
    <!-- Quiz Form -->
    <form id="quiz-form" 
          hx-post="{% url 'quiz_submit' article_id %}"
          hx-target="#quiz-results"
          hx-swap="innerHTML"
          hx-indicator="#quiz-loading">
        
        {% csrf_token %}
        
        <!-- Questions Container -->
        <div id="questions-container">
            <!-- Questions will be rendered by JavaScript -->
        </div>
        
        <!-- Navigation -->
        <div class="quiz-navigation">
            <button type="button" 
                    id="prev-btn" 
                    onclick="previousQuestion()"
                    disabled>
                {% trans "Previous" %}
            </button>
            
            <button type="button" 
                    id="next-btn" 
                    onclick="nextQuestion()">
                {% trans "Next" %}
            </button>
            
            <button type="submit" 
                    id="submit-btn" 
                    style="display: none;"
                    class="primary">
                {% trans "Submit Quiz" %}
            </button>
        </div>
        
        <!-- Hidden fields for submission -->
        <input type="hidden" name="answers" id="answers-input">
        <input type="hidden" name="wmp_used" id="wpm-input" value="250">
        <input type="hidden" name="quiz_time" id="quiz-time-input">
    </form>
    
    <!-- Loading Indicator -->
    <div id="quiz-loading" class="loading-indicator" style="display: none;">
        <div class="spinner"></div>
        <p>{% trans "Calculating your score..." %}</p>
    </div>
    
    <!-- Results Container -->
    <div id="quiz-results"></div>
</div>

<!-- Minimal JavaScript for quiz navigation -->
<script>
// Quiz data from Django
const quizData = {{ quiz_data_json|safe }};
let currentQuestion = 0;
let userAnswers = new Array(quizData.length).fill(null);
let quizStartTime = Date.now();

// Initialize quiz
document.addEventListener('DOMContentLoaded', function() {
    renderQuestion(0);
    updateNavigation();
});

function renderQuestion(index) {
    const question = quizData[index];
    const container = document.getElementById('questions-container');
    
    container.innerHTML = `
        <div class="question">
            <h3>${question.question}</h3>
            <div class="options">
                ${question.options.map((option, i) => `
                    <label class="option">
                        <input type="radio" 
                               name="question_${index}" 
                               value="${i}"
                               ${userAnswers[index] === i ? 'checked' : ''}
                               onchange="selectAnswer(${index}, ${i})">
                        <span class="option-text">${option}</span>
                    </label>
                `).join('')}
            </div>
        </div>
    `;
    
    // Update progress
    document.getElementById('current-question-num').textContent = index + 1;
    const progressFill = document.querySelector('.progress-fill');
    progressFill.style.width = `${((index + 1) / quizData.length) * 100}%`;
}

function selectAnswer(questionIndex, answerIndex) {
    userAnswers[questionIndex] = answerIndex;
    updateNavigation();
}

function nextQuestion() {
    if (currentQuestion < quizData.length - 1) {
        currentQuestion++;
        renderQuestion(currentQuestion);
        updateNavigation();
    }
}

function previousQuestion() {
    if (currentQuestion > 0) {
        currentQuestion--;
        renderQuestion(currentQuestion);
        updateNavigation();
    }
}

function updateNavigation() {
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const submitBtn = document.getElementById('submit-btn');
    
    // Previous button
    prevBtn.disabled = currentQuestion === 0;
    
    // Next/Submit button logic
    const isLastQuestion = currentQuestion === quizData.length - 1;
    const allAnswered = userAnswers.every(answer => answer !== null);
    
    if (isLastQuestion) {
        nextBtn.style.display = 'none';
        submitBtn.style.display = 'inline-block';
        submitBtn.disabled = !allAnswered;
    } else {
        nextBtn.style.display = 'inline-block';
        submitBtn.style.display = 'none';
        nextBtn.disabled = false;
    }
}

// Handle form submission
document.getElementById('quiz-form').addEventListener('submit', function(e) {
    // Prepare submission data
    document.getElementById('answers-input').value = JSON.stringify(userAnswers);
    document.getElementById('quiz-time-input').value = Math.floor((Date.now() - quizStartTime) / 1000);
    
    // Get WPM from speed reader if available
    if (window.speedReader && window.speedReader.wpm) {
        document.getElementById('wpm-input').value = window.speedReader.wpm;
    }
});
</script>
```

#### Quiz Results Template
```html
<!-- templates/partials/quiz_results.html -->
<div class="quiz-results">
    <div class="results-header">
        <h3>{% trans "Quiz Complete!" %}</h3>
        <div class="score-display {{ passed|yesno:'passed,failed' }}">
            <div class="score-circle">
                <span class="score-number">{{ score }}%</span>
            </div>
            <div class="score-details">
                <p>{{ correct_count }} out of {{ total_questions }} correct</p>
                {% if passed %}
                    <p class="success">🎉 {% trans "Congratulations! You passed!" %}</p>
                {% else %}
                    <p class="failure">{% trans "You need 60% or higher to pass. Try reading the article again!" %}</p>
                {% endif %}
            </div>
        </div>
    </div>
    
    {% if user_authenticated and passed %}
    <div class="xp-reward">
        <h4>{% trans "XP Earned" %}</h4>
        <div class="xp-breakdown">
            <div class="xp-total">
                <span class="xp-amount">+{{ xp_awarded }}</span>
                <span class="xp-label">{% trans "Total XP" %}</span>
            </div>
            <div class="xp-details">
                <small>{% trans "Added to your account balance" %}</small>
            </div>
        </div>
    </div>
    {% elif not user_authenticated %}
    <div class="registration-prompt">
        <h4>{% trans "Want to save your progress?" %}</h4>
        <p>{% trans "Register now to save your XP and unlock more features!" %}</p>
        <a href="{% url 'register' %}" class="btn primary">{% trans "Register Free" %}</a>
    </div>
    {% endif %}
    
    {% if feedback and passed %}
    <div class="quiz-feedback">
        <h4>{% trans "Review Your Answers" %}</h4>
        <div class="feedback-list">
            {% for item in feedback %}
            <div class="feedback-item {{ item.is_correct|yesno:'correct,incorrect' }}">
                <div class="feedback-header">
                    <span class="question-number">Q{{ forloop.counter }}</span>
                    <span class="result-icon">{{ item.is_correct|yesno:'✓,✗' }}</span>
                </div>
                <div class="feedback-content">
                    <p class="question-text">{{ item.question }}</p>
                    <div class="answer-comparison">
                        <div class="user-answer">
                            <strong>{% trans "Your answer:" %}</strong> {{ item.user_answer }}
                        </div>
                        {% if not item.is_correct %}
                        <div class="correct-answer">
                            <strong>{% trans "Correct answer:" %}</strong> {{ item.correct_answer }}
                        </div>
                        {% endif %}
                    </div>
                    {% if item.explanation %}
                    <div class="explanation">
                        <strong>{% trans "Explanation:" %}</strong> {{ item.explanation }}
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}
    
    <div class="results-actions">
        {% if not passed %}
        <button onclick="location.reload()" class="btn secondary">
            {% trans "Try Again" %}
        </button>
        {% endif %}
        
        <a href="{% url 'article_list' %}" class="btn primary">
            {% trans "Continue Reading" %}
        </a>
        
        {% if user_authenticated %}
        <a href="{% url 'user_profile' %}" class="btn secondary">
            {% trans "View Profile" %}
        </a>
        {% endif %}
    </div>
</div>
```

## Integration with Speed Reader

### Automatic Quiz Unlock
```html
<!-- Speed reader completion triggers quiz unlock -->
<div x-show="isComplete" 
     x-init="$watch('isComplete', value => { 
         if (value) unlockQuiz(); 
     })">
    
    <div class="reading-complete-message">
        <h3>🎉 {% trans "Reading Complete!" %}</h3>
        <p>{% trans "You're ready to take the quiz and earn XP!" %}</p>
        <button @click="startQuiz()" class="btn primary">
            {% trans "Start Quiz" %}
        </button>
    </div>
</div>

<script>
function unlockQuiz() {
    // Show quiz section
    document.getElementById('quiz-section').style.display = 'block';
    
    // Smooth scroll to quiz
    document.getElementById('quiz-section').scrollIntoView({ 
        behavior: 'smooth' 
    });
    
    // Load quiz via HTMX
    htmx.ajax('GET', `/quiz/init/{{ article.id }}/`, {
        target: '#quiz-container',
        swap: 'innerHTML'
    });
}
</script>
```

### WPM Transfer
```javascript
// Transfer reading speed from speed reader to quiz
function startQuiz() {
    htmx.ajax('GET', `/quiz/init/{{ article.id }}/`, {
        target: '#quiz-container',
        swap: 'innerHTML'
    }).then(() => {
        // Pass WPM to quiz after it loads
        if (window.speedReader && document.getElementById('wpm-input')) {
            document.getElementById('wpm-input').value = window.speedReader.wpm;
        }
    });
}
```

## Anonymous User Support

### Session-Based Tracking
```python
def handle_anonymous_quiz_completion(request, article_id, score_data, wpm_used):
    """Handle quiz completion for anonymous users"""
    
    # Initialize session data if needed
    if 'quiz_attempts' not in request.session:
        request.session['quiz_attempts'] = {}
        request.session['total_xp'] = 0
        request.session.set_expiry(60 * 24 * 60 * 60)  # 60 days
    
    # Calculate simplified XP for anonymous users
    xp_earned = int(score_data['percentage'] * 5)  # 5 XP per percentage point
    
    # Store attempt in session
    article_key = str(article_id)
    request.session['quiz_attempts'][article_key] = {
        'score': score_data['percentage'],
        'wmp_used': wpm_used,
        'xp_awarded': xp_earned,
        'timestamp': time.time(),
        'passed': score_data['percentage'] >= 60
    }
    
    request.session['total_xp'] += xp_earned
    request.session.modified = True
    
    return xp_earned
```

### Registration Transfer
```python
# When anonymous user registers, transfer session data
def transfer_session_data_to_user(request, user):
    """Transfer anonymous session data to newly registered user"""
    
    session_xp = request.session.get('total_xp', 0)
    session_attempts = request.session.get('quiz_attempts', {})
    
    if session_xp > 0 or session_attempts:
        with transaction.atomic():
            # Transfer XP
            user.total_xp += session_xp
            user.current_xp_points += session_xp
            
            # Transfer quiz attempts
            transferred_count = 0
            for article_id, attempt_data in session_attempts.items():
                try:
                    article = Article.objects.get(id=int(article_id))
                    QuizAttempt.objects.create(
                        user=user,
                        article=article,
                        score=attempt_data['score'],
                        wmp_used=attempt_data['wpm_used'],
                        xp_awarded=attempt_data['xp_awarded'],
                        result={'transferred_from_session': True}
                    )
                    transferred_count += 1
                except (Article.DoesNotExist, ValueError):
                    continue
            
            user.save()
            
            # Clear session data
            request.session.pop('total_xp', None)
            request.session.pop('quiz_attempts', None)
            request.session.modified = True
            
            return transferred_count
    
    return 0
```

## Security Considerations

### Server-Side Validation
- **Answer Validation**: All answers validated against stored quiz data
- **Score Calculation**: Performed server-side to prevent manipulation
- **XP Awards**: Cannot be modified client-side
- **Submission Limits**: Rate limiting to prevent spam

### Input Sanitization
```python
def validate_quiz_submission(answers, quiz_data):
    """Validate quiz submission data"""
    
    # Check answer format
    if not isinstance(answers, list):
        raise ValidationError("Answers must be a list")
    
    # Check answer count
    if len(answers) != len(quiz_data):
        raise ValidationError("Answer count mismatch")
    
    # Validate each answer
    for i, answer in enumerate(answers):
        if not isinstance(answer, int) or answer < 0 or answer >= len(quiz_data[i]['options']):
            raise ValidationError(f"Invalid answer for question {i + 1}")
    
    return True
```

### CSRF Protection
- **All forms**: Include Django CSRF tokens
- **HTMX requests**: Automatic CSRF handling
- **API endpoints**: Protected by Django middleware

## Performance Optimization

### Caching Strategy
```python
# Cache quiz data processing
@cache_page(60 * 30)  # 30 minutes
def quiz_init(request, article_id):
    # Implementation with caching
    
# Cache user quiz history
def get_user_quiz_stats(user):
    cache_key = f'quiz_stats_{user.id}'
    return cache.get_or_set(cache_key, calculate_quiz_stats(user), 600)
```

### Database Optimization
```python
# Optimize quiz attempt queries
def get_user_quiz_attempts(user, limit=10):
    return QuizAttempt.objects.filter(user=user)\
        .select_related('article')\
        .order_by('-timestamp')[:limit]
```

## Analytics and Reporting

### Quiz Analytics
```python
class QuizAnalytics:
    @staticmethod
    def get_quiz_completion_rate(article):
        """Calculate completion rate for an article's quiz"""
        total_attempts = QuizAttempt.objects.filter(article=article).count()
        if total_attempts == 0:
            return 0
        
        passed_attempts = QuizAttempt.objects.filter(
            article=article, 
            score__gte=60
        ).count()
        
        return (passed_attempts / total_attempts) * 100
    
    @staticmethod
    def get_average_score(article):
        """Get average quiz score for an article"""
        return QuizAttempt.objects.filter(article=article)\
            .aggregate(avg_score=Avg('score'))['avg_score'] or 0
    
    @staticmethod
    def get_question_difficulty(article):
        """Analyze which questions are most difficult"""
        attempts = QuizAttempt.objects.filter(article=article)
        question_stats = []
        
        for attempt in attempts:
            feedback = attempt.result.get('feedback', [])
            for item in feedback:
                # Analyze question difficulty based on correct/incorrect rates
                pass
        
        return question_stats
```

This documentation provides a comprehensive guide to the Quiz System, covering all aspects from technical implementation to security and performance considerations.