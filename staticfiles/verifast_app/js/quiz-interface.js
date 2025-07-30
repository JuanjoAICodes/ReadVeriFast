/**
 * Quiz Interface class for interactive quiz functionality
 */
class QuizInterface {
    constructor(quizData, articleId) {
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
        if (index < 0 || index >= this.questions.length) {
            console.error('Quiz Interface: Invalid question index:', index);
            return;
        }

        const question = this.questions[index];
        const questionHtml = `
            <div class="question">
                <h3>Question ${index + 1}</h3>
                <p>${this.escapeHtml(question.question)}</p>
                <div class="options">
                    ${question.options.map((option, i) => `
                        <label>
                            <input type="radio" name="answer" value="${i}" 
                                   ${this.userAnswers[index] === i ? 'checked' : ''}>
                            ${this.escapeHtml(option)}
                        </label>
                    `).join('')}
                </div>
            </div>
        `;

        if (this.questionsContainer) {
            this.questionsContainer.innerHTML = questionHtml;
        }

        // Attach event listeners to radio buttons
        const radioButtons = this.questionsContainer?.querySelectorAll('input[type="radio"]');
        radioButtons?.forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.userAnswers[index] = parseInt(e.target.value);
                this.updateNavigationButtons();
            });
        });

        this.updateQuestionCounter();
        this.updateNavigationButtons();
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
            wmp_used: wpmUsed,
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