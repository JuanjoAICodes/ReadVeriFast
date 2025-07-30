"""
Validation pipeline for Pydantic models with comprehensive error handling.

This module provides utilities for validating data against Pydantic models
with proper error handling, logging, and fallback mechanisms.
"""

import json
import logging
import time
from typing import TypeVar, Type, Union, Dict, Any, Optional, Callable
from pydantic import BaseModel, ValidationError

from .exceptions import ValidationException, LLMResponseValidationError

T = TypeVar('T', bound=BaseModel)


class ValidationPipeline:
    """Pipeline for validating data against Pydantic models."""
    
    def __init__(self, logger_name: str = __name__):
        self.logger = logging.getLogger(logger_name)
        self.logger_name = logger_name
        self.stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'average_processing_time': 0.0,
            'total_processing_time': 0.0
        }
    
    def validate_and_parse(
        self, 
        model_class: Type[T], 
        data: Union[Dict[str, Any], str], 
        context: str = "",
        raise_on_error: bool = False
    ) -> Optional[T]:
        """
        Validate data against Pydantic model with comprehensive error handling.
        
        Args:
            model_class: The Pydantic model class to validate against
            data: Data to validate (dict or JSON string)
            context: Additional context for error messages
            raise_on_error: Whether to raise exceptions or return None on validation failure
            
        Returns:
            Validated model instance or None if validation fails
            
        Raises:
            ValidationException: If raise_on_error=True and validation fails
        """
        try:
            if isinstance(data, str):
                # Parse JSON string
                try:
                    parsed_data = json.loads(data)
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON format: {str(e)}"
                    self.logger.error(f"JSON parsing failed for {model_class.__name__} {context}: {error_msg}")
                    
                    if raise_on_error:
                        raise ValidationException(
                            errors={"json": error_msg},
                            message=f"JSON parsing failed for {model_class.__name__}",
                            context=context
                        )
                    return None
                
                return model_class.parse_obj(parsed_data)
            else:
                # Validate dictionary data
                return model_class.parse_obj(data)
                
        except ValidationError as e:
            formatted_errors = self.format_validation_errors(e)
            self.logger.error(
                f"Validation failed for {model_class.__name__} {context}: {formatted_errors}"
            )
            
            if raise_on_error:
                raise ValidationException(
                    errors=formatted_errors,
                    message=f"Validation failed for {model_class.__name__}",
                    context=context
                )
            return None
            
        except Exception as e:
            error_msg = f"Unexpected error during validation: {str(e)}"
            self.logger.error(
                f"Unexpected error validating {model_class.__name__} {context}: {error_msg}",
                exc_info=True
            )
            
            if raise_on_error:
                raise ValidationException(
                    errors={"unexpected": error_msg},
                    message=f"Unexpected validation error for {model_class.__name__}",
                    context=context
                )
            return None
    
    def validate_llm_response(
        self,
        model_class: Type[T],
        raw_response: str,
        model_name: Optional[str] = None,
        raise_on_error: bool = False
    ) -> Optional[T]:
        """
        Specialized validation for LLM API responses.
        
        Args:
            model_class: The Pydantic model class to validate against
            raw_response: Raw response text from LLM API
            model_name: Name of the LLM model used
            raise_on_error: Whether to raise exceptions or return None on validation failure
            
        Returns:
            Validated model instance or None if validation fails
            
        Raises:
            LLMResponseValidationError: If raise_on_error=True and validation fails
        """
        try:
            # Clean common LLM response formatting
            clean_text = raw_response.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            return self.validate_and_parse(
                model_class=model_class,
                data=clean_text,
                context=f"LLM Response ({model_name})" if model_name else "LLM Response",
                raise_on_error=False  # Handle errors specially for LLM responses
            )
            
        except Exception as e:
            self.logger.error(
                f"LLM response validation failed for {model_class.__name__}: {str(e)}",
                exc_info=True
            )
            
            if raise_on_error:
                raise LLMResponseValidationError(
                    errors={"validation": str(e)},
                    raw_response=raw_response,
                    model_name=model_name
                )
            return None
    
    def format_validation_errors(self, error: ValidationError) -> Dict[str, Any]:
        """
        Format Pydantic validation errors for API responses and logging.
        
        Args:
            error: ValidationError from Pydantic
            
        Returns:
            Dictionary with formatted error information
        """
        formatted_errors = {}
        
        for error_detail in error.errors():
            # Create field path from error location
            field_path = '.'.join(str(loc) for loc in error_detail['loc'])
            
            formatted_errors[field_path] = {
                'message': error_detail['msg'],
                'type': error_detail['type'],
                'input': error_detail.get('input'),
                'ctx': error_detail.get('ctx', {})
            }
        
        return formatted_errors
    
    def safe_validate(
        self,
        model_class: Type[T],
        data: Union[Dict[str, Any], str],
        default_factory: Optional[Callable[[], T]] = None,
        context: str = ""
    ) -> T:
        """
        Safely validate data with fallback to default value.
        
        Args:
            model_class: The Pydantic model class to validate against
            data: Data to validate
            default_factory: Function to create default instance if validation fails
            context: Additional context for error messages
            
        Returns:
            Validated model instance or default instance
        """
        result = self.validate_and_parse(
            model_class=model_class,
            data=data,
            context=context,
            raise_on_error=False
        )
        
        if result is not None:
            return result
        
        # Return default instance if validation failed
        if default_factory:
            self.logger.warning(
                f"Using default instance for {model_class.__name__} due to validation failure"
            )
            return default_factory()
        
        # Create empty instance as last resort
        try:
            return model_class()
        except Exception as e:
            self.logger.error(
                f"Failed to create default instance for {model_class.__name__}: {str(e)}"
            )
            raise ValidationException(
                errors={"default_creation": str(e)},
                message=f"Failed to create default {model_class.__name__}",
                context=context
            )
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics and performance metrics"""
        total = self.stats['total_validations']
        successful = self.stats['successful_validations']
        
        return {
            'total_validations': total,
            'successful_validations': successful,
            'failed_validations': self.stats['failed_validations'],
            'success_rate': (successful / max(total, 1)) * 100,
            'average_processing_time': self.stats.get('average_processing_time', 0),
            'total_processing_time': self.stats.get('total_processing_time', 0),
            'pipeline_name': self.logger_name,
            'last_updated': time.time()
        }