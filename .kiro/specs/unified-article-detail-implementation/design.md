# Design Document - Unified Article Detail Implementation

## Overview

This design implements the existing working specifications from `documentation/architecture/speed-reader-single-mode-spec.md` and `documentation/architecture/article-detail-complete-spec.md` as the definitive reference. The implementation follows the established HTMX hybrid architecture while ensuring the single immersive mode speed reader integrates seamlessly with the complete article detail page functionality.

## Architecture

### HTMX Hybrid Architecture Principles

The unified implementation follows these core architectural principles:

1. **Server-Side Dominance**: All business logic, content processing, and data calculations occur on the Django backend
2. **Minimal JavaScript**: Alpine.js components limited to UI state management (≤30 lines each)
3. **Progressive Enhancement**: Full functionality without JavaScript, enhanced experience with it
4. **HTMX Integration**: Dynamic interactions handled via HTMX endpoints with proper fallbacks

### Single Immersive Mode Design

The speed reader implements a single-mode approach:

- **No Dual Interface**: Only immersive full-screen mode available
- **Direct Launch**: Single "Start Reading" button launches immersive mode immediately
- **Full-Width Display**: Text strip spans entire viewport width (100vw) with white background
- **Integrated Flow**: Reading completion automatically unlocks quiz functionality

## Components and Interfaces

### 1. Article Header Component

**Purpose**: Display comprehensive article metadata and information

**Template Structure**:
```html
<header class="article-header">
    <div class="article-header-content">
        <!-- Article image (responsive, left-aligned) -->
        {% if article.image_url %}
        <div class="article-image">
            <img src="{{ article.image_url }}" alt="{{ article.title }}" loading="lazy">
        </div>
        {% endif %}
        
        <!-- Article metadata -->
        <div class="article-meta">
            <h1>{{ article.get_display_title|default:article.title }}</h1>
            <div class="article-info">
                <p><strong>{% trans "Source" %}:</strong> {{ article.get_source_display|default:article.source }}</p>
                {% if article.publication_date %}
                <p><strong>{% trans "Published" %}:</strong> {{ article.publication_date|date:"F j, Y" }}</p>
                {% endif %}
                {% if article.reading_level %}
                <p><strong>{% trans "Reading Level" %}:</strong> {{ article.reading_level|floatformat:1 }}</p>
                {% endif %}
                {% if article.word_count %}
                <p><strong>{% trans "Word Count" %}:</strong> {{ article.word_count|floatformat:0 }}</p>
                {% endif %}
                <p><strong>{% trans "Language" %}:</strong> {% language_badge article.language 'large' %}</p>
                {% if article.is_wikipedia_article %}
                <p><span class="wikipedia-badge">{% trans "Wikipedia Article" %}</span></p>
                {% endif %}
            </div>
        </div>
    </div>
</header>
```

**Backend Processing**:
- Automatic word count calculation if missing
- Automatic reading level calculation using Flesch-Kincaid formula
- Database field updates with calculated values

### 2. Tags Display Component

**Purpose**: Show article tags as navigable links

**Template Structure**:
```html
<section class="article-tags">
    <h3>{% trans "Tags" %}</h3>
    {% if article.tags.exists %}
    <div class="tag-list">
        {% for tag in article.tags.all %}
        <a href="{{ tag.get_absolute_url }}" class="tag-link">{{ tag.name }}</a>
        {% endfor %}
    </div>
    {% else %}
    <p class="no-tags">{% trans "No tags available for this article." %}</p>
    {% endif %}
</section>
```

### 3. Unified Speed Reader Component

**Purpose**: Provide immersive speed reading with HTMX integration

**HTMX Integration**:
```html
<section id="speed-reader-section" 
         class="speed-reader-section"
         data-article-id="{{ article.id }}"
         {% if user.is_authenticated %}
         data-user-wpm="{{ user.current_wpm|default:250 }}"
         {% else %}
         data-user-wpm="250"
         {% endif %}
         data-word-count="{{ article.word_count|default:0 }}">
    
    <h3>{% trans "Speed Reader" %}</h3>
    <p>{% trans "Experience immersive speed reading with full-screen focus." %}</p>
    
    <div class="speed-reader-info">
        {% if user.is_authenticated %}
        <p>{% trans "Reading Speed" %}: {{ user.current_wpm|default:250 }} WPM</p>
        {% else %}
        <p>{% trans "Reading Speed" %}: 250 WPM</p>
        {% endif %}
        <p>{% trans "Words" %}: {{ article.word_count|default:0 }}</p>
    </div>
    
    <div class="reader-controls">
        <button hx-get="{% url 'verifast_app:speed_reader_init' article.id %}" 
                hx-target="#speed-reader-section"
                hx-swap="outerHTML" 
                class="primary-btn" 
                type="button">
            {% trans "Start Reading" %}
        </button>
    </div>
</section>
```

**Immersive Mode Interface** (returned by HTMX endpoint):
```html
{% load i18n %}

<div x-data="speedReader({{ word_chunks_json|safe }}, { wpm: {{ user_wpm|default:250 }} }, '{{ article_id }}', '{{ article_type }}')" 
     class="speed-reader-active">
    
    <!-- Full-screen immersive overlay -->
    <div x-show="isActive" 
         x-transition
         class="immersive-overlay">
        
        <!-- Full-width white text strip -->
        <div class="immersive-word-display" x-text="currentChunk">
            Ready to read
        </div>
        
        <!-- Reading controls -->
        <div class="immersive-controls">
            <button @click="toggleReading()" 
                    class="immersive-control-btn"
                    x-text="isRunning ? 'Pause' : 'Play'">
                Play
            </button>
            
            <div class="speed-controls">
                <button @click="adjustSpeed(-25)" class="speed-btn">-</button>
                <span class="speed-display" x-text="wpm + ' WPM'">250 WPM</span>
                <button @click="adjustSpeed(25)" class="speed-btn">+</button>
            </div>
            
            <button @click="exitReading()" class="immersive-exit-btn">
                {% trans "Exit Reading" %}
            </button>
        </div>
    </div>
    
    <!-- Reading completion handler -->
    <div x-show="isComplete" 
         hx-post="{% url 'verifast_app:speed_reader_complete' article_id %}"
         hx-target="#quiz-section"
         hx-trigger="load"
         hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
    </div>
</div>
```

### 4. Quiz Integration Component

**Purpose**: Provide comprehension testing with XP rewards

**Template Structure**:
```html
<section id="quiz-section" class="quiz-section">
    <h3>{% trans "Comprehension Quiz" %}</h3>
    {% if article.quiz_data %}
    <p>{% trans "Complete the speed reading above to unlock the quiz and earn XP!" %}</p>
    
    <div id="quiz-container">
        <button hx-get="{% url 'verifast_app:quiz_start' article.id %}" 
                hx-target="#quiz-container"
                hx-swap="outerHTML" 
                type="button" 
                class="primary" 
                disabled>
            {% trans "Start Quiz" %} ({% trans "Complete reading first" %})
        </button>
    </div>
    {% else %}
    <section class="quiz-section">
        <h3>{% trans "Comprehension Quiz" %}</h3>
        <p>{% trans "Quiz is being generated for this article. Please check back later." %}</p>
    </section>
    {% endif %}
</section>
```

### 5. Social Comments Component

**Purpose**: Enable user discussions with XP-based interactions

**Template Structure**:
```html
<section class="comments-section">
    <h3>{% trans "Comments" %} ({{ comments.count }})</h3>
    
    <!-- Comment form (conditional based on quiz completion) -->
    <div class="add-comment-form">
        {% if user.is_authenticated and user_can_comment %}
        <form hx-post="{% url 'verifast_app:add_comment' article.id %}" 
              hx-target="#comments-list"
              hx-swap="outerHTML" 
              hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
            {% csrf_token %}
            <textarea name="content" placeholder="{% trans 'Share your thoughts...' %}" required></textarea>
            <div class="comment-form-footer">
                <span class="xp-cost">{% trans "Cost" %}: 10 XP</span>
                <button type="submit" class="primary">{% trans "Add Comment" %}</button>
            </div>
        </form>
        {% elif user.is_authenticated and not user_can_comment %}
        <p class="comment-locked">
            {% trans "Complete the quiz with a passing score to unlock commenting!" %}
        </p>
        {% elif not user.is_authenticated %}
        <div id="anonymous-comment-section">
            <p class="comment-locked">
                {% trans "Complete the quiz with a passing score to unlock commenting!" %}
            </p>
        </div>
        {% endif %}
    </div>
    
    <!-- Comments list -->
    {% include 'verifast_app/partials/comments_list.html' %}
</section>
```

### 6. Related Articles Component

**Purpose**: Show related content based on shared tags

**Template Structure**:
```html
<section class="related-articles">
    <h3>{% trans "Related Articles" %}</h3>
    {% if related_articles %}
    <div class="related-articles-grid">
        {% for related in related_articles %}
        <article class="related-article-card">
            <a href="{{ related.get_absolute_url }}">
                {% if related.image_url %}
                <img src="{{ related.image_url }}" alt="{{ related.title }}" loading="lazy">
                {% endif %}
                <h4>{{ related.title }}</h4>
                <p class="article-meta">
                    {{ related.get_source_display|default:related.source }}
                    {% if related.word_count %} • {{ related.word_count }} words{% endif %}
                </p>
            </a>
        </article>
        {% endfor %}
    </div>
    {% else %}
    <p>{% trans "No related articles found." %}</p>
    {% endif %}
</section>
```

## Data Models

### Enhanced ArticleDetailView Context

The view provides comprehensive context data:

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    article = self.object
    user = self.request.user
    
    # Auto-calculate missing fields
    if not article.word_count:
        article.word_count = self.calculate_word_count(article.content)
        article.save(update_fields=['word_count'])
    
    if not article.reading_level:
        article.reading_level = self.calculate_reading_level(article.content)
        article.save(update_fields=['reading_level'])
    
    # User-specific context
    context.update({
        'user_wmp': user.current_wpm if user.is_authenticated else 250,
        'user_can_comment': self.user_can_comment(user, article),
        'related_articles': self.get_related_articles(article),
        'quiz_completed': self.user_completed_quiz(user, article),
        'comments': self.get_comments(article),
    })
    
    return context
```

### HTMX Endpoint Data Processing

**Speed Reader Initialization**:
```python
def speed_reader_init(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    user = request.user if request.user.is_authenticated else None
    
    # Server-side content processing with user power-ups
    word_chunks = process_content_with_powerups(article.content, user)
    settings = get_user_reading_settings(user)
    
    return render(request, 'verifast_app/partials/speed_reader_active.html', {
        'word_chunks_json': json.dumps(word_chunks),
        'user_wpm': settings.get('wpm', 250),
        'article_id': article.id,
        'article_type': 'wikipedia' if article.is_wikipedia_article else 'regular',
    })
```

## Error Handling

### Graceful Degradation Strategy

1. **JavaScript Disabled**: Provide static content display with basic functionality
2. **HTMX Failures**: Show fallback buttons with page refresh functionality
3. **Content Loading Errors**: Display retry mechanisms with error messages
4. **Anonymous User Handling**: Provide appropriate defaults without authentication errors

### Error Recovery Mechanisms

```html
<!-- Fallback for JavaScript disabled -->
<noscript>
    <div class="speed-reader-fallback">
        <p>{% trans "Speed reading requires JavaScript. You can read the article normally below:" %}</p>
        <div class="article-content">{{ article.content|safe }}</div>
    </div>
</noscript>

<!-- HTMX error handling -->
<div hx-on:htmx:error="this.innerHTML='<p>Error loading content. <button onclick=location.reload()>Retry</button></p>'">
    <!-- HTMX content -->
</div>
```

## Testing Strategy

### Component Testing
- Individual component functionality (header, tags, speed reader, quiz, comments)
- HTMX endpoint responses and error handling
- Alpine.js component state management

### Integration Testing
- Complete user flow from article view to quiz completion
- Cross-component interactions (speed reader → quiz unlock → comments)
- Authentication state handling across all components

### Performance Testing
- Immersive mode activation time (target: <100ms)
- Word display update frequency (target: 60fps)
- Memory usage during extended reading sessions

### Accessibility Testing
- Screen reader compatibility with ARIA labels
- Keyboard navigation functionality
- High contrast mode support
- Mobile touch interface usability

This unified design provides a comprehensive, production-ready article detail page that combines the best aspects of both specifications while maintaining architectural consistency and user experience excellence.