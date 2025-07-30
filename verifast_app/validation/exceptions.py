"""
Custom exception classes for Pydantic validation errors.

This module defines specialized exceptions for different types of
validation failures in the VeriFast application.
"""

from typing import Dict, Any, Optional


class ValidationException(Exception):
    """Base exception for validation errors."""
    
    def __init__(
        self, 
        errors: Dict[str, Any], 
        message: str = "Validation failed",
        context: Optional[str] = None
    ):
        self.errors = errors
        self.message = message
        self.context = context
        super().__init__(message)
    
    def __str__(self):
        if self.context:
            return f"{self.message} ({self.context}): {self.errors}"
        return f"{self.message}: {self.errors}"


class LLMResponseValidationError(ValidationException):
    """Exception raised when LLM API response validation fails."""
    
    def __init__(
        self, 
        errors: Dict[str, Any], 
        raw_response: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.raw_response = raw_response
        self.model_name = model_name
        
        context = f"LLM: {model_name}" if model_name else "LLM Response"
        super().__init__(
            errors=errors,
            message="LLM response validation failed",
            context=context
        )


class APIRequestValidationError(ValidationException):
    """Exception raised when API request validation fails."""
    
    def __init__(
        self, 
        errors: Dict[str, Any], 
        endpoint: Optional[str] = None,
        method: Optional[str] = None
    ):
        self.endpoint = endpoint
        self.method = method
        
        context_parts = []
        if method:
            context_parts.append(method)
        if endpoint:
            context_parts.append(endpoint)
        
        context = " ".join(context_parts) if context_parts else "API Request"
        super().__init__(
            errors=errors,
            message="API request validation failed",
            context=context
        )


class ConfigurationValidationError(ValidationException):
    """Exception raised when configuration validation fails."""
    
    def __init__(
        self, 
        errors: Dict[str, Any], 
        config_section: Optional[str] = None
    ):
        self.config_section = config_section
        
        context = f"Config: {config_section}" if config_section else "Configuration"
        super().__init__(
            errors=errors,
            message="Configuration validation failed",
            context=context
        )