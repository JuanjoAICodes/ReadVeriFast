"""
Pydantic models package for VeriFast application.

This package contains strongly-typed Pydantic models for:
- LLM API responses and validation
- API request/response validation
- Configuration management
- Data transfer objects for internal services
"""

from .llm import QuizQuestion, MasterAnalysisResponse
from .api import (
    ArticleSubmissionRequest,
    QuizSubmissionRequest,
    UserProfileUpdateRequest,
)
from .dto import ArticleAnalysisDTO, XPTransactionDTO, TagAnalyticsDTO

__all__ = [
    # LLM Models
    
    "QuizQuestion",
    "MasterAnalysisResponse",
    # API Models
    "ArticleSubmissionRequest",
    "QuizSubmissionRequest",
    "UserProfileUpdateRequest",
    # Data Transfer Objects
    "ArticleAnalysisDTO",
    "XPTransactionDTO",
    "TagAnalyticsDTO",
]
