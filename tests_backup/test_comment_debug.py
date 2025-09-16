#!/usr/bin/env python
"""Debug script to test comment form functionality."""
import os

# Setup Django before importing Django modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import Client
from verifast_app.models import CustomUser

def test_comment_form():
    # Create a test client
    client = Client()
    
    # Test as anonymous user first
    print("=== ANONYMOUS USER TEST ===")
    response = client.get('/en/articles/4/', HTTP_HOST='localhost:8000')
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        print("✅ Page loaded successfully")
        
        # Check for comment section
        if 'comments-section' in content:
            print("✅ Comments section found")
        else:
            print("❌ Comments section NOT found")
            
        # Check for comment form
        if 'add-comment-form' in content:
            print("✅ Add comment form found")
        else:
            print("❌ Add comment form NOT found")
            
        # Check for locked message
        if 'Complete the quiz' in content:
            print("✅ Quiz completion message found")
        else:
            print("❌ Quiz completion message NOT found")
    else:
        print(f"❌ Page failed to load: {response.status_code}")
    
    print("\n=== AUTHENTICATED USER TEST ===")
    # Login as testuser
    try:
        user = CustomUser.objects.get(username='testuser')
        client.force_login(user)
        print(f"✅ Logged in as {user.username}")
        
        response = client.get('/en/articles/4/', HTTP_HOST='localhost:8000')
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            print("✅ Page loaded successfully")
            
            # Check context
            context = response.context
            if context:
                print("✅ Context available")
                print(f"   user_can_comment: {context.get('user_can_comment')}")
                print(f"   user_has_completed_quiz: {context.get('user_has_completed_quiz')}")
                print(f"   user authenticated: {context.get('user').is_authenticated}")
            
            # Check for textarea (comment input)
            if '<textarea' in content:
                print("✅ Comment textarea found")
            else:
                print("❌ Comment textarea NOT found")
                
            # Check for comment form
            if 'Share your thoughts' in content:
                print("✅ Comment placeholder found")
            else:
                print("❌ Comment placeholder NOT found")
                
        else:
            print(f"❌ Page failed to load: {response.status_code}")
            
    except CustomUser.DoesNotExist:
        print("❌ testuser does not exist")

if __name__ == '__main__':
    test_comment_form()