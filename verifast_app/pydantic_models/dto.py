"""
Data Transfer Objects (DTOs) for internal service communication.

This module contains Pydantic models used for passing data between
different services and components within the application.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class TransactionType(str, Enum):
    """Enumeration for XP transaction types."""
    EARN = "EARN"
    SPEND = "SPEND"


class ProcessingStatus(str, Enum):
    """Enumeration for article processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class ArticleAnalysisDTO(BaseModel):
    """Data transfer object for article analysis data."""
    
    article_id: int = Field(gt=0, description="Unique identifier for the article")
    content: str = Field(min_length=100, description="Article content text for analysis")
    language: str = Field(pattern=r"^(en|es)$", description="Language code of the article content")
    entities: List[str] = Field(description="List of named entities extracted from the content")
    reading_level: Optional[float] = Field(None, ge=0.0, le=100.0, description="Calculated reading difficulty level (0-100)")
    word_count: int = Field(gt=0, description="Total word count of the article")
    processing_time: Optional[float] = Field(None, ge=0.0, description="Time taken for analysis in seconds")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score for the analysis")
    
    @field_validator('entities')
    @classmethod
    def validate_entities(cls, v):
        """Validate and clean entities list."""
        # Remove duplicates and empty strings
        cleaned = list(set(entity.strip() for entity in v if entity.strip()))
        return cleaned[:20]  # Limit to 20 entities

    model_config = {
        "json_schema_extra": {
            "example": {
                "article_id": 123,
                "content": "This is a sample article content that is long enough for analysis...",
                "language": "en",
                "entities": ["Paris", "France", "European Union"],
                "reading_level": 45.2,
                "word_count": 850,
                "processing_time": 2.5,
                "confidence_score": 0.92
            }
        }
    }


class XPTransactionDTO(BaseModel):
    """Data transfer object for XP system transactions."""
    
    user_id: int = Field(gt=0, description="ID of the user involved in the transaction")
    transaction_type: TransactionType = Field(description="Type of transaction: EARN or SPEND")
    amount: int = Field(description="XP amount (positive for earn, negative for spend)")
    source: str = Field(min_length=1, max_length=50, description="Source or reason for the XP transaction")
    description: str = Field(min_length=1, max_length=200, description="Detailed description of the transaction")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the transaction")
    timestamp: Optional[datetime] = Field(None, description="Transaction timestamp")
    
    @field_validator('amount')
    @classmethod
    def validate_amount_sign(cls, v, info):
        """Validate amount sign matches transaction type."""
        transaction_type = info.data.get('transaction_type')
        if transaction_type == TransactionType.EARN and v <= 0:
            raise ValueError('EARN transactions must have positive amounts')
        elif transaction_type == TransactionType.SPEND and v >= 0:
            raise ValueError('SPEND transactions must have negative amounts')
        return v
    
    @field_validator('metadata')
    @classmethod
    def validate_metadata_size(cls, v):
        """Validate metadata is not too large."""
        if v and len(str(v)) > 1000:
            raise ValueError('Metadata is too large (max 1000 characters when serialized)')
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 456,
                "transaction_type": "EARN",
                "amount": 50,
                "source": "quiz_completion",
                "description": "Completed quiz for article 'Introduction to Python'",
                "metadata": {
                    "article_id": 123,
                    "quiz_score": 80,
                    "wpm_used": 250
                },
                "timestamp": "2025-01-21T23:30:00Z"
            }
        }
    }


class TagAnalyticsDTO(BaseModel):
    """Data transfer object for tag analytics and statistics."""
    
    tag_name: str = Field(min_length=1, max_length=50, description="Name of the tag")
    article_count: int = Field(ge=0, description="Number of articles associated with this tag")
    avg_quiz_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Average quiz score for articles with this tag")
    trend_score: float = Field(ge=0.0, description="Calculated trend score for tag popularity")
    last_updated: datetime = Field(description="Timestamp when analytics were last calculated")
    total_quiz_attempts: int = Field(ge=0, description="Total number of quiz attempts for this tag")
    avg_reading_time: Optional[float] = Field(None, ge=0.0, description="Average reading time in seconds")
    
    @field_validator('tag_name')
    @classmethod
    def validate_tag_name(cls, v):
        """Validate and normalize tag name."""
        return v.strip().title()

    model_config = {
        "json_schema_extra": {
            "example": {
                "tag_name": "Science",
                "article_count": 25,
                "avg_quiz_score": 78.5,
                "trend_score": 12.3,
                "last_updated": "2025-01-21T23:30:00Z",
                "total_quiz_attempts": 150,
                "avg_reading_time": 180.5
            }
        }
    }


class ContentAcquisitionDTO(BaseModel):
    """Data transfer object for content acquisition operations."""
    
    source_id: str = Field(min_length=1, max_length=50, description="Identifier for the content source")
    source_type: str = Field(pattern=r"^(rss|api|scraper)$", description="Type of content source")
    url: str = Field(min_length=1, description="Source URL")
    title: str = Field(min_length=1, max_length=200, description="Content title")
    content: str = Field(min_length=100, description="Full content text")
    language: str = Field(pattern=r"^(en|es)$", description="Content language")
    publication_date: Optional[datetime] = Field(None, description="Original publication date")
    author: Optional[str] = Field(None, max_length=100, description="Content author")
    tags: List[str] = Field(default=[], description="Extracted or assigned tags")
    image_url: Optional[str] = Field(None, description="URL of the article's main image")
    priority: str = Field(default="normal", pattern=r"^(low|normal|high)$", description="Processing priority")
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate and clean tags."""
        cleaned = [tag.strip().title() for tag in v if tag.strip()]
        return list(set(cleaned))[:10]  # Limit to 10 unique tags

    model_config = {
        "json_schema_extra": {
            "example": {
                "source_id": "newsapi_tech",
                "source_type": "api",
                "url": "https://example.com/article",
                "title": "Latest Technology Trends",
                "content": "This article discusses the latest trends in technology...",
                "language": "en",
                "publication_date": "2025-01-21T10:00:00Z",
                "author": "John Doe",
                "tags": ["Technology", "Innovation", "AI"],
                "priority": "normal"
            }
        }
    }


class QuizPerformanceDTO(BaseModel):
    """Data transfer object for quiz performance metrics."""
    
    user_id: int = Field(gt=0, description="User ID")
    article_id: int = Field(gt=0, description="Article ID")
    quiz_attempt_id: int = Field(gt=0, description="Quiz attempt ID")
    score: float = Field(ge=0.0, le=100.0, description="Quiz score percentage")
    correct_answers: int = Field(ge=0, description="Number of correct answers")
    total_questions: int = Field(gt=0, description="Total number of questions")
    time_taken: Optional[float] = Field(None, ge=0.0, description="Time taken in seconds")
    wpm_used: Optional[int] = Field(None, ge=50, le=2000, description="Reading speed used")
    difficulty_level: Optional[str] = Field(None, pattern=r"^(easy|medium|hard)$", description="Quiz difficulty")
    
    @field_validator('correct_answers')
    @classmethod
    def validate_correct_answers(cls, v, info):
        """Validate correct answers doesn't exceed total questions."""
        total_questions = info.data.get('total_questions', 0)
        if v > total_questions:
            raise ValueError('Correct answers cannot exceed total questions')
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 123,
                "article_id": 456,
                "quiz_attempt_id": 789,
                "score": 85.0,
                "correct_answers": 17,
                "total_questions": 20,
                "time_taken": 300.5,
                "wpm_used": 275,
                "difficulty_level": "medium"
            }
        }
    }


class SystemHealthDTO(BaseModel):
    """Data transfer object for system health monitoring."""
    
    service_name: str = Field(min_length=1, max_length=50, description="Name of the service")
    status: str = Field(pattern=r"^(healthy|degraded|unhealthy)$", description="Service status")
    response_time: Optional[float] = Field(None, ge=0.0, description="Response time in milliseconds")
    error_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Error rate (0.0 to 1.0)")
    last_check: datetime = Field(description="Timestamp of last health check")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional health details")
    
    @field_validator('details')
    @classmethod
    def validate_details_size(cls, v):
        """Validate details is not too large."""
        if v and len(str(v)) > 500:
            raise ValueError('Details is too large (max 500 characters when serialized)')
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "service_name": "gemini_api",
                "status": "healthy",
                "response_time": 250.5,
                "error_rate": 0.02,
                "last_check": "2025-01-21T23:30:00Z",
                "details": {
                    "api_version": "v1",
                    "rate_limit_remaining": 950
                }
            }
        }
    }


class CacheOperationDTO(BaseModel):
    """Data transfer object for cache operations."""
    
    operation: str = Field(pattern=r"^(get|set|delete|clear)$", description="Cache operation type")
    key: str = Field(min_length=1, max_length=100, description="Cache key")
    value: Optional[Any] = Field(None, description="Cache value (for set operations)")
    ttl: Optional[int] = Field(None, ge=0, description="Time to live in seconds")
    namespace: Optional[str] = Field(None, max_length=50, description="Cache namespace")
    success: bool = Field(description="Whether the operation was successful")
    execution_time: Optional[float] = Field(None, ge=0.0, description="Operation execution time in milliseconds")
    
    @field_validator('key')
    @classmethod
    def validate_cache_key(cls, v):
        """Validate cache key format."""
        # Remove invalid characters for cache keys
        import re
        cleaned = re.sub(r'[^\w\-\.]', '_', v)
        return cleaned

    model_config = {
        "json_schema_extra": {
            "example": {
                "operation": "set",
                "key": "article_123_quiz_data",
                "value": {"questions": [], "metadata": {}},
                "ttl": 3600,
                "namespace": "quiz_cache",
                "success": True,
                "execution_time": 5.2
            }
        }
    }