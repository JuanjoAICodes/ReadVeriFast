# Speed Reader and Quiz Functionality Fix - Design

## Overview

This design addresses the complete failure of speed reader and quiz functionality in VeriFast. The issues stem from multiple problems including JavaScript initialization errors, API endpoint failures, template rendering issues, and missing dependencies. The solution involves a systematic approach to diagnose, fix, and test each component.

## Architecture

### Current System Analysis

Based on the code review, the system has these components:
- **Frontend**: Django templates with embedded JavaScript classes (SpeedReader, QuizInterface)
- **Backend**: Django views and API endpoints for quiz submission
- **Data Flow**: Article content → Speed Reader → Quiz unlock → API submission → XP rewards

### Identified Issues

1. **JavaScript Initialization Problems**
   - SpeedReader class may not be initializing properly
   - Quiz interface dependencies on speed reader completion
   - Missing error handling for DOM element selection

2. **API Endpoint Issues**
   - Quiz submission API may have bugs (typo found: `wmp_used` vs `wpm_used`)
   - Missing imports in views.py
   - CSRF token handling issues

3. **Template Integration Issues**
   - JavaScript loading order problems
   - Missing context variables
   - Template caching issues

4. **Dependency Issues**
   - Missing spacy dependency causing server crashes
   - Import errors in services.py

## Components and Interfaces

### 1. Speed Reader Component

**Class: SpeedReader**
```javascript
class SpeedReader {
    constructor(sectionId)
    init()
    validateElements()
    loadContent()
    startReading()
    pauseReading()
    resetReading()
    toggleImmersive()
    onReadingComplete() // Callback for quiz unlock
}
```

**Key Methods:**
- `validateElements()`: Ensure all required DOM elements exist
- `loadContent()`: Parse article content from data attributes
- `startReading()`: Begin word-by-word display with timing
- `onReadingComplete()`: Trigger quiz unlock when reading finishes

### 2. Quiz Interface Component

**Class: QuizInterface**
```javascript
class QuizInterface {
    constructor(quizData, articleId)
    init()
    startQuiz()
    displayQuestion(index)
    submitQuiz()
    showResults(result)
}
```

**Key Methods:**
- `startQuiz()`: Initialize quiz modal and first question
- `displayQuestion()`: Render question with options
- `submitQuiz()`: Send answers to API endpoint
- `showResults()`: Display score and XP rewards

### 3. API Endpoints

**Quiz Submission API**
```python
@csrf_exempt
@require_http_methods(["POST"])
@login_required
def quiz_submission_api(request):
    # Validate input data
    # Calculate score
    # Award XP for passing scores
    # Return results with feedback
```

**Expected Request Format:**
```json
{
    "article_id": 123,
    "user_answers": [0, 2, 1, 3, 0],
    "wpm_used": 300,
    "quiz_time_seconds": 120
}
```

**Expected Response Format:**
```json
{
    "success": true,
    "score": 80,
    "xp_awarded": 150,
    "feedback": [...]
}
```

### 4. Template Integration

**Article Detail Template Structure:**
```html
<!-- Speed Reader Section -->
<section id="speed-reader-section" 
         data-content="{{ article.content|escape }}"
         data-user-wpm="{{ user_wpm|default:250 }}"
         data-article-id="{{ article.id }}">
    <!-- Speed reader controls and display -->
</section>

<!-- Quiz Section -->
<section class="quiz-section">
    <!-- Quiz trigger button -->
</section>

<!-- JavaScript Initialization -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    const speedReader = new SpeedReader('speed-reader-section');
    const quizInterface = new QuizInterface(quizData, articleId);
    
    // Connect speed reader completion to quiz unlock
    speedReader.onReadingComplete = function() {
        // Enable quiz button
    };
});
</script>
```

## Data Models

### Quiz Submission Data Flow

1. **Input Validation**
   - Validate required fields: article_id, user_answers, wpm_used
   - Verify article exists and has quiz data
   - Check answer count matches question count

2. **Score Calculation**
   - Compare user answers with correct answers
   - Calculate percentage score
   - Generate feedback for each question

3. **XP Processing**
   - Award XP only for passing scores (≥60%)
   - Use QuizResultProcessor for XP calculations
   - Update user's XP balance atomically

4. **Response Generation**
   - Include score, XP awarded, and feedback
   - Set comment permission flag
   - Handle errors gracefully

## Error Handling

### JavaScript Error Handling

```javascript
class SpeedReader {
    init() {
        try {
            if (!this.validateElements()) {
                this.showFallbackMessage();
                return;
            }
            this.loadContent();
            this.attachEventListeners();
        } catch (error) {
            console.error('Speed Reader initialization failed:', error);
            this.showFallbackMessage();
        }
    }
    
    showFallbackMessage() {
        // Display user-friendly error message
        // Provide alternative access to article content
    }
}
```

### API Error Handling

```python
def quiz_submission_api(request):
    try:
        # Process quiz submission
        return JsonResponse(success_response)
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': 'Invalid input data'
        }, status=400)
    except Exception as e:
        logger.error(f"Quiz submission error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)
```

### Template Error Handling

```html
{% if article.quiz_data %}
    <!-- Quiz functionality available -->
{% else %}
    <p>Quiz not available for this article.</p>
{% endif %}

<script>
// Graceful degradation for missing elements
if (document.getElementById('speed-reader-section')) {
    // Initialize speed reader
} else {
    console.warn('Speed reader not available');
}
</script>
```

## Testing Strategy

### 1. Manual Testing with Puppeteer

**Test Scenarios:**
- Load article detail page and verify speed reader appears
- Test speed reader start/pause/reset functionality
- Test speed controls (increase/decrease WPM)
- Test immersive mode toggle
- Complete reading and verify quiz unlock
- Take quiz and verify score calculation
- Test API submission and XP rewards

**Puppeteer Test Flow:**
```javascript
// Navigate to article page
await page.goto('http://localhost:8000/articles/1/');

// Take screenshot of initial state
await page.screenshot({name: 'article-page-loaded'});

// Test speed reader initialization
const speedReaderExists = await page.$('#speed-reader-section');
console.log('Speed reader found:', !!speedReaderExists);

// Test start button functionality
await page.click('#start-pause-btn');
await page.waitForTimeout(2000);
await page.screenshot({name: 'speed-reader-running'});
```

### 2. Unit Testing

**JavaScript Unit Tests:**
- Test SpeedReader class initialization
- Test word parsing and display logic
- Test speed adjustment calculations
- Test quiz interface state management

**Python Unit Tests:**
- Test quiz submission API with valid data
- Test score calculation logic
- Test XP award calculations
- Test error handling scenarios

### 3. Integration Testing

**End-to-End Flow:**
1. User loads article page
2. Speed reader initializes and displays content
3. User completes reading
4. Quiz becomes available
5. User takes quiz and submits answers
6. System calculates score and awards XP
7. Results are displayed to user

## Implementation Priority

### Phase 1: Critical Fixes (Immediate)
1. Fix spacy dependency issue in services.py
2. Fix typo in API views (`wmp_used` → `wpm_used`)
3. Add missing imports in views.py
4. Test basic server functionality

### Phase 2: Speed Reader Restoration
1. Verify SpeedReader class initialization
2. Test DOM element selection and validation
3. Fix word parsing and display logic
4. Test speed controls and immersive mode

### Phase 3: Quiz Interface Restoration
1. Verify QuizInterface class initialization
2. Test quiz modal display and navigation
3. Fix API submission and response handling
4. Test XP award and result display

### Phase 4: Integration and Polish
1. Connect speed reader completion to quiz unlock
2. Improve error handling and user feedback
3. Add comprehensive logging for debugging
4. Optimize performance and user experience

This design provides a systematic approach to diagnosing and fixing the broken speed reader and quiz functionality, with clear testing strategies and implementation priorities.