"""
Pydantic models for API request and response validation.

This module contains models for validating incoming API requests
and ensuring proper data structure for API responses.
"""

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
from typing import List, Optional, Dict, Any
import re
from urllib.parse import urlparse


class ArticleSubmissionRequest(BaseModel):
    """Model for validating article submission requests."""
    
    url: HttpUrl = Field(description="Valid HTTP/HTTPS URL of the article to process")
    title: Optional[str] = Field(None, max_length=200, description="Optional custom title for the article")
    language: Optional[str] = Field(None, pattern=r"^(en|es)$", description="Expected language of the article")
    priority: Optional[str] = Field(None, pattern=r"^(low|normal|high)$", description="Processing priority")
    
    @field_validator('url')
    @classmethod
    def validate_url_domain(cls, v):
        """Validate URL is from allowed domains and not localhost."""
        parsed = urlparse(str(v))
        
        # Block localhost and private IPs for security
        blocked_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
        if parsed.hostname in blocked_hosts:
            raise ValueError('URLs from localhost are not allowed')
        
        # Ensure it's HTTP/HTTPS
        if parsed.scheme not in ['http', 'https']:
            raise ValueError('Only HTTP and HTTPS URLs are allowed')
        
        return v
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Clean and validate title."""
        if v is None:
            return v
        
        # Clean whitespace and remove excessive formatting
        cleaned = re.sub(r'\s+', ' ', v.strip())
        if not cleaned:
            return None
        
        return cleaned

    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "https://example.com/article",
                "title": "Custom Article Title",
                "language": "en",
                "priority": "normal"
            }
        }
    }


class QuizSubmissionRequest(BaseModel):
    """Model for validating quiz submission requests."""
    
    article_id: int = Field(gt=0, description="ID of the article the quiz is for")
    answers: List[int] = Field(min_length=1, max_length=30, description="List of answer indices (0-3) for each question")
    wpm: Optional[int] = Field(None, ge=50, le=2000, description="Words per minute reading speed used")
    reading_time_seconds: Optional[int] = Field(None, gt=0, le=7200, description="Time spent reading the article in seconds (max 2 hours)")
    start_time: Optional[str] = Field(None, description="ISO timestamp when quiz was started")
    user_agent: Optional[str] = Field(None, max_length=500, description="User agent string for analytics")
    
    @field_validator('answers')
    @classmethod
    def validate_answer_indices(cls, v):
        """Ensure all answer indices are valid (0-3)."""
        if any(answer < 0 or answer > 3 for answer in v):
            raise ValueError('Answer indices must be between 0 and 3')
        
        # Check for reasonable number of answers
        if len(v) > 30:
            raise ValueError('Too many answers provided (maximum 30)')
        
        return v
    
    @model_validator(mode='after')
    def validate_wpm_and_time_consistency(self):
        """Validate WPM and reading time are reasonable."""
        if self.wpm and self.reading_time_seconds:
            # Basic sanity check: reading time should be reasonable for WPM
            if self.reading_time_seconds < 10:
                raise ValueError('Reading time too short to be realistic')
            
            if self.wpm > 1500:  # Very fast reading
                if self.reading_time_seconds > 600:  # 10 minutes
                    raise ValueError('Reading time inconsistent with very high WPM')
        
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "article_id": 123,
                "answers": [2, 0, 1, 3, 2],
                "wpm": 250,
                "reading_time_seconds": 180,
                "start_time": "2025-01-21T10:30:00Z"
            }
        }
    }


class UserProfileUpdateRequest(BaseModel):
    """Model for validating user profile update requests."""
    
    current_wpm: Optional[int] = Field(None, ge=50, le=2000, description="User's current reading speed in words per minute")
    preferred_language: Optional[str] = Field(None, pattern=r"^(en|es)$", description="User's preferred language (en or es)")
    theme: Optional[str] = Field(None, pattern=r"^(light|dark)$", description="User's preferred UI theme")
    email_notifications: Optional[bool] = Field(None, description="Whether to receive email notifications")
    difficulty_preference: Optional[str] = Field(None, pattern=r"^(easy|medium|hard)$", description="Preferred quiz difficulty")
    
    @field_validator('current_wpm')
    @classmethod
    def validate_realistic_wpm(cls, v):
        """Ensure WPM is realistic."""
        if v is None:
            return v
        
        if v < 50:
            raise ValueError('WPM too low - minimum is 50')
        if v > 2000:
            raise ValueError('WPM too high - maximum is 2000')
        
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "current_wpm": 300,
                "preferred_language": "en",
                "theme": "dark",
                "email_notifications": True,
                "difficulty_preference": "medium"
            }
        }
    }


class CommentSubmissionRequest(BaseModel):
    """Model for validating comment submission requests."""
    
    article_id: int = Field(gt=0, description="ID of the article to comment on")
    content: str = Field(min_length=10, max_length=2000, description="Comment content")
    parent_comment_id: Optional[int] = Field(None, gt=0, description="ID of parent comment for replies")
    
    @field_validator('content')
    @classmethod
    def validate_comment_content(cls, v):
        """Validate and clean comment content."""
        # Clean whitespace
        cleaned = re.sub(r'\s+', ' ', v.strip())
        
        # Check for minimum meaningful content
        if len(cleaned.split()) < 3:
            raise ValueError('Comment must contain at least 3 words')
        
        # Basic spam detection
        if len(set(cleaned.lower().split())) < len(cleaned.split()) * 0.3:
            raise ValueError('Comment appears to be spam (too many repeated words)')
        
        return cleaned

    model_config = {
        "json_schema_extra": {
            "example": {
                "article_id": 123,
                "content": "This is a thoughtful comment about the article content.",
                "parent_comment_id": None
            }
        }
    }


class XPPurchaseRequest(BaseModel):
    """Model for validating XP feature purchase requests."""
    
    feature_id: str = Field(min_length=1, max_length=50, description="ID of the feature to purchase")
    expected_cost: int = Field(gt=0, description="Expected XP cost (for verification)")
    
    @field_validator('feature_id')
    @classmethod
    def validate_feature_id(cls, v):
        """Validate feature ID format."""
        # Feature IDs should be alphanumeric with underscores
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Feature ID must contain only letters, numbers, and underscores')
        
        return v.lower()  # Normalize to lowercase

    model_config = {
        "json_schema_extra": {
            "example": {
                "feature_id": "word_chunking_2",
                "expected_cost": 100
            }
        }
    }


class SearchRequest(BaseModel):
    """Model for validating search requests."""
    
    query: str = Field(min_length=1, max_length=200, description="Search query")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    page: int = Field(default=1, ge=1, le=100, description="Page number for pagination")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, pattern=r"^(relevance|date|popularity)$", description="Sort criteria")
    
    @field_validator('query')
    @classmethod
    def validate_search_query(cls, v):
        """Validate and clean search query."""
        # Clean whitespace
        cleaned = re.sub(r'\s+', ' ', v.strip())
        
        if not cleaned:
            raise ValueError('Search query cannot be empty')
        
        # Remove potentially harmful characters
        cleaned = re.sub(r'[<>"\']', '', cleaned)
        
        return cleaned
    
    @field_validator('filters')
    @classmethod
    def validate_filters(cls, v):
        """Validate search filters."""
        if v is None:
            return v
        
        # Limit filter complexity
        if len(v) > 10:
            raise ValueError('Too many filters (maximum 10)')
        
        # Validate filter keys
        allowed_filters = {'language', 'tags', 'difficulty', 'date_range', 'author'}
        invalid_filters = set(v.keys()) - allowed_filters
        if invalid_filters:
            raise ValueError(f'Invalid filters: {", ".join(invalid_filters)}')
        
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "machine learning",
                "filters": {"language": "en", "tags": ["Science", "Technology"]},
                "page": 1,
                "per_page": 20,
                "sort_by": "relevance"
            }
        }
    }