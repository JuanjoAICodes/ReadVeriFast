"""
Comprehensive Test Suite for Enhanced XP Economics System

This module contains comprehensive tests for all XP system components.
"""


from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache

from .models import (
    Article, QuizAttempt, Comment, XPTransaction
)
from .xp_system import (
    XPCalculationEngine, XPTransactionManager, PremiumFeatureStore,
    XPValidationManager, XPCacheManager,
    InsufficientXPError, InvalidFeatureError, FeatureAlreadyOwnedError
)

User = get_user_model()


class XPCalculationEngineTestCase(TestCase):
    """Test XP calculation engine with various scenarios"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            current_wpm=250,
            max_wpm=300
        )
        
        self.article = Article.objects.create(
            title='Test Article',
            content='This is a test article with exactly ten words here.',
            reading_level=8.5,
            processing_status='complete'
        )
    
    def test_basic_xp_calculation(self):
        """Test basic XP calculation for quiz completion"""
        quiz_attempt = QuizAttempt.objects.create(
            user=self.user,
            article=self.article,
            score=85.0,
            wpm_used=250,
            xp_awarded=0
        )
        
        xp_earned = XPCalculationEngine.calculate_quiz_xp(quiz_attempt, self.article, self.user)
        
        # Should be positive XP for passing score
        self.assertGreater(xp_earned, 0)
        self.assertIsInstance(xp_earned, int)
    
    def test_perfect_score_bonus(self):
        """Test perfect score bonus calculation"""
        quiz_attempt = QuizAttempt.objects.create(
            user=self.user,
            article=self.article,
            score=100.0,
            wpm_used=250,
            xp_awarded=0
        )
        
        xp_earned = XPCalculationEngine.calculate_quiz_xp(quiz_attempt, self.article, self.user)
        has_privilege = XPCalculationEngine.has_perfect_score_privilege(quiz_attempt)
        
        self.assertGreater(xp_earned, 0)
        self.assertTrue(has_privilege)
    
    def test_failing_score_no_xp(self):
        """Test that failing scores earn no XP"""
        quiz_attempt = QuizAttempt.objects.create(
            user=self.user,
            article=self.article,
            score=45.0,
            wpm_used=250,
            xp_awarded=0
        )
        
        xp_earned = XPCalculationEngine.calculate_quiz_xp(quiz_attempt, self.article, self.user)
        
        self.assertEqual(xp_earned, 0)


class XPTransactionManagerTestCase(TestCase):
    """Test XP transaction management"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            current_xp_points=100
        )
    
    def test_earn_xp_transaction(self):
        """Test earning XP creates proper transaction"""
        initial_total = self.user.total_xp
        initial_spendable = self.user.current_xp_points
        
        transaction_obj = XPTransactionManager.earn_xp(
            user=self.user,
            amount=50,
            source='quiz_completion',
            description='Test quiz completion'
        )
        
        self.user.refresh_from_db()
        
        # Check XP balances updated
        self.assertEqual(self.user.total_xp, initial_total + 50)
        self.assertEqual(self.user.current_xp_points, initial_spendable + 50)
        
        # Check transaction created
        self.assertIsNotNone(transaction_obj)
        self.assertEqual(transaction_obj.transaction_type, 'EARN')
        self.assertEqual(transaction_obj.amount, 50)
    
    def test_spend_xp_transaction(self):
        """Test spending XP creates proper transaction"""
        initial_total = self.user.total_xp
        initial_spendable = self.user.current_xp_points
        
        transaction_obj = XPTransactionManager.spend_xp(
            user=self.user,
            amount=30,
            purpose='comment_post',
            description='Posted comment'
        )
        
        self.user.refresh_from_db()
        
        # Check only spendable XP reduced
        self.assertEqual(self.user.total_xp, initial_total)  # Unchanged
        self.assertEqual(self.user.current_xp_points, initial_spendable - 30)
        
        # Check transaction created
        self.assertIsNotNone(transaction_obj)
        self.assertEqual(transaction_obj.transaction_type, 'SPEND')
        self.assertEqual(transaction_obj.amount, -30)
    
    def test_insufficient_xp_error(self):
        """Test error when user has insufficient XP"""
        with self.assertRaises(InsufficientXPError):
            XPTransactionManager.spend_xp(
                user=self.user,
                amount=200,  # More than user has
                purpose='feature_purchase',
                description='Attempted expensive purchase'
            )


class PremiumFeatureStoreTestCase(TestCase):
    """Test premium feature store functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            current_xp_points=200
        )
    
    def test_feature_purchase_success(self):
        """Test successful feature purchase"""
        initial_balance = self.user.current_xp_points
        feature_cost = PremiumFeatureStore.FEATURES['font_opensans']['cost']
        
        # Purchase feature
        result = PremiumFeatureStore.purchase_feature(self.user, 'font_opensans')
        
        self.assertTrue(result)
        
        # Check user has feature
        self.user.refresh_from_db()
        self.assertTrue(self.user.has_font_opensans)
        
        # Check XP deducted
        self.assertEqual(self.user.current_xp_points, initial_balance - feature_cost)
    
    def test_insufficient_xp_for_purchase(self):
        """Test purchase failure with insufficient XP"""
        # Set user to have very little XP
        self.user.current_xp_points = 10
        self.user.save()
        
        with self.assertRaises(InsufficientXPError):
            PremiumFeatureStore.purchase_feature(self.user, 'font_opensans')
    
    def test_invalid_feature_purchase(self):
        """Test purchase of non-existent feature"""
        with self.assertRaises(InvalidFeatureError):
            PremiumFeatureStore.purchase_feature(self.user, 'nonexistent_feature')
    
    def test_already_owned_feature_purchase(self):
        """Test purchase of already owned feature"""
        # First purchase
        PremiumFeatureStore.purchase_feature(self.user, 'font_opensans')
        
        # Attempt second purchase
        with self.assertRaises(FeatureAlreadyOwnedError):
            PremiumFeatureStore.purchase_feature(self.user, 'font_opensans')


class XPValidationManagerTestCase(TestCase):
    """Test XP validation and security"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            current_xp_points=100
        )
    
    def test_basic_validation(self):
        """Test basic XP transaction validation"""
        # Valid transaction should pass
        XPValidationManager.validate_xp_transaction(self.user, 50, 'EARN')
        XPValidationManager.validate_xp_transaction(self.user, 30, 'SPEND')
        
        # Invalid amounts should fail
        with self.assertRaises(Exception):  # XPValidationError or similar
            XPValidationManager.validate_xp_transaction(self.user, 0, 'EARN')
    
    def test_insufficient_balance_validation(self):
        """Test validation of insufficient balance"""
        with self.assertRaises(InsufficientXPError):
            XPValidationManager.validate_xp_transaction(self.user, 200, 'SPEND')


class XPCacheManagerTestCase(TestCase):
    """Test XP caching functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            current_xp_points=100,
            has_font_opensans=True
        )
        
        # Clear cache before each test
        cache.clear()
    
    def test_user_features_caching(self):
        """Test caching of user feature ownership"""
        # Should not be cached initially
        cached_features = XPCacheManager.get_cached_user_features(self.user.id)
        self.assertIsNone(cached_features)
        
        # Cache features
        features = XPCacheManager.cache_user_features(self.user)
        self.assertIsNotNone(features)
        
        # Should now be cached
        cached_features = XPCacheManager.get_cached_user_features(self.user.id)
        self.assertIsNotNone(cached_features)
    
    def test_cache_invalidation(self):
        """Test cache invalidation after changes"""
        # Cache user features
        XPCacheManager.cache_user_features(self.user)
        
        # Verify cached
        cached_features = XPCacheManager.get_cached_user_features(self.user.id)
        self.assertIsNotNone(cached_features)
        
        # Invalidate cache
        XPCacheManager.invalidate_user_features_cache(self.user.id)
        
        # Should no longer be cached
        cached_features = XPCacheManager.get_cached_user_features(self.user.id)
        self.assertIsNone(cached_features)


class EndToEndXPJourneyTestCase(TestCase):
    """Test complete end-to-end XP user journey"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='journeyuser',
            email='journey@example.com',
            current_wpm=200,
            max_wpm=225
        )
        
        self.article = Article.objects.create(
            title='Journey Article',
            content='This is a comprehensive test article for the user journey.',
            reading_level=8.0,
            processing_status='complete'
        )
    
    def test_complete_user_journey(self):
        """Test complete user XP journey from quiz to feature purchase"""
        # Step 1: User takes quiz and earns XP
        quiz_attempt = QuizAttempt.objects.create(
            user=self.user,
            article=self.article,
            score=85.0,
            wpm_used=200,
            xp_awarded=0
        )
        
        xp_earned = XPCalculationEngine.calculate_quiz_xp(quiz_attempt, self.article, self.user)
        XPTransactionManager.earn_xp(
            user=self.user,
            amount=xp_earned,
            source='quiz_completion',
            description=f'Quiz completed with {quiz_attempt.score}%',
            reference_obj=quiz_attempt
        )
        
        self.user.refresh_from_db()
        initial_xp = self.user.current_xp_points
        self.assertGreater(initial_xp, 0)
        
        # Step 2: User posts a comment (costs XP)
        comment_cost = 10
        comment = Comment.objects.create(
            user=self.user,
            article=self.article,
            content='Great article!'
        )
        
        XPTransactionManager.spend_xp(
            user=self.user,
            amount=comment_cost,
            purpose='comment_post',
            description='Posted comment',
            reference_obj=comment
        )
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.current_xp_points, initial_xp - comment_cost)
        
        # Step 3: Verify transaction history
        transactions = XPTransaction.objects.filter(user=self.user)
        self.assertGreaterEqual(transactions.count(), 2)  # At least 1 earning + 1 spending