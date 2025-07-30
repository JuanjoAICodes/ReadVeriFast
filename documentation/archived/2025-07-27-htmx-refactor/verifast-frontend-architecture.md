# VeriFast Frontend Architecture Guide

This document provides comprehensive guidance for building VeriFast frontend components with proper Django integration, i18n compliance, and modern JavaScript functionality.

## Core Architecture Principles

### 1. Django Template Structure
```html
{% extends 'verifast_app/base.html' %}
{% load static %}
{% load i18n %}
{% load custom_template_tags %}

{% block title %}{{ page_title }} - {{ block.super }}{% endblock %}

{% block content %}
<main class="container" role="main">
    <!-- Content here -->
</main>
{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'verifast_app/css/feature-specific.css' %}">
{% endblock %}

{% block extra_js %}
<script src="{% static 'verifast_app/js/feature-specific.js' %}"></script>
{% endblock %}
```

### 2. Static Files Organization
```
verifast_app/static/verifast_app/
├── css/
│   ├── custom.css          # Global styles extending PicoCSS
│   └── components/         # Component-specific styles
├── js/
│   ├── i18n-helper.js      # Translation utilities
│   ├── speed_reader.js     # Speed reading functionality
│   └── components/         # Feature-specific JavaScript
└── images/                 # Static images
```

### 3. Internationalization (i18n) Compliance

#### Template i18n
```html
<!-- Always use trans for static text -->
<h1>{% trans "Speed Reader" %}</h1>

<!-- Use blocktrans for dynamic content -->
<p>{% blocktrans with speed=user_wpm %}Reading at {{ speed }} WPM{% endblocktrans %}</p>

<!-- Provide context for translators -->
<button aria-label="{% trans 'Start reading this article' context 'speed reader button' %}">
    {% trans "Start" %}
</button>

<!-- Form labels and help text -->
<label for="speed-input">{% trans "Reading Speed (WPM)" %}</label>
<small class="help-text">{% trans "Adjust your preferred reading speed" %}</small>
```

#### JavaScript i18n
```javascript
// Use the global translation function
function _(key, params = {}) {
    return window.i18n ? window.i18n._(key, params) : key;
}

// Example usage
wordDisplay.textContent = _('click_start_reading');
button.setAttribute('aria-label', _('pause_reading'));
```

#### Context Processor Integration
```python
# In context_processors.py
def js_translations_processor(request):
    js_translations = {
        'start_reading': _('Start Reading'),
        'pause_reading': _('Pause'),
        'reading_finished': _('Reading finished!'),
        'click_start_reading': _('Click Start to begin reading'),
        'no_content_available': _('No content available'),
        'speed_wpm': _('WPM'),
        'reading_progress': _('Reading progress'),
    }
    return {'js_translations_json': json.dumps(js_translations)}
```

## Speed Reader Implementation Pattern

### 1. HTML Structure
```html
<section id="speed-reader-section" class="speed-reader-section" 
         aria-label="{% trans 'Speed Reader' %}"
         data-content="{{ article.content|escape }}"
         data-user-wpm="{{ user_wpm|default:250 }}">
    
    <h2>{% trans "Speed Reader" %}</h2>
    
    <!-- Word Display -->
    <div id="word-display" class="word-display" aria-live="polite" role="status">
        {% trans "Click Start to begin reading" %}
    </div>
    
    <!-- Progress Bar -->
    <progress id="progress-bar" class="reading-progress" 
              value="0" max="100" 
              aria-label="{% trans 'Reading progress' %}">
        0%
    </progress>
    
    <!-- Speed Controls -->
    <div class="speed-controls" role="group" aria-label="{% trans 'Speed controls' %}">
        <button id="speed-decrease" class="speed-btn" type="button"
                aria-label="{% trans 'Decrease reading speed' %}">-</button>
        <span class="speed-display" aria-live="polite">
            <span id="current-speed">{{ user_wpm|default:250 }}</span> 
            {% trans "WPM" %}
        </span>
        <button id="speed-increase" class="speed-btn" type="button"
                aria-label="{% trans 'Increase reading speed' %}">+</button>
    </div>
    
    <!-- Main Controls -->
    <div class="reader-controls" role="group" aria-label="{% trans 'Reader controls' %}">
        <button id="start-pause-btn" class="primary-btn" type="button">
            {% trans "Start Reading" %}
        </button>
        <button id="reset-btn" class="secondary-btn" type="button">
            {% trans "Reset" %}
        </button>
        <button id="immersive-btn" class="secondary-btn" type="button">
            {% trans "Immersive Mode" %}
        </button>
    </div>
</section>

<!-- Immersive Overlay -->
<div id="immersive-overlay" class="immersive-overlay" role="dialog" 
     aria-label="{% trans 'Immersive Speed Reader' %}" aria-hidden="true">
    <div id="immersive-word-display" class="immersive-word-display" 
         aria-live="polite" role="status">
        {% trans "Ready to read" %}
    </div>
    <div class="immersive-controls">
        <div class="immersive-progress">
            <div id="immersive-progress-bar" class="immersive-progress-bar"></div>
        </div>
        <button id="immersive-stop-btn" class="immersive-stop-btn" type="button">
            {% trans "Stop Reading" %}
        </button>
    </div>
</div>
```

### 2. CSS Styling (PicoCSS Compatible)
```css
/* Speed Reader Styles */
.speed-reader-section {
    margin: 2rem 0;
    padding: 1.5rem;
    border: 1px solid var(--muted-border-color);
    border-radius: var(--border-radius);
    background-color: var(--card-background-color);
}

.word-display {
    min-height: 4rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    font-weight: 300;
    text-align: center;
    padding: 1rem;
    border: 2px solid var(--primary);
    border-radius: var(--border-radius);
    background-color: var(--background-color);
    margin-bottom: 1rem;
}

.reading-progress {
    width: 100%;
    height: 8px;
    margin-bottom: 1rem;
}

.speed-controls {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    margin-bottom: 1rem;
}

.speed-btn {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 1px solid var(--primary);
    background-color: var(--primary);
    color: var(--primary-inverse);
    font-size: 1.2rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
}

.speed-btn:hover {
    background-color: var(--primary-hover);
}

.speed-display {
    font-weight: 600;
    min-width: 80px;
    text-align: center;
}

.reader-controls {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    justify-content: center;
}

/* Immersive Mode Styles */
.immersive-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.95);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 9999;
    visibility: hidden;
    opacity: 0;
    transition: visibility 0s 0.3s, opacity 0.3s ease;
}

.immersive-overlay.active {
    visibility: visible;
    opacity: 1;
    transition: visibility 0s, opacity 0.3s ease;
}

.immersive-word-display {
    font-size: 4rem;
    color: #ffffff;
    padding: 2rem;
    text-align: center;
    flex-grow: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    white-space: nowrap;
}

/* Responsive Design */
@media (max-width: 768px) {
    .word-display {
        font-size: 1.5rem;
        min-height: 3rem;
    }
    
    .immersive-word-display {
        font-size: 2.5rem;
    }
    
    .reader-controls {
        flex-direction: column;
        align-items: center;
    }
}
```

### 3. JavaScript Implementation Pattern

#### Critical JavaScript Loading Order and Initialization Issues

**Problem**: Multiple critical issues preventing speed reader from working:
1. Django template caching or backup files interfering with updates
2. Template files not being used due to view configuration issues
3. JavaScript files loading before i18n translations are available
4. CSS/HTML structure mismatches

**Root Cause**: Django is not using the template file being edited, likely due to:
- Backup template files (*.backup) taking precedence
- Template caching issues
- View pointing to wrong template
- Middleware interference

**CRITICAL FIX STEPS**:

1. **Delete all backup template files**: `rm verifast_app/templates/**/*.backup`
2. **Clear Django cache**: `python manage.py shell -c "from django.core.cache import cache; cache.clear()"`
3. **Restart Django server**: Kill and restart the development server
4. **Verify template is being used**: Add obvious test markers to confirm changes appear
5. **Use working template structure**: Copy from known working implementation

**Complete Solution**:

**Step 1: Ensure Template Context Variables**
```python
# In views.py - ArticleDetailView
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['user_wpm'] = self.request.user.current_wpm if self.request.user.is_authenticated else 250
    return context
```

**Step 2: Simple, Working Template Structure**
```html
<!-- Speed Reader Section -->
<section id="speed-reader-section" class="speed-reader-section" 
         data-content="{{ article.content|escape }}" 
         data-user-wpm="{{ user_wpm|default:250 }}">
    
    <h2>Speed Reader</h2>
    
    <!-- Word Display -->
    <div id="word-display" class="word-display">
        Click Start to begin reading
    </div>
    
    <!-- Progress Bar -->
    <progress id="progress-bar" value="0" max="100">0%</progress>
    
    <!-- Speed Controls -->
    <div class="speed-controls">
        <button id="speed-decrease" type="button">-</button>
        <span><span id="current-speed">250</span> WPM</span>
        <button id="speed-increase" type="button">+</button>
    </div>
    
    <!-- Main Controls -->
    <div class="reader-controls">
        <button id="start-pause-btn" type="button">Start Reading</button>
        <button id="reset-btn" type="button">Reset</button>
    </div>
</section>
```

**Step 3: Inline JavaScript Implementation**

```javascript
// In article template - Initialize translation function first
{% block extra_js %}
<script>
// Initialize global translation function before loading other scripts
document.addEventListener('DOMContentLoaded', function() {
    // Global translation function
    window._ = function(key, params = {}) {
        if (typeof window.i18n === 'object' && typeof window.i18n._ === 'function') {
            return window.i18n._(key, params);
        }
        return key;
    };
    
    console.log('Translation function initialized');
});
</script>
<script src="{% static 'verifast_app/js/speed-reader.js' %}"></script>
</script>
{% endblock %}
```

```javascript
// In speed-reader.js - Wait for i18n before initializing
document.addEventListener('DOMContentLoaded', function() {
    console.log('Speed Reader: DOM loaded, waiting for i18n...');
    
    // Wait for i18n to be available
    function initializeWhenReady() {
        if (typeof window._ === 'function') {
            console.log('Speed Reader: i18n ready, initializing...');
            
            // Initialize speed reader
            const speedReader = new SpeedReader('speed-reader-section');
            
            // Make available globally for debugging
            window.speedReader = speedReader;
        } else {
            console.log('Speed Reader: Waiting for i18n...');
            setTimeout(initializeWhenReady, 100);
        }
    }
    
    initializeWhenReady();
});
```

#### Modern ES6+ Speed Reader Implementation
```javascript
class SpeedReader {
    constructor(sectionId) {
        this.section = document.getElementById(sectionId);
        this.wordDisplay = document.getElementById('word-display');
        this.startPauseBtn = document.getElementById('start-pause-btn');
        this.resetBtn = document.getElementById('reset-btn');
        this.immersiveBtn = document.getElementById('immersive-btn');
        this.speedDisplay = document.getElementById('current-speed');
        this.progressBar = document.getElementById('progress-bar');
        
        // Immersive elements
        this.immersiveOverlay = document.getElementById('immersive-overlay');
        this.immersiveWordDisplay = document.getElementById('immersive-word-display');
        this.immersiveProgressBar = document.getElementById('immersive-progress-bar');
        this.immersiveStopBtn = document.getElementById('immersive-stop-btn');
        
        // State
        this.words = [];
        this.currentIndex = 0;
        this.isRunning = false;
        this.isImmersive = false;
        this.intervalId = null;
        this.wpm = parseInt(this.section.dataset.userWpm) || 250;
        
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
        return this.section && this.wordDisplay && this.startPauseBtn && 
               this.resetBtn && this.speedDisplay && this.progressBar;
    }
    
    loadContent() {
        const content = this.section.dataset.content;
        if (!content) {
            this.showError(_('no_content_available'));
            return;
        }
        
        // Clean and split content
        this.words = content
            .replace(/\s+/g, ' ')
            .trim()
            .split(' ')
            .filter(word => word.length > 0);
            
        console.log(`Speed Reader: Loaded ${this.words.length} words`);
    }
    
    attachEventListeners() {
        this.startPauseBtn.addEventListener('click', () => this.toggleReading());
        this.resetBtn.addEventListener('click', () => this.resetReading());
        
        if (this.immersiveBtn) {
            this.immersiveBtn.addEventListener('click', () => this.toggleImmersive());
        }
        
        if (this.immersiveStopBtn) {
            this.immersiveStopBtn.addEventListener('click', () => this.stopImmersive());
        }
        
        // Speed controls
        const speedInc = document.getElementById('speed-increase');
        const speedDec = document.getElementById('speed-decrease');
        
        if (speedInc) speedInc.addEventListener('click', () => this.adjustSpeed(25));
        if (speedDec) speedDec.addEventListener('click', () => this.adjustSpeed(-25));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        // Escape key for immersive mode
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isImmersive) {
                this.stopImmersive();
            }
        });
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
            this.showError(_('no_content_available'));
            return;
        }
        
        if (this.currentIndex >= this.words.length) {
            this.resetReading();
        }
        
        const interval = 60000 / this.wpm;
        this.intervalId = setInterval(() => this.showNextWord(), interval);
        this.isRunning = true;
        this.updateButton(_('pause_reading'));
        
        console.log(`Speed Reader: Started at ${this.wpm} WPM`);
    }
    
    pauseReading() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.isRunning = false;
        this.updateButton(_('start_reading'));
        
        console.log('Speed Reader: Paused');
    }
    
    resetReading() {
        this.pauseReading();
        this.currentIndex = 0;
        this.updateProgress(0);
        this.showWord(_('click_start_reading'));
        this.updateButton(_('start_reading'));
        
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
        if (this.isImmersive && this.immersiveWordDisplay) {
            this.immersiveWordDisplay.textContent = word;
        }
    }
    
    finishReading() {
        this.pauseReading();
        this.showWord(_('reading_finished'));
        console.log('Speed Reader: Finished');
    }
    
    updateProgress(percentage) {
        this.progressBar.value = percentage;
        if (this.immersiveProgressBar) {
            this.immersiveProgressBar.style.width = percentage + '%';
        }
    }
    
    updateButton(text) {
        this.startPauseBtn.textContent = text;
    }
    
    adjustSpeed(delta) {
        this.wpm = Math.max(50, Math.min(1000, this.wpm + delta));
        this.updateSpeedDisplay();
        
        if (this.isRunning) {
            this.pauseReading();
            this.startReading();
        }
        
        console.log(`Speed Reader: Speed adjusted to ${this.wpm} WPM`);
    }
    
    updateSpeedDisplay() {
        this.speedDisplay.textContent = this.wpm;
    }
    
    toggleImmersive() {
        if (this.isImmersive) {
            this.stopImmersive();
        } else {
            this.startImmersive();
        }
    }
    
    startImmersive() {
        if (!this.immersiveOverlay) return;
        
        this.isImmersive = true;
        this.immersiveOverlay.classList.add('active');
        this.immersiveOverlay.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        
        // Sync current word
        const currentWord = this.currentIndex < this.words.length ? 
            this.words[this.currentIndex] : _('ready_to_read');
        this.immersiveWordDisplay.textContent = currentWord;
        
        console.log('Speed Reader: Immersive mode activated');
    }
    
    stopImmersive() {
        if (!this.immersiveOverlay) return;
        
        this.isImmersive = false;
        this.immersiveOverlay.classList.remove('active');
        this.immersiveOverlay.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        
        console.log('Speed Reader: Immersive mode deactivated');
    }
    
    handleKeyboard(e) {
        // Don't interfere with form inputs
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        
        switch (e.key) {
            case ' ':
                e.preventDefault();
                this.toggleReading();
                break;
            case 'r':
            case 'R':
                this.resetReading();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.adjustSpeed(25);
                break;
            case 'ArrowDown':
                e.preventDefault();
                this.adjustSpeed(-25);
                break;
        }
    }
    
    showError(message) {
        this.wordDisplay.textContent = message;
        this.wordDisplay.classList.add('error');
        console.error('Speed Reader:', message);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Global translation function
    window._ = function(key, params = {}) {
        return window.i18n ? window.i18n._(key, params) : key;
    };
    
    // Initialize speed reader
    const speedReader = new SpeedReader('speed-reader-section');
    
    // Make available globally for debugging
    window.speedReader = speedReader;
});
```

## Error Handling and Debugging

### 1. Console Logging
```javascript
// Use consistent logging levels
console.log('Speed Reader: Info message');
console.warn('Speed Reader: Warning message');
console.error('Speed Reader: Error message');

// Debug mode
const DEBUG = window.location.search.includes('debug=true');
if (DEBUG) {
    console.log('Speed Reader: Debug info', debugData);
}
```

### 2. User Feedback
```javascript
showError(message) {
    this.wordDisplay.textContent = message;
    this.wordDisplay.classList.add('error');
    
    // Announce to screen readers
    this.wordDisplay.setAttribute('aria-live', 'assertive');
    
    // Auto-clear after delay
    setTimeout(() => {
        this.wordDisplay.classList.remove('error');
        this.wordDisplay.setAttribute('aria-live', 'polite');
    }, 3000);
}
```

### 3. Graceful Degradation
```javascript
validateElements() {
    const required = [this.section, this.wordDisplay, this.startPauseBtn];
    const missing = required.filter(el => !el);
    
    if (missing.length > 0) {
        console.error('Speed Reader: Missing elements:', missing);
        this.showFallbackMessage();
        return false;
    }
    
    return true;
}

showFallbackMessage() {
    const fallback = document.createElement('div');
    fallback.innerHTML = `
        <p>${_('speed_reader_unavailable')}</p>
        <p><a href="${window.location.href}?fallback=true">${_('view_article_text')}</a></p>
    `;
    this.section.appendChild(fallback);
}
```

## Testing Guidelines

### 1. Manual Testing Checklist
- [ ] Speed reader loads without errors
- [ ] Start/pause button works
- [ ] Speed controls adjust WPM correctly
- [ ] Progress bar updates during reading
- [ ] Reset button works
- [ ] Immersive mode toggles correctly
- [ ] Keyboard shortcuts work
- [ ] Responsive design works on mobile
- [ ] Screen reader accessibility
- [ ] All text is translatable

### 2. Browser Console Tests
```javascript
// Test in browser console
speedReader.startReading();
speedReader.adjustSpeed(100);
speedReader.toggleImmersive();
```

This architecture ensures robust, accessible, and maintainable frontend components that integrate seamlessly with Django's backend systems while maintaining full i18n compliance.

## Troubleshooting Reference

For comprehensive debugging guidance and solutions to common issues, see:
- **Speed Reader Debugging Guide**: `documentation/troubleshooting/speed-reader-debugging-guide.md`

This guide contains detailed findings from debugging the VeriFast Speed Reader implementation, including:
- Django template loading problems and solutions
- JavaScript initialization timing issues
- CSS/HTML structure mismatches
- Port conflicts with honcho/gunicorn
- Complete working implementations
- Prevention strategies and testing checklists