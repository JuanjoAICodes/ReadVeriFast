# VeriFast API Specification

*Last Updated: July 21, 2025*
*Status: Current*

## Overview

VeriFast provides a REST API for accessing articles, user data, XP information, and quiz functionality. The API is built using Django REST Framework and follows RESTful conventions.

## Base URL

```
Development: http://localhost:8000/api/
Production: https://your-domain.com/api/
```

## Authentication

The API uses session-based authentication for web interface and token-based authentication for external access.

### Session Authentication
```html
<!-- Login via HTMX form submission -->
<form hx-post="/api/auth/login/" hx-target="#login-result">
    {% csrf_token %}
    <!-- Login form fields -->
</form>

<!-- Or traditional JavaScript for API access -->
<script>
fetch('/api/auth/login/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({
        username: 'user@example.com',
        password: 'password'
    })
})
```

## Endpoints

### User Management

#### Get Current User
```http
GET /api/user/
```

**Response:**
```json
{
    "id": 1,
    "username": "user@example.com",
    "current_xp_points": 150,
    "current_wpm": 250,
    "max_wpm": 300,
    "preferred_language": "en"
}
```

#### Update User Profile
```http
PUT /api/user/
```

**Request Body:**
```json
{
    "current_wpm": 275,
    "preferred_language": "es"
}
```

### Articles

#### List Articles
```http
GET /api/articles/
```

**Query Parameters:**
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20)
- `tag` - Filter by tag name
- `search` - Search in title and content

**Response:**
```json
{
    "count": 45,
    "next": "http://localhost:8000/api/articles/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Article Title",
            "content": "Article content...",
            "tags": ["technology", "ai"],
            "created_at": "2025-07-21T10:00:00Z",
            "processing_status": "complete"
        }
    ]
}
```

#### Get Article Detail
```http
GET /api/articles/{id}/
```

**Response:**
```json
{
    "id": 1,
    "title": "Article Title",
    "content": "Full article content...",
    "tags": ["technology", "ai"],
    "created_at": "2025-07-21T10:00:00Z",
    "processing_status": "complete",
    "word_count": 1250,
    "estimated_reading_time": 5
}
```

### XP System

#### Get User XP Balance
```http
GET /api/user/xp/
```

**Response:**
```json
{
    "current_xp_points": 150,
    "total_earned": 500,
    "total_spent": 350
}
```

#### Get XP Transactions
```http
GET /api/user/xp/transactions/
```

**Response:**
```json
{
    "count": 25,
    "results": [
        {
            "id": 1,
            "amount": 25,
            "transaction_type": "EARN",
            "source": "quiz_completion",
            "description": "Quiz completed with 90% score",
            "created_at": "2025-07-21T10:00:00Z"
        }
    ]
}
```

#### Purchase Premium Feature
```http
POST /api/user/xp/purchase/
```

**Request Body:**
```json
{
    "feature_key": "font_opensans"
}
```

**Response:**
```json
{
    "success": true,
    "feature": {
        "key": "font_opensans",
        "name": "OpenSans Font",
        "cost": 30
    },
    "new_balance": 120
}
```

### Quiz System

#### Generate Quiz
```http
POST /api/articles/{id}/quiz/
```

**Response:**
```json
{
    "quiz_id": "uuid-string",
    "questions": [
        {
            "id": 1,
            "question": "What is the main topic of this article?",
            "options": ["A", "B", "C", "D"],
            "type": "multiple_choice"
        }
    ]
}
```

#### Submit Quiz Attempt
```http
POST /api/quiz/{quiz_id}/submit/
```

**Request Body:**
```json
{
    "answers": {
        "1": "A",
        "2": "C"
    },
    "wpm_used": 250,
    "time_taken": 120
}
```

**Response:**
```json
{
    "score": 85.0,
    "xp_earned": 25,
    "correct_answers": 17,
    "total_questions": 20,
    "feedback": "Great job! You scored 85%"
}
```

### Tags

#### List Tags
```http
GET /api/tags/
```

**Query Parameters:**
- `search` - Search tag names
- `validated_only` - Only Wikipedia-validated tags (default: true)

**Response:**
```json
{
    "results": [
        {
            "id": 1,
            "name": "Technology",
            "slug": "technology",
            "is_validated": true,
            "article_count": 15,
            "wikipedia_url": "https://en.wikipedia.org/wiki/Technology"
        }
    ]
}
```

### Comments

#### List Article Comments
```http
GET /api/articles/{id}/comments/
```

#### Post Comment
```http
POST /api/articles/{id}/comments/
```

**Request Body:**
```json
{
    "content": "Great article! Very informative.",
    "parent": null
}
```

#### Interact with Comment
```http
POST /api/comments/{id}/interact/
```

**Request Body:**
```json
{
    "interaction_type": "bronze"
}
```

## Error Handling

### Error Response Format
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {
            "field_name": ["This field is required"]
        }
    }
}
```

### Common Error Codes
- `AUTHENTICATION_REQUIRED` - User must be logged in
- `PERMISSION_DENIED` - User lacks required permissions
- `VALIDATION_ERROR` - Invalid input data
- `NOT_FOUND` - Resource not found
- `RATE_LIMITED` - Too many requests

## Rate Limiting

- **Authenticated users**: 1000 requests per hour
- **Anonymous users**: 100 requests per hour
- **Quiz generation**: 10 requests per hour per user

## Related Documentation
- [XP System](../features/xp-system.md)
- [Tag System](../features/tag-system.md)
- [Authentication](../features/user-management.md)