"""
Cache utilities for automated content acquisition system.
"""

import hashlib
from typing import Any, Optional, Dict
from datetime import date
from django.core.cache import cache
from django.utils import timezone
from .content_acquisition_config import CACHE_KEYS, CACHE_TIMEOUTS


class ContentAcquisitionCache:
    """Cache manager for content acquisition system."""
    
    @staticmethod
    def get_api_usage(api_name: str) -> Dict[str, int]:
        """Get current API usage for the day."""
        cache_key = CACHE_KEYS['api_usage'].format(api_name=api_name)
        usage = cache.get(cache_key)
        
        if usage is None:
            usage = {'daily': 0, 'current': 0}
            ContentAcquisitionCache.set_api_usage(api_name, usage)
        
        return usage
    
    @staticmethod
    def set_api_usage(api_name: str, usage: Dict[str, int]) -> None:
        """Set API usage for the day."""
        cache_key = CACHE_KEYS['api_usage'].format(api_name=api_name)
        cache.set(cache_key, usage, CACHE_TIMEOUTS['api_usage'])
    
    @staticmethod
    def increment_api_usage(api_name: str, count: int = 1) -> Dict[str, int]:
        """Increment API usage counter."""
        usage = ContentAcquisitionCache.get_api_usage(api_name)
        usage['current'] += count
        ContentAcquisitionCache.set_api_usage(api_name, usage)
        return usage
    
    @staticmethod
    def get_daily_topic_counts(language: str, target_date: Optional[date] = None) -> Dict[str, int]:
        """Get topic counts for a specific day and language."""
        if target_date is None:
            target_date = timezone.now().date()
        
        cache_key = CACHE_KEYS['daily_topic_counts'].format(
            language=language, 
            date=target_date.isoformat()
        )
        counts = cache.get(cache_key)
        
        if counts is None:
            counts = {}
            ContentAcquisitionCache.set_daily_topic_counts(language, counts, target_date)
        
        return counts
    
    @staticmethod
    def set_daily_topic_counts(language: str, counts: Dict[str, int], target_date: Optional[date] = None) -> None:
        """Set topic counts for a specific day and language."""
        if target_date is None:
            target_date = timezone.now().date()
        
        cache_key = CACHE_KEYS['daily_topic_counts'].format(
            language=language, 
            date=target_date.isoformat()
        )
        cache.set(cache_key, counts, CACHE_TIMEOUTS['topic_counts'])
    
    @staticmethod
    def increment_topic_count(language: str, topic: str, target_date: Optional[date] = None) -> int:
        """Increment topic count for a specific day and language."""
        counts = ContentAcquisitionCache.get_daily_topic_counts(language, target_date)
        counts[topic] = counts.get(topic, 0) + 1
        ContentAcquisitionCache.set_daily_topic_counts(language, counts, target_date)
        return counts[topic]
    
    @staticmethod
    def get_source_status(source_name: str) -> Dict[str, Any]:
        """Get status information for a content source."""
        cache_key = CACHE_KEYS['source_status'].format(source_name=source_name)
        status = cache.get(cache_key)
        
        if status is None:
            status = {
                'last_check': None,
                'status': 'unknown',
                'error_count': 0,
                'last_error': None
            }
            ContentAcquisitionCache.set_source_status(source_name, status)
        
        return status
    
    @staticmethod
    def set_source_status(source_name: str, status: Dict[str, Any]) -> None:
        """Set status information for a content source."""
        cache_key = CACHE_KEYS['source_status'].format(source_name=source_name)
        status['last_check'] = timezone.now().isoformat()
        cache.set(cache_key, status, CACHE_TIMEOUTS['source_status'])
    
    @staticmethod
    def acquire_lock(lock_name: str = 'cycle', timeout: Optional[int] = None) -> bool:
        """Acquire a distributed lock for acquisition processes."""
        if timeout is None:
            timeout = CACHE_TIMEOUTS['acquisition_lock']
        
        cache_key = CACHE_KEYS['acquisition_lock'].format(lock_name=lock_name)
        
        # Try to set the lock with a unique value
        lock_value = f"{timezone.now().timestamp()}_{hash(lock_name)}"
        
        # Use cache.add() which only sets if key doesn't exist
        return cache.add(cache_key, lock_value, timeout)
    
    @staticmethod
    def release_lock(lock_name: str = 'cycle') -> None:
        """Release a distributed lock."""
        cache_key = CACHE_KEYS['acquisition_lock'].format(lock_name=lock_name)
        cache.delete(cache_key)
    
    @staticmethod
    def is_duplicate_content(content: str) -> bool:
        """Check if content is a duplicate based on hash."""
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        cache_key = CACHE_KEYS['duplicate_hashes']
        
        # Get existing hashes
        existing_hashes = cache.get(cache_key, set())
        
        if content_hash in existing_hashes:
            return True
        
        # Add new hash
        existing_hashes.add(content_hash)
        cache.set(cache_key, existing_hashes, CACHE_TIMEOUTS['duplicate_hashes'])
        
        return False
    
    @staticmethod
    def add_duplicate_hash(content_hash: str) -> None:
        """Add a content hash to the duplicate detection cache."""
        cache_key = CACHE_KEYS['duplicate_hashes']
        existing_hashes = cache.get(cache_key, set())
        existing_hashes.add(content_hash)
        cache.set(cache_key, existing_hashes, CACHE_TIMEOUTS['duplicate_hashes'])
    
    @staticmethod
    def clear_daily_caches() -> None:
        """Clear daily caches (typically run at midnight)."""
        # This would be called by a scheduled task to reset daily counters
        today = timezone.now().date()
        
        # Clear topic counts for today
        for language in ['en', 'es']:
            cache_key = CACHE_KEYS['daily_topic_counts'].format(
                language=language, 
                date=today.isoformat()
            )
            cache.delete(cache_key)
        
        # Clear API usage counters
        for api_name in ['newsdata_io', 'gemini']:
            cache_key = CACHE_KEYS['api_usage'].format(api_name=api_name)
            cache.delete(cache_key)
    
    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        stats = {
            'api_usage': {},
            'topic_counts': {},
            'source_statuses': {},
            'locks_active': 0
        }
        
        # Get API usage stats
        for api_name in ['newsdata_io', 'gemini']:
            stats['api_usage'][api_name] = ContentAcquisitionCache.get_api_usage(api_name)
        
        # Get topic counts for today
        today = timezone.now().date()
        for language in ['en', 'es']:
            stats['topic_counts'][language] = ContentAcquisitionCache.get_daily_topic_counts(language, today)
        
        return stats


class CacheContextManager:
    """Context manager for cache operations with automatic cleanup."""
    
    def __init__(self, lock_name: str, timeout: Optional[int] = None):
        self.lock_name = lock_name
        self.timeout = timeout
        self.acquired = False
    
    def __enter__(self):
        self.acquired = ContentAcquisitionCache.acquire_lock(self.lock_name, self.timeout)
        if not self.acquired:
            raise RuntimeError(f"Could not acquire lock: {self.lock_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.acquired:
            ContentAcquisitionCache.release_lock(self.lock_name)