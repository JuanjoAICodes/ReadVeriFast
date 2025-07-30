# HTMX Hybrid Architecture Debugging Guide

*Last Updated: July 27, 2025*  
*Status: HTMX Hybrid Architecture*

## Overview

This guide provides comprehensive debugging strategies for the HTMX hybrid architecture implementation in VeriFast. The new architecture emphasizes server-side processing with minimal client-side JavaScript, requiring different debugging approaches than traditional JavaScript-heavy applications.

## Architecture-Specific Debugging

### 1. Server-Side Processing Issues

**Issue**: Content processing or power-up application not working correctly.

**Root Causes**:
- User power-up data not being retrieved correctly
- Content chunking logic errors
- Font settings generation problems
- Database query issues

**Debugging Steps**:
```python
# Add logging to service methods
import logging
logger = logging.getLogger(__name__)

class SpeedReaderService:
    @staticmethod
    def prepare_content(article, user):
        logger.info(f"Processing content for article {article.id}, user {user.id if user else 'anonymous'}")
        
        # Debug user power-ups
        if user:
            logger.info(f"User power-ups: chunking={user.has_2word_chunking}, smart_grouping={user.has_smart_connector_grouping}")
        
        # Debug content processing
        word_chunks = SpeedReaderService.get_chunked_words(article.content, user)
        logger.info(f"Generated {len(word_chunks)} word chunks")
        
        return {
            'word_chunks': word_chunks,
            # ... other data
        }
```

**Solution Checklist**:
- [ ] Verify user authentication and power-up data
- [ ] Check article content exists and is properly formatted
- [ ] Validate chunking logic with test data
- [ ] Ensure font settings are properly generated
- [ ] Test with different user power-up combinations

### 2. HTMX Request/Response Issues

**Issue**: HTMX requests not working or returning unexpected responses.

**Root Causes**:
- Incorrect HTMX attributes or selectors
- CSRF token issues
- Server-side view errors
- Template rendering problems

**Debugging Steps**:
```html
<!-- Add HTMX debugging attributes -->
<div hx-get="/speed-reader/init/123/regular/" 
     hx-target="#speed-reader-container"
     hx-swap="innerHTML"
     hx-indicator="#loading"
     hx-on::before-request="console.log('HTMX request starting')"
     hx-on::after-request="console.log('HTMX request completed')"
     hx-on::response-error="console.error('HTMX error:', event.detail)">
    Start Speed Reader
</div>
```

**Server-Side Debugging**:
```python
# Add comprehensive logging to HTMX views
def speed_reader_init(request, article_id, article_type='regular'):
    logger.info(f"Speed reader init: article_id={article_id}, type={article_type}, user={request.user}")
    
    try:
        if article_type == 'wikipedia':
            article = get_object_or_404(WikipediaArticle, id=article_id)
        else:
            article = get_object_or_404(Article, id=article_id)
        
        logger.info(f"Article found: {article.title}")
        
        user = request.user if request.user.is_authenticated else None
        content_data = SpeedReaderService.prepare_content(article, user)
        
        logger.info(f"Content prepared: {len(content_data['word_chunks'])} chunks")
        
        return render(request, 'partials/speed_reader_active.html', {
            'word_chunks_json': json.dumps(content_data['word_chunks']),
            'font_settings': content_data['font_settings'],
            'reading_settings': content_data['reading_settings'],
            'article_id': article_id,
            'article_type': article_type,
            'total_words': content_data['total_words']
        })
        
    except Exception as e:
        logger.error(f"Speed reader init error: {e}", exc_info=True)
        return render(request, 'partials/error.html', {
            'error_message': 'Unable to initialize speed reader'
        }, status=500)
```

**Solution Checklist**:
- [ ] Verify HTMX attributes are correct
- [ ] Check CSRF tokens are included
- [ ] Validate URL patterns and view names
- [ ] Test server-side view logic independently
- [ ] Check template rendering with test data

### 3. Alpine.js Component Issues

**Issue**: Alpine.js speed reader component not initializing or functioning correctly.

**Root Causes**:
- Alpine.js not loaded or initialized
- Component data format issues
- JavaScript errors in component logic
- DOM element selection problems

**Debugging Steps**:
```javascript
// Add comprehensive logging to Alpine.js component
function speedReader(wordChunks, fontSettings, readingSettings, articleId, articleType) {
    console.log('Speed Reader initializing:', {
        wordChunks: wordChunks?.length || 0,
        fontSettings,
        readingSettings,
        articleId,
        articleType
    });
    
    return {
        // State
        chunks: wordChunks || [],
        currentIndex: 0,
        currentChunk: 'Click Start to begin reading',
        isRunning: false,
        currentWpm: readingSettings?.default_wpm || 250,
        interval: null,
        error: null,
        
        // Initialization
        init() {
            console.log('Speed Reader component initialized');
            
            // Validate data
            if (!Array.isArray(this.chunks) || this.chunks.length === 0) {
                this.error = 'No content available';
                console.error('Speed Reader: Invalid or empty word chunks');
                return;
            }
            
            console.log(`Speed Reader: Ready with ${this.chunks.length} chunks`);
        },
        
        // Methods with error handling
        toggleReading() {
            try {
                this.isRunning ? this.pauseReading() : this.startReading();
            } catch (error) {
                console.error('Speed Reader toggle error:', error);
                this.error = 'Unable to control reading';
            }
        },
        
        startReading() {
            console.log(`Starting reading at ${this.currentWpm} WPM`);
            
            if (this.currentIndex >= this.chunks.length) {
                this.resetReading();
            }
            
            this.isRunning = true;
            const intervalMs = 60000 / this.currentWpm;
            
            this.interval = setInterval(() => {
                try {
                    this.showNextWord();
                } catch (error) {
                    console.error('Speed Reader word display error:', error);
                    this.pauseReading();
                    this.error = 'Reading error occurred';
                }
            }, intervalMs);
        },
        
        completeReading() {
            console.log('Reading completed, notifying server');
            this.pauseReading();
            this.currentChunk = 'Reading Complete! 🎉';
            
            // Notify server via HTMX with error handling
            try {
                htmx.ajax('POST', `/reading-complete/${articleId}/${articleType}/`, {
                    target: '#quiz-section',
                    swap: 'innerHTML'
                });
            } catch (error) {
                console.error('HTMX completion notification error:', error);
                this.error = 'Unable to unlock quiz';
            }
        }
    }
}
```

**Solution Checklist**:
- [ ] Verify Alpine.js is loaded before component initialization
- [ ] Check data format matches component expectations
- [ ] Validate DOM elements exist when component initializes
- [ ] Test component methods individually
- [ ] Check browser console for JavaScript errors

### 4. Template Rendering Issues

**Issue**: Templates not rendering correctly or missing data.

**Root Causes**:
- Template syntax errors
- Missing context variables
- Template inheritance problems
- Static file loading issues

**Debugging Steps**:
```html
<!-- Add debug information to templates -->
<div class="debug-info" style="display: none;">
    <h4>Debug Information</h4>
    <p>Article ID: {{ article.id }}</p>
    <p>Article Type: {{ article_type }}</p>
    <p>User Authenticated: {{ user.is_authenticated }}</p>
    <p>Word Chunks Count: {{ word_chunks_json|length }}</p>
    <p>Font Settings: {{ font_settings }}</p>
    <p>Reading Settings: {{ reading_settings }}</p>
</div>

<!-- Add error boundaries -->
{% if word_chunks_json %}
    <div id="speed-reader-active" 
         x-data="speedReader({{ word_chunks_json|safe }}, {{ font_settings|safe }}, {{ reading_settings|safe }}, '{{ article_id }}', '{{ article_type }}')">
        <!-- Component content -->
    </div>
{% else %}
    <div class="error-message">
        <h3>Speed Reader Unavailable</h3>
        <p>Unable to load article content. Please try refreshing the page.</p>
    </div>
{% endif %}
```

**Solution Checklist**:
- [ ] Verify all template variables are passed from view
- [ ] Check template syntax is valid
- [ ] Test template rendering with minimal data
- [ ] Validate static file references
- [ ] Check template inheritance chain

## Common Issues and Solutions

### 1. "Speed Reader Not Loading"

**Symptoms**:
- Speed reader section appears but doesn't initialize
- No word chunks displayed
- Alpine.js component not responding

**Debugging Process**:
1. Check browser console for JavaScript errors
2. Verify HTMX request completed successfully
3. Check server logs for view processing errors
4. Validate article content exists and is processed

**Solution**:
```python
# Ensure robust content processing
def speed_reader_init(request, article_id, article_type='regular'):
    try:
        # Get article with error handling
        if article_type == 'wikipedia':
            article = get_object_or_404(WikipediaArticle, id=article_id)
        else:
            article = get_object_or_404(Article, id=article_id)
        
        # Validate article has content
        if not article.content or not article.content.strip():
            return render(request, 'partials/no_content_error.html', {
                'article_title': article.title
            })
        
        # Process content with fallbacks
        user = request.user if request.user.is_authenticated else None
        content_data = SpeedReaderService.prepare_content(article, user)
        
        # Validate processed data
        if not content_data['word_chunks']:
            return render(request, 'partials/processing_error.html')
        
        return render(request, 'partials/speed_reader_active.html', {
            'word_chunks_json': json.dumps(content_data['word_chunks']),
            'font_settings': content_data['font_settings'],
            'reading_settings': content_data['reading_settings'],
            'article_id': article_id,
            'article_type': article_type,
            'total_words': content_data['total_words']
        })
        
    except Exception as e:
        logger.error(f"Speed reader initialization failed: {e}", exc_info=True)
        return render(request, 'partials/speed_reader_error.html', {
            'error_message': 'Unable to initialize speed reader'
        }, status=500)
```

### 2. "HTMX Requests Failing"

**Symptoms**:
- HTMX requests return 404 or 500 errors
- No response or incorrect response format
- CSRF token errors

**Debugging Process**:
1. Check URL patterns match HTMX requests
2. Verify CSRF tokens are included
3. Check server logs for view errors
4. Test URLs directly in browser

**Solution**:
```python
# Ensure proper URL patterns
urlpatterns = [
    # Speed reader endpoints
    path('speed-reader/init/<int:article_id>/<str:article_type>/', 
         views.speed_reader_init, name='speed_reader_init'),
    path('reading-complete/<int:article_id>/<str:article_type>/', 
         views.speed_reader_complete, name='reading_complete'),
    
    # Quiz endpoints
    path('quiz/init/<int:article_id>/<str:article_type>/', 
         views.quiz_init, name='quiz_init'),
    path('quiz/submit/<int:article_id>/<str:article_type>/', 
         views.quiz_submit, name='quiz_submit'),
]
```

```html
<!-- Ensure CSRF tokens in HTMX requests -->
<div hx-post="/reading-complete/{{ article.id }}/{{ article_type }}/"
     hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
    <!-- Content -->
</div>
```

### 3. "Power-ups Not Applied"

**Symptoms**:
- Word chunking not working as expected
- Font customization not applied
- User features not reflected in interface

**Debugging Process**:
1. Check user power-up data in database
2. Verify power-up application logic
3. Test with different user configurations
4. Check font settings generation

**Solution**:
```python
# Debug power-up application
def get_chunked_words(content, user):
    logger.info(f"Chunking content for user: {user.id if user else 'anonymous'}")
    
    words = content.split()
    logger.info(f"Initial word count: {len(words)}")
    
    # Apply smart grouping with debugging
    if user and user.has_smart_connector_grouping:
        logger.info("Applying smart connector grouping")
        words = apply_smart_connector_grouping(words)
        logger.info(f"After smart grouping: {len(words)} words")
    
    # Apply chunking with debugging
    chunk_size = get_user_chunk_size(user)
    logger.info(f"Using chunk size: {chunk_size}")
    
    chunks = create_word_chunks(words, chunk_size)
    logger.info(f"Generated {len(chunks)} chunks")
    
    return chunks
```

## Performance Debugging

### 1. Slow Server Response Times

**Debugging Steps**:
```python
# Add timing to views
import time

def speed_reader_init(request, article_id, article_type='regular'):
    start_time = time.time()
    
    try:
        # View logic here
        result = render(request, template, context)
        
        duration = time.time() - start_time
        logger.info(f"Speed reader init took {duration:.2f}s")
        
        return result
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Speed reader init failed after {duration:.2f}s: {e}")
        raise
```

### 2. Database Query Optimization

**Debugging Steps**:
```python
# Use Django debug toolbar or logging
from django.db import connection

def speed_reader_init(request, article_id, article_type='regular'):
    initial_queries = len(connection.queries)
    
    # View logic here
    
    final_queries = len(connection.queries)
    query_count = final_queries - initial_queries
    
    if query_count > 5:  # Threshold for concern
        logger.warning(f"Speed reader init used {query_count} database queries")
        for query in connection.queries[initial_queries:]:
            logger.debug(f"Query: {query['sql']}")
```

## Testing and Validation

### 1. Component Testing

```javascript
// Test Alpine.js components in browser console
// After page loads, test component functionality
const testSpeedReader = () => {
    const component = Alpine.$data(document.getElementById('speed-reader-active'));
    
    console.log('Component state:', {
        chunks: component.chunks.length,
        currentIndex: component.currentIndex,
        isRunning: component.isRunning
    });
    
    // Test methods
    component.startReading();
    setTimeout(() => {
        console.log('After start:', component.currentChunk);
        component.pauseReading();
    }, 1000);
};
```

### 2. HTMX Testing

```html
<!-- Add test buttons for debugging -->
<div class="debug-controls" style="display: none;">
    <button hx-get="/speed-reader/init/{{ article.id }}/{{ article_type }}/"
            hx-target="#debug-output">
        Test Speed Reader Init
    </button>
    <div id="debug-output"></div>
</div>
```

## Prevention Strategies

### 1. Robust Error Handling

```python
# Implement comprehensive error handling
class SpeedReaderError(Exception):
    pass

def safe_speed_reader_init(request, article_id, article_type='regular'):
    try:
        return speed_reader_init(request, article_id, article_type)
    except Article.DoesNotExist:
        return render(request, 'partials/article_not_found.html', status=404)
    except SpeedReaderError as e:
        return render(request, 'partials/speed_reader_error.html', {
            'error_message': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected speed reader error: {e}", exc_info=True)
        return render(request, 'partials/generic_error.html', status=500)
```

### 2. Progressive Enhancement

```html
<!-- Ensure fallbacks for all interactive elements -->
<noscript>
    <div class="fallback-message">
        <h3>Enhanced Features Unavailable</h3>
        <p>JavaScript is required for the speed reader. You can still read the article content below.</p>
    </div>
</noscript>

<div class="speed-reader-fallback" style="display: none;">
    <h3>Speed Reader Unavailable</h3>
    <p>The speed reader is temporarily unavailable. Please try refreshing the page.</p>
    <div class="article-content">{{ article.content }}</div>
</div>
```

### 3. Monitoring and Alerting

```python
# Add monitoring for critical paths
import logging
from django.core.mail import mail_admins

def monitor_speed_reader_errors():
    error_count = SpeedReaderSession.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=1),
        error_occurred=True
    ).count()
    
    if error_count > 10:  # Threshold
        mail_admins(
            'High Speed Reader Error Rate',
            f'Speed reader errors: {error_count} in the last hour'
        )
```

This debugging guide provides comprehensive strategies for troubleshooting the HTMX hybrid architecture, focusing on server-side processing, minimal client-side debugging, and robust error handling patterns.