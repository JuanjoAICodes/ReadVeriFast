# Speed Reader Documentation

*Last Updated: July 21, 2025*
*Status: Current*

## Overview

The VeriFast Speed Reader provides an immersive, distraction-free reading experience with configurable speed settings, word chunking, and progress tracking to help users improve their reading speed and comprehension.

## Core Features

### 1. Immersive Reading Mode
**Full-Screen Experience:**
- **Distraction-Free Interface** - Removes all navigation and UI elements
- **Focus Mode** - Centers content for optimal reading
- **Dark Mode Support** - Reduces eye strain during extended reading
- **Customizable Backgrounds** - Multiple theme options

### 2. Configurable Reading Speed
**WPM (Words Per Minute) Control:**
- **Speed Range** - 50 to 1000+ WPM
- **Real-Time Adjustment** - Change speed during reading
- **Speed Presets** - Quick access to common speeds
- **Personal Speed Tracking** - Remembers user preferences

### 3. Word Chunking System
**Advanced Text Processing:**
- **Configurable Chunks** - 1-5 words per display
- **Smart Grouping** - Respects natural word boundaries
- **Punctuation Handling** - Pauses at sentence endings
- **Symbol Processing** - Handles special characters appropriately

### 4. Progress Tracking
**Reading Analytics:**
- **Progress Bar** - Visual reading progress
- **Time Tracking** - Total reading time
- **Speed Monitoring** - Current and average WPM
- **Completion Status** - Article completion tracking

## User Interface

### Speed Reader Controls
**Location:** `verifast_app/templates/verifast_app/speed_reader.html`

**Control Elements:**
```html
<!-- Speed Controls -->
<div class="speed-controls">
    <label for="wpm-slider">Reading Speed: <span id="wpm-display">250</span> WPM</label>
    <input type="range" id="wpm-slider" min="50" max="1000" value="250">
</div>

<!-- Chunking Controls -->
<div class="chunk-controls">
    <label for="chunk-size">Words per chunk:</label>
    <select id="chunk-size">
        <option value="1">1 word</option>
        <option value="2" selected>2 words</option>
        <option value="3">3 words</option>
    </select>
</div>

<!-- Reading Controls -->
<div class="reading-controls">
    <button id="start-btn">Start Reading</button>
    <button id="pause-btn">Pause</button>
    <button id="reset-btn">Reset</button>
</div>
```

### Display Area
**Word Display:**
- **Large, Clear Text** - Optimized for readability
- **Centered Layout** - Reduces eye movement
- **Smooth Transitions** - Prevents jarring changes
- **Highlighting** - Current word emphasis

## Technical Implementation

### JavaScript Engine
**Location:** `verifast_app/static/verifast_app/js/speed_reader.js`

**Core Functions:**
```javascript
class SpeedReader {
    constructor(articleContent, options = {}) {
        this.content = this.processContent(articleContent);
        this.wpm = options.wpm || 250;
        this.chunkSize = options.chunkSize || 2;
        this.currentIndex = 0;
        this.isPlaying = false;
    }
    
    processContent(content) {
        // Clean and prepare text for reading
        return content
            .replace(/\s+/g, ' ')
            .split(' ')
            .filter(word => word.length > 0);
    }
    
    start() {
        this.isPlaying = true;
        this.displayNextChunk();
    }
    
    displayNextChunk() {
        if (!this.isPlaying || this.currentIndex >= this.content.length) {
            return this.complete();
        }
        
        const chunk = this.getNextChunk();
        this.displayChunk(chunk);
        this.updateProgress();
        
        const delay = this.calculateDelay(chunk);
        setTimeout(() => this.displayNextChunk(), delay);
    }
    
    calculateDelay(chunk) {
        const wordsPerMinute = this.wpm;
        const wordsPerSecond = wordsPerMinute / 60;
        const baseDelay = (chunk.length / wordsPerSecond) * 1000;
        
        // Add extra time for punctuation
        const punctuationDelay = this.getPunctuationDelay(chunk);
        return baseDelay + punctuationDelay;
    }
}
```

### Backend Integration
**Location:** `verifast_app/views.py`

**Speed Reader View:**
```python
class SpeedReaderView(DetailView):
    model = Article
    template_name = 'verifast_app/speed_reader.html'
    context_object_name = 'article'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user preferences
        if self.request.user.is_authenticated:
            context['user_wpm'] = self.request.user.current_wpm
            context['max_wpm'] = self.request.user.max_wpm
        else:
            context['user_wpm'] = 250
            context['max_wpm'] = 500
            
        # Prepare article content
        context['word_count'] = len(self.object.content.split())
        context['estimated_time'] = self.calculate_reading_time(
            context['word_count'], 
            context['user_wpm']
        )
        
        return context
    
    def calculate_reading_time(self, word_count, wpm):
        """Calculate estimated reading time in minutes"""
        return max(1, round(word_count / wpm))
```

## User Experience Features

### Personalization
**User Preferences:**
- **Saved Speed Settings** - Remembers preferred WPM
- **Chunk Size Preferences** - Saves optimal chunk size
- **Theme Selection** - Dark/light mode preference
- **Font Customization** - Premium feature for font selection

### Accessibility
**Inclusive Design:**
- **Keyboard Navigation** - Full keyboard control
- **Screen Reader Support** - ARIA labels and descriptions
- **High Contrast Mode** - For visual accessibility
- **Adjustable Text Size** - Scalable interface

### Mobile Optimization
**Responsive Design:**
- **Touch Controls** - Mobile-friendly interface
- **Swipe Gestures** - Intuitive mobile navigation
- **Orientation Support** - Portrait and landscape modes
- **Performance Optimization** - Smooth on mobile devices

## Integration with Other Systems

### XP System Integration
**Gamification Features:**
- **Reading Completion XP** - Points for finishing articles
- **Speed Improvement Bonuses** - XP for increasing WPM
- **Consistency Rewards** - Daily reading streak bonuses
- **Achievement Unlocks** - Speed milestones

### Quiz System Integration
**Comprehension Testing:**
- **Post-Reading Quizzes** - Automatic quiz generation
- **Speed vs Comprehension** - Balance tracking
- **Performance Analytics** - Reading effectiveness metrics
- **Adaptive Difficulty** - Quiz difficulty based on reading speed

### Analytics Integration
**Reading Metrics:**
- **Session Tracking** - Individual reading sessions
- **Progress Monitoring** - Long-term improvement tracking
- **Speed Trends** - WPM improvement over time
- **Engagement Metrics** - Reading frequency and duration

## Performance Optimizations

### Frontend Optimizations
- **Efficient DOM Updates** - Minimal reflows and repaints
- **Memory Management** - Proper cleanup of intervals
- **Smooth Animations** - CSS transitions for better UX
- **Lazy Loading** - Load content as needed

### Backend Optimizations
- **Content Caching** - Cache processed article content
- **User Preference Caching** - Cache user settings
- **Database Optimization** - Efficient queries for user data
- **CDN Integration** - Fast static file delivery

## Testing

### Frontend Testing
**Location:** `verifast_app/static/verifast_app/js/tests/`

**Test Coverage:**
- **Speed Calculation** - WPM timing accuracy
- **Chunk Processing** - Word grouping logic
- **User Interactions** - Control responsiveness
- **Cross-Browser Compatibility** - Multiple browser testing

### Integration Testing
- **User Preference Persistence** - Settings saving/loading
- **XP Integration** - Point calculation accuracy
- **Quiz Transition** - Smooth handoff to quiz system
- **Mobile Functionality** - Touch and gesture testing

## Configuration

### Speed Reader Settings
```python
# settings.py
SPEED_READER_CONFIG = {
    'MIN_WPM': 50,
    'MAX_WPM': 1000,
    'DEFAULT_WPM': 250,
    'MAX_CHUNK_SIZE': 5,
    'DEFAULT_CHUNK_SIZE': 2,
    'PUNCTUATION_DELAY': 300,  # milliseconds
    'SENTENCE_DELAY': 500,     # milliseconds
}
```

### Premium Features
```python
PREMIUM_SPEED_FEATURES = {
    'font_customization': {
        'cost': 30,
        'fonts': ['OpenSans', 'Roboto', 'Lato']
    },
    'advanced_analytics': {
        'cost': 50,
        'features': ['detailed_metrics', 'progress_charts']
    }
}
```

## Future Enhancements

### Planned Features
- **Voice Reading Mode** - Text-to-speech integration
- **Eye Tracking** - Advanced reading pattern analysis
- **Bionic Reading** - Highlight word beginnings
- **Reading Challenges** - Competitive reading goals

### Advanced Analytics
- **Comprehension Correlation** - Speed vs understanding metrics
- **Optimal Speed Detection** - AI-recommended reading speeds
- **Content Difficulty Analysis** - Automatic speed adjustment
- **Reading Pattern Recognition** - Personalized optimization

## Related Documentation
- [XP System](xp-system.md) - Gamification integration
- [Tag System](tag-system.md) - Content organization
- [API Specification](../api/specification.md) - Speed reader endpoints
- [User Management](user-management.md) - User preferences and settings