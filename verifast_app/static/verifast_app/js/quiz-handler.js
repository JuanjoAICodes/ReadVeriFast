/**
 * VeriFast Quiz Handler - Modern Implementation
 * Handles quiz functionality with full i18n support
 */

class QuizHandler {
    constructor() {
        this.quizModal = document.getElementById('quiz-modal');
        this.startQuizBtn = document.getElementById('start-quiz-btn');
        this.closeBtn = document.querySelector('.quiz-close-btn');
        this.questionContainer = document.getElementById('quiz-question-container');
        this.prevBtn = document.getElementById('quiz-prev-btn');
        this.nextBtn = document.getElementById('quiz-next-btn');
        this.submitBtn = document.getElementById('quiz-submit-btn');
        this.resultsContainer = document.getElementById('quiz-results');
        
        this.questions = [];
        this.currentQuestion = 0;
        this.answers = {};
        this.isSubmitted = false;
        
        this.init();
    }
    
    init() {
        if (!this.startQuizBtn) {
            console.log('Quiz Handler: No quiz button found, quiz not available');
            return;
        }
        
        this.attachEventListeners();
        console.log('Quiz Handler: Initialized successfully');
    }
    
    attachEventListeners() {
        if (this.startQuizBtn) {
            this.startQuizBtn.addEventListener('click', () => this.startQuiz());
        }
        
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.closeQuiz());
        }
        
        if (this.prevBtn) {
            this.prevBtn.addEventListener('click', () => this.previousQuestion());
        }
        
        if (this.nextBtn) {
            this.nextBtn.addEventListener('click', () => this.nextQuestion());
        }
        
        if (this.submitBtn) {
            this.submitBtn.addEventListener('click', () => this.submitQuiz());
        }
        
        // Close modal when clicking outside
        if (this.quizModal) {
            this.quizModal.addEventListener('click', (e) => {
                if (e.target === this.quizModal) {
                    this.closeQuiz();
                }
            });
        }
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (this.quizModal && this.quizModal.style.display !== 'none') {
                this.handleKeyboard(e);
            }
        });
    }
    
    async startQuiz() {
        try {
            this.showLoading();
            await this.loadQuizData();
            this.showQuiz();
        } catch (error) {
            console.error('Quiz Handler: Error starting quiz:', error);
            this.showError(_('quiz_error') || 'Error loading quiz');
        }
    }
    
    async loadQuizData() {
        // Get article ID from URL or data attribute
        const articleId = this.getArticleId();
        
        if (!articleId) {
            throw new Error('No article ID found');
        }
        
        // For now, create sample quiz data
        // In production, this would fetch from the API
        this.questions = this.generateSampleQuiz();
        
        if (this.questions.length === 0) {
            throw new Error('No quiz questions available');
        }
    }
    
    generateSampleQuiz() {
        // Sample quiz questions - in production this would come from the API
        return [
            {
                id: 1,
                question: "What is the main topic of this article?",
                type: "multiple_choice",
                options: [
                    "Technology and Innovation",
                    "Health and Medicine", 
                    "Politics and Government",
                    "Sports and Entertainment"
                ],
                correct_answer: 0
            },
            {
                id: 2,
                question: "According to the article, what are the key benefits mentioned?",
                type: "multiple_choice",
                options: [
                    "Cost reduction and efficiency",
                    "Environmental protection",
                    "Social impact and accessibility",
                    "All of the above"
                ],
                correct_answer: 3
            },
            {
                id: 3,
                question: "What conclusion does the author reach?",
                type: "multiple_choice",
                options: [
                    "More research is needed",
                    "The technology is ready for deployment",
                    "There are significant challenges ahead",
                    "The results are inconclusive"
                ],
                correct_answer: 1
            }
        ];
    }
    
    getArticleId() {
        // Try to get article ID from URL
        const pathParts = window.location.pathname.split('/');
        const articleIndex = pathParts.indexOf('articles');
        
        if (articleIndex !== -1 && pathParts[articleIndex + 1]) {
            return parseInt(pathParts[articleIndex + 1]);
        }
        
        return null;
    }
    
    showQuiz() {
        if (!this.quizModal) return;
        
        this.quizModal.style.display = 'flex';
        this.quizModal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        
        this.currentQuestion = 0;
        this.answers = {};
        this.isSubmitted = false;
        
        this.renderQuestion();
        this.updateNavigation();
        
        // Focus management
        this.closeBtn?.focus();
    }
    
    closeQuiz() {
        if (!this.quizModal) return;
        
        this.quizModal.style.display = 'none';
        this.quizModal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        
        // Return focus to start button
        this.startQuizBtn?.focus();
    }
    
    renderQuestion() {
        if (!this.questionContainer || !this.questions[this.currentQuestion]) return;
        
        const question = this.questions[this.currentQuestion];
        const questionNumber = this.currentQuestion + 1;
        const totalQuestions = this.questions.length;
        
        let html = `
            <div class="quiz-question">
                <div class="quiz-progress">
                    <span>${_('question') || 'Question'} ${questionNumber} ${_('of') || 'of'} ${totalQuestions}</span>
                    <div class="quiz-progress-bar">
                        <div class="quiz-progress-fill" style="width: ${(questionNumber / totalQuestions) * 100}%"></div>
                    </div>
                </div>
                <h3>${question.question}</h3>
                <div class="quiz-options">
        `;
        
        if (question.type === 'multiple_choice') {
            question.options.forEach((option, index) => {
                const isSelected = this.answers[question.id] === index;
                html += `
                    <label class="quiz-option ${isSelected ? 'selected' : ''}">
                        <input type="radio" 
                               name="question_${question.id}" 
                               value="${index}"
                               ${isSelected ? 'checked' : ''}
                               ${this.isSubmitted ? 'disabled' : ''}>
                        <span class="option-text">${option}</span>
                    </label>
                `;
            });
        }
        
        html += `
                </div>
            </div>
        `;
        
        this.questionContainer.innerHTML = html;
        
        // Add event listeners to options
        if (!this.isSubmitted) {
            const radioButtons = this.questionContainer.querySelectorAll('input[type="radio"]');
            radioButtons.forEach(radio => {
                radio.addEventListener('change', (e) => {
                    this.answers[question.id] = parseInt(e.target.value);
                    this.updateOptionStyles();
                    this.updateNavigation();
                });
            });
        }
    }
    
    updateOptionStyles() {
        const labels = this.questionContainer.querySelectorAll('.quiz-option');
        labels.forEach(label => {
            const radio = label.querySelector('input[type="radio"]');
            if (radio.checked) {
                label.classList.add('selected');
            } else {
                label.classList.remove('selected');
            }
        });
    }
    
    updateNavigation() {
        if (!this.prevBtn || !this.nextBtn || !this.submitBtn) return;
        
        // Previous button
        this.prevBtn.disabled = this.currentQuestion === 0;
        
        // Next button
        const isLastQuestion = this.currentQuestion === this.questions.length - 1;
        this.nextBtn.disabled = isLastQuestion || this.isSubmitted;
        
        // Submit button
        const allAnswered = this.questions.every(q => this.answers.hasOwnProperty(q.id));
        this.submitBtn.style.display = isLastQuestion && allAnswered ? 'block' : 'none';
        this.submitBtn.disabled = this.isSubmitted;
    }
    
    previousQuestion() {
        if (this.currentQuestion > 0) {
            this.currentQuestion--;
            this.renderQuestion();
            this.updateNavigation();
        }
    }
    
    nextQuestion() {
        if (this.currentQuestion < this.questions.length - 1) {
            this.currentQuestion++;
            this.renderQuestion();
            this.updateNavigation();
        }
    }
    
    async submitQuiz() {
        try {
            this.submitBtn.disabled = true;
            this.submitBtn.textContent = _('submitting') || 'Submitting...';
            
            const score = this.calculateScore();
            await this.saveQuizResult(score);
            
            this.showResults(score);
            this.isSubmitted = true;
            
        } catch (error) {
            console.error('Quiz Handler: Error submitting quiz:', error);
            this.showError(_('quiz_submit_error') || 'Error submitting quiz');
            this.submitBtn.disabled = false;
            this.submitBtn.textContent = _('submit_quiz') || 'Submit Quiz';
        }
    }
    
    calculateScore() {
        let correct = 0;
        
        this.questions.forEach(question => {
            const userAnswer = this.answers[question.id];
            if (userAnswer === question.correct_answer) {
                correct++;
            }
        });
        
        return {
            correct: correct,
            total: this.questions.length,
            percentage: Math.round((correct / this.questions.length) * 100)
        };
    }
    
    async saveQuizResult(score) {
        const articleId = this.getArticleId();
        
        // In production, this would send to the API
        const data = {
            article_id: articleId,
            score: score.percentage,
            answers: this.answers,
            completed_at: new Date().toISOString()
        };
        
        // For now, just save to session storage
        const quizResults = JSON.parse(sessionStorage.getItem('quiz_results') || '{}');
        quizResults[articleId] = data;
        sessionStorage.setItem('quiz_results', JSON.stringify(quizResults));
        
        console.log('Quiz result saved:', data);
    }
    
    showResults(score) {
        if (!this.resultsContainer) return;
        
        const passed = score.percentage >= 60;
        const resultClass = passed ? 'quiz-passed' : 'quiz-failed';
        const resultMessage = passed ? 
            (_('quiz_passed') || 'Congratulations! You passed!') :
            (_('quiz_failed') || 'Try again to improve your score');
        
        let html = `
            <div class="quiz-result ${resultClass}">
                <h3>${_('quiz_score') || 'Your Score'}: ${score.percentage}%</h3>
                <p>${score.correct} ${_('out_of') || 'out of'} ${score.total} ${_('correct') || 'correct'}</p>
                <p class="result-message">${resultMessage}</p>
        `;
        
        if (passed) {
            html += `
                <div class="xp-reward">
                    <p>🎉 ${_('xp_earned') || 'XP Earned'}: ${this.calculateXPReward(score)}!</p>
                </div>
            `;
        }
        
        html += `
                <button class="quiz-close-result-btn" onclick="window.location.reload()">
                    ${_('continue') || 'Continue'}
                </button>
            </div>
        `;
        
        this.resultsContainer.innerHTML = html;
        this.resultsContainer.style.display = 'block';
        
        // Hide question container and navigation
        if (this.questionContainer) this.questionContainer.style.display = 'none';
        if (this.prevBtn) this.prevBtn.style.display = 'none';
        if (this.nextBtn) this.nextBtn.style.display = 'none';
        if (this.submitBtn) this.submitBtn.style.display = 'none';
    }
    
    calculateXPReward(score) {
        // Base XP calculation
        const baseXP = 50;
        const bonusXP = Math.floor(score.percentage / 10) * 5;
        return baseXP + bonusXP;
    }
    
    showLoading() {
        if (!this.questionContainer) return;
        
        this.questionContainer.innerHTML = `
            <div class="quiz-loading">
                <div class="loading-spinner"></div>
                <p>${_('quiz_loading') || 'Loading quiz...'}</p>
            </div>
        `;
    }
    
    showError(message) {
        if (!this.questionContainer) return;
        
        this.questionContainer.innerHTML = `
            <div class="quiz-error">
                <p class="error-message">${message}</p>
                <button onclick="this.parentElement.parentElement.parentElement.style.display='none'">
                    ${_('close') || 'Close'}
                </button>
            </div>
        `;
    }
    
    handleKeyboard(e) {
        switch (e.key) {
            case 'Escape':
                this.closeQuiz();
                break;
            case 'ArrowLeft':
                if (!this.prevBtn.disabled) {
                    this.previousQuestion();
                }
                break;
            case 'ArrowRight':
                if (!this.nextBtn.disabled) {
                    this.nextQuestion();
                }
                break;
            case 'Enter':
                if (this.submitBtn.style.display !== 'none' && !this.submitBtn.disabled) {
                    this.submitQuiz();
                }
                break;
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Quiz Handler: DOM loaded, initializing...');
    
    // Initialize quiz handler
    const quizHandler = new QuizHandler();
    
    // Make available globally for debugging
    window.quizHandler = quizHandler;
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = QuizHandler;
}