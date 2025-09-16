"""
Test suite for the XP System
Tests XP earning, spending, validation, and related functionality
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

from .models import Article, QuizAttempt, XPTransaction
from .xp_system import XPCalculationEngine, XPTransactionManager, XPValidationManager

User = get_user_model()


class XPCalculationEngineTestCase(TestCase):
    """Test XP calculation logic"""
    
    def setUp(self):
        self.engine = XPCalculationEngine()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.article = Article.objects.create(
            title='Test Article',
            content='Test content for XP calculation',
            processing_status='complete'
        )
    
    def test_quiz_xp_calculation(self):
        """Test XP calculation for quiz attempts"""
        quiz_attempt = QuizAttempt.objects.create(
            user=self.user,
            article=self.article,
            score=85.0,
            wpm_used=200,
            xp_awarded=0
        )
        
        xp_earned = self.engine.calculate_quiz_xp(quiz_attempt, self.article, self.user)
        
        # Should earn XP based on score and WPM
        self.assertGreater(xp_earned, 0)
        self.assertIsInstance(xp_earned, int)
    
    def test_perfect_score_bonus(self):
        """Test bonus XP for perfect quiz scores"""
        perfect_attempt = QuizAttempt.objects.create(
            user=self.user,
            article=self.article,
            score=100.0,
            wpm_used=250,
            xp_awarded=0
        )
        
        regular_attempt = QuizAttempt.objects.create(
            user=self.user,
            article=self.article,
            score=85.0,
            wpm_used=250,
            xp_awarded=0
        )
        
        perfect_xp = self.engine.calculate_quiz_xp(perfect_attempt, self.article, self.user)
        regular_xp = self.engine.calculate_quiz_xp(regular_attempt, self.article, self.user)
        
        # Perfect score should earn more XP
        self.assertGreater(perfect_xp, regular_xp)


class XPTransactionManagerTestCase(TestCase):
    """Test XP transaction management"""
    
    def setUp(self):
        self.manager = XPTransactionManager()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            current_xp_points=100
        )
    
    def test_earn_xp(self):
        """Test earning XP"""
        initial_xp = self.user.current_xp_points
        
        result = self.manager.earn_xp(
            user=self.user,
            amount=50,
            source='test',
            description='Test XP earning'
        )
        
        self.user.refresh_from_db()
        
        self.assertIsNotNone(result)
        self.assertEqual(self.user.current_xp_points, initial_xp + 50)
    
    def test_spend_xp_success(self):
        """Test successful XP spending"""
        initial_xp = self.user.current_xp_points
        
        result = self.manager.spend_xp(
            user=self.user,
            amount=30,
            purpose='test',
            description='Test XP spending'
        )
        
        self.user.refresh_from_db()
        
        self.assertIsNotNone(result)
        self.assertEqual(self.user.current_xp_points, initial_xp - 30)
    
    def test_spend_xp_insufficient_balance(self):
        """Test XP spending with insufficient balance"""
        # Try to spend more than available
        result = self.manager.spend_xp(
            user=self.user,
            amount=200,  # More than the 100 XP available
            purpose='test',
            description='Test insufficient XP'
        )
        
        # Should fail and return None
        self.assertIsNone(result)
        
        # User balance should remain unchanged
        self.user.refresh_from_db()
        self.assertEqual(self.user.current_xp_points, 100)


class XPValidationManagerTestCase(TestCase):
    """Test XP validation and security"""
    
    def setUp(self):
        self.validator = XPValidationManager()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            current_xp_points=100
        )
    
    def test_validate_transaction_valid(self):
        """Test validation of valid XP transaction"""
        transaction = XPTransaction.objects.create(
            user=self.user,
            amount=50,
            transaction_type='EARN',
            source='test',
            description='Valid test transaction',
            balance_after=150
        )
        
        is_valid = self.validator.validate_xp_transaction(transaction)
        self.assertTrue(is_valid)
    
    def test_validate_transaction_invalid_amount(self):
        """Test validation of transaction with invalid amount"""
        transaction = XPTransaction.objects.create(
            user=self.user,
            amount=-10,  # Negative amount for EARN transaction
            transaction_type='EARN',
            source='test',
            description='Invalid test transaction',
            balance_after=90
        )
        
        is_valid = self.validator.validate_xp_transaction(transaction)
        self.assertFalse(is_valid)


class XPSystemIntegrationTestCase(TestCase):
    """Test end-to-end XP system functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            current_xp_points=0
        )
        self.article = Article.objects.create(
            title='Integration Test Article',
            content='Content for integration testing',
            processing_status='complete'
        )
    
    def test_complete_quiz_journey(self):
        """Test complete user journey from quiz to XP earning"""
        # User takes a quiz
        quiz_attempt = QuizAttempt.objects.create(
            user=self.user,
            article=self.article,
            score=90.0,
            wpm_used=220,
            xp_awarded=0
        )
        
        # Calculate and award XP
        engine = XPCalculationEngine()
        manager = XPTransactionManager()
        
        xp_earned = engine.calculate_quiz_xp(quiz_attempt, self.article, self.user)
        transaction = manager.earn_xp(
            user=self.user,
            amount=xp_earned,
            source='quiz_completion',
            transaction_type='EARN',
            description=f'Quiz completed with {quiz_attempt.score}% score',
            reference_obj=quiz_attempt
        )
        
        # Verify results
        self.user.refresh_from_db()
        self.assertGreater(self.user.current_xp_points, 0)
        self.assertIsNotNone(transaction)
        
        # Verify transaction was recorded
        transactions = XPTransaction.objects.filter(user=self.user)
        self.assertEqual(transactions.count(), 1)
        self.assertEqual(transactions.first().amount, xp_earned)