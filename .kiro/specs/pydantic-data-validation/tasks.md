# Pydantic Data Validation Implementation Plan

- [x] 1. Set up Pydantic models package structure
  - Create `verifast_app/pydantic_models/` directory with `__init__.py`
  - Create separate modules for different model categories (llm.py, api.py, dto.py)
  - Set up proper imports and module organization
  - _Requirements: 6.1, 6.2_

- [x] 2. Implement LLM response validation models
  - Create `QuizOption` model with text validation and length constraints
  - Create `QuizQuestion` model with question, options, correct_answer, and explanation fields
  - Add custom validator for unique quiz options
  - Create `MasterAnalysisResponse` model for complete LLM response structure
  - Add tag validation with deduplication and length limits
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 3. Create validation pipeline and error handling
  - Create `verifast_app/validation/` directory with pipeline utilities
  - Implement `ValidationPipeline` class with validate_and_parse method
  - Create custom exception classes for different validation scenarios
  - Implement error formatting utilities for API responses
  - Add logging integration for validation failures
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 4. Update services.py to use Pydantic validation
  - Modify `generate_master_analysis` function to return typed Pydantic models
  - Add validation for LLM response parsing with error handling
  - Update function signature to use proper return types
  - Add fallback handling for validation failures
  - Maintain backward compatibility with existing callers
  - _Requirements: 1.4, 1.5, 6.3_

- [x] 5. Implement API request validation models
  - Create `ArticleSubmissionRequest` model with URL validation
  - Create `QuizSubmissionRequest` model with answer validation and WPM constraints
  - Create `UserProfileUpdateRequest` model with field validation
  - Add custom validators for answer indices and language codes
  - Test all validation rules with edge cases
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 6. Create configuration management with Pydantic Settings
  - Create `config/pydantic_settings.py` with environment-based settings
  - Implement `GeminiConfig` class with API key and generation parameters
  - Implement `CeleryConfig` class with broker URL validation
  - Create `XPSystemConfig` class with XP calculation parameters
  - Add validators for Redis URLs and numeric constraints
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 7. Integrate Pydantic models with API views
  - Update API views to use Pydantic models for request parsing
  - Add validation error handling to return HTTP 422 responses
  - Implement custom exception handler for ValidationException
  - Update DRF settings to use custom exception handler
  - Test API endpoints with valid and invalid data
  - _Requirements: 2.4, 2.5, 5.4_

- [x] 8. Create data transfer objects for internal services
  - Implement `ArticleAnalysisDTO` for article processing data
  - Create `XPTransactionDTO` for XP system communications
  - Implement `TagAnalyticsDTO` for tag analysis data
  - Add validation for all DTO fields with appropriate constraints
  - Update service methods to use DTOs for data exchange
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 9. Update background tasks to use Pydantic serialization
  - Modify Celery tasks to accept and return Pydantic models
  - Add serialization/deserialization for task parameters
  - Update task error handling to work with validation errors
  - Test task execution with validated data structures
  - Ensure task retry logic works with Pydantic models
  - _Requirements: 4.4, 4.5_

- [ ] 10. Implement comprehensive test suite
  - Create unit tests for all Pydantic models with valid/invalid data
  - Add integration tests for LLM response validation
  - Create API endpoint tests with request validation
  - Add configuration loading tests with environment variables
  - Implement performance tests for validation pipeline
  - Test error handling and exception formatting
  - _Requirements: 5.5, 6.5_

- [ ] 11. Add startup configuration validation
  - Integrate Pydantic Settings into Django settings loading
  - Add configuration validation at application startup
  - Implement clear error messages for configuration failures
  - Test startup behavior with invalid configuration
  - Document configuration requirements and validation rules
  - _Requirements: 3.4, 3.5_

- [ ] 12. Update documentation and type hints
  - Add type hints throughout codebase using Pydantic models
  - Update docstrings to reflect new validation behavior
  - Create developer documentation for Pydantic model usage
  - Add examples of common validation patterns
  - Document migration from dict-based to model-based data handling
  - _Requirements: 6.1, 6.4_