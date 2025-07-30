/**
 * Speed Reader class for word-by-word reading functionality
 */
class SpeedReader {
    constructor(sectionId) {
        this.section = document.getElementById(sectionId);
        if (!this.section) {
            console.error('Speed Reader: Section not found:', sectionId);
            return;
        }

        // DOM elements
        this.wordDisplay = document.getElementById('word-display');
        this.progressFill = document.getElementById('progress-fill');
        this.progressText = document.getElementById('progress-text');
        this.currentSpeedSpan = document.getElementById('current-speed');
        this.maxSpeedSpan = document.getElementById('max-speed');

        // Control buttons
        this.startPauseBtn = document.getElementById('start-pause-btn');
        this.resetBtn = document.getElementById('reset-btn');
        this.immersiveBtn = document.getElementById('immersive-btn');
        this.speedDecreaseBtn = document.getElementById('speed-decrease');
        this.speedIncreaseBtn = document.getElementById('speed-increase');

        // Immersive mode elements
        this.immersiveOverlay = document.getElementById('immersive-overlay');
        this.immersiveWordDisplay = document.getElementById('immersive-word-display');
        this.immersiveExitBtn = document.getElementById('immersive-exit-btn');

        // State management
        this.words = [];
        this.currentIndex = 0;
        this.isRunning = false;
        this.isImmersive = false;
        this.intervalId = null;
        this.onReadingComplete = null;

        // Settings
        this.wpm = parseInt(this.section.dataset.userWpm) || 250;
        this.maxWpm = parseInt(this.maxSpeedSpan?.textContent) || 250;
        this.articleId = parseInt(this.section.dataset.articleId);

        this.init();
    }

    init() {
        if (!this.validateElements()) {
            console.error('Speed Reader: Essential elements missing');
            return;
        }

        this.loadContent();
        this.attachEventListeners();
        this.updateSpeedDisplay();
        
        console.log('Speed Reader: Initialized successfully');
    }

    validateElements() {
        const required = [
            this.wordDisplay,
            this.startPauseBtn,
            this.resetBtn,
            this.currentSpeedSpan
        ];

        return required.every(element => {
            if (!element) {
                console.error('Speed Reader: Missing required element');
                return false;
            }
            return true;
        });
    }

    loadContent() {
        const content = this.section.dataset.content;
        if (!content) {
            console.error('Speed Reader: No content found');
            this.showError('No content available');
            return;
        }

        this.words = this.chunkWords(this.cleanContent(content));
        console.log(`Speed Reader: Loaded ${this.words.length} word chunks`);
    }

    cleanContent(content) {
        // Remove extra whitespace and split into words
        return content.replace(/\\s+/g, ' ').trim().split(' ');
    }

    chunkWords(words) {
        // For now, return individual words
        // TODO: Implement advanced chunking based on user preferences
        return words.filter(word => word.length > 0);
    }

    attachEventListeners() {
        // Main controls
        this.startPauseBtn?.addEventListener('click', () => this.toggleReading());
        this.resetBtn?.addEventListener('click', () => this.resetReading());
        this.immersiveBtn?.addEventListener('click', () => this.toggleImmersive());

        // Speed controls
        this.speedDecreaseBtn?.addEventListener('click', () => this.adjustSpeed(-25));
        this.speedIncreaseBtn?.addEventListener('click', () => this.adjustSpeed(25));

        // Immersive mode
        this.immersiveExitBtn?.addEventListener('click', () => this.toggleImmersive());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }

    toggleReading() {
        if (this.isRunning) {
            this.pauseReading();
        } else {
            this.startReading();
        }
    }

    startReading() {
        if (this.words.length === 0) {
            console.error('Speed Reader: No words to read');
            this.showError('No content to read');
            return;
        }

        const interval = 60000 / this.wpm; // Convert WPM to milliseconds
        this.intervalId = setInterval(() => this.showNextWord(), interval);
        this.isRunning = true;
        this.updateButton('Pause');
        
        console.log(`Speed Reader: Started at ${this.wpm} WPM`);
    }

    pauseReading() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.isRunning = false;
        this.updateButton('Resume');
    }

    resetReading() {
        this.pauseReading();
        this.currentIndex = 0;
        this.updateDisplay();
        this.updateProgress();
        this.updateButton('Start Reading');
    }

    showNextWord() {
        if (this.currentIndex >= this.words.length) {
            this.completeReading();
            return;
        }

        this.updateDisplay();
        this.updateProgress();
        this.currentIndex++;
    }

    completeReading() {
        this.pauseReading();
        this.updateButton('Reading Complete!');
        
        if (this.onReadingComplete) {
            this.onReadingComplete();
        }
        
        console.log('Speed Reader: Reading completed');
    }

    updateDisplay() {
        const currentWord = this.words[this.currentIndex] || 'Click Start to begin reading';
        
        if (this.isImmersive && this.immersiveWordDisplay) {
            this.immersiveWordDisplay.textContent = currentWord;
        } else if (this.wordDisplay) {
            this.wordDisplay.textContent = currentWord;
        }
    }

    updateProgress() {
        if (!this.progressFill || !this.progressText) return;

        const progress = Math.round((this.currentIndex / this.words.length) * 100);
        this.progressFill.style.width = `${progress}%`;
        this.progressText.textContent = `${progress}%`;
    }

    updateButton(text) {
        if (this.startPauseBtn) {
            this.startPauseBtn.textContent = text;
        }
    }

    adjustSpeed(change) {
        const newSpeed = Math.max(50, Math.min(this.maxWpm, this.wpm + change));
        if (newSpeed !== this.wpm) {
            this.wpm = newSpeed;
            this.updateSpeedDisplay();
            
            // Restart reading with new speed if currently running
            if (this.isRunning) {
                this.pauseReading();
                this.startReading();
            }
        }
    }

    updateSpeedDisplay() {
        if (this.currentSpeedSpan) {
            this.currentSpeedSpan.textContent = this.wpm;
        }
    }

    toggleImmersive() {
        this.isImmersive = !this.isImmersive;
        
        if (this.immersiveOverlay) {
            this.immersiveOverlay.classList.toggle('active', this.isImmersive);
        }
        
        if (this.isImmersive) {
            document.body.style.overflow = 'hidden';
            this.updateDisplay(); // Update immersive display
        } else {
            document.body.style.overflow = '';
        }
    }

    handleKeyboard(event) {
        // Only handle shortcuts when speed reader is focused or immersive
        if (!this.isImmersive && !this.section.contains(document.activeElement)) {
            return;
        }

        switch (event.code) {
            case 'Space':
                event.preventDefault();
                this.toggleReading();
                break;
            case 'Escape':
                if (this.isImmersive) {
                    this.toggleImmersive();
                }
                break;
            case 'KeyF':
                event.preventDefault();
                this.toggleImmersive();
                break;
            case 'KeyR':
                event.preventDefault();
                this.resetReading();
                break;
            case 'ArrowUp':
                event.preventDefault();
                this.adjustSpeed(25);
                break;
            case 'ArrowDown':
                event.preventDefault();
                this.adjustSpeed(-25);
                break;
        }
    }

    showError(message) {
        if (this.wordDisplay) {
            this.wordDisplay.textContent = message;
            this.wordDisplay.classList.add('error');
        }
        console.error('Speed Reader:', message);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Speed Reader: DOM loaded, initializing...');
    
    // Global translation function fallback
    if (typeof window._ !== 'function') {
        window._ = function(key, params = {}) {
            return key; // Fallback to key if no translation available
        };
    }
    
    // Initialize speed reader
    const speedReaderSection = document.getElementById('speed-reader-section');
    if (speedReaderSection) {
        const speedReader = new SpeedReader('speed-reader-section');
        
        // Make available globally for debugging
        window.speedReader = speedReader;
        
        console.log('Speed Reader: Initialization complete');
    } else {
        console.error('Speed Reader: Section not found');
    }
});