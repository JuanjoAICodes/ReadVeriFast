# Pydantic Data Validation Design

## Overview

This design implements a comprehensive Pydantic-based data validation system for the VeriFast application. The implementation will introduce strongly-typed models for LLM responses, API requests, configuration management, and internal data transfer while maintaining compatibility with existing Django models and DRF serializers.

## Architecture

### Core Components

1. **Models Package** (`verifast_app/pydantic_models/`)
   - LLM response models
   - API request/response models  
   - Configuration models
   - Data transfer objects

2. **Validation Layer** (`verifast_app/validation/`)
   - Custom validators
   - Error formatters
   - Integration utilities

3. **Configuration Management** (`config/pydantic_settings.py`)
   - Environment-based settings
   - Typed configuration classes

## Components and Interfaces

### 1. LLM Response Models

```python
# verifast_app/pydantic_models/llm.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional

class QuizOption(BaseModel):
    text: str = Field(min_length=1, max_length=200)
    
class QuizQuestion(BaseModel):
    question: str = Field(min_length=10, max_length=500)
    options: List[QuizOption] = Field(min_length=4, max_length=4)
    correct_answer: int = Field(ge=0, le=3)
    explanation: Optional[str] = Field(max_length=1000)
    
    @validator('options')
    def validate_unique_options(cls, v):
        texts = [opt.text for opt in v]
        if len(set(texts)) != len(texts):
            raise ValueError('Quiz options must be unique')
        return v

class MasterAnalysisResponse(BaseModel):
    quiz: List[QuizQuestion] = Field(min_length=3, max_length=5)
    tags: List[str] = Field(min_length=1, max_length=7)
    
    @validator('tags')
    def validate_tags(cls, v):
        # Remove duplicates and empty strings
        cleaned = list(set(tag.strip() for tag in v if tag.strip()))
        if len(cleaned) < 1:
            raise ValueError('At least one tag is required')
        return cleaned[:7]  # Limit to 7 tags
```

### 2. API Request Models

```python
# verifast_app/pydantic_models/api.py
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional

class ArticleSubmissionRequest(BaseModel):
    url: HttpUrl
    title: Optional[str] = Field(max_length=200)
    
class QuizSubmissionRequest(BaseModel):
    article_id: int = Field(gt=0)
    answers: List[int] = Field(min_length=1, max_length=10)
    wpm: Optional[int] = Field(gt=50, le=2000)
    reading_time_seconds: Optional[int] = Field(gt=0)
    
    @validator('answers')
    def validate_answers(cls, v):
        if any(answer < 0 or answer > 3 for answer in v):
            raise ValueError('Answer indices must be between 0 and 3')
        return v

class UserProfileUpdateRequest(BaseModel):
    current_wpm: Optional[int] = Field(gt=50, le=2000)
    preferred_language: Optional[str] = Field(regex=r'^(en|es)$')
    theme: Optional[str] = Field(regex=r'^(light|dark)$')
```

### 3. Configuration Models

```python
# config/pydantic_settings.py
from pydantic import BaseSettings, Field, validator
from typing import Optional

class GeminiConfig(BaseSettings):
    api_key: str = Field(env='GEMINI_API_KEY')
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    top_k: int = Field(default=64, ge=1, le=100)
    max_output_tokens: int = Field(default=8192, ge=1, le=8192)
    
class CeleryConfig(BaseSettings):
    broker_url: str = Field(env='BROKER_URL', default='redis://localhost:6379/0')
    result_backend: str = Field(env='BROKER_URL', default='redis://localhost:6379/0')
    
    @validator('broker_url', 'result_backend')
    def validate_redis_url(cls, v):
        if not v.startswith(('redis://', 'rediss://')):
            raise ValueError('Must be a valid Redis URL')
        return v

class XPSystemConfig(BaseSettings):
    base_xp_per_question: int = Field(default=10, ge=1, le=100)
    perfect_score_bonus: int = Field(default=50, ge=0, le=500)
    wpm_improvement_multiplier: float = Field(default=1.5, ge=1.0, le=3.0)
```

### 4. Data Transfer Objects

```python
# verifast_app/pydantic_models/dto.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class ArticleAnalysisDTO(BaseModel):
    article_id: int
    content: str = Field(min_length=100)
    language: str = Field(regex=r'^(en|es)$')
    entities: List[str]
    reading_level: Optional[float] = Field(ge=0.0, le=100.0)
    
class XPTransactionDTO(BaseModel):
    user_id: int = Field(gt=0)
    transaction_type: str = Field(regex=r'^(EARN|SPEND)$')
    amount: int
    source: str
    description: str
    metadata: Optional[Dict] = None
    
class TagAnalyticsDTO(BaseModel):
    tag_name: str = Field(min_length=1, max_length=50)
    article_count: int = Field(ge=0)
    avg_quiz_score: Optional[float] = Field(ge=0.0, le=100.0)
    trend_score: float = Field(ge=0.0)
    last_updated: datetime
```

## Data Models

### Validation Pipeline

```python
# verifast_app/validation/pipeline.py
from typing import TypeVar, Type, Union, Dict, Any
from pydantic import BaseModel, ValidationError
import logging

T = TypeVar('T', bound=BaseModel)

class ValidationPipeline:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_and_parse(
        self, 
        model_class: Type[T], 
        data: Union[Dict, str], 
        context: str = ""
    ) -> Union[T, None]:
        """Validate data against Pydantic model with error handling"""
        try:
            if isinstance(data, str):
                return model_class.parse_raw(data)
            return model_class.parse_obj(data)
        except ValidationError as e:
            self.logger.error(f"Validation failed for {model_class.__name__} {context}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error validating {model_class.__name__} {context}: {e}")
            return None
    
    def format_validation_errors(self, error: ValidationError) -> Dict[str, Any]:
        """Format Pydantic validation errors for API responses"""
        formatted_errors = {}
        for error_detail in error.errors():
            field_path = '.'.join(str(loc) for loc in error_detail['loc'])
            formatted_errors[field_path] = {
                'message': error_detail['msg'],
                'type': error_detail['type'],
                'input': error_detail.get('input')
            }
        return formatted_errors
```

## Error Handling

### Custom Exception Classes

```python
# verifast_app/validation/exceptions.py
from typing import Dict, Any

class ValidationException(Exception):
    def __init__(self, errors: Dict[str, Any], message: str = "Validation failed"):
        self.errors = errors
        self.message = message
        super().__init__(message)

class LLMResponseValidationError(ValidationException):
    pass

class APIRequestValidationError(ValidationException):
    pass

class ConfigurationValidationError(ValidationException):
    pass
```

### Error Handlers

```python
# verifast_app/validation/handlers.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from .exceptions import ValidationException

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if isinstance(exc, ValidationException):
        return Response({
            'error': 'Validation failed',
            'details': exc.errors,
            'message': exc.message
        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    return response
```

## Testing Strategy

### Unit Tests

1. **Model Validation Tests**
   - Test valid data parsing
   - Test invalid data rejection
   - Test edge cases and boundary conditions
   - Test custom validators

2. **Integration Tests**
   - Test LLM response parsing
   - Test API request validation
   - Test configuration loading
   - Test error handling

3. **Performance Tests**
   - Validate parsing performance
   - Memory usage with large datasets
   - Concurrent validation handling

### Test Structure

```python
# verifast_app/tests/test_pydantic_models.py
import pytest
from pydantic import ValidationError
from verifast_app.pydantic_models.llm import QuizQuestion, MasterAnalysisResponse

class TestQuizQuestion:
    def test_valid_quiz_question(self):
        data = {
            'question': 'What is the capital of France?',
            'options': [
                {'text': 'London'},
                {'text': 'Berlin'}, 
                {'text': 'Paris'},
                {'text': 'Madrid'}
            ],
            'correct_answer': 2,
            'explanation': 'Paris is the capital of France.'
        }
        question = QuizQuestion.parse_obj(data)
        assert question.question == 'What is the capital of France?'
        assert len(question.options) == 4
        assert question.correct_answer == 2
    
    def test_invalid_correct_answer(self):
        data = {
            'question': 'Test question?',
            'options': [{'text': 'A'}, {'text': 'B'}, {'text': 'C'}, {'text': 'D'}],
            'correct_answer': 5  # Invalid - out of range
        }
        with pytest.raises(ValidationError):
            QuizQuestion.parse_obj(data)
```

## Integration Points

### Django Integration

1. **Middleware Integration**
   - Request validation middleware
   - Response serialization middleware

2. **View Integration**
   - Pydantic model parsing in API views
   - Error response formatting

3. **Service Layer Integration**
   - Update services.py to use Pydantic models
   - Maintain backward compatibility

### Celery Integration

1. **Task Serialization**
   - Use Pydantic models for task parameters
   - Validate task inputs before processing

2. **Result Handling**
   - Serialize task results using Pydantic
   - Validate task outputs

## Migration Strategy

### Phase 1: Core Models
- Implement LLM response models
- Update services.py to use validation
- Add basic error handling

### Phase 2: API Integration  
- Add API request models
- Update API views to use validation
- Implement error formatters

### Phase 3: Configuration
- Migrate to Pydantic Settings
- Update configuration loading
- Add startup validation

### Phase 4: Full Integration
- Add data transfer objects
- Update all service communications
- Complete test coverage

This design ensures a gradual, safe migration to Pydantic while maintaining all existing functionality and improving data reliability throughout the application.