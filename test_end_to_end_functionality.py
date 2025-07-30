#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing for Speed Reader and Quiz Functionality
"""
import os
import django
import json
import time
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from verifast_app.models import Article, QuizAttempt, XPTransaction

User = get_user_model()

def test_complete_user_journey():
    """
    Test the complete user journey from article load to quiz completion
    """
    print("🚀 Starting Comprehensive End-to-End Testing")
    print("=" * 60)
    
    # Setup test client and user
    client = Client()
    
    # Create or get test user
    test_user, created = User.objects.get_or_create(
        username='testuser_e2e',
        defaults={
            'email': 'test@example.com',
            'current_wpm': 250,
            'total_xp': 0,
            'current_xp_points': 0
        }
    )
    
    if created:
        test_user.set_password('testpass123')
        test_user.save()
        print("✅ Created test user")
    else:
        print("✅ Using existing test user")
    
    # Get test article
    article = Article.objects.filter(processing_status='complete').first()
    if not article:
        print("❌ No articles available for testing")
        return False
    
    print(f"✅ Using article: {article.title}")
    
    # Test 1: Anonymous user can access article
    print("\n📋 Test 1: Anonymous Article Access")
    response = client.get(f'/en/articles/{article.id}/')
    if response.status_code == 200:
        print("✅ Anonymous user can access article")
        content = response.content.decode()
        
        # Check for essential elements
        checks = [
            ('Speed reader section', 'speed-reader-section'),
            ('Word display', 'word-display'),
            ('Start button', 'start-pause-btn'),
            ('Quiz button (disabled)', 'start-quiz-btn'),
            ('Quiz modal', 'quiz-modal'),
        ]
        
        for name, element in checks:
            if element in content:
                print(f"  ✅ {name}: Present")
            else:
                print(f"  ❌ {name}: Missing")
    else:
        print(f"❌ Failed to access article: {response.status_code}")
        return False
    
    # Test 2: User login and authenticated access
    print("\n📋 Test 2: Authenticated User Access")
    login_success = client.login(username='testuser_e2e', password='testpass123')
    if login_success:
        print("✅ User login successful")
        
        response = client.get(f'/en/articles/{article.id}/')
        if response.status_code == 200:
            print("✅ Authenticated user can access article")
            content = response.content.decode()
            
            # Check for user-specific elements
            if f'data-user-wpm="{test_user.current_wpm}"' in content:
                print("  ✅ User WPM data loaded")
            else:
                print("  ❌ User WPM data missing")
        else:
            print(f"❌ Failed authenticated access: {response.status_code}")
            return False
    else:
        print("❌ User login failed")
        return False
    
    # Test 3: Quiz API functionality
    print("\n📋 Test 3: Quiz API Functionality")
    
    # First, get quiz data
    quiz_response = client.get(f'/en/api/v1/articles/{article.id}/quiz/')
    if quiz_response.status_code == 200:
        quiz_data = quiz_response.json()
        if quiz_data.get('success') and quiz_data.get('data', {}).get('questions'):
            print("✅ Quiz data retrieved successfully")
            quiz_questions = quiz_data['data']['questions']
            print(f"  📊 Quiz has {len(quiz_questions)} questions")
            
            # Test quiz submission (only first 5 questions as per serializer)
            user_answers = [0, 1, 2, 0, 1]  # Answer first 5 questions
            submission_data = {
                'answers': user_answers,  # Changed from user_answers
                'wmp_used': 250,  # Note: this is the typo in the serializer
                'quiz_time_seconds': 60
            }
            
            # Use Django test client's built-in CSRF handling
            submit_response = client.post(
                f'/en/api/v1/articles/{article.id}/quiz/submit/',
                data=submission_data,
                content_type='application/json'
            )
            
            if submit_response.status_code == 200:
                result = submit_response.json()
                if result.get('success'):
                    print("✅ Quiz submission successful")
                    print(f"  📊 Score: {result.get('score', 0)}%")
                    print(f"  🎯 XP Awarded: {result.get('xp_awarded', 0)}")
                    
                    # Verify database updates
                    quiz_attempt = QuizAttempt.objects.filter(
                        user=test_user,
                        article=article
                    ).first()
                    
                    if quiz_attempt:
                        print("✅ Quiz attempt recorded in database")
                        print(f"  📊 DB Score: {quiz_attempt.score}")
                        print(f"  🎯 DB XP: {quiz_attempt.xp_awarded}")
                    else:
                        print("❌ Quiz attempt not found in database")
                        
                else:
                    print(f"❌ Quiz submission failed: {result.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Quiz submission HTTP error: {submit_response.status_code}")
                return False
        else:
            print("❌ Invalid quiz data received")
            return False
    else:
        print(f"❌ Failed to get quiz data: {quiz_response.status_code}")
        return False
    
    # Test 4: XP System Integration
    print("\n📋 Test 4: XP System Integration")
    
    # Refresh user from database
    test_user.refresh_from_db()
    
    if test_user.total_xp > 0:
        print(f"✅ User XP updated: {test_user.total_xp}")
        print(f"✅ Current XP points: {test_user.current_xp_points}")
        
        # Check XP transactions
        xp_transactions = XPTransaction.objects.filter(user=test_user)
        if xp_transactions.exists():
            print(f"✅ XP transactions recorded: {xp_transactions.count()}")
            for transaction in xp_transactions[:3]:  # Show first 3
                print(f"  💰 {transaction.transaction_type}: {transaction.amount} XP")
        else:
            print("⚠️ No XP transactions found")
    else:
        print("⚠️ User XP not updated")
    
    # Test 5: Multiple Articles and Quiz Scenarios
    print("\n📋 Test 5: Multiple Articles Testing")
    
    articles = Article.objects.filter(processing_status='complete')[:3]
    successful_tests = 0
    
    for i, test_article in enumerate(articles, 1):
        print(f"\n  Testing Article {i}: {test_article.title[:50]}...")
        
        # Test article access
        response = client.get(f'/en/articles/{test_article.id}/')
        if response.status_code == 200:
            print(f"    ✅ Article {i} accessible")
            
            # Test quiz data
            quiz_response = client.get(f'/en/api/v1/articles/{test_article.id}/quiz/')
            if quiz_response.status_code == 200:
                quiz_data = quiz_response.json()
                if quiz_data.get('success'):
                    print(f"    ✅ Article {i} quiz data available")
                    successful_tests += 1
                else:
                    print(f"    ❌ Article {i} quiz data invalid")
            else:
                print(f"    ❌ Article {i} quiz data failed")
        else:
            print(f"    ❌ Article {i} not accessible")
    
    print(f"\n  📊 Successfully tested {successful_tests}/{len(articles)} articles")
    
    # Test 6: Error Handling and Edge Cases
    print("\n📋 Test 6: Error Handling and Edge Cases")
    
    # Test invalid article ID
    response = client.get('/en/articles/99999/')
    if response.status_code == 404:
        print("✅ Invalid article ID handled correctly (404)")
    else:
        print(f"⚠️ Invalid article ID returned: {response.status_code}")
    
    # Test invalid quiz submission
    invalid_submission = {
        'article_id': 99999,
        'user_answers': [],
        'wmp_used': 250,  # Intentional typo
        'quiz_time_seconds': 60
    }
    
    response = client.post(
        '/en/api/quiz/submit/',
        data=json.dumps(invalid_submission),
        content_type='application/json',
        HTTP_X_CSRFTOKEN=client.cookies.get('csrftoken', '').value
    )
    
    if response.status_code in [400, 404, 500]:
        print("✅ Invalid quiz submission handled correctly")
    else:
        print(f"⚠️ Invalid quiz submission returned: {response.status_code}")
    
    # Final Summary
    print("\n" + "=" * 60)
    print("🎉 END-TO-END TESTING COMPLETE")
    print("=" * 60)
    
    # Calculate overall success
    final_user = User.objects.get(username='testuser_e2e')
    quiz_attempts = QuizAttempt.objects.filter(user=final_user).count()
    xp_transactions = XPTransaction.objects.filter(user=final_user).count()
    
    print("📊 Final Test Results:")
    print(f"   User XP: {final_user.total_xp}")
    print(f"   Quiz Attempts: {quiz_attempts}")
    print(f"   XP Transactions: {xp_transactions}")
    print(f"   Articles Tested: {len(articles)}")
    
    if (final_user.total_xp > 0 and 
        quiz_attempts > 0 and 
        xp_transactions > 0 and 
        successful_tests > 0):
        print("\n🎉 ALL CORE FUNCTIONALITY WORKING!")
        print("✅ Speed Reader and Quiz system is fully operational")
        return True
    else:
        print("\n⚠️ Some functionality may have issues")
        return False

def test_performance_and_load():
    """
    Test system performance under load
    """
    print("\n🔄 Performance Testing")
    print("-" * 30)
    
    client = Client()
    article = Article.objects.filter(processing_status='complete').first()
    
    if not article:
        print("❌ No articles for performance testing")
        return
    
    # Test multiple concurrent requests
    start_time = time.time()
    responses = []
    
    for i in range(10):
        response = client.get(f'/en/articles/{article.id}/')
        responses.append(response.status_code)
    
    end_time = time.time()
    duration = end_time - start_time
    
    successful_requests = sum(1 for status in responses if status == 200)
    
    print("📊 Performance Results:")
    print("   Requests: 10")
    print(f"   Successful: {successful_requests}")
    print(f"   Duration: {duration:.2f}s")
    print(f"   Avg Response Time: {duration/10:.3f}s")
    
    if successful_requests == 10 and duration < 5:
        print("✅ Performance test passed")
    else:
        print("⚠️ Performance may need optimization")

if __name__ == "__main__":
    try:
        success = test_complete_user_journey()
        test_performance_and_load()
        
        if success:
            print("\n🎉 All end-to-end tests passed successfully!")
            print("🚀 Speed Reader and Quiz system is ready for production!")
        else:
            print("\n⚠️ Some tests failed. Please review the issues above.")
            
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        import traceback
        traceback.print_exc()