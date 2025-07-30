/**
 * Quiz Interface class for interactive quiz functionality
 */
class QuizInterface {
    constructor(quizData, articleId) {
        // Translation function using context processor data
        this._ = function(key) {
            const translations = window.jsTranslations || {};
            return translations[key] || key;
        };

        this.questions = quizData || [];
        this.articleId = articleId;
        this.currentQuestion = 0;
        this.userAnswers = [];
        this.startTime = null;
        this.isActive = false;

        // DOM elements
        this.modal = document.getElementById('quiz-modal');
        this.questionsContainer = document.getElementById('quiz-questions');
        this.startQuizBtn = document.getElementById('start-quiz-btn');
        this.prevBtn = document.getElementById('prev-question');
        this.nextBtn = document.getElementById('next-question');
        this.submitBtn = document.getElementById('submit-quiz');
        this.currentQuestionSpan = document.getElementById('current-question');
        
        // Performance optimization variables
        this.debounceTimeout = null;
        this.lastInteractionTime = 0;
        this.totalQuestionsSpan = document.getElementById('total-questions');

        this.init();
    }

    init() {
        if (!this.validateElements()) {
            console.error('Quiz Interface: Essential elements missing');
            return;
        }

        if (this.questions.length === 0) {
            console.warn('Quiz Interface: No quiz questions available');
            return;
        }

        this.attachEventListeners();
        this.updateTotalQuestions();
        
        console.log(`Quiz Interface: Initialized with ${this.questions.length} questions`);
    }

    validateElements() {
        const required = [
            this.modal,
            this.questionsContainer,
            this.startQuizBtn
        ];

        return required.every(element => {
            if (!element) {
                console.error('Quiz Interface: Missing required element');
                return false;
            }
            return true;
        });
    }

    attachEventListeners() {
        // Start quiz button
        this.startQuizBtn?.addEventListener('click', () => this.startQuiz());

        // Navigation buttons
        this.prevBtn?.addEventListener('click', () => this.previousQuestion());
        this.nextBtn?.addEventListener('click', () => this.nextQuestion());
        this.submitBtn?.addEventListener('click', () => this.submitQuiz());

        // Modal close on background click
        this.modal?.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeQuiz();
            }
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }

    startQuiz() {
        if (this.questions.length === 0) {
            alert('No quiz questions available for this article.');
            return;
        }

        this.isActive = true;
        this.startTime = Date.now();
        this.currentQuestion = 0;
        this.userAnswers = new Array(this.questions.length).fill(null);

        this.showModal();
        this.displayQuestion(0);
        
        console.log('Quiz Interface: Quiz started');
    }

    showModal() {
        if (this.modal) {
            this.modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    closeQuiz() {
        if (this.modal) {
            this.modal.classList.remove('active');
            document.body.style.overflow = '';
        }
        this.isActive = false;
    }

    displayQuestion(index) {
        try {
            if (index < 0 || index >= this.questions.length) {
                console.error('Quiz Interface: Invalid question index:', index);
                return;
            }

            const question = this.questions[index];
            const questionNumber = index + 1;
            const totalQuestions = this.questions.length;
            
            const questionHtml = `
                <div class="question" role="group" aria-labelledby="question-${index}-title">
                    <h3 id="question-${index}-title" class="question-title">
                        Question ${questionNumber} of ${totalQuestions}
                    </h3>
                    <p class="question-text" id="question-${index}-text">
                        ${this.escapeHtml(question.question)}
                    </p>
                    <fieldset class="options" aria-labelledby="question-${index}-title" aria-describedby="question-${index}-text">
                        <legend class="sr-only">Choose your answer</legend>
                        ${question.options.map((option, i) => `
                            <label class="option-label" for="option-${index}-${i}">
                                <input type="radio" 
                                       id="option-${index}-${i}"
                                       name="question-${index}" 
                                       value="${i}" 
                                       ${this.userAnswers[index] === i ? 'checked' : ''}
                                       aria-describedby="question-${index}-text">
                                <span class="option-text">${this.escapeHtml(option)}</span>
                            </label>
                        `).join('')}
                    </fieldset>
                </div>
            `;

            if (this.questionsContainer) {
                this.questionsContainer.innerHTML = questionHtml;
                
                // Focus on the first radio button for keyboard navigation
                const firstRadio = this.questionsContainer.querySelector('input[type="radio"]');
                if (firstRadio && !this.userAnswers[index]) {
                    setTimeout(() => firstRadio.focus(), 100);
                }
            }

            // Attach event listeners to radio buttons
            const radioButtons = this.questionsContainer?.querySelectorAll('input[type="radio"]');
            radioButtons?.forEach(radio => {
                radio.addEventListener('change', (e) => {
                    const answerIndex = parseInt(e.target.value);
                    this.userAnswers[index] = answerIndex;
                    this.updateNavigationButtons();
                    
                    // Announce selection to screen readers
                    const optionText = e.target.nextElementSibling?.textContent || `Option ${answerIndex + 1}`;
                    this.announceToScreenReader(`Selected: ${optionText}`);
                });
                
                // Add keyboard support for radio buttons
                radio.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        radio.checked = true;
                        radio.dispatchEvent(new Event('change'));
                    }
                });
            });

            this.updateQuestionCounter();
            this.updateNavigationButtons();
            
            // Announce question change to screen readers
            this.announceToScreenReader(`Question ${questionNumber} of ${totalQuestions}: ${question.question}`);
            
        } catch (error) {
            console.error('Quiz Interface: Error displaying question:', error);
            this.showError('Failed to display question. Please refresh and try again.');
        }
    }

    previousQuestion() {
        if (this.currentQuestion > 0) {
            this.currentQuestion--;
            this.displayQuestion(this.currentQuestion);
        }
    }

    nextQuestion() {
        if (this.currentQuestion < this.questions.length - 1) {
            this.currentQuestion++;
            this.displayQuestion(this.currentQuestion);
        }
    }

    updateQuestionCounter() {
        if (this.currentQuestionSpan) {
            this.currentQuestionSpan.textContent = this.currentQuestion + 1;
        }
    }

    updateTotalQuestions() {
        if (this.totalQuestionsSpan) {
            this.totalQuestionsSpan.textContent = this.questions.length;
        }
    }

    updateNavigationButtons() {
        // Previous button
        if (this.prevBtn) {
            this.prevBtn.disabled = this.currentQuestion === 0;
        }

        // Next/Submit button logic
        const isLastQuestion = this.currentQuestion === this.questions.length - 1;
        const allAnswered = this.userAnswers.every(answer => answer !== null);

        if (this.nextBtn && this.submitBtn) {
            if (isLastQuestion) {
                this.nextBtn.style.display = 'none';
                this.submitBtn.style.display = 'inline-block';
                this.submitBtn.disabled = !allAnswered;
            } else {
                this.nextBtn.style.display = 'inline-block';
                this.submitBtn.style.display = 'none';
                this.nextBtn.disabled = false;
            }
        }
    }

    async submitQuiz() {
        if (!this.validateAnswers()) {
            alert('Please answer all questions before submitting.');
            return;
        }

        const quizTime = Math.floor((Date.now() - this.startTime) / 1000);
        const wpmUsed = parseInt(document.getElementById('current-speed')?.textContent) || 250;

        const submissionData = {
            article_id: this.articleId,
            user_answers: this.userAnswers,
            wpm_used: wpmUsed,  // Fixed typo: was 'wmp_used'
            quiz_time_seconds: quizTime
        };

        try {
            const response = await fetch('/api/quiz/submit/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(submissionData)
            });

            const result = await response.json();

            if (result.success) {
                this.showResults(result);
            } else {
                throw new Error(result.error || 'Quiz submission failed');
            }
        } catch (error) {
            console.error('Quiz submission error:', error);
            alert('Failed to submit quiz. Please try again.');
        }
    }

    validateAnswers() {
        return this.userAnswers.every(answer => answer !== null && answer !== undefined);
    }

    showResults(result) {
        const resultsHtml = `
            <div class="quiz-results">
                <h3>Quiz Results</h3>
                <div class="score-display">
                    <h4>Your Score: ${result.score}%</h4>
                    ${result.score >= 60 ? 
                        `<p class="success">Congratulations! You passed the quiz.</p>
                         <p>XP Awarded: ${result.xp_awarded}</p>` :
                        `<p class="error">You need 60% or higher to pass. Try reading the article again!</p>`
                    }
                </div>
                ${result.feedback && result.score >= 60 ? `
                    <div class="feedback">
                        <h4>Correct Answers:</h4>
                        ${this.formatFeedback(result.feedback)}
                    </div>
                ` : ''}
                <div class="results-actions">
                    <button onclick="location.reload()" class="primary">
                        Continue
                    </button>
                </div>
            </div>
        `;

        if (this.questionsContainer) {
            this.questionsContainer.innerHTML = resultsHtml;
        }

        // Hide navigation buttons
        if (this.prevBtn) this.prevBtn.style.display = 'none';
        if (this.nextBtn) this.nextBtn.style.display = 'none';
        if (this.submitBtn) this.submitBtn.style.display = 'none';
    }

    formatFeedback(feedback) {
        if (!feedback || !Array.isArray(feedback)) return '';
        
        return feedback.map((item, index) => `
            <div class="feedback-item">
                <strong>Question ${index + 1}:</strong> ${this.escapeHtml(item.correct_answer)}
            </div>
        `).join('');
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showError(message) {
        try {
            if (this.questionsContainer) {
                this.questionsContainer.innerHTML = `
                    <div class="quiz-error" style="text-align: center; padding: 2rem; color: #dc3545;">
                        <h3>⚠️ Quiz Error</h3>
                        <p>${message}</p>
                        <button onclick="location.reload()" class="primary" style="margin-top: 1rem;">
                            Refresh Page
                        </button>
                    </div>
                `;
            } else {
                alert('Quiz Error: ' + message);
            }
        } catch (error) {
            console.error('Quiz Interface: Error showing error message:', error);
            alert('Quiz Error: ' + message);
        }
    }

    announceToScreenReader(message) {
        try {
            // Create or use existing screen reader announcer
            let announcer = document.getElementById('quiz-sr-announcer');
            if (!announcer) {
                announcer = document.createElement('div');
                announcer.id = 'quiz-sr-announcer';
                announcer.setAttribute('aria-live', 'polite');
                announcer.setAttribute('aria-atomic', 'true');
                announcer.style.position = 'absolute';
                announcer.style.left = '-10000px';
                announcer.style.width = '1px';
                announcer.style.height = '1px';
                announcer.style.overflow = 'hidden';
                document.body.appendChild(announcer);
            }
            
            announcer.textContent = message;
            
            // Clear after announcement
            setTimeout(() => {
                announcer.textContent = '';
            }, 1000);
        } catch (error) {
            console.error('Quiz Interface: Error announcing to screen reader:', error);
        }
    }

    handleKeyboard(event) {
        if (!this.isActive) return;

        switch (event.code) {
            case 'ArrowLeft':
                event.preventDefault();
                this.previousQuestion();
                break;
            case 'ArrowRight':
                event.preventDefault();
                if (this.currentQuestion < this.questions.length - 1) {
                    this.nextQuestion();
                }
                break;
            case 'Enter':
                if (this.currentQuestion === this.questions.length - 1) {
                    event.preventDefault();
                    this.submitQuiz();
                }
                break;
            case 'Escape':
                this.closeQuiz();
                break;
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Quiz Interface: DOM loaded, checking for quiz data...');
    
    // Quiz data should be provided by the template
    if (typeof window.quizData !== 'undefined' && typeof window.articleId !== 'undefined') {
        const quizInterface = new QuizInterface(window.quizData, window.articleId);
        
        // Make available globally for debugging
        window.quizInterface = quizInterface;
        
        console.log('Quiz Interface: Initialization complete');
    } else {
        console.warn('Quiz Interface: Missing quiz data or article ID');
    }
});