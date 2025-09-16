"""
XP Economics System - Transaction Management and Business Logic

This module contains the core XP transaction management system, custom exceptions,
and business logic for the Enhanced XP Economics System.
"""

import logging
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.db.models import Count, Sum, Avg
from django.core.cache import cache
from django.conf import settings
from .models import CustomUser, XPTransaction, FeaturePurchase, QuizAttempt, Article, Comment

logger = logging.getLogger(__name__)


# Custom Exceptions for XP System
class XPSystemError(Exception):
    """Base exception for XP system errors"""
    pass


class InsufficientXPError(XPSystemError):
    """Raised when user doesn't have enough XP for transaction"""
    pass


class InvalidFeatureError(XPSystemError):
    """Raised when trying to purchase non-existent feature"""
    pass


class FeatureAlreadyOwnedError(XPSystemError):
    """Raised when trying to purchase already owned feature"""
    pass


class XPTransactionError(XPSystemError):
    """Raised when XP transaction fails"""
    pass


class ConcurrentTransactionError(XPSystemError):
    """Raised when concurrent XP transactions conflict"""
    pass


class XPValidationError(XPSystemError):
    """Raised when XP validation fails"""
    pass


class SuspiciousActivityError(XPSystemError):
    """Raised when suspicious XP activity is detected"""
    pass


class XPValidationManager:
    """
    Comprehensive XP validation and security manager.
    Handles concurrent transactions, suspicious activity detection, and data integrity.
    """
    
    # Thresholds for suspicious activity detection
    MAX_XP_PER_HOUR = 5000
    MAX_TRANSACTIONS_PER_MINUTE = 10
    MAX_FEATURE_PURCHASES_PER_DAY = 20
    
    @staticmethod
    def validate_xp_transaction(user, amount, transaction_type):
        """
        Validate XP transaction for security and integrity.
        
        Args:
            user: CustomUser instance
            amount: XP amount
            transaction_type: 'EARN' or 'SPEND'
        
        Raises:
            XPValidationError: If validation fails
            SuspiciousActivityError: If suspicious activity detected
        """
        # Basic validation
        if amount <= 0:
            raise XPValidationError(f"XP amount must be positive, got {amount}")
        
        if amount > 10000:  # Prevent extremely large transactions
            raise XPValidationError(f"XP amount too large: {amount}")
        
        # Check for suspicious activity patterns
        XPValidationManager._check_suspicious_activity(user, amount, transaction_type)
        
        # Validate user balance for spending
        if transaction_type == 'SPEND':
            if user.current_xp_points < amount:
                raise InsufficientXPError(
                    f"User {user.username} has {user.current_xp_points} XP, needs {amount}"
                )
        
        # Check for negative balance (should never happen)
        if user.current_xp_points < 0:
            logger.error(f"User {user.username} has negative XP balance: {user.current_xp_points}")
            raise XPValidationError("User has negative XP balance")
    
    @staticmethod
    def _check_suspicious_activity(user, amount, transaction_type):
        """
        Check for suspicious XP activity patterns.
        
        Args:
            user: CustomUser instance
            amount: XP amount
            transaction_type: 'EARN' or 'SPEND'
        
        Raises:
            SuspiciousActivityError: If suspicious patterns detected
        """
        from datetime import timedelta
        
        now = timezone.now()
        
        # Check XP earning rate (per hour)
        if transaction_type == 'EARN':
            hour_ago = now - timedelta(hours=1)
            recent_earnings = XPTransaction.objects.filter(
                user=user,
                transaction_type='EARN',
                timestamp__gte=hour_ago
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            if recent_earnings + amount > XPValidationManager.MAX_XP_PER_HOUR:
                logger.warning(f"Suspicious XP earning rate for user {user.username}: {recent_earnings + amount} XP/hour")
                raise SuspiciousActivityError(f"XP earning rate too high: {recent_earnings + amount} XP/hour")
        
        # Check transaction frequency
        minute_ago = now - timedelta(minutes=1)
        recent_transactions = XPTransaction.objects.filter(
            user=user,
            timestamp__gte=minute_ago
        ).count()
        
        if recent_transactions >= XPValidationManager.MAX_TRANSACTIONS_PER_MINUTE:
            logger.warning(f"High transaction frequency for user {user.username}: {recent_transactions}/minute")
            raise SuspiciousActivityError(f"Transaction frequency too high: {recent_transactions}/minute")
        
        # Check feature purchase frequency
        if transaction_type == 'SPEND':
            day_ago = now - timedelta(days=1)
            recent_purchases = FeaturePurchase.objects.filter(
                user=user,
                purchase_date__gte=day_ago
            ).count()
            
            if recent_purchases >= XPValidationManager.MAX_FEATURE_PURCHASES_PER_DAY:
                logger.warning(f"High feature purchase rate for user {user.username}: {recent_purchases}/day")
                raise SuspiciousActivityError(f"Feature purchase rate too high: {recent_purchases}/day")
    
    @staticmethod
    @transaction.atomic
    def safe_xp_transaction(user, amount, transaction_type, source, description, reference_obj=None):
        """
        Perform XP transaction with comprehensive validation and concurrent handling.
        
        Args:
            user: CustomUser instance
            amount: XP amount
            transaction_type: 'EARN' or 'SPEND'
            source: Transaction source
            description: Transaction description
            reference_obj: Optional reference object
        
        Returns:
            XPTransaction instance
        
        Raises:
            ConcurrentTransactionError: If concurrent transaction conflict
            XPValidationError: If validation fails
            SuspiciousActivityError: If suspicious activity detected
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Use select_for_update to prevent concurrent modifications
                user = CustomUser.objects.select_for_update().get(id=user.id)
                
                # Validate transaction
                XPValidationManager.validate_xp_transaction(user, amount, transaction_type)
                
                # Perform transaction based on type
                if transaction_type == 'EARN':
                    return XPTransactionManager.earn_xp(
                        user, amount, source, description, reference_obj
                    )
                else:
                    return XPTransactionManager.spend_xp(
                        user, amount, source, description, reference_obj
                    )
                    
            except IntegrityError as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Concurrent transaction failed after {max_retries} retries: {e}")
                    raise ConcurrentTransactionError("Transaction failed due to concurrent access")
                
                # Wait briefly before retry
                import time
                time.sleep(0.1 * retry_count)
                
            except (XPValidationError, SuspiciousActivityError, InsufficientXPError):
                raise  # Re-raise validation errors immediately
                
            except Exception as e:
                logger.error(f"Unexpected error in XP transaction: {e}", exc_info=True)
                raise XPTransactionError(f"Transaction failed: {str(e)}")
    
    @staticmethod
    def audit_user_xp_balance(user):
        """
        Audit user's XP balance for consistency.
        
        Args:
            user: CustomUser instance
        
        Returns:
            Dictionary with audit results
        """
        # Calculate expected balances from transactions
        transactions = XPTransaction.objects.filter(user=user)
        
        total_earned = transactions.filter(transaction_type='EARN').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        total_spent = abs(transactions.filter(transaction_type='SPEND').aggregate(
            total=Sum('amount')
        )['total'] or 0)
        
        expected_total_xp = total_earned
        expected_current_xp = total_earned - total_spent
        
        # Check for discrepancies
        total_xp_discrepancy = user.total_xp - expected_total_xp
        current_xp_discrepancy = user.current_xp_points - expected_current_xp
        
        audit_result = {
            'user_id': user.id,
            'username': user.username,
            'current_total_xp': user.total_xp,
            'current_spendable_xp': user.current_xp_points,
            'expected_total_xp': expected_total_xp,
            'expected_spendable_xp': expected_current_xp,
            'total_xp_discrepancy': total_xp_discrepancy,
            'current_xp_discrepancy': current_xp_discrepancy,
            'has_discrepancy': total_xp_discrepancy != 0 or current_xp_discrepancy != 0,
            'transaction_count': transactions.count(),
            'last_transaction': transactions.first().timestamp if transactions.exists() else None
        }
        
        # Log discrepancies
        if audit_result['has_discrepancy']:
            logger.warning(f"XP balance discrepancy for user {user.username}: {audit_result}")
        
        return audit_result


class XPCacheManager:
    """
    XP system caching manager for performance optimization.
    Handles caching of user features, balances, and frequently accessed data.
    """
    
    # Cache key prefixes
    USER_FEATURES_PREFIX = 'xp_user_features'
    USER_BALANCE_PREFIX = 'xp_user_balance'
    FEATURE_STORE_PREFIX = 'xp_feature_store'
    TRANSACTION_HISTORY_PREFIX = 'xp_transaction_history'
    
    # Cache timeouts (in seconds)
    FEATURES_TIMEOUT = 3600  # 1 hour
    BALANCE_TIMEOUT = 300    # 5 minutes
    STORE_TIMEOUT = 7200     # 2 hours
    HISTORY_TIMEOUT = 1800   # 30 minutes
    
    @staticmethod
    def get_user_features_cache_key(user_id):
        """Get cache key for user features"""
        return f"{XPCacheManager.USER_FEATURES_PREFIX}_{user_id}"
    
    @staticmethod
    def get_user_balance_cache_key(user_id):
        """Get cache key for user balance"""
        return f"{XPCacheManager.USER_BALANCE_PREFIX}_{user_id}"
    
    @staticmethod
    def get_feature_store_cache_key():
        """Get cache key for feature store"""
        return XPCacheManager.FEATURE_STORE_PREFIX
    
    @staticmethod
    def get_transaction_history_cache_key(user_id, transaction_type=None, limit=None):
        """Get cache key for transaction history"""
        key = f"{XPCacheManager.TRANSACTION_HISTORY_PREFIX}_{user_id}"
        if transaction_type:
            key += f"_{transaction_type}"
        if limit:
            key += f"_{limit}"
        return key
    
    @staticmethod
    def get_cached_user_features(user_id):
        """
        Get cached user feature ownership status.
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary of feature ownership or None if not cached
        """
        cache_key = XPCacheManager.get_user_features_cache_key(user_id)
        return cache.get(cache_key)
    
    @staticmethod
    def cache_user_features(user):
        """
        Cache user feature ownership status.
        
        Args:
            user: CustomUser instance
        """
        features = {}
        for feature_key in PremiumFeatureStore.FEATURES.keys():
            features[feature_key] = PremiumFeatureStore.user_owns_feature(user, feature_key)
        
        cache_key = XPCacheManager.get_user_features_cache_key(user.id)
        cache.set(cache_key, features, XPCacheManager.FEATURES_TIMEOUT)
        
        return features
    
    @staticmethod
    def invalidate_user_features_cache(user_id):
        """
        Invalidate user features cache after purchase.
        
        Args:
            user_id: User ID
        """
        cache_key = XPCacheManager.get_user_features_cache_key(user_id)
        cache.delete(cache_key)
    
    @staticmethod
    def get_cached_user_balance(user_id):
        """
        Get cached user XP balance.
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with balance info or None if not cached
        """
        cache_key = XPCacheManager.get_user_balance_cache_key(user_id)
        return cache.get(cache_key)
    
    @staticmethod
    def cache_user_balance(user):
        """
        Cache user XP balance information.
        
        Args:
            user: CustomUser instance
        """
        balance_info = {
            'total_xp': user.total_xp,
            'current_xp_points': user.current_xp_points,
            'lifetime_earned': user.lifetime_xp_earned,
            'lifetime_spent': user.lifetime_xp_spent,
            'last_updated': timezone.now().isoformat()
        }
        
        cache_key = XPCacheManager.get_user_balance_cache_key(user.id)
        cache.set(cache_key, balance_info, XPCacheManager.BALANCE_TIMEOUT)
        
        return balance_info
    
    @staticmethod
    def invalidate_user_balance_cache(user_id):
        """
        Invalidate user balance cache after transaction.
        
        Args:
            user_id: User ID
        """
        cache_key = XPCacheManager.get_user_balance_cache_key(user_id)
        cache.delete(cache_key)
    
    @staticmethod
    def get_cached_feature_store():
        """
        Get cached feature store data.
        
        Returns:
            Feature store data or None if not cached
        """
        cache_key = XPCacheManager.get_feature_store_cache_key()
        return cache.get(cache_key)
    
    @staticmethod
    def cache_feature_store():
        """
        Cache feature store data.
        
        Returns:
            Cached feature store data
        """
        # Prepare feature store data for caching
        features_data = {}
        for key, feature in PremiumFeatureStore.FEATURES.items():
            features_data[key] = {
                'name': feature['name'],
                'description': feature['description'],
                'cost': feature['cost'],
                'category': feature['category'],
                'subcategory': feature.get('subcategory', ''),
                'benefits': feature.get('benefits', []),
                'difficulty_level': feature.get('difficulty_level', 'beginner'),
                'preview_text': feature.get('preview_text', ''),
            }
        
        store_data = {
            'features': features_data,
            'pricing_tiers': PremiumFeatureStore.PRICING_TIERS,
            'cached_at': timezone.now().isoformat()
        }
        
        cache_key = XPCacheManager.get_feature_store_cache_key()
        cache.set(cache_key, store_data, XPCacheManager.STORE_TIMEOUT)
        
        return store_data
    
    @staticmethod
    def get_cached_transaction_history(user_id, transaction_type=None, limit=None):
        """
        Get cached transaction history.
        
        Args:
            user_id: User ID
            transaction_type: Optional transaction type filter
            limit: Optional limit
        
        Returns:
            Cached transaction history or None
        """
        cache_key = XPCacheManager.get_transaction_history_cache_key(
            user_id, transaction_type, limit
        )
        return cache.get(cache_key)
    
    @staticmethod
    def cache_transaction_history(user_id, transactions, transaction_type=None, limit=None):
        """
        Cache transaction history.
        
        Args:
            user_id: User ID
            transactions: QuerySet of transactions
            transaction_type: Optional transaction type filter
            limit: Optional limit
        """
        # Serialize transaction data for caching
        transaction_data = []
        for trans in transactions:
            transaction_data.append({
                'id': transaction.id,
                'transaction_type': transaction.transaction_type,
                'amount': transaction.amount,
                'source': transaction.source,
                'description': transaction.description,
                'balance_after': transaction.balance_after,
                'timestamp': transaction.timestamp.isoformat(),
            })
        
        cache_data = {
            'transactions': transaction_data,
            'cached_at': timezone.now().isoformat(),
            'count': len(transaction_data)
        }
        
        cache_key = XPCacheManager.get_transaction_history_cache_key(
            user_id, transaction_type, limit
        )
        cache.set(cache_key, cache_data, XPCacheManager.HISTORY_TIMEOUT)
        
        return cache_data
    
    @staticmethod
    def invalidate_user_transaction_cache(user_id):
        """
        Invalidate all transaction-related caches for a user.
        
        Args:
            user_id: User ID
        """
        # Invalidate various transaction cache combinations
        cache_keys = [
            XPCacheManager.get_transaction_history_cache_key(user_id),
            XPCacheManager.get_transaction_history_cache_key(user_id, 'EARN'),
            XPCacheManager.get_transaction_history_cache_key(user_id, 'SPEND'),
            XPCacheManager.get_transaction_history_cache_key(user_id, None, 10),
            XPCacheManager.get_transaction_history_cache_key(user_id, None, 20),
            XPCacheManager.get_transaction_history_cache_key(user_id, 'EARN', 10),
            XPCacheManager.get_transaction_history_cache_key(user_id, 'SPEND', 10),
        ]
        
        cache.delete_many(cache_keys)
    
    @staticmethod
    def warm_user_cache(user):
        """
        Pre-warm cache for a user with commonly accessed data.
        
        Args:
            user: CustomUser instance
        """
        # Cache user features
        XPCacheManager.cache_user_features(user)
        
        # Cache user balance
        XPCacheManager.cache_user_balance(user)
        
        # Cache recent transaction history
        recent_transactions = XPTransaction.objects.filter(user=user)[:20]
        XPCacheManager.cache_transaction_history(user.id, recent_transactions, limit=20)
    
    @staticmethod
    def invalidate_all_user_cache(user_id):
        """
        Invalidate all cached data for a user.
        
        Args:
            user_id: User ID
        """
        XPCacheManager.invalidate_user_features_cache(user_id)
        XPCacheManager.invalidate_user_balance_cache(user_id)
        XPCacheManager.invalidate_user_transaction_cache(user_id)


class XPPerformanceManager:
    """
    XP system performance optimization manager.
    Handles batch operations, query optimization, and performance monitoring.
    """
    
    @staticmethod
    def batch_xp_calculation(quiz_attempts):
        """
        Calculate XP for multiple quiz attempts efficiently.
        
        Args:
            quiz_attempts: QuerySet or list of QuizAttempt objects
        
        Returns:
            Dictionary mapping quiz_attempt_id to calculated XP
        """
        xp_results = {}
        
        # Prefetch related data to avoid N+1 queries
        quiz_attempts = quiz_attempts.select_related('user', 'article')
        
        for attempt in quiz_attempts:
            try:
                xp_earned = XPCalculationEngine.calculate_quiz_xp(attempt, attempt.article)
                xp_results[attempt.id] = xp_earned
            except Exception as e:
                logger.error(f"Error calculating XP for quiz attempt {attempt.id}: {e}")
                xp_results[attempt.id] = 0
        
        return xp_results
    
    @staticmethod
    def batch_feature_ownership_check(users, feature_keys):
        """
        Check feature ownership for multiple users efficiently.
        
        Args:
            users: QuerySet or list of CustomUser objects
            feature_keys: List of feature keys to check
        
        Returns:
            Dictionary mapping user_id to feature ownership dict
        """
        ownership_results = {}
        
        for user in users:
            user_features = {}
            for feature_key in feature_keys:
                user_features[feature_key] = PremiumFeatureStore.user_owns_feature(user, feature_key)
            ownership_results[user.id] = user_features
        
        return ownership_results
    
    @staticmethod
    def optimize_transaction_queries():
        """
        Optimize XP transaction queries with proper indexing suggestions.
        
        Returns:
            Dictionary with optimization recommendations
        """
        from django.db import connection
        
        recommendations = []
        
        # Check if proper indexes exist
        with connection.cursor() as cursor:
            # Check for user + timestamp index
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='index' AND name LIKE '%xptransaction%user%timestamp%'
            """)
            
            if cursor.fetchone()[0] == 0:
                recommendations.append({
                    'type': 'missing_index',
                    'table': 'XPTransaction',
                    'fields': ['user', 'timestamp'],
                    'reason': 'Optimize user transaction history queries'
                })
            
            # Check for transaction_type index
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='index' AND name LIKE '%xptransaction%transaction_type%'
            """)
            
            if cursor.fetchone()[0] == 0:
                recommendations.append({
                    'type': 'missing_index',
                    'table': 'XPTransaction',
                    'fields': ['transaction_type'],
                    'reason': 'Optimize transaction type filtering'
                })
        
        return {
            'recommendations': recommendations,
            'query_optimization_tips': [
                'Use select_related() for user and related objects',
                'Use prefetch_related() for reverse foreign key relationships',
                'Cache frequently accessed user features',
                'Batch XP calculations when possible',
                'Use database aggregation instead of Python loops'
            ]
        }
    
    @staticmethod
    def get_performance_metrics():
        """
        Get XP system performance metrics.
        
        Returns:
            Dictionary with performance statistics
        """
        from django.db import connection
        from datetime import timedelta
        
        now = timezone.now()
        hour_ago = now - timedelta(hours=1)
        
        # Query performance metrics
        with connection.cursor() as cursor:
            # Get transaction count in last hour
            cursor.execute("""
                SELECT COUNT(*) FROM verifast_app_xptransaction 
                WHERE timestamp >= %s
            """, [hour_ago])
            recent_transactions = cursor.fetchone()[0]
            
            # Get average transaction processing time (simulated)
            avg_processing_time = 0.05  # 50ms average
            
        # Cache hit rates (simulated - would need actual cache monitoring)
        cache_metrics = {
            'user_features_hit_rate': 0.85,
            'user_balance_hit_rate': 0.75,
            'transaction_history_hit_rate': 0.60,
            'feature_store_hit_rate': 0.95
        }
        
        return {
            'timestamp': now.isoformat(),
            'transaction_metrics': {
                'recent_transactions_per_hour': recent_transactions,
                'avg_processing_time_ms': avg_processing_time * 1000,
                'estimated_throughput_per_second': 1 / avg_processing_time if avg_processing_time > 0 else 0
            },
            'cache_metrics': cache_metrics,
            'database_metrics': {
                'connection_pool_size': getattr(settings, 'DATABASES', {}).get('default', {}).get('CONN_MAX_AGE', 0),
                'query_optimization_enabled': True
            },
            'recommendations': XPPerformanceManager.optimize_transaction_queries()
        }


class XPMonitoringManager:
    """
    XP system monitoring and analytics manager.
    Provides insights into XP economy health and user behavior.
    """
    
    @staticmethod
    def get_xp_economy_metrics():
        """
        Get comprehensive XP economy metrics.
        
        Returns:
            Dictionary with economy health metrics
        """
        from datetime import timedelta
        from django.db.models import Sum, Avg, Count
        
        now = timezone.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Transaction metrics
        daily_transactions = XPTransaction.objects.filter(timestamp__gte=day_ago)
        weekly_transactions = XPTransaction.objects.filter(timestamp__gte=week_ago)
        monthly_transactions = XPTransaction.objects.filter(timestamp__gte=month_ago)
        
        # XP flow metrics
        daily_earned = daily_transactions.filter(transaction_type='EARN').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        daily_spent = abs(daily_transactions.filter(transaction_type='SPEND').aggregate(
            total=Sum('amount')
        )['total'] or 0)
        
        # User activity metrics
        active_users_daily = daily_transactions.values('user').distinct().count()
        active_users_weekly = weekly_transactions.values('user').distinct().count()
        
        # Feature purchase metrics
        daily_purchases = FeaturePurchase.objects.filter(purchase_date__gte=day_ago)
        popular_features = FeaturePurchase.objects.values('feature_name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        return {
            'timestamp': now.isoformat(),
            'transaction_metrics': {
                'daily_transactions': daily_transactions.count(),
                'weekly_transactions': weekly_transactions.count(),
                'monthly_transactions': monthly_transactions.count(),
            },
            'xp_flow': {
                'daily_earned': daily_earned,
                'daily_spent': daily_spent,
                'daily_net': daily_earned - daily_spent,
                'economy_health': 'healthy' if daily_earned > daily_spent else 'deflation'
            },
            'user_activity': {
                'active_users_daily': active_users_daily,
                'active_users_weekly': active_users_weekly,
                'avg_transactions_per_user': daily_transactions.count() / max(active_users_daily, 1)
            },
            'feature_purchases': {
                'daily_purchases': daily_purchases.count(),
                'popular_features': list(popular_features),
                'avg_purchase_value': daily_purchases.aggregate(
                    avg=Avg('xp_cost')
                )['avg'] or 0
            }
        }
    
    @staticmethod
    def detect_anomalies():
        """
        Detect anomalies in XP system usage.
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Check for users with negative XP
        negative_xp_users = CustomUser.objects.filter(current_xp_points__lt=0)
        if negative_xp_users.exists():
            anomalies.append({
                'type': 'negative_xp_balance',
                'severity': 'critical',
                'count': negative_xp_users.count(),
                'users': list(negative_xp_users.values_list('username', flat=True))
            })
        
        # Check for extremely high XP balances
        high_xp_users = CustomUser.objects.filter(current_xp_points__gt=100000)
        if high_xp_users.exists():
            anomalies.append({
                'type': 'extremely_high_xp',
                'severity': 'warning',
                'count': high_xp_users.count(),
                'threshold': 100000
            })
        
        # Check for users with inconsistent XP data
        from datetime import timedelta
        recent_time = timezone.now() - timedelta(hours=1)
        
        suspicious_transactions = XPTransaction.objects.filter(
            timestamp__gte=recent_time,
            amount__gt=5000
        )
        
        if suspicious_transactions.exists():
            anomalies.append({
                'type': 'large_transactions',
                'severity': 'warning',
                'count': suspicious_transactions.count(),
                'threshold': 5000
            })
        
        return anomalies
    
    @staticmethod
    def generate_user_xp_report(user):
        """
        Generate comprehensive XP report for a user.
        
        Args:
            user: CustomUser instance
        
        Returns:
            Dictionary with detailed user XP report
        """
        from datetime import timedelta
        
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        
        # Transaction history
        all_transactions = XPTransaction.objects.filter(user=user)
        recent_transactions = all_transactions.filter(timestamp__gte=week_ago)
        
        # Feature purchases
        feature_purchases = FeaturePurchase.objects.filter(user=user)
        
        # Calculate statistics
        total_earned = all_transactions.filter(transaction_type='EARN').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        total_spent = abs(all_transactions.filter(transaction_type='SPEND').aggregate(
            total=Sum('amount')
        )['total'] or 0)
        
        weekly_activity = recent_transactions.count()
        
        return {
            'user_info': {
                'username': user.username,
                'user_id': user.id,
                'join_date': user.date_joined.isoformat(),
            },
            'xp_balances': {
                'total_xp': user.total_xp,
                'current_xp_points': user.current_xp_points,
                'lifetime_earned': user.lifetime_xp_earned,
                'lifetime_spent': user.lifetime_xp_spent,
            },
            'activity_metrics': {
                'total_transactions': all_transactions.count(),
                'weekly_transactions': weekly_activity,
                'xp_earning_streak': user.xp_earning_streak,
                'last_xp_earned': user.last_xp_earned.isoformat() if user.last_xp_earned else None,
            },
            'spending_patterns': {
                'total_earned_calculated': total_earned,
                'total_spent_calculated': total_spent,
                'feature_purchases': feature_purchases.count(),
                'avg_transaction_size': all_transactions.aggregate(
                    avg=Avg('amount')
                )['avg'] or 0,
            },
            'audit_status': XPValidationManager.audit_user_xp_balance(user),
            'owned_features': [
                fp.feature_name for fp in feature_purchases
            ]
        }


class XPTransactionManager:
    """
    Handles all XP transactions with atomic operations and proper logging.
    Ensures data integrity and provides complete audit trail.
    """
    
    @staticmethod
    @transaction.atomic
    def earn_xp(user, amount, source, description, reference_obj=None):
        """
        Award XP to user with transaction logging.
        
        Args:
            user: CustomUser instance
            amount: Positive integer amount of XP to award
            source: Source type from XPTransaction.SOURCES
            description: Human-readable description
            reference_obj: Optional related object (QuizAttempt, Comment, etc.)
        
        Returns:
            XPTransaction instance
        
        Raises:
            XPTransactionError: If transaction fails
        """
        try:
            # Validate amount is positive
            if amount <= 0:
                raise XPTransactionError(f"XP amount must be positive, got {amount}")
            
            # Update both total and spendable XP
            user.total_xp += amount
            user.current_xp_points += amount
            user.lifetime_xp_earned += amount
            user.last_xp_earned = timezone.now()
            user.save()
            
            # Create transaction record
            xp_transaction = XPTransaction.objects.create(
                user=user,
                transaction_type='EARN',
                amount=amount,
                source=source,
                description=description,
                balance_after=user.current_xp_points,
                quiz_attempt=reference_obj if isinstance(reference_obj, QuizAttempt) else None,
                comment=reference_obj if isinstance(reference_obj, Comment) else None
            )
            
            return xp_transaction
            
        except Exception as e:
            raise XPTransactionError(f"Failed to award XP: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def spend_xp(user, amount, purpose, description, reference_obj=None):
        if user.is_superuser or user.is_staff:
            return (True, "Admin user, no XP deducted.")
        """
        Spend user's XP with validation and logging.
        
        Args:
            user: CustomUser instance
            amount: Positive integer amount of XP to spend
            purpose: Purpose type from XPTransaction.SOURCES
            description: Human-readable description
            reference_obj: Optional related object (Comment, etc.)
        
        Returns:
            XPTransaction instance
        
        Raises:
            InsufficientXPError: If user doesn't have enough XP
            XPTransactionError: If transaction fails
        """
        try:
            # Validate amount is positive
            if amount <= 0:
                raise XPTransactionError(f"XP amount must be positive, got {amount}")
            
            # Check if user has sufficient balance
            if user.current_xp_points < amount:
                raise InsufficientXPError(
                    f"User {user.username} has {user.current_xp_points} XP, needs {amount}"
                )
            
            # Deduct only from spendable XP (total_xp remains unchanged)
            user.current_xp_points -= amount
            user.lifetime_xp_spent += amount
            user.save()
            
            # Create transaction record
            xp_transaction = XPTransaction.objects.create(
                user=user,
                transaction_type='SPEND',
                amount=-amount,  # Negative for spending
                source=purpose,
                description=description,
                balance_after=user.current_xp_points,
                comment=reference_obj if isinstance(reference_obj, Comment) else None,
                feature_purchased=reference_obj if isinstance(reference_obj, str) else None
            )
            
            return xp_transaction
            
        except InsufficientXPError:
            raise  # Re-raise as-is
        except Exception as e:
            raise XPTransactionError(f"Failed to spend XP: {str(e)}")
    
    @staticmethod
    def get_user_transaction_history(user, transaction_type=None, limit=None):
        """
        Get user's XP transaction history with optional filtering.
        
        Args:
            user: CustomUser instance
            transaction_type: Optional filter ('EARN' or 'SPEND')
            limit: Optional limit on number of transactions
        
        Returns:
            QuerySet of XPTransaction objects
        """
        transactions = XPTransaction.objects.filter(user=user)
        
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        
        if limit:
            transactions = transactions[:limit]
        
        return transactions
    
    @staticmethod
    def get_xp_balance_summary(user):
        """
        Get comprehensive XP balance summary for user.
        
        Args:
            user: CustomUser instance
        
        Returns:
            Dictionary with XP balance information
        """
        recent_transactions = XPTransaction.objects.filter(user=user)[:5]
        
        return {
            'total_xp': user.total_xp,
            'current_xp_points': user.current_xp_points,
            'lifetime_earned': user.lifetime_xp_earned,
            'lifetime_spent': user.lifetime_xp_spent,
            'xp_earning_streak': user.xp_earning_streak,
            'last_xp_earned': user.last_xp_earned,
            'recent_transactions': [
                {
                    'amount': t.amount,
                    'source': t.get_source_display(),
                    'description': t.description,
                    'timestamp': t.timestamp
                }
                for t in recent_transactions
            ]
        }


class PremiumFeatureStore:
    """
    Enhanced premium feature store with granular features and configurable pricing.
    Manages individual word chunking purchases, smart features, and font options.
    """
    
    # Configurable pricing tiers for easy adjustments
    PRICING_TIERS = {
        'basic_font': 25,
        'premium_font': 35,
        'accessibility_font': 50,
        'basic_chunking': 75,
        'advanced_chunking': 100,
        'expert_chunking': 125,
        'master_chunking': 150,
        'smart_feature_basic': 50,
        'smart_feature_advanced': 75,
        'theme_basic': 40,
        'theme_premium': 60
    }
    
    # Comprehensive feature definitions with granular control
    FEATURES = {
        # Premium Font Collection - Individual Purchases
        'font_opensans': {
            'name': 'OpenSans Font',
            'description': 'Clean, professional font for enhanced readability',
            'cost': PRICING_TIERS['basic_font'],
            'category': 'fonts',
            'subcategory': 'professional',
            'field_name': 'has_font_opensans',
            'preview_text': 'The quick brown fox jumps over the lazy dog.',
            'benefits': ['Clean lines', 'High readability', 'Professional appearance'],
            'difficulty_level': 'beginner'
        },
        'font_opendyslexic': {
            'name': 'OpenDyslexic Font',
            'description': 'Dyslexia-friendly font designed for easier reading',
            'cost': PRICING_TIERS['accessibility_font'],
            'category': 'fonts',
            'subcategory': 'accessibility',
            'field_name': 'has_font_opendyslexic',
            'preview_text': 'Specially designed for dyslexic readers.',
            'benefits': ['Reduces letter confusion', 'Improves reading flow', 'Accessibility focused'],
            'difficulty_level': 'beginner',
            'accessibility': True
        },
        'font_roboto': {
            'name': 'Roboto Font',
            'description': 'Modern, geometric font for clean reading experience',
            'cost': PRICING_TIERS['basic_font'],
            'category': 'fonts',
            'subcategory': 'modern',
            'field_name': 'has_font_roboto',
            'preview_text': 'Modern geometric design for digital reading.',
            'benefits': ['Modern design', 'Excellent screen clarity', 'Geometric precision'],
            'difficulty_level': 'beginner'
        },
        'font_merriweather': {
            'name': 'Merriweather Font',
            'description': 'Serif font optimized for reading on screens',
            'cost': PRICING_TIERS['basic_font'] + 5,
            'category': 'fonts',
            'subcategory': 'serif',
            'field_name': 'has_font_merriweather',
            'preview_text': 'Traditional serif elegance meets digital optimization.',
            'benefits': ['Screen optimized', 'Traditional elegance', 'Enhanced readability'],
            'difficulty_level': 'intermediate'
        },
        'font_playfair': {
            'name': 'Playfair Display Font',
            'description': 'Elegant serif font for sophisticated reading',
            'cost': PRICING_TIERS['premium_font'],
            'category': 'fonts',
            'subcategory': 'elegant',
            'field_name': 'has_font_playfair',
            'preview_text': 'Sophisticated elegance for discerning readers.',
            'benefits': ['Sophisticated design', 'High contrast', 'Distinctive character'],
            'difficulty_level': 'advanced'
        },
        
        # Granular Word Chunking Features - Individual Purchases
        '2word_chunking': {
            'name': '2-Word Chunking',
            'description': 'Read 2 words at a time for improved speed and comprehension',
            'cost': PRICING_TIERS['basic_chunking'],
            'category': 'chunking',
            'subcategory': 'basic',
            'field_name': 'has_2word_chunking',
            'preview_text': 'The quick | brown fox | jumps over',
            'benefits': ['Improved focus', 'Reduced eye movement', 'Better comprehension'],
            'difficulty_level': 'beginner',
            'speed_improvement': '15-25%',
            'prerequisites': []
        },
        '3word_chunking': {
            'name': '3-Word Chunking',
            'description': 'Read 3 words at a time for advanced speed reading',
            'cost': PRICING_TIERS['advanced_chunking'],
            'category': 'chunking',
            'subcategory': 'intermediate',
            'field_name': 'has_3word_chunking',
            'preview_text': 'The quick brown | fox jumps over | the lazy dog',
            'benefits': ['Faster reading', 'Enhanced flow', 'Improved retention'],
            'difficulty_level': 'intermediate',
            'speed_improvement': '25-40%',
            'prerequisites': ['2word_chunking']
        },
        '4word_chunking': {
            'name': '4-Word Chunking',
            'description': 'Read 4 words at a time for expert-level speed',
            'cost': PRICING_TIERS['expert_chunking'],
            'category': 'chunking',
            'subcategory': 'advanced',
            'field_name': 'has_4word_chunking',
            'preview_text': 'The quick brown fox | jumps over the lazy | dog in the yard',
            'benefits': ['Expert speed reading', 'Minimal eye movement', 'Maximum efficiency'],
            'difficulty_level': 'advanced',
            'speed_improvement': '40-60%',
            'prerequisites': ['2word_chunking', '3word_chunking']
        },
        '5word_chunking': {
            'name': '5-Word Chunking',
            'description': 'Read 5 words at a time for maximum speed',
            'cost': PRICING_TIERS['master_chunking'],
            'category': 'chunking',
            'subcategory': 'master',
            'field_name': 'has_5word_chunking',
            'preview_text': 'The quick brown fox jumps | over the lazy dog in | the sunny green yard today',
            'benefits': ['Master-level speed', 'Exceptional efficiency', 'Professional reading'],
            'difficulty_level': 'master',
            'speed_improvement': '60-80%',
            'prerequisites': ['2word_chunking', '3word_chunking', '4word_chunking']
        },
        
        # Smart Reading Features - Separate Premium Features
        'smart_connector_grouping': {
            'name': 'Smart Connector Grouping',
            'description': 'Intelligent grouping of connecting words like "the dragon" vs "the" + "dragon"',
            'cost': PRICING_TIERS['smart_feature_advanced'],
            'category': 'smart_features',
            'subcategory': 'grouping',
            'field_name': 'has_smart_connector_grouping',
            'preview_text': 'Groups: "the dragon" | "flies over" | "the mountain"',
            'benefits': ['Natural word grouping', 'Improved comprehension', 'Contextual reading'],
            'difficulty_level': 'intermediate',
            'technical_details': 'Uses NLP to identify semantic word groups'
        },
        'smart_symbol_handling': {
            'name': 'Smart Symbol Handling',
            'description': 'Elegant punctuation display and hyphen removal for better flow',
            'cost': PRICING_TIERS['smart_feature_basic'],
            'category': 'smart_features',
            'subcategory': 'formatting',
            'field_name': 'has_smart_symbol_handling',
            'preview_text': '( word ), ( another ), instead of (word, another)',
            'benefits': ['Cleaner display', 'Reduced distractions', 'Better flow'],
            'difficulty_level': 'beginner',
            'features': ['Hyphen removal', 'Elegant punctuation', 'Context preservation']
        }
    }
    
    # Feature bundles for discounted purchases
    FEATURE_BUNDLES = {
        'font_starter_pack': {
            'name': 'Font Starter Pack',
            'description': 'OpenSans + Roboto fonts at a discount',
            'features': ['font_opensans', 'font_roboto'],
            'individual_cost': 50,
            'bundle_cost': 40,
            'savings': 10
        },
        'chunking_progression': {
            'name': 'Chunking Progression Pack',
            'description': '2-word and 3-word chunking together',
            'features': ['2word_chunking', '3word_chunking'],
            'individual_cost': 175,
            'bundle_cost': 150,
            'savings': 25
        },
        'smart_reading_combo': {
            'name': 'Smart Reading Combo',
            'description': 'Both smart features at a discount',
            'features': ['smart_connector_grouping', 'smart_symbol_handling'],
            'individual_cost': 125,
            'bundle_cost': 100,
            'savings': 25
        }
    }
    
    @staticmethod
    @transaction.atomic
    def purchase_feature(user, feature_key):
        """
        Purchase a premium feature for user.
        
        Args:
            user: CustomUser instance
            feature_key: Key from FEATURES dictionary
        
        Returns:
            FeaturePurchase instance
        
        Raises:
            InvalidFeatureError: If feature doesn't exist
            FeatureAlreadyOwnedError: If user already owns feature
            InsufficientXPError: If user doesn't have enough XP
        """
        # Validate feature exists
        if feature_key not in PremiumFeatureStore.FEATURES:
            raise InvalidFeatureError(f"Feature '{feature_key}' does not exist")
        
        feature = PremiumFeatureStore.FEATURES[feature_key]
        
        # Check if already owned
        if PremiumFeatureStore.user_owns_feature(user, feature_key):
            if user.is_staff:
                # Admin users already have all features - return a mock purchase
                return FeaturePurchase(
                    user=user,
                    feature_name=feature_key,
                    feature_display_name=feature['name'],
                    xp_cost=0,
                    transaction=None
                )
            else:
                raise FeatureAlreadyOwnedError(f"User already owns {feature['name']}")
        
        # Process XP transaction (skip for admin users)
        if user.is_staff:
            xp_transaction = None
        else:
            xp_transaction = XPTransactionManager.spend_xp(
                user=user,
                amount=feature['cost'],
                purpose='feature_purchase',
                description=f"Purchased {feature['name']}",
                reference_obj=feature_key
            )
        
        # Unlock feature
        setattr(user, feature['field_name'], True)
        user.save()
        
        # Record purchase
        feature_purchase = FeaturePurchase.objects.create(
            user=user,
            feature_name=feature_key,
            feature_display_name=feature['name'],
            xp_cost=0 if user.is_staff else feature['cost'],
            transaction=xp_transaction
        )
        
        return feature_purchase
    
    @staticmethod
    def user_owns_feature(user, feature_key):
        """
        Check if user owns a specific feature.
        Admin users (is_staff=True) automatically own all premium features.
        
        Args:
            user: CustomUser instance
            feature_key: Key from FEATURES dictionary
        
        Returns:
            Boolean indicating ownership
        """
        # Admin users have all premium features unlocked
        if user.is_staff:
            return True
            
        if feature_key not in PremiumFeatureStore.FEATURES:
            return False
        
        feature = PremiumFeatureStore.FEATURES[feature_key]
        return getattr(user, feature['field_name'], False)
    
    @staticmethod
    def get_available_features(user):
        """
        Get all features with ownership status for user.
        
        Args:
            user: CustomUser instance
        
        Returns:
            List of feature dictionaries with ownership info
        """
        features = []
        
        for key, feature in PremiumFeatureStore.FEATURES.items():
            features.append({
                'key': key,
                'name': feature['name'],
                'description': feature['description'],
                'cost': feature['cost'],
                'category': feature['category'],
                'owned': PremiumFeatureStore.user_owns_feature(user, key),
                'can_afford': user.current_xp_points >= feature['cost']
            })
        
        return features
    
    @staticmethod
    def get_features_by_category(user):
        """
        Get features organized by category with ownership status.
        
        Args:
            user: CustomUser instance
        
        Returns:
            Dictionary with categories as keys and feature lists as values
        """
        features_by_category = {}
        
        for key, feature in PremiumFeatureStore.FEATURES.items():
            category = feature['category']
            
            if category not in features_by_category:
                features_by_category[category] = []
            
            features_by_category[category].append({
                'key': key,
                'name': feature['name'],
                'description': feature['description'],
                'cost': feature['cost'],
                'owned': PremiumFeatureStore.user_owns_feature(user, key),
                'can_afford': user.current_xp_points >= feature['cost']
            })
        
        return features_by_category


class XPCalculationEngine:
    """
    Handles XP calculation with complex formulas and bonuses.
    Implements the business rules for XP earning with advanced bonus systems.
    """
    
    @staticmethod
    def calculate_quiz_xp(quiz_attempt, article, user, use_letters=False):
        """
        Calculate XP using complex formula with word/letter count and bonuses.
        
        Args:
            quiz_attempt: QuizAttempt instance
            article: Article instance
            user: CustomUser instance
            use_letters: Boolean to use letter count instead of word count
        
        Returns:
            Dictionary with XP breakdown and bonuses
        """
        # Only award XP if quiz score >= 60%
        if quiz_attempt.score < 60:
            return {
                'base_xp': 0,
                'perfect_score_bonus': 0,
                'wpm_improvement_bonus': 0,
                'reading_streak_bonus': 0,
                'complexity_multiplier': 1.0,
                'total_xp': 0,
                'has_perfect_score_privilege': False,
                'is_new_wpm_record': False
            }
        
        # Choose between word count or letter count (configurable)
        if use_letters:
            base_count = len(article.content.replace(' ', ''))  # Letter count
        else:
            base_count = len(article.content.split())  # Word count
        
        # Complexity multiplier based on article reading level
        complexity_factor = max((article.reading_level or 10) / 10, 0.5)  # Min 0.5x multiplier
        
        # Speed multiplier based on WPM and complexity
        speed_multiplier = (quiz_attempt.wpm_used / 250) * complexity_factor
        
        # Accuracy bonus (quiz score percentage)
        accuracy_bonus = quiz_attempt.score / 100
        
        # Calculate base XP
        base_xp = int(base_count * speed_multiplier * accuracy_bonus)
        base_xp = max(base_xp, 1)  # Minimum 1 XP
        
        # Perfect score bonus (25% extra XP)
        perfect_score_bonus = 0
        has_perfect_score_privilege = False
        if quiz_attempt.score >= 100:
            perfect_score_bonus = int(base_xp * 0.25)
            has_perfect_score_privilege = True
        
        # WPM improvement bonus (50 XP for new personal record)
        wpm_improvement_bonus = 0
        is_new_wpm_record = False
        if quiz_attempt.wpm_used > user.max_wpm:
            wpm_improvement_bonus = 50
            is_new_wpm_record = True
            # Update user's max WPM
            user.max_wpm = quiz_attempt.wpm_used
            user.save()
        
        # Reading streak bonus
        reading_streak_bonus = XPCalculationEngine.calculate_reading_streak_bonus(user)
        
        # Calculate total XP
        total_xp = base_xp + perfect_score_bonus + wpm_improvement_bonus + reading_streak_bonus
        
        return {
            'base_xp': base_xp,
            'perfect_score_bonus': perfect_score_bonus,
            'wpm_improvement_bonus': wpm_improvement_bonus,
            'reading_streak_bonus': reading_streak_bonus,
            'complexity_multiplier': complexity_factor,
            'total_xp': total_xp,
            'has_perfect_score_privilege': has_perfect_score_privilege,
            'is_new_wpm_record': is_new_wpm_record
        }
    
    @staticmethod
    def calculate_reading_streak_bonus(user):
        """
        Calculate bonus XP based on user's reading streak.
        
        Args:
            user: CustomUser instance
        
        Returns:
            Integer bonus XP amount
        """
        streak = user.xp_earning_streak
        
        # Bonus XP based on streak length
        if streak >= 30:  # 30+ days
            return 50
        elif streak >= 14:  # 2+ weeks
            return 25
        elif streak >= 7:   # 1+ week
            return 10
        elif streak >= 3:   # 3+ days
            return 5
        else:
            return 0
    
    @staticmethod
    def update_reading_streak(user):
        """
        Update user's reading streak based on XP earning activity.
        
        Args:
            user: CustomUser instance
        
        Returns:
            Boolean indicating if streak was updated
        """
        from django.utils import timezone
        
        now = timezone.now()
        
        # If user has never earned XP, start streak at 1
        if not user.last_xp_earned:
            user.xp_earning_streak = 1
            user.last_xp_earned = now
            user.save()
            return True
        
        # Calculate days since last XP earning
        days_since_last = (now - user.last_xp_earned).days
        
        if days_since_last == 0:
            # Same day, no streak change
            return False
        elif days_since_last == 1:
            # Consecutive day, increment streak
            user.xp_earning_streak += 1
            user.last_xp_earned = now
            user.save()
            return True
        else:
            # Streak broken, reset to 1
            user.xp_earning_streak = 1
            user.last_xp_earned = now
            user.save()
            return True
    
    @staticmethod
    def has_perfect_score_privilege(quiz_attempt):
        """
        Check if user gets free comment for perfect score.
        
        Args:
            quiz_attempt: QuizAttempt instance
        
        Returns:
            Boolean indicating perfect score privilege
        """
        return quiz_attempt.score >= 100
    
    @staticmethod
    def calculate_perfect_score_bonus(base_xp):
        """
        Calculate bonus XP for perfect quiz scores.
        
        Args:
            base_xp: Base XP amount
        
        Returns:
            Integer bonus XP amount (25% of base)
        """
        return int(base_xp * 0.25)
    
    @staticmethod
    def get_recommended_wpm(user, failed_attempts=0):
        """
        Get recommended WPM after quiz failure.
        
        Args:
            user: CustomUser instance
            failed_attempts: Number of consecutive failed attempts
        
        Returns:
            Integer recommended WPM
        """
        last_successful_wpm = user.last_successful_wpm_used or 200
        
        # Progressively slower recommendations
        reduction = min(failed_attempts * 25, 100)  # Max 100 WPM reduction
        recommended_wmp = max(last_successful_wpm - reduction, 100)
        
        return recommended_wmp
    
    @staticmethod
    def get_next_recommended_articles(user, current_article, limit=2):
        """
        Get recommended articles based on tags and reading status.
        
        Args:
            user: CustomUser instance
            current_article: Article instance
            limit: Maximum number of recommendations
        
        Returns:
            Dictionary with 'next_similar' and 'random_unread' articles
        """
        # Find unread articles with most common tags
        user_read_articles = QuizAttempt.objects.filter(
            user=user, score__gte=60
        ).values_list('article_id', flat=True)
        
        unread_articles = Article.objects.exclude(
            id__in=user_read_articles
        ).filter(processing_status='complete')
        
        # Find articles with common tags
        current_tags = current_article.tags.all()
        if current_tags.exists():
            tagged_articles = unread_articles.filter(
                tags__in=current_tags
            ).annotate(
                common_tags=Count('tags')
            ).order_by('-common_tags')[:1]
        else:
            tagged_articles = []
        
        # Get random unread article
        random_article = unread_articles.order_by('?')[:1]
        
        return {
            'next_similar': tagged_articles[0] if tagged_articles else None,
            'random_unread': random_article[0] if random_article else None
        }


class QuizResultProcessor:
    """
    Handles quiz result processing, XP awarding, user feedback, and feedback construction
    for incorrect answers when passed.
    Implements the complete quiz completion workflow with bonuses and messaging.
    """
    
    @staticmethod
    def grade_quiz(quiz_attempt, article):
        """
        Calculate the quiz score based on user answers and correct answers.
        Robust to multiple quiz schemas:
        - List[question] or Dict with 'quiz'/'questions'
        - Correct answer provided as index or text under 'correct_answer' or 'answer'
        
        Args:
            quiz_attempt: QuizAttempt instance with user_answers in result field
            article: Article instance with quiz_data
        
        Returns:
            Float score percentage (0-100)
        """
        try:
            import json as _json
            # Get user answers from quiz attempt (ensure ints)
            user_answers = quiz_attempt.result.get('user_answers', [])
            if isinstance(user_answers, str):
                try:
                    user_answers = _json.loads(user_answers)
                except Exception:
                    user_answers = []
            try:
                user_answers = [int(a) if a is not None and a != '' else -1 for a in user_answers]
            except Exception:
                # Fallback: keep as-is
                pass
            
            # Load quiz data (prefer snapshot stored with attempt, else article)
            qd = quiz_attempt.result.get('quiz_data') if quiz_attempt.result.get('quiz_data') is not None else article.quiz_data
            if isinstance(qd, str):
                try:
                    qd = _json.loads(qd)
                except Exception:
                    qd = []
            
            # Normalize to list of question dicts
            if isinstance(qd, dict):
                if isinstance(qd.get('quiz'), list):
                    quiz_list = qd.get('quiz')
                elif isinstance(qd.get('questions'), list):
                    quiz_list = qd.get('questions')
                else:
                    quiz_list = []
            elif isinstance(qd, list):
                quiz_list = qd
            else:
                quiz_list = []
            
            if not quiz_list or not user_answers:
                return 0.0
            
            # Calculate score
            correct_count = 0
            total_questions = min(len(quiz_list), len(user_answers))
            
            for i in range(total_questions):
                q = quiz_list[i] if isinstance(quiz_list[i], dict) else {}
                user_ans = user_answers[i]
                # Normalize options to text list
                opts = q.get('options', [])
                norm_opts = [o.get('text') if isinstance(o, dict) else o for o in opts]
                # Determine correct index from 'correct_answer' or 'answer'
                correct_val = q.get('correct_answer', q.get('answer', None))
                correct_idx = None
                if isinstance(correct_val, int):
                    correct_idx = correct_val
                elif isinstance(correct_val, str) and norm_opts and correct_val in norm_opts:
                    correct_idx = norm_opts.index(correct_val)
                # Compare; ensure user_ans is int
                try:
                    user_idx = int(user_ans)
                except (TypeError, ValueError):
                    user_idx = -1
                if correct_idx is not None and user_idx == int(correct_idx):
                    correct_count += 1
            
            # Calculate percentage
            if total_questions > 0:
                score = (correct_count / total_questions) * 100
                return round(score, 1)
            return 0.0
                
        except Exception as e:
            print(f"Error grading quiz: {e}")
            return 0.0

    @staticmethod
    @transaction.atomic
    def process_quiz_completion(quiz_attempt, article, user):
        """
        Process a completed quiz attempt with XP calculation and user updates.
        Also builds detailed feedback for incorrect answers when the user passes (>=60%).
        
        Args:
            quiz_attempt: QuizAttempt instance
            article: Article instance
            user: CustomUser instance
        
        Returns:
            Dictionary with complete quiz result information, including optional feedback list
        """
        # First, grade the quiz to calculate the actual score
        actual_score = QuizResultProcessor.grade_quiz(quiz_attempt, article)
        quiz_attempt.score = actual_score
        quiz_attempt.save()
        
        # Calculate XP with all bonuses
        xp_breakdown = XPCalculationEngine.calculate_quiz_xp(quiz_attempt, article, user)
        
        # Update user statistics
        user.quiz_attempts_count += 1
        if quiz_attempt.score >= 100:
            user.perfect_quiz_count += 1
        
        # Update reading streak if XP was earned
        if xp_breakdown['total_xp'] > 0:
            XPCalculationEngine.update_reading_streak(user)
            
            # Update last successful WPM if quiz passed
            if quiz_attempt.score >= 60:
                user.last_successful_wpm_used = quiz_attempt.wpm_used
        
        user.save()
        
        # Award XP if earned
        if xp_breakdown['total_xp'] > 0:
            # Create detailed description
            description_parts = [f"Quiz completed with {quiz_attempt.score}% score"]
            if xp_breakdown['perfect_score_bonus'] > 0:
                description_parts.append("Perfect score bonus!")
            if xp_breakdown['wpm_improvement_bonus'] > 0:
                description_parts.append("New WPM record!")
            if xp_breakdown['reading_streak_bonus'] > 0:
                description_parts.append(f"Reading streak bonus ({user.xp_earning_streak} days)")
            
            description = " | ".join(description_parts)
            
            # Award XP
            XPTransactionManager.earn_xp(
                user=user,
                amount=xp_breakdown['total_xp'],
                source='quiz_completion',
                description=description,
                reference_obj=quiz_attempt
            )
            
            # Update quiz attempt with awarded XP
            quiz_attempt.xp_awarded = xp_breakdown['total_xp']
            quiz_attempt.save()
        
        # Build feedback for incorrect answers only if passed (>=60%)
        feedback = []
        if quiz_attempt.score >= 60:
            feedback = QuizResultProcessor.build_incorrect_feedback(quiz_attempt, article)
        
        # Generate result messaging and navigation
        result_data = QuizResultProcessor.generate_quiz_result_data(
            quiz_attempt, article, user, xp_breakdown
        )
        
        # Attach feedback (only provided on pass)
        result_data['feedback'] = feedback
        
        return result_data
    
    @staticmethod
    def build_incorrect_feedback(quiz_attempt, article):
        """
        Build a list of feedback items for incorrect answers only, but only used for passing scores.
        Handles multiple quiz_data schemas:
        - List[question]
        - Dict with key 'quiz' or 'questions'
        And supports 'correct_answer' (index or text) or 'answer' (index or text).
        """
        try:
            import json as _json
            # Parse stored result data
            result = quiz_attempt.result or {}
            user_answers = result.get('user_answers')
            if isinstance(user_answers, str):
                user_answers = _json.loads(user_answers)
            if user_answers is None:
                user_answers = []
            
            # Load quiz_data, prefer the snapshot stored with the attempt
            qd = result.get('quiz_data') if result.get('quiz_data') is not None else article.quiz_data
            if isinstance(qd, str):
                qd = _json.loads(qd)
            # Normalize to list of questions
            if isinstance(qd, dict):
                if 'quiz' in qd and isinstance(qd['quiz'], list):
                    quiz_list = qd['quiz']
                elif 'questions' in qd and isinstance(qd['questions'], list):
                    quiz_list = qd['questions']
                else:
                    quiz_list = []
            elif isinstance(qd, list):
                quiz_list = qd
            else:
                quiz_list = []
            
            feedback = []
            for i, q in enumerate(quiz_list):
                # Normalize options to text
                options = q.get('options', [])
                norm_opts = [o.get('text') if isinstance(o, dict) else o for o in options]
                # Determine correct answer index
                correct_val = q.get('correct_answer', q.get('answer', None))
                correct_idx = None
                if isinstance(correct_val, int):
                    correct_idx = correct_val
                elif isinstance(correct_val, str):
                    if norm_opts and correct_val in norm_opts:
                        correct_idx = norm_opts.index(correct_val)
                
                user_ans = user_answers[i] if i < len(user_answers) else None
                if correct_idx is None or user_ans is None:
                    continue
                
                # Compare; ensure user_ans is int
                try:
                    user_idx = int(user_ans)
                except (TypeError, ValueError):
                    continue
                
                if user_idx != int(correct_idx):
                    feedback.append({
                        'question': q.get('question', ''),
                        'user_answer_index': user_idx,
                        'user_answer': norm_opts[user_idx] if 0 <= user_idx < len(norm_opts) else None,
                        'correct_answer_index': int(correct_idx) if isinstance(correct_idx, int) else correct_idx,
                        'correct_answer': norm_opts[int(correct_idx)] if isinstance(correct_idx, int) and 0 <= int(correct_idx) < len(norm_opts) else (correct_val if isinstance(correct_val, str) else None),
                        'explanation': q.get('explanation')
                    })
            return feedback
        except Exception:
            # Fail quietly to avoid breaking quiz flow
            return []
    
    @staticmethod
    def generate_quiz_result_data(quiz_attempt, article, user, xp_breakdown):
        """
        Generate comprehensive quiz result data for UI display.
        
        Args:
            quiz_attempt: QuizAttempt instance
            article: Article instance
            user: CustomUser instance
            xp_breakdown: XP calculation breakdown dictionary
        
        Returns:
            Dictionary with complete quiz result information
        """
        score = quiz_attempt.score
        
        # Determine result type
        if score >= 100:
            result_type = 'perfect'
        elif score >= 60:
            result_type = 'passed'
        else:
            result_type = 'failed'
        
        # Get recommended articles
        recommendations = XPCalculationEngine.get_next_recommended_articles(user, article)
        
        # Generate messages based on result type
        if result_type == 'perfect':
            messages = QuizResultProcessor.get_perfect_score_messages(xp_breakdown)
        elif result_type == 'passed':
            messages = QuizResultProcessor.get_passed_quiz_messages(quiz_attempt, xp_breakdown)
        else:
            messages = QuizResultProcessor.get_failed_quiz_messages(quiz_attempt, user)
        
        return {
            'result_type': result_type,
            'score': score,
            'xp_breakdown': xp_breakdown,
            'messages': messages,
            'recommendations': recommendations,
            'has_perfect_score_privilege': xp_breakdown.get('has_perfect_score_privilege', False),
            'is_new_wpm_record': xp_breakdown.get('is_new_wpm_record', False),
            'user_stats': {
                'total_xp': user.total_xp,
                'current_xp_points': user.current_xp_points,
                'perfect_quiz_count': user.perfect_quiz_count,
                'quiz_attempts_count': user.quiz_attempts_count,
                'xp_earning_streak': user.xp_earning_streak
            }
        }
    
    @staticmethod
    def get_perfect_score_messages(xp_breakdown):
        """
        Generate messages for perfect quiz scores.
        
        Args:
            xp_breakdown: XP calculation breakdown dictionary
        
        Returns:
            Dictionary with message components
        """
        messages = {
            'title': '🎉 Perfect Quiz!',
            'subtitle': 'Outstanding performance!',
            'main_message': 'You can comment on this article for free!',
            'encouragement': 'What do you think about this news/event?',
            'retention_tip': 'Writing about news you understood 100% improves retention and helps you remember the content better.',
            'xp_celebration': f"Amazing! You earned {xp_breakdown['total_xp']} XP!",
            'bonus_messages': []
        }
        
        # Add bonus messages
        if xp_breakdown['perfect_score_bonus'] > 0:
            messages['bonus_messages'].append(f"🏆 Perfect Score Bonus: +{xp_breakdown['perfect_score_bonus']} XP")
        
        if xp_breakdown['wpm_improvement_bonus'] > 0:
            messages['bonus_messages'].append(f"🚀 New Speed Record: +{xp_breakdown['wpm_improvement_bonus']} XP")
        
        if xp_breakdown['reading_streak_bonus'] > 0:
            messages['bonus_messages'].append(f"🔥 Reading Streak: +{xp_breakdown['reading_streak_bonus']} XP")
        
        return messages
    
    @staticmethod
    def get_passed_quiz_messages(quiz_attempt, xp_breakdown):
        """
        Generate messages for passed quizzes (60-99%).
        
        Args:
            quiz_attempt: QuizAttempt instance
            xp_breakdown: XP calculation breakdown dictionary
        
        Returns:
            Dictionary with message components
        """
        messages = {
            'title': '✅ Quiz Passed!',
            'subtitle': f'Great job! You scored {quiz_attempt.score}%',
            'main_message': 'Well done on passing the quiz!',
            'xp_earned': f"You earned {xp_breakdown['total_xp']} XP",
            'improvement_tip': 'Keep reading to improve your comprehension and speed!',
            'bonus_messages': []
        }
        
        # Add bonus messages
        if xp_breakdown['wpm_improvement_bonus'] > 0:
            messages['bonus_messages'].append(f"🚀 New Speed Record: +{xp_breakdown['wpm_improvement_bonus']} XP")
        
        if xp_breakdown['reading_streak_bonus'] > 0:
            messages['bonus_messages'].append(f"🔥 Reading Streak: +{xp_breakdown['reading_streak_bonus']} XP")
        
        return messages
    
    @staticmethod
    def get_failed_quiz_messages(quiz_attempt, user):
        """
        Generate messages for failed quizzes (<60%).
        
        Args:
            quiz_attempt: QuizAttempt instance
            user: CustomUser instance
        
        Returns:
            Dictionary with message components
        """
        # Calculate consecutive failures for this user
        recent_attempts = QuizAttempt.objects.filter(
            user=user
        ).order_by('-timestamp')[:5]
        
        consecutive_failures = 0
        for attempt in recent_attempts:
            if attempt.score < 60:
                consecutive_failures += 1
            else:
                break
        
        # Get recommended WPM
        recommended_wpm = XPCalculationEngine.get_recommended_wpm(user, consecutive_failures)
        
        messages = {
            'title': '📚 Keep Learning!',
            'subtitle': f'You scored {quiz_attempt.score}%',
            'main_message': "Don't worry! Reading comprehension improves with practice.",
            'no_xp_message': 'Score 60% or higher to earn XP',
            'speed_recommendation': {
                'message': f'Try reading at {recommended_wpm} WPM for better comprehension.',
                'current_wpm': quiz_attempt.wpm_used,
                'recommended_wpm': recommended_wpm,
                'last_successful_wpm': user.last_successful_wpm_used
            },
            'encouragement': 'Take your time and focus on understanding the content.',
            'consecutive_failures': consecutive_failures
        }
        
        return messages
    
    @staticmethod
    def get_quiz_navigation_links(result_type, recommendations, article):
        """
        Generate navigation links based on quiz result.
        
        Args:
            result_type: 'perfect', 'passed', or 'failed'
            recommendations: Dictionary with recommended articles
            article: Current article instance
        
        Returns:
            List of navigation link dictionaries
        """
        links = []
        
        if result_type in ['perfect', 'passed']:
            # Success navigation
            if recommendations['next_similar']:
                links.append({
                    'type': 'next_similar',
                    'url': recommendations['next_similar'].get_absolute_url(),
                    'title': recommendations['next_similar'].title,
                    'label': 'Next: Similar Topic',
                    'icon': '📖',
                    'description': 'Continue with related content'
                })
            
            if recommendations['random_unread']:
                links.append({
                    'type': 'random',
                    'url': recommendations['random_unread'].get_absolute_url(),
                    'title': recommendations['random_unread'].title,
                    'label': 'Random Article',
                    'icon': '🎲',
                    'description': 'Discover something new'
                })
            
            # Comment section link
            comment_cost = 0 if result_type == 'perfect' else 10
            comment_label = 'Comment Section (FREE)' if result_type == 'perfect' else 'Comment Section (10 XP)'
            
            links.append({
                'type': 'comments',
                'url': f"{article.get_absolute_url()}#comments",
                'title': 'Share your thoughts',
                'label': comment_label,
                'icon': '💬',
                'description': 'Join the discussion',
                'xp_cost': comment_cost
            })
        
        else:
            # Failure navigation
            links.append({
                'type': 'reread',
                'url': article.get_absolute_url(),
                'title': 'Re-read Article',
                'label': 'Read Again',
                'icon': '📖',
                'description': 'Take your time'
            })
            
            links.append({
                'type': 'retry_quiz',
                'url': f"{article.get_absolute_url()}?retry_quiz=1",
                'title': 'Try Quiz Again',
                'label': 'Retry Quiz',
                'icon': '🔄',
                'description': 'You can do it!'
            })
        
        return links


# Enhanced Premium Feature Store Methods
class PremiumFeatureStoreExtensions:
    """
    Extended methods for the Premium Feature Store system.
    """
    
    @staticmethod
    def check_prerequisites(user, feature_key):
        """
        Check if user meets prerequisites for a feature.
        
        Args:
            user: CustomUser instance
            feature_key: Key from FEATURES dictionary
        
        Returns:
            Tuple (can_purchase: bool, missing_prerequisites: list)
        """
        if feature_key not in PremiumFeatureStore.FEATURES:
            return False, ['Feature does not exist']
        
        feature = PremiumFeatureStore.FEATURES[feature_key]
        prerequisites = feature.get('prerequisites', [])
        
        if not prerequisites:
            return True, []
        
        missing = []
        for prereq in prerequisites:
            if not PremiumFeatureStore.user_owns_feature(user, prereq):
                prereq_name = PremiumFeatureStore.FEATURES.get(prereq, {}).get('name', prereq)
                missing.append(prereq_name)
        
        return len(missing) == 0, missing
    
    @staticmethod
    def get_chunking_progression_status(user):
        """
        Get user's chunking progression status with recommendations.
        
        Args:
            user: CustomUser instance
        
        Returns:
            Dictionary with progression information
        """
        chunking_features = ['2word_chunking', '3word_chunking', '4word_chunking', '5word_chunking']
        owned_features = []
        next_feature = None
        
        for feature_key in chunking_features:
            if PremiumFeatureStore.user_owns_feature(user, feature_key):
                owned_features.append(feature_key)
            elif next_feature is None:
                # Check prerequisites
                can_purchase, missing = PremiumFeatureStore.check_prerequisites(user, feature_key)
                if can_purchase:
                    next_feature = feature_key
        
        return {
            'owned_features': owned_features,
            'next_recommended': next_feature,
            'progression_level': len(owned_features),
            'max_level': len(chunking_features),
            'completion_percentage': (len(owned_features) / len(chunking_features)) * 100
        }
    
    @staticmethod
    def get_feature_recommendations(user):
        """
        Get personalized feature recommendations for user.
        
        Args:
            user: CustomUser instance
        
        Returns:
            Dictionary with recommended features by category
        """
        recommendations = {
            'beginner': [],
            'progression': [],
            'affordable': [],
            'bundles': []
        }
        
        # Beginner recommendations (difficulty level beginner)
        for key, feature in PremiumFeatureStore.FEATURES.items():
            if (feature.get('difficulty_level') == 'beginner' and 
                not PremiumFeatureStore.user_owns_feature(user, key) and
                user.current_xp_points >= feature['cost']):
                recommendations['beginner'].append({
                    'key': key,
                    'name': feature['name'],
                    'cost': feature['cost'],
                    'benefits': feature.get('benefits', [])
                })
        
        # Progression recommendations (next logical step)
        chunking_status = PremiumFeatureStore.get_chunking_progression_status(user)
        if chunking_status['next_recommended']:
            next_key = chunking_status['next_recommended']
            feature = PremiumFeatureStore.FEATURES[next_key]
            recommendations['progression'].append({
                'key': next_key,
                'name': feature['name'],
                'cost': feature['cost'],
                'reason': 'Next step in chunking progression'
            })
        
        # Affordable recommendations (within budget)
        affordable_features = []
        for key, feature in PremiumFeatureStore.FEATURES.items():
            if (not PremiumFeatureStore.user_owns_feature(user, key) and
                user.current_xp_points >= feature['cost']):
                affordable_features.append({
                    'key': key,
                    'name': feature['name'],
                    'cost': feature['cost'],
                    'category': feature['category']
                })
        
        # Sort by cost (cheapest first)
        recommendations['affordable'] = sorted(affordable_features, key=lambda x: x['cost'])[:3]
        
        # Bundle recommendations
        for bundle_key, bundle in PremiumFeatureStore.FEATURE_BUNDLES.items():
            # Check if user can benefit from bundle
            unowned_features = [f for f in bundle['features'] 
                             if not PremiumFeatureStore.user_owns_feature(user, f)]
            if len(unowned_features) >= 2 and user.current_xp_points >= bundle['bundle_cost']:
                recommendations['bundles'].append({
                    'key': bundle_key,
                    'name': bundle['name'],
                    'cost': bundle['bundle_cost'],
                    'savings': bundle['savings'],
                    'features': unowned_features
                })
        
        return recommendations
    
    @staticmethod
    def purchase_bundle(user, bundle_key):
        """
        Purchase a feature bundle for user.
        
        Args:
            user: CustomUser instance
            bundle_key: Key from FEATURE_BUNDLES dictionary
        
        Returns:
            List of FeaturePurchase instances
        
        Raises:
            InvalidFeatureError: If bundle doesn't exist
            InsufficientXPError: If user doesn't have enough XP
            FeatureAlreadyOwnedError: If user already owns all features
        """
        if bundle_key not in PremiumFeatureStore.FEATURE_BUNDLES:
            raise InvalidFeatureError(f"Bundle '{bundle_key}' does not exist")
        
        bundle = PremiumFeatureStore.FEATURE_BUNDLES[bundle_key]
        
        # Check which features user doesn't own
        unowned_features = []
        for feature_key in bundle['features']:
            if not PremiumFeatureStore.user_owns_feature(user, feature_key):
                unowned_features.append(feature_key)
        
        if not unowned_features:
            raise FeatureAlreadyOwnedError("User already owns all features in this bundle")
        
        # Calculate actual cost (only for unowned features)
        actual_cost = sum(PremiumFeatureStore.FEATURES[f]['cost'] for f in unowned_features)
        bundle_discount = min(bundle['bundle_cost'], actual_cost)
        
        # Process XP transaction for bundle
        xp_transaction = XPTransactionManager.spend_xp(
            user=user,
            amount=bundle_discount,
            purpose='feature_purchase',
            description=f"Purchased bundle: {bundle['name']}",
            reference_obj=bundle_key
        )
        
        # Purchase individual features
        purchases = []
        for feature_key in unowned_features:
            feature = PremiumFeatureStore.FEATURES[feature_key]
            
            # Unlock feature
            setattr(user, feature['field_name'], True)
            
            # Record individual purchase (with bundle pricing)
            purchase = FeaturePurchase.objects.create(
                user=user,
                feature_name=feature_key,
                feature_display_name=feature['name'],
                xp_cost=0,  # Cost was handled by bundle transaction
                transaction=xp_transaction
            )
            purchases.append(purchase)
        
        user.save()
        return purchases
    
    @staticmethod
    def get_user_feature_summary(user):
        """
        Get comprehensive summary of user's feature ownership.
        
        Args:
            user: CustomUser instance
        
        Returns:
            Dictionary with detailed feature summary
        """
        summary = {
            'total_features': len(PremiumFeatureStore.FEATURES),
            'owned_features': 0,
            'total_spent': user.lifetime_xp_spent,
            'categories': {},
            'progression': {},
            'recommendations': PremiumFeatureStore.get_feature_recommendations(user)
        }
        
        # Analyze by category
        for key, feature in PremiumFeatureStore.FEATURES.items():
            category = feature['category']
            if category not in summary['categories']:
                summary['categories'][category] = {
                    'total': 0,
                    'owned': 0,
                    'features': []
                }
            
            summary['categories'][category]['total'] += 1
            is_owned = PremiumFeatureStore.user_owns_feature(user, key)
            
            if is_owned:
                summary['owned_features'] += 1
                summary['categories'][category]['owned'] += 1
            
            summary['categories'][category]['features'].append({
                'key': key,
                'name': feature['name'],
                'owned': is_owned,
                'cost': feature['cost']
            })
        
        # Calculate completion percentages
        for category in summary['categories']:
            cat_data = summary['categories'][category]
            cat_data['completion_percentage'] = (cat_data['owned'] / cat_data['total']) * 100
        
        # Chunking progression
        summary['progression']['chunking'] = PremiumFeatureStore.get_chunking_progression_status(user)
        
        # Overall completion
        summary['completion_percentage'] = (summary['owned_features'] / summary['total_features']) * 100
        
        return summary
    
    @staticmethod
    def update_pricing_tier(tier_name, new_price):
        """
        Update pricing tier for easy price adjustments.
        
        Args:
            tier_name: Name of pricing tier
            new_price: New price for the tier
        
        Returns:
            Boolean indicating success
        """
        if tier_name in PremiumFeatureStore.PRICING_TIERS:
            PremiumFeatureStore.PRICING_TIERS[tier_name] = new_price
            return True
        return False
    
    @staticmethod
    def get_pricing_analytics():
        """
        Get analytics about feature pricing and purchases.
        
        Returns:
            Dictionary with pricing analytics
        """
        analytics = {
            'pricing_tiers': PremiumFeatureStore.PRICING_TIERS.copy(),
            'feature_costs': {},
            'category_averages': {},
            'bundle_savings': {}
        }
        
        # Feature costs by category
        category_costs = {}
        for key, feature in PremiumFeatureStore.FEATURES.items():
            category = feature['category']
            if category not in category_costs:
                category_costs[category] = []
            category_costs[category].append(feature['cost'])
            analytics['feature_costs'][key] = feature['cost']
        
        # Calculate category averages
        for category, costs in category_costs.items():
            analytics['category_averages'][category] = {
                'average': sum(costs) / len(costs),
                'min': min(costs),
                'max': max(costs),
                'count': len(costs)
            }
        
        # Bundle savings analysis
        for bundle_key, bundle in PremiumFeatureStore.FEATURE_BUNDLES.items():
            analytics['bundle_savings'][bundle_key] = {
                'individual_cost': bundle['individual_cost'],
                'bundle_cost': bundle['bundle_cost'],
                'savings': bundle['savings'],
                'discount_percentage': (bundle['savings'] / bundle['individual_cost']) * 100
            }
        
        return analytics


class SocialInteractionManager:
    """
    Manages XP costs and rewards for social interactions.
    Handles comment posting, interactions, and author rewards.
    """
    
    # Social interaction costs
    INTERACTION_COSTS = {
        'comment_new': 10,      # New comment costs 10 XP
        'comment_reply': 5,     # Reply to comment costs 5 XP
        'interaction_bronze': 5,    # Bronze interaction costs 5 XP
        'interaction_silver': 15,   # Silver interaction costs 15 XP
        'interaction_gold': 30,     # Gold interaction costs 30 XP
        'interaction_report_troll': 0,   # Troll report (mild negative) - free
        'interaction_report_bad': 0,     # Bad report (moderate negative) - free
        'interaction_report_shit': 0     # Shit report (severe negative) - free
    }
    
    # Negative report tiers for community moderation
    NEGATIVE_REPORT_TIERS = {
        'REPORT_TROLL': {
            'name': 'Troll',
            'description': 'Mildly inappropriate or trolling behavior',
            'severity': 1,
            'icon': '😒',
            'color': '#FFA500'  # Orange
        },
        'REPORT_BAD': {
            'name': 'Bad',
            'description': 'Inappropriate content or behavior',
            'severity': 2,
            'icon': '😠',
            'color': '#FF6B35'  # Red-Orange
        },
        'REPORT_SHIT': {
            'name': 'Shit',
            'description': 'Severely inappropriate or offensive content',
            'severity': 3,
            'icon': '💩',
            'color': '#DC143C'  # Dark Red
        }
    }
    
    # Author reward percentage (50% of interaction cost)
    AUTHOR_REWARD_PERCENTAGE = 0.5
    
    @staticmethod
    @transaction.atomic
    def post_comment(user, article, content, parent_comment=None, is_perfect_score_free=False):
        """
        Handle comment posting with XP costs and validation.
        
        Args:
            user: CustomUser instance
            article: Article instance
            content: Comment content string
            parent_comment: Parent Comment instance (for replies)
            is_perfect_score_free: Boolean for perfect score free comment privilege
        
        Returns:
            Comment instance
        
        Raises:
            InsufficientXPError: If user doesn't have enough XP
        """
        # Determine XP cost
        if user.is_staff:
            # Admin users get free comments for testing
            xp_cost = 0
        elif is_perfect_score_free:
            xp_cost = 0
        elif parent_comment:
            xp_cost = SocialInteractionManager.INTERACTION_COSTS['comment_reply']
        else:
            xp_cost = SocialInteractionManager.INTERACTION_COSTS['comment_new']
        
        # Validate XP balance (unless free)
        if xp_cost > 0 and user.current_xp_points < xp_cost:
            raise InsufficientXPError(
                f"Need {xp_cost} XP to post comment. You have {user.current_xp_points} XP."
            )
        
        # Create comment
        comment = Comment.objects.create(
            user=user,
            article=article,
            content=content,
            parent_comment=parent_comment
        )
        
        # Process XP transaction (if cost > 0)
        if xp_cost > 0:
            comment_type = 'reply' if parent_comment else 'new comment'
            description = f"Posted {comment_type} on '{article.title}'"
            if is_perfect_score_free:
                description += " (Perfect score - FREE!)"
            
            XPTransactionManager.spend_xp(
                user=user,
                amount=xp_cost,
                purpose='comment_reply' if parent_comment else 'comment_post',
                description=description,
                reference_obj=comment
            )
        
        return comment
    
    @staticmethod
    @transaction.atomic
    def add_interaction(user, comment, interaction_type):
        """
        Handle comment interactions with XP costs and author rewards.
        
        Args:
            user: CustomUser instance (person giving interaction)
            comment: Comment instance
            interaction_type: String ('BRONZE', 'SILVER', 'GOLD', 'REPORT')
        
        Returns:
            CommentInteraction instance
        
        Raises:
            InsufficientXPError: If user doesn't have enough XP
        """
        from .models import CommentInteraction
        
        # Get XP cost for interaction
        cost_key = f"interaction_{interaction_type.lower()}"
        xp_cost = SocialInteractionManager.INTERACTION_COSTS.get(cost_key, 0)
        
        # Validate XP balance (unless free)
        if xp_cost > 0 and user.current_xp_points < xp_cost:
            raise InsufficientXPError(
                f"Need {xp_cost} XP for {interaction_type} interaction. You have {user.current_xp_points} XP."
            )
        
        # Check if user already interacted with this comment
        existing_interaction = CommentInteraction.objects.filter(
            user=user, comment=comment
        ).first()
        
        if existing_interaction:
            # Update existing interaction
            old_cost = SocialInteractionManager.INTERACTION_COSTS.get(
                f"interaction_{existing_interaction.interaction_type.lower()}", 0
            )
            
            # Refund old interaction cost
            if old_cost > 0:
                XPTransactionManager.earn_xp(
                    user=user,
                    amount=old_cost,
                    source='admin_adjustment',
                    description=f"Refund for changing {existing_interaction.interaction_type} to {interaction_type}",
                    reference_obj=comment
                )
            
            # Remove old author reward
            if old_cost > 0 and comment.user != user:
                old_reward = int(old_cost * SocialInteractionManager.AUTHOR_REWARD_PERCENTAGE)
                if old_reward > 0:
                    XPTransactionManager.spend_xp(
                        user=comment.user,
                        amount=old_reward,
                        purpose='admin_adjustment',
                        description="Removed reward for changed interaction",
                        reference_obj=comment
                    )
            
            # Update interaction
            existing_interaction.interaction_type = interaction_type
            existing_interaction.xp_cost = xp_cost
            existing_interaction.save()
            interaction = existing_interaction
        else:
            # Create new interaction
            interaction = CommentInteraction.objects.create(
                user=user,
                comment=comment,
                interaction_type=interaction_type,
                xp_cost=xp_cost
            )
        
        # Process XP transaction for new interaction (if cost > 0)
        if xp_cost > 0:
            # Charge user for interaction
            XPTransactionManager.spend_xp(
                user=user,
                amount=xp_cost,
                purpose=cost_key,
                description=f"Gave {interaction_type} interaction to comment by {comment.user.username}",
                reference_obj=comment
            )
            
            # Reward comment author (50% of cost, if not self-interaction)
            if comment.user != user:
                author_reward = int(xp_cost * SocialInteractionManager.AUTHOR_REWARD_PERCENTAGE)
                if author_reward > 0:
                    XPTransactionManager.earn_xp(
                        user=comment.user,
                        amount=author_reward,
                        source='interaction_reward',
                        description=f"Received {interaction_type} interaction reward from {user.username}",
                        reference_obj=comment
                    )
                    
                    # Create notification for author
                    SocialInteractionManager.create_interaction_notification(
                        comment.user, user, interaction_type, author_reward, comment
                    )
        
        return interaction
    
    @staticmethod
    def create_interaction_notification(author, giver, interaction_type, xp_reward, comment):
        """
        Create notification for comment author about interaction reward.
        
        Args:
            author: CustomUser instance (comment author)
            giver: CustomUser instance (person who gave interaction)
            interaction_type: String ('BRONZE', 'SILVER', 'GOLD')
            xp_reward: Integer XP amount rewarded
            comment: Comment instance
        """
        # This would integrate with a notification system
        # For now, we'll create a simple notification record
        
        notification_data = {
            'type': 'interaction_reward',
            'message': f"Hey! Someone liked what you wrote! {giver.username} gave your comment a {interaction_type} interaction.",
            'xp_reward': xp_reward,
            'interaction_type': interaction_type,
            'giver': giver.username,
            'comment_preview': comment.content[:100] + '...' if len(comment.content) > 100 else comment.content,
            'article_title': comment.article.title
        }
        
        # TODO: Integrate with actual notification system
        # For now, this could be stored in a Notification model or sent via email
        print(f"NOTIFICATION for {author.username}: {notification_data['message']} (+{xp_reward} XP)")
        
        return notification_data
    
    @staticmethod
    def get_user_interaction_summary(user):
        """
        Get summary of user's social interaction activity.
        
        Args:
            user: CustomUser instance
        
        Returns:
            Dictionary with interaction statistics
        """
        from .models import CommentInteraction, Comment
        
        # Comments posted by user
        comments_posted = Comment.objects.filter(user=user).count()
        
        # Interactions given by user
        interactions_given = CommentInteraction.objects.filter(user=user).exclude(
            interaction_type='REPORT'
        ).count()
        
        # Interactions received on user's comments
        user_comments = Comment.objects.filter(user=user)
        interactions_received = CommentInteraction.objects.filter(
            comment__in=user_comments
        ).exclude(interaction_type='REPORT').count()
        
        # XP spent on social interactions
        social_transactions = XPTransaction.objects.filter(
            user=user,
            source__in=['comment_post', 'comment_reply', 'interaction_bronze', 
                       'interaction_silver', 'interaction_gold']
        )
        xp_spent_social = sum(abs(t.amount) for t in social_transactions)
        
        # XP earned from interaction rewards
        reward_transactions = XPTransaction.objects.filter(
            user=user,
            source='interaction_reward'
        )
        xp_earned_rewards = sum(t.amount for t in reward_transactions)
        
        return {
            'comments_posted': comments_posted,
            'interactions_given': interactions_given,
            'interactions_received': interactions_received,
            'xp_spent_on_social': xp_spent_social,
            'xp_earned_from_rewards': xp_earned_rewards,
            'net_social_xp': xp_earned_rewards - xp_spent_social,
            'interaction_ratio': interactions_received / max(interactions_given, 1)
        }
    
    @staticmethod
    def can_user_afford_interaction(user, interaction_type):
        """
        Check if user can afford a specific interaction.
        
        Args:
            user: CustomUser instance
            interaction_type: String ('BRONZE', 'SILVER', 'GOLD', 'REPORT')
        
        Returns:
            Tuple (can_afford: bool, cost: int, current_balance: int)
        """
        cost_key = f"interaction_{interaction_type.lower()}"
        cost = SocialInteractionManager.INTERACTION_COSTS.get(cost_key, 0)
        can_afford = user.current_xp_points >= cost
        
        return can_afford, cost, user.current_xp_points
    
    @staticmethod
    def can_user_afford_comment(user, is_reply=False, is_perfect_score_free=False):
        """
        Check if user can afford to post a comment.
        
        Args:
            user: CustomUser instance
            is_reply: Boolean indicating if this is a reply
            is_perfect_score_free: Boolean for perfect score privilege
        
        Returns:
            Tuple (can_afford: bool, cost: int, current_balance: int)
        """
        if is_perfect_score_free:
            cost = 0
        elif is_reply:
            cost = SocialInteractionManager.INTERACTION_COSTS['comment_reply']
        else:
            cost = SocialInteractionManager.INTERACTION_COSTS['comment_new']
        
        can_afford = user.current_xp_points >= cost
        return can_afford, cost, user.current_xp_points
    
    @staticmethod
    def get_interaction_costs():
        """
        Get current interaction costs for UI display.
        
        Returns:
            Dictionary with interaction costs
        """
        return SocialInteractionManager.INTERACTION_COSTS.copy()
    
    @staticmethod
    def update_interaction_cost(interaction_type, new_cost):
        """
        Update interaction cost for easy price adjustments.
        
        Args:
            interaction_type: String key from INTERACTION_COSTS
            new_cost: New cost in XP
        
        Returns:
            Boolean indicating success
        """
        if interaction_type in SocialInteractionManager.INTERACTION_COSTS:
            SocialInteractionManager.INTERACTION_COSTS[interaction_type] = new_cost
            return True
        return False