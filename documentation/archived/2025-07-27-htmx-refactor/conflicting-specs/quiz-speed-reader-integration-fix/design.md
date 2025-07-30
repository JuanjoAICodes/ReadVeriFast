# Design Document

## Overview

This document outlines the solution for fixing the critical frontend integration issue between the quiz and speed reader functionality. The current problem stems from JavaScript code that incorrectly hides the speed reader section when the quiz is activated, breaking both features. The solution involves implementing a proper modal system for the quiz while preserving the speed reader functionality.

## Architecture

### Current Problem Analysis

The issue is in the article detail template's JavaScript:

```javascript
startQuizBtn.addEventListener('click', function() {
    speedReaderSection.style.display = 'none';  // ❌ This breaks everything
    quizContainer.style.display = 'block';
});
```

This approach:
- Completely hides the speed reader, making it inaccessible
- Uses inline display changes that conflict with CSS styling
- Doesn't provide proper modal functionality
- Breaks the user experience flow

### Proposed Solution Architecture

#### Modal-Based Quiz System
- **Quiz Modal Overlay**: Full-screen modal that appears over the article content
- **Background Preservation**: Speed reader and article content remain visible but dimmed
- **Proper Z-Index Management**: Modal appears above content without hiding it
- **Event Isolation**: Modal events don't interfere with background functionality

#### Component Separation
- **Speed Reader Component**: Remains independent and functional
- **Quiz Component**: Operates in its own modal context
- **Shared State Management**: Both components can coexist without conflicts
- **Error Boundaries**: Failures in one component don't break the other

## Components and Interfaces

### Quiz Modal Component

```html
<!-- Modal overlay structure -->
<div id="quiz-modal" class="quiz-modal" role="dialog" aria-hidden="true">
    <div class="quiz-modal-backdrop" aria-hidden="true"></div>
    <div class="quiz-modal-content" role="document">
        <div class="quiz-modal-header">
            <h2>Article Quiz</h2>
            <button class="quiz-modal-close" aria-label="Close quiz">&times;</button>
        </div>
        <div class="quiz-modal-body">
            <!-- Quiz content will be dynamically inserted here -->
        </div>
    </div>
</div>
```

### Quiz Modal CSS

```css
.quiz-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1000;
    display: none;
    align-items: center;
    justify-content: center;
}

.quiz-modal.active {
    display: flex;
}

.quiz-modal-backdrop {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
}

.quiz-modal-content {
    position: relative;
    background: var(--background-color);
    border-radius: var(--border-radius);
    max-width: 90%;
    max-height: 90%;
    overflow-y: auto;
    padding: 2rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}
```

### Quiz JavaScript Architecture

```javascript
class QuizModal {
    constructor(quizData, articleId) {
        this.quizData = quizData;
        this.articleId = articleId;
        this.currentQuestion = 0;
        this.answers = {};
        this.modal = null;
        
        this.init();
    }
    
    init() {
        this.createModal();
        this.attachEventListeners();
    }
    
    show() {
        this.modal.classList.add('active');
        this.modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        this.renderCurrentQuestion();
    }
    
    hide() {
        this.modal.classList.remove('active');
        this.modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    }
    
    // Additional methods for quiz functionality...
}
```

### Error Handling System

```javascript
class ErrorHandler {
    static showError(message, container) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        errorDiv.setAttribute('role', 'alert');
        
        container.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }
    
    static handleQuizError(error) {
        console.error('Quiz Error:', error);
        this.showError(
            'Quiz failed to load. Please refresh the page and try again.',
            document.getElementById('quiz-container')
        );
    }
}
```

## Data Models

### Quiz State Model
```javascript
{
    quizData: Array,           // Quiz questions and answers
    articleId: Number,         // Article identifier
    currentQuestion: Number,   // Current question index
    answers: Object,           // User's selected answers
    startTime: Date,          // Quiz start timestamp
    isSubmitting: Boolean,    // Submission state
    score: Number,            // Final score (after submission)
    xpEarned: Number         // XP earned from quiz
}
```

### Modal State Model
```javascript
{
    isVisible: Boolean,       // Modal visibility state
    isLoading: Boolean,       // Loading state
    hasError: Boolean,        // Error state
    errorMessage: String,     // Error message text
    canClose: Boolean        // Whether modal can be closed
}
```

## Error Handling

### JavaScript Error Boundaries
- **Try-catch blocks** around all quiz operations
- **Graceful degradation** when quiz data is missing
- **User-friendly error messages** instead of console errors
- **Fallback functionality** when modal fails to load

### Network Error Handling
- **Retry mechanisms** for failed quiz submissions
- **Timeout handling** for slow network requests
- **Offline detection** and appropriate messaging
- **Connection recovery** when network is restored

### Data Validation
- **Quiz data validation** before rendering questions
- **Answer validation** before submission
- **Type checking** for all data structures
- **Sanitization** of user inputs

## Testing Strategy

### Unit Tests
- Test quiz modal creation and destruction
- Verify error handling for missing data
- Test answer tracking and submission
- Validate modal accessibility features

### Integration Tests
- Test quiz modal with speed reader running
- Verify both components work independently
- Test modal behavior with different screen sizes
- Validate keyboard navigation and focus management

### User Experience Tests
- Test modal opening and closing smoothness
- Verify background dimming and interaction blocking
- Test quiz completion flow end-to-end
- Validate error message display and clarity

## Implementation Approach

### Phase 1: Remove Problematic Code
1. Remove the JavaScript that hides the speed reader section
2. Remove the inline quiz container that conflicts with modal approach
3. Clean up any conflicting CSS or JavaScript

### Phase 2: Implement Modal System
1. Create quiz modal HTML structure
2. Implement modal CSS with proper z-index management
3. Add modal JavaScript class with show/hide functionality
4. Test basic modal opening and closing

### Phase 3: Quiz Functionality
1. Implement quiz question rendering in modal
2. Add answer tracking and navigation
3. Implement quiz submission logic
4. Add result display in modal

### Phase 4: Error Handling
1. Add comprehensive error handling
2. Implement user-friendly error messages
3. Add retry mechanisms for failed operations
4. Test all error scenarios

### Phase 5: Integration Testing
1. Test quiz modal with speed reader active
2. Verify both components work independently
3. Test on multiple devices and browsers
4. Validate accessibility compliance

## Success Criteria

### Functional Requirements
- Quiz opens in modal without hiding speed reader
- Both features work independently and simultaneously
- Error handling provides clear user feedback
- Modal is accessible and keyboard navigable

### User Experience Requirements
- Smooth modal transitions and animations
- Clear visual hierarchy with proper background dimming
- Intuitive quiz navigation and submission flow
- Consistent behavior across devices and browsers

### Technical Requirements
- No JavaScript errors in browser console
- Proper memory management and cleanup
- Efficient DOM manipulation and event handling
- Cross-browser compatibility maintained