#!/usr/bin/env python3
"""
Simple test script to verify quiz functionality is working
"""
import requests

def test_quiz_functionality():
    """Test if quiz functionality is properly loaded"""
    try:
        # Get the article page
        response = requests.get('http://localhost:8000/articles/4/')
        if response.status_code != 200:
            print(f"❌ Failed to load article page: {response.status_code}")
            return False
        
        html_content = response.text
        
        # Check if quiz button exists
        if 'id="start-quiz-btn"' in html_content:
            print("✅ Quiz button found in HTML")
        else:
            print("❌ Quiz button not found in HTML")
            return False
        
        # Check if quiz overlay exists
        if 'id="quiz-overlay"' in html_content:
            print("✅ Quiz overlay found in HTML")
        else:
            print("❌ Quiz overlay not found in HTML")
            return False
        
        # Check if quiz data is loaded
        if 'quizDataRaw' in html_content:
            print("✅ Quiz data variable found in JavaScript")
        else:
            print("❌ Quiz data variable not found in JavaScript")
            return False
        
        # Check if event listeners are set up
        if 'addEventListener' in html_content and 'start-quiz-btn' in html_content:
            print("✅ Event listeners setup found in JavaScript")
        else:
            print("❌ Event listeners setup not found in JavaScript")
            return False
        
        # Check if debug functions are available
        if 'window.debugQuiz' in html_content:
            print("✅ Debug functions available")
        else:
            print("❌ Debug functions not available")
            return False
        
        print("\n🎯 Quiz functionality appears to be properly implemented!")
        print("📝 To test manually:")
        print("   1. Open http://localhost:8000/articles/4/ in browser")
        print("   2. Open browser console (F12)")
        print("   3. Look for 'Quiz: Implementation ready' message")
        print("   4. Try: window.debugQuiz.showQuizOverlay()")
        print("   5. Click the 'Start Quiz' button")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing quiz functionality: {e}")
        return False

if __name__ == "__main__":
    test_quiz_functionality()