# Speed Reader Feature Documentation

*Last Updated: July 27, 2025*  
*Status: HTMX Hybrid Architecture*

## Overview

The VeriFast Speed Reader is a full-screen immersive reading system that provides word-by-word reading functionality with a single-mode design. The interface uses a full-width white text strip spanning the entire screen width for maximum visibility and focus.

**IMPORTANT: SINGLE-MODE DESIGN**
- **Primary Interface**: Immersive mode is the ONLY speed reading interface
- **No Regular Mode**: The traditional inline speed reader has been removed
- **Full-Width Display**: Text strip spans entire screen width (side to side)
- **Simplified UX**: Single "Start Reading" button launches immersive mode directly

## Architecture

### HTMX Hybrid Approach
- **Server-Side Processing**: All business logic, power-ups, and content processing in Django
- **Minimal Client JavaScript**: 30 lines of Alpine.js for word display timing only
- **Network Optimization**: Single initialization request, zero requests during reading
- **Progressive Enhancement**: Works without JavaScript, enhanced with minimal client code

### Key Benefits
- **95% Network Reduction**: From 100+ requests to 2-4 requests per session
- **Maintainable**: All logic in Python/Django (no complex JavaScript debugging)
- **Reliable**: Server-side processing eliminates client-side errors
- **Unified**: Same architecture for regular articles and Wikipedia articles

## Core Features

### 1. Server-Side Content Processing
**Power-up Application:**
- **Word Chunking**: 1-5 words per display based on user's purchased features
- **Smart Connector Grouping**: Intelligently groups small words with adjacent content
- **Font Customization**: CSS generation based on user's font preferences
- **Dyslexia Support**: Specialized fonts and spacing applied server-side

**Content Preparation:**
```python
# Server processes content once with user's power-ups
def prepare_speed_reader_content(article, user):
    # Apply chunking based on user's purchased power-ups
    word_chunks = get_chunked_words(article.content, user)
    
    # Generate font settings based on user preferences
    font_settings = get_user_font_settings(user)
    
    # Configure reading behavior
    reading_settings = get_reading_settings(user)
    
    return {
        'word_chunks': word_chunks,
        'font_settings': font_settings,
        'reading_settings': reading_settings
    }
```

### 2. Minimal Client-Side Display
**Alpine.js Component (30 lines):**
```javascript
function speedReader(wordChunks, fontSettings, readingSettings, articleId, articleType) {
    return {
        chunks: wordChunks,
        currentIndex: 0,
        currentChunk: 'Click Start to begin reading',
        isRunning: false,
        currentWpm: readingSettings.default_wpm,
        
        toggleReading() {
            this.isRunning ? this.pauseReading() : this.startReading();
        },
        
        startReading() {
            const intervalMs = 60000 / this.currentWpm;
            this.interval = setInterval(() => this.showNextWord(), intervalMs);
            this.isRunning = true;
        },
        
        showNextWord() {
            if (this.currentIndex < this.chunks.length) {
                this.currentChunk = this.chunks[this.currentIndex];
                this.currentIndex++;
            } else {
                this.completeReading();
            }
        },
        
        completeReading() {
            this.pauseReading();
            // Notify server via HTMX
            htmx.ajax('POST', `/reading-complete/${articleId}/${articleType}/`, {
                target: '#quiz-section',
                swap: 'innerHTML'
            });
        }
    }
}
```

### 3. HTMX Integration Points

**Initialization Endpoint:**
```
GET /speed-reader/init/{article_id}/{article_type}/
→ Returns processed content + Alpine.js component
```

**Completion Endpoint:**
```
POST /reading-complete/{article_id}/{article_type}/
→ Awards XP, unlocks quiz, returns quiz interface
```

## User Experience Features

### 1. Power-up Integration
**Available Power-ups:**
- **2-5 Word Chunking** (500-1500 XP): Display multiple words simultaneously
- **Smart Connector Grouping** (1000 XP): Intelligent word grouping
- **Font Customization** (750 XP): Custom fonts, sizes, and spacing
- **Dyslexia Support** (1200 XP): Specialized fonts and enhanced spacing

**Note**: Immersive mode is now the default interface for all users (no longer a premium feature)

**Server-Side Application:**
```python
def get_chunked_words(content, user):
    words = content.split()
    
    # Apply smart grouping if user has the power-up
    if user and user.has_smart_connector_grouping:
        words = apply_smart_connector_grouping(words)
    
    # Determine chunk size based on purchased power-ups
    chunk_size = get_user_chunk_size(user)  # 1-5 based on purchases
    
    return create_word_chunks(words, chunk_size)
```

### 2. Reading Controls
**User Interface:**
- **Start/Pause/Reset**: Full reading control
- **Speed Adjustment**: Real-time WPM modification (50-1000 WPM)
- **Progress Tracking**: Visual progress bar and percentage
- **Immersive Mode**: Full-screen overlay (premium feature)

**Keyboard Shortcuts:**
- **Space**: Start/pause reading
- **Arrow Up/Down**: Adjust speed
- **R**: Reset reading
- **F**: Toggle immersive mode (if available)
- **Escape**: Exit immersive mode

### 3. Accessibility Features
**WCAG AA Compliance:**
- **Screen Reader Support**: Proper ARIA labels and live regions
- **Keyboard Navigation**: Full keyboard accessibility
- **High Contrast Mode**: Enhanced visual contrast (premium feature)
- **Font Scaling**: Respects user's browser settings
- **Motion Reduction**: Respects prefers-reduced-motion

## Technical Implementation

### Backend Services
**Location:** `verifast_app/services.py`

```python
class SpeedReaderService:
    @staticmethod
    def prepare_content(article, user):
        \"\"\"Prepare article content with user-specific processing\"\"\"
        content = SpeedReaderService.clean_content(article.content)
        word_chunks = SpeedReaderService.get_chunked_words(content, user)
        font_settings = SpeedReaderService.get_font_settings(user)
        reading_settings = SpeedReaderService.get_reading_settings(user)
        
        return {
            'word_chunks': word_chunks,
            'font_settings': font_settings,
            'reading_settings': reading_settings,
            'total_words': len(word_chunks),
            'estimated_time': SpeedReaderService.estimate_reading_time(word_chunks, user)
        }
```

### HTMX Views
**Location:** `verifast_app/views.py`

```python
def speed_reader_init(request, article_id, article_type='regular'):
    \"\"\"Initialize speed reader with preprocessed content\"\"\"
    if article_type == 'wikipedia':
        article = get_object_or_404(WikipediaArticle, id=article_id)
    else:
        article = get_object_or_404(Article, id=article_id)
    
    user = request.user if request.user.is_authenticated else None
    content_data = SpeedReaderService.prepare_content(article, user)
    
    return render(request, 'partials/speed_reader_active.html', {
        'word_chunks_json': json.dumps(content_data['word_chunks']),
        'font_settings': content_data['font_settings'],
        'reading_settings': content_data['reading_settings'],
        'article_id': article_id,
        'article_type': article_type,
        'total_words': content_data['total_words']
    })

def speed_reader_complete(request, article_id, article_type='regular'):
    \"\"\"Handle reading completion and unlock quiz\"\"\"
    if request.user.is_authenticated:
        # Track completion and award XP
        xp_awarded = calculate_reading_xp(request.user, article_id, article_type)
        request.user.total_xp += xp_awarded
        request.user.current_xp_points += xp_awarded
        request.user.save()
    
    return render(request, 'partials/quiz_unlock.html', {
        'article_id': article_id,
        'article_type': article_type,
        'xp_awarded': xp_awarded if request.user.is_authenticated else 0
    })
```

### Templates
**Location:** `verifast_app/templates/partials/`

**Speed Reader Interface:**
```html
<!-- speed_reader_active.html -->
<div id=\"speed-reader-active\" 
     x-data=\"speedReader({{ word_chunks_json|safe }}, {{ font_settings|safe }}, {{ reading_settings|safe }}, '{{ article_id }}', '{{ article_type }}')\"
     class=\"speed-reader-active\">
    
    <!-- Word Display -->
    <div class=\"word-display\" 
         :style=\"wordDisplayStyles\"
         x-text=\"currentChunk\">
        Click Start to begin reading
    </div>
    
    <!-- Progress Bar -->
    <div class=\"progress-container\">
        <div class=\"progress-bar\">
            <div class=\"progress-fill\" :style=\"`width: ${progress}%`\"></div>
        </div>
        <div class=\"progress-text\">
            <span x-text=\"currentIndex\"></span> / <span x-text=\"totalChunks\"></span>
            (<span x-text=\"Math.round(progress)\"></span>%)
        </div>
    </div>
    
    <!-- Controls -->
    <div class=\"reader-controls\">
        <button @click=\"toggleReading()\" class=\"primary\">
            <span x-text=\"isRunning ? 'Pause' : 'Start Reading'\"></span>
        </button>
        <button @click=\"resetReading()\">Reset</button>
        <button @click=\"toggleImmersive()\" x-show=\"hasImmersiveMode\">
            Immersive Mode
        </button>
    </div>
</div>
```

## Performance Characteristics

### Network Optimization
| Metric | Old JavaScript | HTMX Hybrid |
|--------|---------------|-------------|
| Initial Load | 1 request | 1 request |
| Speed Reader Init | 1 request | 1 request |
| During Reading | 100+ requests | 0 requests |
| Reading Complete | 1 request | 1 request |
| **Total per Session** | **103+ requests** | **3 requests** |

### JavaScript Complexity
| Metric | Old Approach | HTMX Hybrid |
|--------|-------------|-------------|
| Lines of Code | 500+ lines | 30 lines |
| External Dependencies | Multiple | Alpine.js only |
| Debugging Complexity | High | Low |
| Maintenance Burden | High | Minimal |

## Integration with Other Systems

### XP System Integration
**Reading Completion XP:**
```python
def calculate_reading_xp(user, article_id, article_type):
    base_xp = 50  # Base reading completion XP
    
    # Speed bonus based on user's WPM
    if user.current_wmp > 300:
        speed_bonus = min((user.current_wpm - 300) / 10, 50)
        base_xp += speed_bonus
    
    # First-time reading bonus
    if not has_read_article_before(user, article_id, article_type):
        base_xp += 25
    
    return int(base_xp)
```

### Quiz System Integration
**Automatic Quiz Unlock:**
- Reading completion triggers quiz availability via HTMX
- User's reading speed passed to quiz for XP calculation
- Seamless transition from reading to quiz interface

### Analytics Integration
**Reading Session Tracking:**
```python
class SpeedReaderSession(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    article_id = models.IntegerField()
    article_type = models.CharField(max_length=20)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True)
    initial_wpm = models.IntegerField()
    final_wpm = models.IntegerField(null=True)
    completed = models.BooleanField(default=False)
```

## Mobile Responsiveness

### Responsive Design
- **Mobile-First**: Optimized for touch interactions
- **Adaptive Layout**: Scales appropriately on all screen sizes
- **Touch Controls**: Large, finger-friendly buttons
- **Performance**: Optimized for mobile network conditions

### Progressive Web App Features
- **Offline Support**: Cache articles for offline reading
- **Install Prompt**: Add to home screen functionality
- **Background Sync**: Sync reading progress when online

## Error Handling and Fallbacks

### Progressive Enhancement
```html
<!-- Fallback for no JavaScript -->
<noscript>
    <div class=\"fallback-reader\">
        <h3>Speed Reader Unavailable</h3>
        <p>JavaScript is required for the speed reader. You can still read the article normally:</p>
        <div class=\"article-content\">{{ article.content }}</div>
    </div>
</noscript>
```

### HTMX Error Handling
```javascript
// Global HTMX error handling
document.addEventListener('htmx:responseError', function(event) {
    console.error('Speed Reader Error:', event.detail);
    showUserFriendlyError('Unable to load speed reader. Please refresh and try again.');
});
```

## Testing Strategy

### Backend Testing
```python
class SpeedReaderServiceTest(TestCase):
    def test_content_chunking_with_power_ups(self):
        user = self.create_user_with_chunking_power_up()
        chunks = SpeedReaderService.get_chunked_words(\"test content\", user)
        self.assertEqual(len(chunks), expected_chunk_count)
    
    def test_font_settings_generation(self):
        user = self.create_user_with_font_customization()
        settings = SpeedReaderService.get_font_settings(user)
        self.assertEqual(settings['font_family'], user.preferred_font)
```

### Frontend Testing
```javascript
// Alpine.js component testing
describe('Speed Reader Component', () => {
    test('initializes with correct state', () => {
        const reader = speedReader(['hello', 'world'], {}, {}, 1, 'regular');
        expect(reader.currentChunk).toBe('Click Start to begin reading');
    });
    
    test('progresses through words correctly', () => {
        const reader = speedReader(['hello', 'world'], {}, {}, 1, 'regular');
        reader.startReading();
        // Test word progression
    });
});
```

## Future Enhancements

### Planned Features
- **Voice Reading Mode**: Text-to-speech integration
- **Reading Analytics**: Advanced progress tracking
- **Social Features**: Reading challenges and leaderboards
- **AI Optimization**: Personalized speed recommendations

### Performance Improvements
- **Content Caching**: Cache processed word chunks
- **CDN Integration**: Faster static file delivery
- **Service Worker**: Enhanced offline capabilities
- **Database Optimization**: Improved query performance

## Related Documentation
- [HTMX Hybrid Architecture Spec](../.kiro/specs/htmx-hybrid-architecture/)
- [XP System](xp-system.md)
- [Tag System](tag-system.md)
- [User Management](user-management.md)
- [API Specification](../api/specification.md)