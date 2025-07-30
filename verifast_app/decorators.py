import logging
import functools
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')

def with_fallback(fallback_return: Any = None, log_error: bool = True):
    """
    Decorator for graceful degradation of service functions.
    If the decorated function raises an exception, returns the fallback value.
    
    Args:
        fallback_return: Value to return if function fails
        log_error: Whether to log the error
        
    Returns:
        Decorated function that handles exceptions gracefully
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except ImportError as e:
                if log_error:
                    logger.warning(f"{func.__name__} disabled due to missing dependency: {e}")
                return fallback_return
            except Exception as e:
                if log_error:
                    logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                return fallback_return
        return wrapper
    return decorator