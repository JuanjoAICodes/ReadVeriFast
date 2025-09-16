#!/usr/bin/env python3
"""
Test script to verify quiz API functionality
"""
import json
from django.test import Client
from django.contrib.auth import get_user_model
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from verifast_app.models import Article

def test_quiz_api():
    """Test the quiz API endpoint"""
    print("🧪 Testing Quiz API Functionality")
    print("=" * 50)
    
    try:
        # Get or create a test user
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'current_wpm': 250,
                'total_xp': 100,
                'current_xp_points': 50
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print("✅ Created test user")
        else:
            print("✅ Using existing test user")
        
        # Get an article with quiz data
        article = Article.objects.filter(
            processing_status='complete',
            quiz_data__isnull=False
        ).first()
        
        if not article:
            print("❌ No articles with quiz data found")
            return False
        
        print(f"✅ Found article: {article.title}")
        print(f"✅ Quiz data length: {len(str(article.quiz_data))}")
        
        # Create a Django test client
        client = Client()
        
        # Login the test user
        login_success = client.login(username='testuser', password='testpass123')
        if not login_success:
            print("❌ Failed to login test user")
            return False
        
        print("✅ Test user logged in successfully")
        
        # Prepare quiz submission data for HTMX/JSON API
        quiz_data = {
            'article_id': article.id,
            'user_answers': [0, 1, 0, 2, 1],
            'wpm_used': 300,
            'quiz_time_seconds': 45
        }
        
        print("✅ Prepared quiz submission data")
        
        # Submit quiz via API (same endpoint used by HTMX form)
        response = client.post(
            '/en/api/quiz/submit/',
            data=json.dumps(quiz_data),
            content_type='application/json'
        )
        
        print(f"✅ API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Quiz API Response:")
            print(f"   Success: {result.get('success')}")
            print(f"   Score: {result.get('score')}%")
            print(f"   XP Earned: {result.get('xp_earned')}")
            print(f"   Result Type: {result.get('result_type')}")
            print(f"   New XP Balance: {result.get('new_xp_balance')}")
            
            if result.get('success'):
                print("\n🎉 Quiz API is working correctly!")
                return True
            else:
                print(f"❌ Quiz API returned success=False: {result.get('error')}")
                return False
        else:
            print(f"❌ Quiz API returned status {response.status_code}")
            print(f"Response: {response.content.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing quiz API: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quiz_interface_elements():
    """Test if quiz interface elements are present in the HTML"""
    print("\n🔍 Testing Quiz Interface Elements")
    print("=" * 50)
    
    try:
        client = Client()
        
        # Get an article page
        article = Article.objects.filter(processing_status='complete').first()
        if not article:
            print("❌ No articles found")
            return False
        
        response = client.get(f'/en/articles/{article.id}/')
        
        if response.status_code != 200:
            print(f"❌ Failed to load article page: {response.status_code}")
            return False
        
        html_content = response.content.decode()
        
        # Check for essential quiz elements
        checks = [
            ('Quiz button', 'id="start-quiz-btn"'),
            ('Start Quiz button', 'id="start-quiz-btn"'),
            ('Quiz section', 'id="quiz-section"'),
            ('Quiz container', 'id="quiz-container"'),
            ('Speed reader section', 'id="speed-reader-section"'),
            ('HTMX quiz start hook', 'hx-get=\"/en/quiz/start/'),
        ]
        
        all_passed = True
        for name, pattern in checks:
            if pattern in html_content:
                print(f"✅ {name} found")
            else:
                print(f"❌ {name} missing")
                all_passed = False
        
        if all_passed:
            print("\n🎉 All quiz interface elements are present!")
            return True
        else:
            print("\n❌ Some quiz interface elements are missing")
            return False
            
    except Exception as e:
        print(f"❌ Error testing quiz interface: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Quiz Functionality Tests")
    print("=" * 60)
    
    # Test quiz interface elements
    interface_test = test_quiz_interface_elements()
    
    # Test quiz API
    api_test = test_quiz_api()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   Quiz Interface Elements: {'✅ PASS' if interface_test else '❌ FAIL'}")
    print(f"   Quiz API Functionality: {'✅ PASS' if api_test else '❌ FAIL'}")
    
    if interface_test and api_test:
        print("\n🎉 All tests passed! Quiz functionality is working correctly.")
        print("\n📝 Manual testing steps:")
        print("   1. Visit http://localhost:8000/en/articles/1/")
        print("   2. Complete the speed reader (or skip to end)")
        print("   3. Click 'Start Quiz' button")
        print("   4. Answer questions and submit")
        print("   5. Check for XP rewards and score display")
    else:
        print("\n❌ Some tests failed. Please check the issues above.")