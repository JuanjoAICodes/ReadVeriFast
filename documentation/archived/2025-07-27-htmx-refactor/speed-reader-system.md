# Speed Reader System Documentation

## Overview

The VeriFast Speed Reader is a hybrid HTMX + Django system that provides word-by-word reading functionality with advanced features and gamification integration.

## Core Features

### 1. Word-by-Word Display
- **Configurable Speed**: 50-1000 WPM range
- **Smooth Timing**: Client-side timing for consistent display
- **Progress Tracking**: Real-time progress bar and percentage
- **Completion Detection**: Automatic quiz unlock on completion

### 2. User Controls
- **Start/Pause/Reset**: Full playback control
- **Speed Adjustment**: Real-time WPM modification
- **Immersive Mode**: Full-screen distraction-free reading
- **Keyboard Shortcuts**: Space, arrows, escape key support

### 3. Power-ups Integration
- **Smart Chunking**: Groups related words together
- **Multi-word Display**: 2, 3, 4, or 5 words at once
- **Font Customization**: User-selected fonts and sizes
- **Dyslexia Support**: Specialized fonts and spacing

## Technical Architecture

### Backend Components

#### Views
```python
# verifast_app/views/speed_reader.py
def speed_reader_init(request, article_id):
    """Initialize speed reader with user's purchased power-ups"""
    article = get_object_or_404(Article, id=article_id)
    user = request.user if request.user.is_authenticated else None
    
    # Apply user's power-ups to content processing
    word_chunks = get_chunked_words(article.content, user)
    font_settings = get_user_font_settings(user)
    
    return render(request, 'partials/speed_reader_init.html', {
        'word_chunks_json': json.dumps(word_chunks),
        'font_settings': font_settings,
        'user_features': get_user_features(user),
        'article_id': article_id,
        'total_words': len(word_chunks)
    })

def reading_complete(request, article_id):
    """Handle reading completion and unlock quiz"""
    if request.user.is_authenticated:
        # Track reading completion for analytics
        ReadingSession.objects.create(
            user=request.user,
            article_id=article_id,
            completed_at=timezone.now()
        )
    
    return render(request, 'partials/quiz_unlock.html', {
        'article_id': article_id
    })
```

#### Services
```python
# verifast_app/services/speed_reader.py
def get_chunked_words(article_content, user):
    """Process article content based on user's power-ups"""
    words = article_content.split()
    
    # Apply smart connector grouping if user has the power-up
    if user and user.has_smart_connector_grouping:
        words = apply_smart_connector_grouping(words)
    
    # Apply chunking based on user's purchased features
    chunk_size = get_user_chunk_size(user)
    return create_word_chunks(words, chunk_size)

def apply_smart_connector_grouping(words):
    """Group small connector words with adjacent content words"""
    connectors = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by']
    grouped_words = []
    
    i = 0
    while i < len(words):
        current_group = [words[i]]
        
        # Look ahead for connectors
        if (i + 1 < len(words) and 
            words[i + 1].lower() in connectors and 
            len(words[i + 1]) <= 3):
            
            current_group.append(words[i + 1])
            
            # Include the word after the connector
            if i + 2 < len(words):
                current_group.append(words[i + 2])
                i += 3
            else:
                i += 2
        else:
            i += 1
        
        grouped_words.append(' '.join(current_group))
    
    return grouped_words

def get_user_chunk_size(user):
    """Determine chunk size based on user's purchased power-ups"""
    if not user or not user.is_authenticated:
        return 1
    
    if user.has_5word_chunking:
        return 5
    elif user.has_4word_chunking:
        return 4
    elif user.has_3word_chunking:
        return 3
    elif user.has_2word_chunking:
        return 2
    else:
        return 1

def get_user_font_settings(user):
    """Get font settings based on user's preferences and power-ups"""
    default_settings = {
        'font_family': 'Arial, sans-serif',
        'font_size': '3rem',
        'font_weight': 'normal',
        'letter_spacing': 'normal',
        'line_height': '1.2'
    }
    
    if not user or not user.is_authenticated:
        return default_settings
    
    settings = default_settings.copy()
    
    # Apply font customization power-up
    if user.has_font_customization:
        settings.update({
            'font_family': user.preferred_font or default_settings['font_family'],
            'font_size': f"{user.preferred_font_size or 3}rem",
            'font_weight': user.preferred_font_weight or default_settings['font_weight']
        })
    
    # Apply dyslexia-friendly settings
    if user.has_dyslexia_support:
        settings.update({
            'font_family': 'OpenDyslexic, Arial, sans-serif',
            'letter_spacing': '0.1em',
            'line_height': '1.5'
        })
    
    return settings
```

### Frontend Components

#### Alpine.js Controller
```javascript
// static/js/speed-reader.js
function speedReader(wordChunks, fontSettings, articleId) {
    return {
        // State
        chunks: wordChunks,
        currentIndex: 0,
        currentChunk: 'Click Start to begin reading',
        isRunning: false,
        isComplete: false,
        wpm: 250,
        interval: null,
        
        // Computed properties
        get progress() {
            return this.chunks.length > 0 ? 
                Math.round((this.currentIndex / this.chunks.length) * 100) : 0;
        },
        
        get fontStyles() {
            return {
                fontFamily: fontSettings.font_family,
                fontSize: fontSettings.font_size,
                fontWeight: fontSettings.font_weight,
                letterSpacing: fontSettings.letter_spacing,
                lineHeight: fontSettings.line_height
            };
        },
        
        // Methods
        toggleReading() {
            this.isRunning ? this.pauseReading() : this.startReading();
        },
        
        startReading() {
            if (this.currentIndex >= this.chunks.length) {
                this.resetReading();
            }
            
            this.isRunning = true;
            const intervalMs = 60000 / this.wpm;
            
            this.interval = setInterval(() => {
                if (this.currentIndex < this.chunks.length) {
                    this.currentChunk = this.chunks[this.currentIndex];
                    this.currentIndex++;
                } else {
                    this.completeReading();
                }
            }, intervalMs);
        },
        
        pauseReading() {
            this.isRunning = false;
            if (this.interval) {
                clearInterval(this.interval);
                this.interval = null;
            }
        },
        
        resetReading() {
            this.pauseReading();
            this.currentIndex = 0;
            this.currentChunk = 'Click Start to begin reading';
            this.isComplete = false;
        },
        
        adjustSpeed(delta) {
            this.wpm = Math.max(50, Math.min(1000, this.wpm + delta));
            if (this.isRunning) {
                this.pauseReading();
                this.startReading();
            }
        },
        
        completeReading() {
            this.pauseReading();
            this.currentChunk = 'Reading Complete! 🎉';
            this.isComplete = true;
            
            // Notify server of completion via HTMX
            htmx.ajax('POST', `/reading-complete/${articleId}/`, {
                target: '#quiz-section',
                swap: 'innerHTML'
            });
        }
    }
}
```

#### Templates
```html
<!-- templates/partials/speed_reader_init.html -->
<div id="speed-reader-container" 
     x-data="speedReader({{ word_chunks_json|safe }}, {{ font_settings|safe }}, {{ article_id }})"
     class="speed-reader-section">
    
    <!-- Word Display -->
    <div class="word-display" 
         x-text="currentChunk"
         :style="fontStyles"
         :class="{'reading-complete': isComplete}">
    </div>
    
    <!-- Progress Bar -->
    <div class="progress-container">
        <div class="progress-bar">
            <div class="progress-fill" 
                 :style="`width: ${progress}%`">
            </div>
        </div>
        <div class="progress-text">
            <span x-text="progress"></span>% - 
            <span x-text="currentIndex"></span> / <span x-text="chunks.length"></span> chunks
        </div>
    </div>
    
    <!-- Controls -->
    <div class="speed-controls">
        <button @click="adjustSpeed(-25)" 
                :disabled="wpm <= 50"
                aria-label="Decrease speed">
            -
        </button>
        
        <span class="speed-display">
            <span x-text="wpm"></span> WPM
        </span>
        
        <button @click="adjustSpeed(25)" 
                :disabled="wpm >= 1000"
                aria-label="Increase speed">
            +
        </button>
    </div>
    
    <!-- Main Controls -->
    <div class="reader-controls">
        <button @click="toggleReading()" 
                class="primary"
                :disabled="chunks.length === 0">
            <span x-text="isRunning ? 'Pause' : (isComplete ? 'Restart' : 'Start Reading')"></span>
        </button>
        
        <button @click="resetReading()" 
                :disabled="currentIndex === 0 && !isComplete">
            Reset
        </button>
        
        {% if user_features.has_immersive_mode %}
        <button @click="toggleImmersive()" 
                class="secondary">
            Immersive Mode
        </button>
        {% endif %}
    </div>
    
    <!-- Feature-specific controls -->
    {% if user_features.has_advanced_controls %}
    <div class="advanced-controls" x-show="showAdvanced">
        <h4>Advanced Settings</h4>
        
        {% if user_features.has_chunking_options %}
        <div class="chunk-size-control">
            <label for="chunk-size">Chunk Size:</label>
            <select id="chunk-size" @change="updateChunkSize($event.target.value)">
                <option value="1">Single Words</option>
                {% if user_features.has_2word_chunking %}<option value="2">2 Words</option>{% endif %}
                {% if user_features.has_3word_chunking %}<option value="3">3 Words</option>{% endif %}
                {% if user_features.has_4word_chunking %}<option value="4">4 Words</option>{% endif %}
                {% if user_features.has_5word_chunking %}<option value="5">5 Words</option>{% endif %}
            </select>
        </div>
        {% endif %}
        
        {% if user_features.has_font_customization %}
        <div class="font-controls">
            <label for="font-family">Font:</label>
            <select id="font-family" @change="updateFont($event.target.value)">
                <option value="Arial, sans-serif">Arial</option>
                <option value="Georgia, serif">Georgia</option>
                <option value="'Courier New', monospace">Courier New</option>
                {% if user_features.has_dyslexia_support %}
                <option value="OpenDyslexic, Arial, sans-serif">OpenDyslexic</option>
                {% endif %}
            </select>
        </div>
        {% endif %}
    </div>
    {% endif %}
    
    <!-- Reading completion message -->
    <div x-show="isComplete" class="completion-message">
        <h3>🎉 Reading Complete!</h3>
        <p>You read <span x-text="chunks.length"></span> word chunks at <span x-text="wpm"></span> WPM.</p>
        <p>Quiz unlocked below! Complete it to earn XP.</p>
    </div>
</div>

<!-- Immersive Mode Overlay -->
{% if user_features.has_immersive_mode %}
<div id="immersive-overlay" 
     x-show="immersiveMode" 
     x-transition
     class="immersive-overlay"
     @keydown.escape="toggleImmersive()">
    
    <div class="immersive-word-display" 
         x-text="currentChunk"
         :style="fontStyles">
    </div>
    
    <div class="immersive-controls">
        <div class="immersive-progress">
            <div class="progress-bar">
                <div class="progress-fill" :style="`width: ${progress}%`"></div>
            </div>
        </div>
        
        <button @click="toggleReading()" class="immersive-play-pause">
            <span x-text="isRunning ? '⏸️' : '▶️'"></span>
        </button>
        
        <button @click="toggleImmersive()" class="immersive-exit">
            Exit Immersive
        </button>
    </div>
</div>
{% endif %}
```

## Power-ups Integration

### Available Power-ups

#### Chunking Features
- **2-Word Chunking** (500 XP): Display 2 words at once
- **3-Word Chunking** (750 XP): Display 3 words at once  
- **4-Word Chunking** (1000 XP): Display 4 words at once
- **5-Word Chunking** (1500 XP): Display 5 words at once

#### Smart Features
- **Smart Connector Grouping** (1000 XP): Automatically group small words
- **Immersive Mode** (500 XP): Full-screen distraction-free reading
- **Advanced Controls** (300 XP): Additional customization options

#### Accessibility Features
- **Font Customization** (750 XP): Choose preferred fonts and sizes
- **Dyslexia Support** (1200 XP): Specialized fonts and spacing
- **High Contrast Mode** (400 XP): Enhanced visual contrast

### Power-up Application
```python
# Power-ups are applied server-side during initialization
def apply_user_powerups(article_content, user):
    """Apply all user's purchased power-ups to article content"""
    
    # Start with base word splitting
    words = article_content.split()
    
    # Apply smart connector grouping
    if user.has_smart_connector_grouping:
        words = apply_smart_connector_grouping(words)
    
    # Apply chunking
    chunk_size = get_user_chunk_size(user)
    chunks = create_word_chunks(words, chunk_size)
    
    return chunks
```

## Performance Optimization

### Caching Strategy
```python
# Cache processed article content
@cache_page(60 * 15)  # 15 minutes
def speed_reader_init(request, article_id):
    # Implementation with caching
    
# Cache user features
def get_user_features(user):
    if not user.is_authenticated:
        return get_anonymous_features()
    
    cache_key = f'user_features_{user.id}_{user.updated_at.timestamp()}'
    return cache.get_or_set(cache_key, calculate_user_features(user), 300)
```

### Network Optimization
- **Single Request**: All data sent in initial request
- **Minimal Payload**: Only necessary data transmitted
- **Compression**: Gzip compression for JSON data

## Accessibility Features

### Screen Reader Support
- **Semantic HTML**: Proper heading structure and landmarks
- **ARIA Labels**: Descriptive labels for all controls
- **Live Regions**: Progress announcements
- **Focus Management**: Logical tab order

### Keyboard Navigation
- **Space**: Start/pause reading
- **Arrow Up/Down**: Adjust speed
- **R**: Reset reading
- **F**: Toggle immersive mode (if available)
- **Escape**: Exit immersive mode

### Visual Accessibility
- **High Contrast**: WCAG AA compliant colors
- **Font Scaling**: Respects user's browser settings
- **Motion Reduction**: Respects prefers-reduced-motion
- **Focus Indicators**: Clear visual focus states

## Mobile Responsiveness

### Responsive Design
```css
/* Mobile-first responsive design */
.speed-reader-section {
    padding: 1rem;
}

.word-display {
    font-size: 2rem;
    min-height: 80px;
}

@media (min-width: 768px) {
    .speed-reader-section {
        padding: 2rem;
    }
    
    .word-display {
        font-size: 3rem;
        min-height: 120px;
    }
}

@media (min-width: 1024px) {
    .word-display {
        font-size: 4rem;
        min-height: 150px;
    }
}
```

### Touch Interactions
- **Large Touch Targets**: Minimum 44px for all buttons
- **Touch-friendly Controls**: Optimized for finger interaction
- **Swipe Gestures**: Optional swipe for speed adjustment

## Error Handling

### Frontend Error Handling
```javascript
// Error boundaries in Alpine.js
function speedReader(wordChunks, fontSettings, articleId) {
    return {
        error: null,
        
        init() {
            try {
                // Validate input data
                if (!Array.isArray(wordChunks) || wordChunks.length === 0) {
                    throw new Error('Invalid article content');
                }
                this.chunks = wordChunks;
            } catch (error) {
                this.handleError(error);
            }
        },
        
        handleError(error) {
            this.error = 'Unable to load speed reader. Please refresh and try again.';
            console.error('Speed Reader Error:', error);
        }
    }
}
```

### Backend Error Handling
```python
def speed_reader_init(request, article_id):
    try:
        article = get_object_or_404(Article, id=article_id)
        
        if not article.content:
            raise ValueError("Article has no content")
        
        # Process article...
        return render(request, 'speed_reader.html', context)
        
    except Article.DoesNotExist:
        return render(request, 'errors/article_not_found.html', status=404)
    except Exception as e:
        logger.error(f"Speed reader initialization error: {e}")
        return render(request, 'errors/speed_reader_error.html', {
            'error_message': 'Unable to initialize speed reader'
        }, status=500)
```

## Analytics and Tracking

### Reading Analytics
```python
# Track reading sessions for analytics
class ReadingSession(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    wpm_used = models.IntegerField()
    completion_rate = models.FloatField()  # Percentage completed
    session_duration = models.DurationField()
    created_at = models.DateTimeField(auto_now_add=True)
```

### Performance Metrics
- **Load Time**: Time to initialize speed reader
- **Completion Rate**: Percentage of users who finish reading
- **Average WPM**: User reading speed trends
- **Feature Usage**: Which power-ups are most popular

This documentation provides a comprehensive guide to the Speed Reader system, covering all aspects from technical implementation to user experience considerations.