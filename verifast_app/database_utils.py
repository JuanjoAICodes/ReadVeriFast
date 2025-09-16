"""
Database utilities for handling SQLite locks and connection management.
"""
import time
import random
import logging
from functools import wraps
from django.db import OperationalError, transaction, connection
from django.db.utils import DatabaseError

logger = logging.getLogger(__name__)


def with_database_retry(max_retries=5, base_delay=1, max_delay=30):
    """
    Decorator to handle database lock errors with exponential backoff retry.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    # Close any existing connections to prevent lock accumulation
                    if attempt > 0:
                        connection.close()
                        
                    return func(*args, **kwargs)
                    
                except OperationalError as e:
                    last_exception = e
                    error_msg = str(e).lower()
                    
                    if 'database is locked' in error_msg or 'database locked' in error_msg:
                        if attempt < max_retries:
                            # Calculate delay with exponential backoff and jitter
                            delay = min(base_delay * (2 ** attempt), max_delay)
                            jitter = random.uniform(0.1, 0.5) * delay
                            total_delay = delay + jitter
                            
                            logger.warning(
                                f"Database locked on attempt {attempt + 1}/{max_retries + 1} "
                                f"for function {func.__name__}. Retrying in {total_delay:.2f}s"
                            )
                            
                            time.sleep(total_delay)
                            continue
                        else:
                            logger.error(
                                f"Database lock persisted after {max_retries} retries "
                                f"for function {func.__name__}"
                            )
                            raise
                    else:
                        # Non-lock database error, don't retry
                        raise
                        
                except DatabaseError as e:
                    # Other database errors that might be transient
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"Database error on attempt {attempt + 1}/{max_retries + 1} "
                            f"for function {func.__name__}: {e}. Retrying in {delay}s"
                        )
                        time.sleep(delay)
                        continue
                    else:
                        raise
            
            # If we get here, all retries failed
            raise last_exception
            
        return wrapper
    return decorator


def safe_database_operation(operation_func, *args, **kwargs):
    """
    Execute a database operation with automatic retry on lock errors.
    
    Args:
        operation_func: Function to execute
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        Result of the operation
    """
    @with_database_retry(max_retries=3, base_delay=0.5, max_delay=10)
    def _execute():
        return operation_func(*args, **kwargs)
    
    return _execute()


def ensure_connection_closed():
    """
    Ensure database connection is properly closed to prevent locks.
    """
    try:
        if connection.connection:
            connection.close()
            logger.debug("Database connection closed")
    except Exception as e:
        logger.warning(f"Error closing database connection: {e}")


class DatabaseLockManager:
    """
    Context manager for handling database operations with lock prevention.
    """
    
    def __init__(self, timeout=60, close_on_exit=True):
        self.timeout = timeout
        self.close_on_exit = close_on_exit
        
    def __enter__(self):
        # Set a longer timeout for this operation
        with connection.cursor() as cursor:
            cursor.execute(f"PRAGMA busy_timeout={self.timeout * 1000}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.close_on_exit:
            ensure_connection_closed()
        
        # If there was a database lock error, log it
        if exc_type and issubclass(exc_type, OperationalError):
            if 'database is locked' in str(exc_val).lower():
                logger.error(f"Database lock occurred: {exc_val}")
        
        return False  # Don't suppress exceptions


def optimize_sqlite_connection():
    """
    Apply SQLite optimizations to the current connection.
    """
    try:
        with connection.cursor() as cursor:
            # Apply optimizations
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=1000")
            cursor.execute("PRAGMA temp_store=memory")
            cursor.execute("PRAGMA busy_timeout=60000")
            cursor.execute("PRAGMA wal_autocheckpoint=1000")
            
        logger.debug("SQLite connection optimized")
    except Exception as e:
        logger.warning(f"Failed to optimize SQLite connection: {e}")


def get_database_status():
    """
    Get current database status and lock information.
    
    Returns:
        Dict with database status information
    """
    try:
        with connection.cursor() as cursor:
            status = {}
            
            # Check journal mode
            cursor.execute("PRAGMA journal_mode")
            status['journal_mode'] = cursor.fetchone()[0]
            
            # Check if database is locked
            try:
                cursor.execute("BEGIN IMMEDIATE")
                cursor.execute("ROLLBACK")
                status['locked'] = False
            except OperationalError:
                status['locked'] = True
            
            # Get database size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            status['size_mb'] = (page_count * page_size) / (1024 * 1024)
            
            # Get connection count (approximation)
            cursor.execute("PRAGMA database_list")
            status['databases'] = len(cursor.fetchall())
            
            return status
            
    except Exception as e:
        logger.error(f"Failed to get database status: {e}")
        return {'error': str(e)}