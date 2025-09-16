# Article Detail Page - Complete Specification

*Last Updated: July 28, 2025*  
*Status: DEFINITIVE SPECIFICATION*  
*Version: 3.0 - HTMX Hybrid Architecture*

## CRITICAL: ARCHITECTURAL REQUIREMENTS

**This document establishes the definitive specification for the VeriFast Article Detail Page. All implementations MUST follow this specification.**

### Architecture Principles
- **HTMX Hybrid**: Server-side processing with minimal client-side JavaScript
- **Progressive Enhancement**: Works without JavaScript, enhanced with Alpine.js
- **Single Immersive Mode**: Full-screen speed reading as primary interface
- **Complete Feature Set**: All model fields and relationships displayed

## Required Page Sections

### 1. Article Header Section

**Required Elements:**
- Article title (prominent H1)
- Article image (if available) - left side, responsive
- Source display with proper formatting
- Publication date (if available)
- Reading level calculation and display
- Word count calculation and display
- Language indicator
- Article type indicator (Wikipedia vs Regular)

**Template Structure:**
```html
<header class="article-header">
    <div class="article-header-content">
        {% if article.image_url %}
        <div class="article-image">
            <img src="{{ article.image_url }}" alt="{{ article.title }}" loading="lazy">
        </div>
        {% endif %}
        
        <div class="article-meta">
            <h1>{{ article.get_display_title }}</h1>
            
            <div class="article-info">
                <p><strong>{% trans "Source" %}:</strong> {{ article.get_source_display }}</p>
                
                {% if article.publication_date %}
                <p><strong>{% trans "Published" %}:</strong> {{ article.publication_date|date:"F j, Y" }}</p>
                {% endif %}
                
                {% if article.reading_level %}
                <p><strong>{% trans "Reading Level" %}:</strong> {{ article.reading_level|floatformat:1 }}</p>
                {% endif %}
                
                {% if article.word_count %}
                <p><strong>{% trans "Word Count" %}:</strong> {{ article.word_count|floatformat:0 }}</p>
                {% endif %}
                
                <p><strong>{% trans "Language" %}:</strong> 
                    {% if article.language == 'en' %}{% trans "English" %}
                    {% elif article.language == 'es' %}{% trans "Spanish" %}
                    {% else %}{{ article.language|upper }}{% endif %}
                </p>
                
                {% if article.is_wikipedia_article %}
                <p><span class="wikipedia-badge">{% trans "Wikipedia Article" %}</span></p>
                {% endif %}
            </div>
        </div>
    </div>
</header>
```

### 2. Tags Section

**Required Elements:**
- Display all article tags as clickable links
- Tag count indicator
- Responsive tag layout
- Links to tag detail pages

**Template Structure:**
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

### 3. Speed Reader Section (HTMX Hybrid)

**Architecture Requirements:**
- HTMX endpoint for initialization: `/speed-reader/init/{article_id}/`
- Alpine.js component (max 30 lines)
- Server-side content processing with user power-ups
- Single immersive mode interface

**Template Structure:**
```html
<section class="speed-reader-section">
    <h3>{% trans "Speed Reader" %}</h3>
    <p>{% trans "Experience immersive speed reading with full-screen focus." %}</p>
    
    <div class="speed-reader-info">
        <p>
            {% trans "Current Speed" %}: <span id="current-wpm">{{ user_wpm|default:250 }}</span> {% trans "WPM" %}
            {% if user.is_authenticated %}
                | {% trans "Max Speed" %}: {{ user.max_wpm|default:250 }} {% trans "WPM" %}
            {% endif %}
        </p>
    </div>
    
    <div id="speed-reader-container">
        <button hx-get="{% url 'verifast_app:speed_reader_init' article.id %}"
                hx-target="#speed-reader-container"
                hx-swap="innerHTML"
                class="primary">
            {% trans "Start Reading" %}
        </button>
    </div>
</section>
```

**HTMX Endpoint Response:**
```html
<!-- speed_reader_active.html -->
<div x-data="speedReader({{ word_chunks|safe }}, {{ settings|safe }})" 
     class="speed-reader-active">
    
    <!-- Immersive Overlay -->
    <div x-show="isActive" 
         x-transition
         class="immersive-overlay">
        
        <!-- Full-width white strip -->
        <div class="immersive-word-display" x-text="currentChunk"></div>
        
        <!-- Controls -->
        <div class="immersive-controls">
            <button @click="toggleReading()" x-text="isRunning ? 'Pause' : 'Play'"></button>
            <button @click="exitReading()">{% trans "Exit" %}</button>
            <div class="speed-controls">
                <button @click="adjustSpeed(-25)">-</button>
                <span x-text="wpm + ' WPM'"></span>
                <button @click="adjustSpeed(25)">+</button>
            </div>
        </div>
    </div>
    
    <!-- Reading Complete Handler -->
    <div x-show="isComplete" 
         hx-post="{% url 'verifast_app:reading_complete' article.id %}"
         hx-target="#quiz-section"
         hx-trigger="load">
    </div>
</div>
```

### 4. Quiz Section (HTMX)

**Architecture Requirements:**
- HTMX endpoint for quiz loading: `/quiz/load/{article_id}/`
- Server-side quiz processing and XP calculation
- Progressive enhancement with minimal JavaScript

**Template Structure:**
```html
<section id="quiz-section" class="quiz-section">
    <h3>{% trans "Comprehension Quiz" %}</h3>
    {% if article.quiz_data %}
        <p>{% trans "Complete the speed reading above to unlock the quiz and earn XP!" %}</p>
        
        <div id="quiz-container">
            <button id="quiz-start-btn" 
                    hx-get="{% url 'verifast_app:quiz_load' article.id %}"
                    hx-target="#quiz-container"
                    hx-swap="innerHTML"
                    class="primary"
                    disabled>
                {% trans "Start Quiz" %} ({% trans "Complete reading first" %})
            </button>
        </div>
    {% else %}
        <p>{% trans "Quiz is being generated for this article. Please check back later." %}</p>
    {% endif %}
</section>
```

### 5. Comments Section

**Required Elements:**
- Comment count display
- Add comment form (XP cost validation)
- Threaded comment display
- Bronze/Silver/Gold interaction buttons
- XP cost indicators

**Template Structure:**
```html
<section class="comments-section">
    <h3>{% trans "Comments" %} ({{ article.comments.count }})</h3>
    
    {% if user.is_authenticated %}
        <!-- Add Comment Form -->
        <div class="add-comment-form">
            {% if user_can_comment %}
                <form hx-post="{% url 'verifast_app:add_comment' article.id %}"
                      hx-target="#comments-list"
                      hx-swap="afterbegin">
                    {% csrf_token %}
                    <textarea name="content" 
                              placeholder="{% trans 'Share your thoughts...' %}"
                              required></textarea>
                    <div class="comment-form-footer">
                        <span class="xp-cost">{% trans "Cost" %}: 10 XP</span>
                        <button type="submit" class="primary">
                            {% trans "Add Comment" %}
                        </button>
                    </div>
                </form>
            {% else %}
                <p class="comment-locked">
                    {% trans "Complete the quiz to unlock commenting!" %}
                </p>
            {% endif %}
        </div>
    {% endif %}
    
    <!-- Comments List -->
    <div id="comments-list" class="comments-list">
        {% for comment in article.comments.all %}
            {% include 'verifast_app/partials/comment.html' with comment=comment %}
        {% empty %}
            <p class="no-comments">{% trans "No comments yet. Be the first to share your thoughts!" %}</p>
        {% endfor %}
    </div>
</section>
```

### 6. Related Articles Section

**Required Elements:**
- Articles with shared tags
- Responsive grid layout
- Article preview cards

**Template Structure:**
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
                            {{ related.get_source_display }} • 
                            {% if related.word_count %}{{ related.word_count }} words{% endif %}
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

## Backend Requirements

### 1. View Updates Required

**ArticleDetailView Enhancements:**
```python
class ArticleDetailView(DetailView):
    model = Article
    template_name = 'verifast_app/article_detail.html'
    context_object_name = 'article'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object
        user = self.request.user
        
        # Calculate missing fields
        if not article.word_count:
            article.word_count = self.calculate_word_count(article.content)
            article.save(update_fields=['word_count'])
        
        if not article.reading_level:
            article.reading_level = self.calculate_reading_level(article.content)
            article.save(update_fields=['reading_level'])
        
        # User-specific data
        context.update({
            'user_wpm': user.current_wpm if user.is_authenticated else 250,
            'user_can_comment': self.user_can_comment(user, article),
            'related_articles': self.get_related_articles(article),
            'quiz_completed': self.user_completed_quiz(user, article),
        })
        
        return context
    
    def calculate_word_count(self, content):
        """Calculate word count from article content."""
        import re
        words = re.findall(r'\b\w+\b', content)
        return len(words)
    
    def calculate_reading_level(self, content):
        """Calculate reading level using Flesch-Kincaid formula."""
        # Implementation here
        pass
    
    def get_related_articles(self, article):
        """Get articles with shared tags."""
        if not article.tags.exists():
            return Article.objects.none()
        
        return Article.objects.filter(
            tags__in=article.tags.all(),
            processing_status='complete'
        ).exclude(
            id=article.id
        ).distinct()[:6]
    
    def user_can_comment(self, user, article):
        """Check if user can comment (completed quiz)."""
        if not user.is_authenticated:
            return False
        
        return QuizAttempt.objects.filter(
            user=user,
            article=article,
            score__gte=70  # Passing score
        ).exists()
    
    def user_completed_quiz(self, user, article):
        """Check if user completed quiz."""
        if not user.is_authenticated:
            return False
        
        return QuizAttempt.objects.filter(
            user=user,
            article=article
        ).exists()
```

### 2. HTMX Endpoints Required

**Speed Reader Endpoints:**
```python
def speed_reader_init(request, article_id):
    """Initialize speed reader with HTMX."""
    article = get_object_or_404(Article, id=article_id)
    user = request.user if request.user.is_authenticated else None
    
    # Server-side content processing
    word_chunks = process_content_with_powerups(article.content, user)
    settings = get_user_reading_settings(user)
    
    return render(request, 'verifast_app/partials/speed_reader_active.html', {
        'word_chunks': json.dumps(word_chunks),
        'settings': json.dumps(settings),
        'article': article,
    })

def reading_complete(request, article_id):
    """Handle reading completion via HTMX."""
    if request.method == 'POST':
        article = get_object_or_404(Article, id=article_id)
        user = request.user
        
        if user.is_authenticated:
            # Award reading XP
            xp_awarded = calculate_reading_xp(user, article)
            user.total_xp += xp_awarded
            user.current_xp_points += xp_awarded
            user.save()
        
        return render(request, 'verifast_app/partials/quiz_unlocked.html', {
            'article': article,
            'xp_awarded': xp_awarded if user.is_authenticated else 0,
        })
```

**Quiz Endpoints:**
```python
def quiz_load(request, article_id):
    """Load quiz interface via HTMX."""
    article = get_object_or_404(Article, id=article_id)
    
    return render(request, 'verifast_app/partials/quiz_interface.html', {
        'article': article,
        'quiz_data': article.quiz_data,
    })

def quiz_submit(request, article_id):
    """Process quiz submission via HTMX."""
    if request.method == 'POST':
        # Process quiz submission
        # Award XP
        # Return results
        pass
```

## CSS Requirements

### 1. Article Header Styles
```css
.article-header {
    margin-bottom: 2rem;
    padding: 2rem;
    background: var(--card-background-color);
    border-radius: var(--border-radius);
    border: 1px solid var(--muted-border-color);
}

.article-header-content {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 2rem;
    align-items: start;
}

.article-image img {
    max-width: 300px;
    height: auto;
    border-radius: var(--border-radius);
}

.article-meta h1 {
    margin-bottom: 1rem;
    color: var(--color);
}

.article-info p {
    margin-bottom: 0.5rem;
    color: var(--muted-color);
}

.wikipedia-badge {
    background: #0066cc;
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.875rem;
}

@media (max-width: 768px) {
    .article-header-content {
        grid-template-columns: 1fr;
    }
    
    .article-image {
        text-align: center;
    }
}
```

### 2. Immersive Mode Styles (Full-Width White Strip)
```css
.immersive-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.9);
    z-index: 9999;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.immersive-word-display {
    width: 100vw;
    height: 200px;
    background: #ffffff;
    color: #000000;
    font-size: 4rem;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 3px solid #333333;
    box-sizing: border-box;
    padding: 2rem;
    text-align: center;
    word-wrap: break-word;
}

.immersive-controls {
    margin-top: 2rem;
    display: flex;
    gap: 1rem;
    align-items: center;
}
```

## Testing Requirements

### 1. Feature Testing Checklist
- [ ] Article image displays correctly (when available)
- [ ] All metadata fields display properly
- [ ] Tags are clickable and link to tag pages
- [ ] Word count calculation works
- [ ] Reading level calculation works
- [ ] Speed reader launches immersive mode
- [ ] Quiz unlocks after reading completion
- [ ] Comments section displays and functions
- [ ] Related articles show correctly
- [ ] Mobile responsiveness works

### 2. HTMX Integration Testing
- [ ] Speed reader initialization via HTMX
- [ ] Reading completion triggers quiz unlock
- [ ] Quiz loading via HTMX
- [ ] Comment submission via HTMX
- [ ] All HTMX endpoints return proper responses

## Migration Requirements

### 1. Data Migration for Missing Fields
```python
# Create migration to calculate missing word_count and reading_level
def calculate_missing_fields(apps, schema_editor):
    Article = apps.get_model('verifast_app', 'Article')
    
    for article in Article.objects.filter(word_count__isnull=True):
        # Calculate word count
        words = len(article.content.split())
        article.word_count = words
        article.save(update_fields=['word_count'])
    
    # Calculate reading levels
    # Implementation here
```

This specification provides the complete blueprint for implementing a fully-featured article detail page that follows the HTMX hybrid architecture and includes all required functionality.