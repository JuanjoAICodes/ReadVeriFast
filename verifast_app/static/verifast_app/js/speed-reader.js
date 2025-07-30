/**
 * VeriFast Speed Reader - Modern Implementation
 * Provides immersive speed reading with premium features and full i18n support
 */

class SpeedReader {
    constructor(sectionId) {
        this.section = document.getElementById(sectionId);
        this.wordDisplay = document.getElementById('word-display');
        this.startPauseBtn = document.getElementById('start-pause-btn');
        this.resetBtn = document.getElementById('reset-btn');
        this.immersiveBtn = document.getElementById('immersive-btn');
        this.speedDisplay = document.getElementById('current-speed');
        this.progressBar = document.getElementById('progress-bar');
        this.speedIncBtn = document.getElementById('speed-increase');
        this.speedDecBtn = document.getElementById('speed-decrease');
        
        // Immersive elements
        this.immersiveOverlay = document.getElementById('immersive-overlay');
        this.immersiveWordDisplay = document.getElementById('immersive-word-display');
        
        // Performance optimization variables
        this.rafId = null;
        this.lastUpdateTime = 0;
        this.updateThrottle = 16; // ~60fps
        this.immersiveStopBtn = document.getElementById('immersive-stop-btn');
        
        // State
        this.words = [];
        this.currentIndex = 0;
        this.isRunning = false;
        this.isImmersive = false;
        this.intervalId = null;
        this.wpm = 250;
        
        this.init();
    }
    
    init() {
        console.log('Speed Reader: Initializing...');
        
        if (!this.validateElements()) {
            console.error('Speed Reader: Essential elements missing');
            this.showFallbackMessage();
            return;
        }
        
        this.loadContent();
        this.loadUserSettings();
        this.attachEventListeners();
        this.updateSpeedDisplay();
        
        console.log('Speed Reader: Initialized successfully');
    }
    
    validateElements() {
        const required = [this.section, this.wordDisplay, this.startPauseBtn, this.resetBtn, this.speedDisplay, this.progressBar];
        const missing = required.filter(el => !el);
        
        if (missing.length > 0) {
            console.error('Speed Reader: Missing required elements:', missing.map(el => el?.id || 'unknown'));
            return false;
        }
        
        return true;
    }
    
    loadContent() {
        const content = this.section.dataset.content;
        if (!content) {
            this.showError(_('no_content_available'));
            return;
        }
        
        // Clean and split content into words
        this.words = this.cleanAndSplitWords(content);
        console.log(`Speed Reader: Loaded ${this.words.length} words`);
        
        if (this.words.length === 0) {
            this.showError(_('no_content_available'));
        }
    }
    
    cleanAndSplitWords(content) {
        // Create temporary div to strip HTML tags
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = content;
        const cleanContent = (tempDiv.textContent || tempDiv.innerText || '')
            .replace(/\s+/g, ' ')
            .trim();
        
        return cleanContent.split(/\s+/).filter(word => word.length > 0);
    }
    
    loadUserSettings() {
        // Load WPM from data attribute or default
        const userWpm = parseInt(this.section.dataset.userWpm);
        if (userWpm && userWpm > 0) {
            this.wpm = Math.max(50, Math.min(1000, userWpm));
        }
    }
    
    attachEventListeners() {
        // Main controls
        this.startPauseBtn.addEventListener('click', () => this.toggleReading());
        this.resetBtn.addEventListener('click', () => this.resetReading());
        
        // Speed controls
        if (this.speedIncBtn) {
            this.speedIncBtn.addEventListener('click', () => this.adjustSpeed(25));
        }
        if (this.speedDecBtn) {
            this.speedDecBtn.addEventListener('click', () => this.adjustSpeed(-25));
        }
        
        // Immersive mode
        if (this.immersiveBtn) {
            this.immersiveBtn.addEventListener('click', () => this.toggleImmersive());
        }
        if (this.immersiveStopBtn) {
            this.immersiveStopBtn.addEventListener('click', () => this.stopImmersive());
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        // Escape key for immersive mode
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isImmersive) {
                this.stopImmersive();
            }
        });
        
        // Prevent accidental page navigation during reading
        window.addEventListener('beforeunload', (e) => {
            if (this.isRunning) {
                e.preventDefault();
                e.returnValue = _('reading_in_progress_warning') || 'Reading in progress. Are you sure you want to leave?';
            }
        });
    }
    
    toggleReading() {
        if (this.words.length === 0) {
            this.showError(_('no_content_available'));
            return;
        }
        
        if (this.isRunning) {
            this.pauseReading();
        } else {
            this.startReading();
        }
    }
    
    startReading() {
        // Reset if finished
        if (this.currentIndex >= this.words.length) {
            this.resetReading();
        }
        
        // Start immersive mode if button was clicked
        // Note: Immersive mode is handled by separate button click
        
        const interval = 60000 / this.wpm; // Convert WPM to milliseconds
        this.intervalId = setInterval(() => this.showNextWord(), interval);
        this.isRunning = true;
        this.updateButton(_('pause_reading') || 'Pause');
        
        // Update button states
        this.startPauseBtn.setAttribute('aria-pressed', 'true');
        
        console.log(`Speed Reader: Started at ${this.wpm} WPM`);
    }
    
    pauseReading() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.isRunning = false;
        this.updateButton(_('start_reading') || 'Start Reading');
        
        // Update button states
        this.startPauseBtn.setAttribute('aria-pressed', 'false');
        
        console.log('Speed Reader: Paused');
    }
    
    resetReading() {
        this.pauseReading();
        this.currentIndex = 0;
        this.updateProgress(0);
        this.showWord(_('click_start_reading') || 'Click Start to begin reading');
        this.updateButton(_('start_reading') || 'Start Reading');
        
        // Exit immersive mode if active
        if (this.isImmersive) {
            this.stopImmersive();
        }
        
        console.log('Speed Reader: Reset');
    }
    
    showNextWord() {
        if (this.currentIndex < this.words.length) {
            const word = this.words[this.currentIndex];
            this.showWord(word);
            this.updateProgress((this.currentIndex + 1) / this.words.length * 100);
            this.currentIndex++;
        } else {
            this.finishReading();
        }
    }
    
    showWord(word) {
        this.wordDisplay.textContent = word;
        
        // Update immersive display if active
        if (this.isImmersive && this.immersiveWordDisplay) {
            this.immersiveWordDisplay.textContent = word;
            this.adjustImmersiveFontSize(word);
        }
        
        // Clear any error states
        this.wordDisplay.classList.remove('error');
    }
    
    adjustImmersiveFontSize(word) {
        if (!this.immersiveWordDisplay) return;
        
        // Reset to default size
        this.immersiveWordDisplay.style.fontSize = '4rem';
        
        // Check if word is too wide and reduce font size if needed
        const maxWidth = window.innerWidth * 0.9;
        
        // Create temporary element to measure text width
        const tempElement = document.createElement('div');
        tempElement.style.position = 'absolute';
        tempElement.style.visibility = 'hidden';
        tempElement.style.whiteSpace = 'nowrap';
        tempElement.style.fontSize = '4rem';
        tempElement.style.fontWeight = '300';
        tempElement.style.letterSpacing = '0.05em';
        tempElement.textContent = word;
        document.body.appendChild(tempElement);
        
        let fontSize = 4;
        while (tempElement.offsetWidth > maxWidth && fontSize > 1.5) {
            fontSize -= 0.2;
            tempElement.style.fontSize = fontSize + 'rem';
            this.immersiveWordDisplay.style.fontSize = fontSize + 'rem';
        }
        
        document.body.removeChild(tempElement);
    }
    
    finishReading() {
        this.pauseReading();
        this.showWord(_('reading_finished') || 'Reading finished!');
        
        // Exit immersive mode
        if (this.isImmersive) {
            setTimeout(() => this.stopImmersive(), 2000);
        }
        
        // Trigger reading completion callback
        if (typeof this.onReadingComplete === 'function') {
            this.onReadingComplete();
        }
        
        console.log('Speed Reader: Finished');
    }
    
    updateProgress(percentage) {
        this.progressBar.value = percentage;
        this.progressBar.setAttribute('aria-valuenow', Math.round(percentage));
        
        // Update progress text
        const progressText = document.getElementById('progress-text');
        if (progressText) {
            progressText.textContent = Math.round(percentage) + '%';
        }
    }
    
    updateButton(text) {
        this.startPauseBtn.textContent = text;
    }
    
    adjustSpeed(delta) {
        const newWpm = this.wpm + delta;
        this.wpm = Math.max(50, Math.min(1000, newWpm));
        this.updateSpeedDisplay();
        
        // Debounce speed changes to prevent excessive restarts
        clearTimeout(this.speedChangeTimeout);
        this.speedChangeTimeout = setTimeout(() => {
            // Restart reading with new speed if currently running
            if (this.isRunning) {
                this.pauseReading();
                this.startReading();
            }
            
            // Announce speed change to screen readers
            const announcement = _('speed_changed_to') || 'Speed changed to';
            this.announceToScreenReader(`${announcement} ${this.wpm} ${_('speed_wpm') || 'WPM'}`);
        }, 300);
        
        console.log(`Speed Reader: Speed adjusted to ${this.wpm} WPM`);
    }
    
    updateSpeedDisplay() {
        this.speedDisplay.textContent = this.wpm;
        this.speedDisplay.setAttribute('aria-label', `${this.wpm} ${_('speed_wpm') || 'WPM'}`);
    }
    
    toggleImmersive() {
        if (this.isImmersive) {
            this.stopImmersive();
        } else {
            this.startImmersive();
        }
    }
    
    startImmersive() {
        if (!this.immersiveOverlay || !this.immersiveWordDisplay) {
            console.warn('Speed Reader: Immersive mode not available');
            return;
        }
        
        this.isImmersive = true;
        this.immersiveOverlay.classList.add('active');
        this.immersiveOverlay.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        
        // Sync current word
        const currentWord = this.currentIndex < this.words.length ? 
            this.words[this.currentIndex] : (_('ready_to_read') || 'Ready to read');
        this.immersiveWordDisplay.textContent = currentWord;
        this.adjustImmersiveFontSize(currentWord);
        
        // Progress is handled by the main progress bar
        
        // Focus management
        this.immersiveStopBtn?.focus();
        
        console.log('Speed Reader: Immersive mode activated');
    }
    
    stopImmersive() {
        if (!this.immersiveOverlay) return;
        
        this.isImmersive = false;
        this.immersiveOverlay.classList.remove('active');
        this.immersiveOverlay.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        
        // Return focus to main controls
        this.startPauseBtn?.focus();
        
        console.log('Speed Reader: Immersive mode deactivated');
    }
    
    handleKeyboard(e) {
        // Don't interfere with form inputs
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
            return;
        }
        
        // Don't interfere with modifier keys
        if (e.ctrlKey || e.altKey || e.metaKey) {
            return;
        }
        
        switch (e.key) {
            case ' ':
                e.preventDefault();
                this.toggleReading();
                break;
            case 'r':
            case 'R':
                e.preventDefault();
                this.resetReading();
                break;
            case 'i':
            case 'I':
                e.preventDefault();
                this.toggleImmersive();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.adjustSpeed(25);
                break;
            case 'ArrowDown':
                e.preventDefault();
                this.adjustSpeed(-25);
                break;
            case '+':
            case '=':
                e.preventDefault();
                this.adjustSpeed(25);
                break;
            case '-':
                e.preventDefault();
                this.adjustSpeed(-25);
                break;
        }
    }
    
    showError(message) {
        this.wordDisplay.textContent = message;
        this.wordDisplay.classList.add('error');
        this.wordDisplay.setAttribute('aria-live', 'assertive');
        
        // Auto-clear error after delay
        setTimeout(() => {
            this.wordDisplay.classList.remove('error');
            this.wordDisplay.setAttribute('aria-live', 'polite');
        }, 3000);
        
        console.error('Speed Reader:', message);
    }
    
    showFallbackMessage() {
        if (!this.section) return;
        
        const fallback = document.createElement('div');
        fallback.className = 'speed-reader-fallback';
        fallback.innerHTML = `
            <p><strong>${_('speed_reader_unavailable') || 'Speed Reader Unavailable'}</strong></p>
            <p>${_('speed_reader_fallback_message') || 'The speed reader could not be loaded. You can still read the article below.'}</p>
        `;
        
        this.section.appendChild(fallback);
    }
    
    announceToScreenReader(message) {
        // Create temporary element for screen reader announcements
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.style.position = 'absolute';
        announcement.style.left = '-10000px';
        announcement.style.width = '1px';
        announcement.style.height = '1px';
        announcement.style.overflow = 'hidden';
        
        document.body.appendChild(announcement);
        announcement.textContent = message;
        
        // Remove after announcement
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }
    
    // Public API methods for external control
    getState() {
        return {
            isRunning: this.isRunning,
            isImmersive: this.isImmersive,
            currentIndex: this.currentIndex,
            totalWords: this.words.length,
            wpm: this.wpm,
            progress: this.words.length > 0 ? (this.currentIndex / this.words.length) * 100 : 0
        };
    }
    
    setWPM(wpm) {
        if (typeof wpm === 'number' && wpm >= 50 && wpm <= 1000) {
            this.wpm = wpm;
            this.updateSpeedDisplay();
            
            if (this.isRunning) {
                this.pauseReading();
                this.startReading();
            }
        }
    }
    
    jumpToWord(index) {
        if (typeof index === 'number' && index >= 0 && index < this.words.length) {
            this.currentIndex = index;
            this.showWord(this.words[index]);
            this.updateProgress((index / this.words.length) * 100);
        }
    }
}

// Initialize when DOM is ready and i18n is available
document.addEventListener('DOMContentLoaded', function() {
    console.log('Speed Reader: DOM loaded, waiting for i18n...');
    
    // Wait for i18n to be available
    function initializeWhenReady() {
        if (typeof window._ === 'function') {
            console.log('Speed Reader: i18n ready, initializing...');
            
            // Initialize speed reader
            const speedReader = new SpeedReader('speed-reader-section');
            
            // Make available globally for debugging and external control
            window.speedReader = speedReader;
        } else {
            console.log('Speed Reader: Waiting for i18n...');
            setTimeout(initializeWhenReady, 100);
        }
    }
    
    initializeWhenReady();
    
    // Add keyboard shortcut help
    const helpText = document.createElement('div');
    helpText.className = 'keyboard-shortcuts-help';
    helpText.style.display = 'none';
    helpText.innerHTML = `
        <h4>${_('keyboard_shortcuts') || 'Keyboard Shortcuts'}</h4>
        <ul>
            <li><kbd>Space</kbd> - ${_('start_pause_reading') || 'Start/Pause reading'}</li>
            <li><kbd>R</kbd> - ${_('reset_reading') || 'Reset reading'}</li>
            <li><kbd>I</kbd> - ${_('toggle_immersive') || 'Toggle immersive mode'}</li>
            <li><kbd>↑/+</kbd> - ${_('increase_speed') || 'Increase speed'}</li>
            <li><kbd>↓/-</kbd> - ${_('decrease_speed') || 'Decrease speed'}</li>
            <li><kbd>Esc</kbd> - ${_('exit_immersive') || 'Exit immersive mode'}</li>
        </ul>
    `;
    
    // Add help toggle button
    const helpButton = document.createElement('button');
    helpButton.textContent = '?';
    helpButton.className = 'help-button';
    helpButton.setAttribute('aria-label', _('show_keyboard_shortcuts') || 'Show keyboard shortcuts');
    helpButton.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: var(--primary);
        color: var(--primary-inverse);
        border: none;
        cursor: pointer;
        font-size: 1.2rem;
        z-index: 1000;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    `;
    
    helpButton.addEventListener('click', () => {
        helpText.style.display = helpText.style.display === 'none' ? 'block' : 'none';
    });
    
    // Add help button after speed reader is initialized
    setTimeout(() => {
        if (window.speedReader && window.speedReader.section) {
            document.body.appendChild(helpButton);
            document.body.appendChild(helpText);
        }
    }, 200);
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SpeedReader;
}