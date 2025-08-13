# Quiz Generation & Speed Reader Fix Roadmap

## Current Status & Context

### What We've Accomplished
- ✅ **Identified the root cause**: Quiz button was hiding speed reader due to problematic JavaScript
- ✅ **Created working quiz overlay**: Implemented via JavaScript injection with full functionality
- ✅ **Tested quiz flow**: Complete question navigation, scoring, and results display working
- ✅ **Analyzed entire system**: Comprehensive review of quiz generation pipeline

### Current Working State
- **Speed Reader**: Functional with normal and immersive modes
- **Quiz System**: Working on Wikipedia articles via JavaScript injection
- **Integration**: Quiz opens in centered overlay without breaking speed reader

### Issues Discovered
- **Quiz Generation**: Hard-coded to 5 questions regardless of article length
- **Article Coverage**: Long articles (10k+ words) get insufficient question coverage
- **Regular Articles**: May not have quiz data due to processing failures
- **Speed Reader**: Needs to be immersive-only with enhanced visual design
- **Template Issues**: Django template caching preventing proper HTML structure updates

---

## Complete Issues List

### Backend Issues (Priority Order)

#### 1. **Dynamic Quiz Question Count** 🔴 HIGH PRIORITY
- **Problem**: Hard-coded 5 questions for all articles
- **Files**: `verifast_app/services.py`, `verifast_app/pydantic_models/llm.py`
- **Impact**: Insufficient coverage for long articles, over-questioning short articles
- **Solution**: Implement content-length-based question scaling (5-30 questions)

#### 2. **Enhanced Content Coverage Algorithm** 🔴 HIGH PRIORITY  
- **Problem**: Questions don't cover all main points comprehensively
- **Files**: `verifast_app/services.py` (prompt engineering)
- **Impact**: Important topics missed in quiz generation
- **Solution**: Update prompts to ensure comprehensive main point coverage

#### 3. **Regular Article Quiz Generation Reliability** 🔴 HIGH PRIORITY
- **Problem**: Regular articles may not have quiz_data due to failed processing
- **Files**: `verifast_app/tasks.py`, `verifast_app/views.py`
- **Impact**: Users see "Quiz not available" for processable articles
- **Solution**: Add fallback quiz generation and better error handling

#### 4. **Unified Article Processing** 🟡 MEDIUM PRIORITY
- **Problem**: Different processing paths for Wikipedia vs regular articles
- **Files**: `verifast_app/tasks.py`
- **Impact**: Inconsistent user experience and maintenance complexity
- **Solution**: Consolidate processing logic with article-type-aware handling

#### 5. **Reading-Level-Aware Question Complexity** 🟡 MEDIUM PRIORITY
- **Problem**: All articles get same question difficulty
- **Files**: `verifast_app/services.py`
- **Impact**: Mismatched question complexity for article difficulty
- **Solution**: Scale question complexity based on reading level

### Frontend Issues (Priority Order)

#### 6. **Speed Reader Immersive Mode Enhancement** 🔴 HIGH PRIORITY
- **Problem**: Current immersive mode lacks optimal visual design
- **Files**: `verifast_app/templates/verifast_app/article_detail.html`, CSS
- **Current**: Basic overlay with word display
- **Required**: Thick white stripe with black letters on darkened background
- **Visual Specs**:
  - Background: Dark overlay (rgba(0, 0, 0, 0.9))
  - Word display: Thick white horizontal stripe/banner
  - Text: Bold black letters on white stripe for maximum contrast
  - Typography: Large, readable font optimized for speed reading

#### 7. **Remove Speed Reader Normal Mode** 🔴 HIGH PRIORITY
- **Problem**: Multiple modes create user confusion
- **Files**: `verifast_app/templates/verifast_app/article_detail.html`
- **Solution**: Make immersive mode the default and only option
- **Impact**: Simplified UX, better reading experience

#### 8. **Template Integration Fixes** 🟡 MEDIUM PRIORITY
- **Problem**: Django template caching preventing HTML structure updates
- **Files**: `verifast_app/templates/verifast_app/article_detail.html`
- **Current Workaround**: JavaScript injection for quiz functionality
- **Solution**: Resolve template rendering issues for proper HTML structure

#### 9. **Quiz Overlay Proper Implementation** 🟡 MEDIUM PRIORITY
- **Problem**: Quiz currently implemented via JavaScript injection
- **Files**: `verifast_app/templates/verifast_app/article_detail.html`
- **Solution**: Move to proper Django template-based implementation
- **Dependency**: Requires template integration fixes first

---

## Implementation Roadmap

### Phase 1: Backend Quiz Generation Fixes

#### Step 1.1: Dynamic Question Count Algorithm
**Files to modify**: `verifast_app/services.py`, `verifast_app/pydantic_models/llm.py`

```python
# Add to services.py
def calculate_optimal_question_count(article_text: str, min_questions: int = 5, max_questions: int = 30) -> int:
    """Calculate optimal number of questions based on article characteristics."""
    word_count = len(article_text.split())
    
    # Base calculation: 1 question per 200-300 words
    base_questions = max(min_questions, word_count // 250)
    
    # Adjust for content complexity
    sentences = len([s for s in article_text.split('.') if s.strip()])
    if sentences > 0:
        avg_sentence_length = word_count / sentences
        if avg_sentence_length > 20:  # Complex sentences
            base_questions = int(base_questions * 1.2)
    
    # Cap at maximum
    return min(base_questions, max_questions)
```

```python
# Update pydantic_models/llm.py
class MasterAnalysisResponse(BaseModel):
    quiz: List[QuizQuestion] = Field(
        min_length=5, 
        max_length=30, 
        description="List of 5-30 quiz questions generated based on article length and complexity"
    )
```

#### Step 1.2: Enhanced Content Coverage Prompts
**Files to modify**: `verifast_app/services.py`

```python
# Update generate_master_analysis function
def generate_master_analysis(model_name: str, entity_list: list, article_text: str, language: str = 'en') -> dict:
    # Calculate optimal question count
    question_count = calculate_optimal_question_count(article_text)
    
    prompts = {
        'en': f"""
    Analyze the following article and generate a single JSON object with comprehensive quiz questions and tags.

    **QUIZ GENERATION INSTRUCTIONS:**
    1. First, identify ALL main ideas, thesis statements, and key concepts in the article
    2. Create ONE comprehensive multiple-choice question for EACH unique main idea
    3. If a main idea is repeated multiple times, create only ONE question that covers that concept thoroughly
    4. Ensure questions cover the breadth and depth of the article's content
    5. Generate exactly {question_count} questions based on the article's length and complexity
    6. Each question should test understanding of a distinct main point or concept

    **Article Text:**
    {article_text[:6000]}
    
    **Required JSON Format:**
    {{
        "quiz": [
            {{
                "question": "Question text about main idea 1",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "answer": "Correct option text"
            }},
            // ... exactly {question_count} questions covering all main ideas
        ],
        "tags": ["canonical_entity_1", "canonical_entity_2", ...]
    }}

    Return only the raw JSON object and nothing else.
    """
    }
```

#### Step 1.3: Reliable Quiz Generation for Regular Articles
**Files to modify**: `verifast_app/tasks.py`, `verifast_app/views.py`

```python
# Add to tasks.py
@shared_task(bind=True, max_retries=3)
def ensure_article_has_quiz(self, article_id):
    """Ensure article has quiz data, retry if generation fails."""
    try:
        article = Article.objects.get(id=article_id)
        
        if not article.quiz_data and article.can_generate_quiz():
            # Retry quiz generation
            process_article.delay(article_id)
            
    except Exception as e:
        logger.error(f"Failed to ensure quiz for article {article_id}: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
```

### Phase 2: Frontend Speed Reader Enhancement

#### Step 2.1: Immersive Mode Visual Enhancement
**Files to modify**: `verifast_app/templates/verifast_app/article_detail.html`

```css
/* Enhanced Immersive Mode Styles */
.immersive-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.9); /* Dark background */
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}

.immersive-word-display {
    /* Thick white stripe design */
    background: white;
    color: black;
    padding: 2rem 4rem;
    border-radius: 8px;
    font-size: 4rem;
    font-weight: bold;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    min-width: 60%;
    min-height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
}
```

#### Step 2.2: Remove Normal Mode, Make Immersive Default
**Files to modify**: `verifast_app/templates/verifast_app/article_detail.html`

```javascript
// Update speed reader to automatically use immersive mode
function startReading() {
    // Always start in immersive mode
    showImmersiveMode();
    // ... rest of reading logic
}
```

### Phase 3: Template Integration Fixes

#### Step 3.1: Resolve Template Caching Issues
**Actions needed**:
1. Clear Django template cache: `python manage.py shell -c "from django.core.cache import cache; cache.clear()"`
2. Restart Django development server
3. Check for template loader configuration issues
4. Verify template inheritance chain

#### Step 3.2: Proper Quiz Overlay Implementation
**Files to modify**: `verifast_app/templates/verifast_app/article_detail.html`

```html
<!-- Proper Django template implementation -->
{% if article.quiz_data %}
<div id="quiz-overlay" class="quiz-overlay" role="dialog" aria-hidden="true">
    <div class="quiz-overlay-content">
        <!-- Quiz content structure -->
    </div>
</div>
{% endif %}
```

---

## Testing Strategy

### Backend Testing
1. **Question Count Validation**:
   - Test short article (500 words) → expect ~5 questions
   - Test medium article (2000 words) → expect ~8-10 questions  
   - Test long article (5000+ words) → expect 20+ questions

2. **Content Coverage Testing**:
   - Verify questions cover introduction, body, and conclusion
   - Check that all major topics mentioned in article have corresponding questions
   - Ensure no duplicate concepts in questions

3. **Processing Reliability**:
   - Test regular article processing with network failures
   - Verify fallback mechanisms work
   - Check that failed articles get retry attempts

### Frontend Testing
1. **Speed Reader Visual Testing**:
   - Verify thick white stripe appearance
   - Test contrast and readability
   - Check responsive behavior on different screen sizes

2. **User Experience Testing**:
   - Confirm immersive mode is default and only option
   - Test smooth transitions and animations
   - Verify keyboard shortcuts work in immersive mode

3. **Quiz Integration Testing**:
   - Test quiz overlay opens properly
   - Verify question navigation works
   - Check score calculation and XP awarding

---

## Rollback Plan

### If Issues Arise
1. **Backend Rollback**: Revert `services.py` and `pydantic_models/llm.py` to fixed 5-question system
2. **Frontend Rollback**: Keep current JavaScript injection quiz system
3. **Speed Reader Rollback**: Maintain both normal and immersive modes if needed

### Monitoring Points
- Quiz generation success rate
- User completion rates
- Performance impact of longer quizzes
- User feedback on immersive mode design

---

## Current Progress Status

### ✅ **Completed**
- **Dynamic Question Count Algorithm**: Implemented in `services.py` with `calculate_optimal_question_count()`
- **Enhanced Content Coverage Prompts**: Updated with specific question count based on article length
- **Pydantic Model Updates**: Updated to allow 5-30 questions instead of fixed 3-5
- **Quiz Reliability Task**: Added `ensure_article_has_quiz()` function for better reliability
- **Immersive Mode CSS**: Enhanced with thick white stripe design (ready to use)
- **UI Cleanup**: Removed separate "Immersive Mode" button, made immersive default
- **JavaScript Cleanup**: Removed duplicate functions and fixed syntax errors
- **Quiz Integration**: Working quiz overlay system with proper navigation

### 🔄 **Current Issue**
- **JavaScript Execution**: DOMContentLoaded event listener not executing despite clean syntax
- **Template Caching**: Django template changes may not be applying immediately

### ❌ **Current Blocker**
- **Speed Reader Not Starting**: JavaScript script exists in DOM but event listeners not attaching
- **Immersive Mode Not Activating**: CSS is ready but JavaScript functions not executing

## Next Steps When Resuming

1. **URGENT: Fix JavaScript Issues**: Clean up duplicate functions in article_detail.html template
2. **Test Immersive Mode**: Verify thick white stripe design works properly
3. **Test Dynamic Quiz Generation**: Verify backend changes work for different article lengths
4. **Continue with Phase 3**: Template integration fixes once JavaScript is working

---

## Files That Will Be Modified

### Backend Files
- `verifast_app/services.py` - Quiz generation logic
- `verifast_app/pydantic_models/llm.py` - Validation models
- `verifast_app/tasks.py` - Article processing tasks
- `verifast_app/views.py` - View logic for quiz handling

### Frontend Files  
- `verifast_app/templates/verifast_app/article_detail.html` - Main template
- `verifast_app/static/verifast_app/css/speed-reader.css` - Styling (if separate)

### Configuration Files
- May need Django settings updates for template caching
- Possible Celery task configuration updates

---

*Document created: $(date)*
*Status: Ready for implementation*
*Priority: Start with Phase 1 (Backend Quiz Generation Fixes)*