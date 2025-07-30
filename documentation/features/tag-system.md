# Tag System Documentation

*Last Updated: July 21, 2025*
*Status: Current*

## Overview

The VeriFast Tag System provides Wikipedia-validated content tagging that enables users to discover articles by topic and ensures content quality through external validation.

## Core Components

### 1. Tag Model
**Location:** `verifast_app/models.py`

**Key Features:**
- **Wikipedia Integration** - Tags validated against Wikipedia API
- **URL-Friendly Slugs** - Auto-generated for clean URLs
- **Article Counting** - Automatic article count tracking
- **Validation Status** - Boolean flag for Wikipedia validation

**Model Fields:**
```python
class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_validated = models.BooleanField(default=False)
    wikipedia_url = models.URLField(blank=True, null=True)
    wikipedia_content = models.TextField(blank=True)
    article_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
```

### 2. Wikipedia Integration Service
**Location:** `verifast_app/wikipedia_service.py`

**Features:**
- **Tag Validation** - Verifies tags against Wikipedia
- **Content Extraction** - Retrieves Wikipedia article content
- **Disambiguation Handling** - Manages ambiguous tag names
- **Error Recovery** - Handles API failures gracefully

**Key Methods:**
```python
class WikipediaService:
    def validate_tag_with_wikipedia(self, tag_name):
        """Validate a tag against Wikipedia API"""
        
    def update_tag_with_wikipedia(self, tag):
        """Update tag with Wikipedia data"""
        
    def create_wikipedia_article_for_tag(self, tag):
        """Create article from Wikipedia content"""
```

### 3. Tag Analytics
**Location:** `verifast_app/tag_analytics.py`

**Analytics Features:**
- **Popularity Tracking** - Most used tags
- **Trending Analysis** - Recently popular tags
- **Relationship Mapping** - Tags that appear together
- **Performance Metrics** - Tag usage statistics

### 4. Tag Views and Templates
**Location:** `verifast_app/views.py`, `verifast_app/templates/`

**User Interface:**
- **Tag Search Page** - Browse and search tags
- **Tag Detail Pages** - Individual tag information
- **Article Integration** - Tags displayed on articles
- **Tag Cloud** - Visual tag popularity display

## User Experience

### Tag Discovery
Users can discover content through:
- **Tag Search** - Search for specific topics
- **Tag Cloud** - Visual representation of popular tags
- **Related Tags** - Suggestions based on current content
- **Article Tags** - Tags displayed on each article

### Tag Validation Process
1. **Tag Creation** - User or system creates tag
2. **Wikipedia Lookup** - System queries Wikipedia API
3. **Validation** - Confirms tag exists and is relevant
4. **Content Enrichment** - Adds Wikipedia description
5. **Article Association** - Links tag to relevant articles

## Technical Implementation

### Database Schema
```sql
-- Tag table with indexes for performance
CREATE TABLE verifast_app_tag (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_validated BOOLEAN DEFAULT FALSE,
    wikipedia_url VARCHAR(200),
    wikipedia_content TEXT,
    article_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_tag_name ON verifast_app_tag(name);
CREATE INDEX idx_tag_validated ON verifast_app_tag(is_validated);
CREATE INDEX idx_tag_article_count ON verifast_app_tag(article_count);
```

### API Endpoints
- `GET /api/tags/` - List all validated tags
- `GET /api/tags/{slug}/` - Get tag details
- `GET /api/tags/{slug}/articles/` - Get articles for tag
- `POST /api/tags/validate/` - Validate tag with Wikipedia

### Caching Strategy
- **Tag Lists** - Cached for 15 minutes
- **Tag Details** - Cached for 30 minutes
- **Wikipedia Content** - Cached for 24 hours
- **Tag Analytics** - Cached for 1 hour

## Admin Interface

### Tag Management
**Location:** `verifast_app/admin.py`

**Admin Features:**
- **Tag Listing** - View all tags with validation status
- **Bulk Actions** - Validate multiple tags at once
- **Wikipedia Sync** - Update tags with latest Wikipedia data
- **Article Count Updates** - Refresh tag statistics

**Admin Actions:**
```python
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_validated', 'article_count', 'created_at')
    actions = ['validate_with_wikipedia', 'update_article_counts']
```

## Performance Optimizations

### Database Optimizations
- **Strategic Indexes** - On frequently queried fields
- **Query Optimization** - Use select_related and prefetch_related
- **Bulk Operations** - Efficient bulk tag operations

### Caching Implementation
- **View Caching** - Cache expensive tag queries
- **Template Fragment Caching** - Cache tag clouds and lists
- **API Response Caching** - Cache API responses

### Wikipedia API Optimization
- **Rate Limiting** - Respect Wikipedia API limits
- **Batch Requests** - Process multiple tags efficiently
- **Error Handling** - Graceful degradation on API failures

## Testing

### Test Coverage
**Location:** `verifast_app/test_tag_system.py`

**Test Areas:**
- **Tag Model** - Creation, validation, methods
- **Wikipedia Service** - API integration, error handling
- **Tag Views** - Search, detail, listing functionality
- **Tag Analytics** - Statistics and relationships

### Integration Tests
- **End-to-End Workflows** - Complete tag lifecycle
- **API Testing** - All tag-related endpoints
- **Performance Testing** - Tag search and analytics

## Configuration

### Wikipedia API Settings
```python
# settings.py
WIKIPEDIA_API_URL = 'https://en.wikipedia.org/api/rest_v1/'
WIKIPEDIA_RATE_LIMIT = 100  # requests per hour
WIKIPEDIA_TIMEOUT = 30  # seconds
```

### Tag System Settings
```python
# Tag validation settings
TAG_AUTO_VALIDATE = True
TAG_MIN_ARTICLE_COUNT = 1
TAG_CACHE_TIMEOUT = 900  # 15 minutes
```

## Future Enhancements

### Planned Features
- **Multi-language Support** - Tags in multiple languages
- **Tag Hierarchies** - Parent-child tag relationships
- **User-Generated Tags** - Allow users to create tags
- **Tag Recommendations** - AI-powered tag suggestions

### Advanced Analytics
- **Tag Performance Metrics** - Click-through rates
- **User Engagement** - Tag interaction analytics
- **Content Optimization** - Tag-based content recommendations

## Related Documentation
- [XP System](xp-system.md) - Gamification integration
- [Speed Reader](speed-reader.md) - Reading interface
- [API Specification](../api/specification.md) - Tag API endpoints
- [Wikipedia Service](../architecture/overview.md#external-integrations) - Technical details