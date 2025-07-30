"""
Error handlers and formatters for API responses.

This module provides Django REST Framework integration for Pydantic
validation errors and consistent error response formatting.
"""

from typing import Dict, Any, Optional
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from pydantic import ValidationError

from .exceptions import (
    ValidationException,
    LLMResponseValidationError,
    APIRequestValidationError,
    ConfigurationValidationError
)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django REST Framework.
    
    Handles Pydantic validation exceptions and formats them
    as proper API error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Handle our custom validation exceptions
    if isinstance(exc, ValidationException):
        return Response(
            data={
                'error': 'Validation failed',
                'details': exc.errors,
                'message': exc.message,
                'context': exc.context
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    
    # Handle specific validation error types
    if isinstance(exc, APIRequestValidationError):
        return Response(
            data={
                'error': 'Invalid request data',
                'details': exc.errors,
                'endpoint': exc.endpoint,
                'method': exc.method
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if isinstance(exc, LLMResponseValidationError):
        return Response(
            data={
                'error': 'Internal processing error',
                'message': 'Failed to process AI response',
                'details': 'The AI service returned invalid data'
            },
            status=status.HTTP_502_BAD_GATEWAY
        )
    
    if isinstance(exc, ConfigurationValidationError):
        return Response(
            data={
                'error': 'Configuration error',
                'message': 'Server configuration is invalid',
                'details': 'Please contact system administrator'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Handle raw Pydantic ValidationError
    if isinstance(exc, ValidationError):
        formatted_errors = format_validation_errors(exc)
        return Response(
            data={
                'error': 'Validation failed',
                'details': formatted_errors
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    
    # Return the default response for other exceptions
    return response


def format_validation_errors(error: ValidationError) -> Dict[str, Any]:
    """
    Format Pydantic validation errors for API responses.
    
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
            'input': error_detail.get('input')
        }
    
    return formatted_errors


def format_api_error_response(
    message: str,
    details: Optional[Dict[str, Any]] = None,
    error_code: Optional[str] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> Response:
    """
    Create a standardized API error response.
    
    Args:
        message: Human-readable error message
        details: Additional error details
        error_code: Machine-readable error code
        status_code: HTTP status code
        
    Returns:
        DRF Response object with formatted error
    """
    response_data: Dict[str, Any] = {
        'error': message,
        'timestamp': None,  # Will be added by middleware if needed
    }
    
    if details:
        response_data['details'] = details
    
    if error_code:
        response_data['code'] = error_code
    
    return Response(response_data, status=status_code)


def create_validation_error_response(
    validation_errors: Dict[str, Any],
    message: str = "Validation failed"
) -> Response:
    """
    Create a validation error response with field-level details.
    
    Args:
        validation_errors: Dictionary of field validation errors
        message: Overall error message
        
    Returns:
        DRF Response object with validation errors
    """
    return Response(
        data={
            'error': message,
            'details': validation_errors,
            'type': 'validation_error'
        },
        status=status.HTTP_422_UNPROCESSABLE_ENTITY
    )