#!/usr/bin/env python3
"""
Test script to verify speed reader and quiz functionality
"""
import requests

def test_speed_reader_and_quiz():
    """Test if speed reader and quiz functionality are properly implemented"""
    try:
        # Get the article page
        response = requests.get('http://localhost:8000/articles/4/', allow_redirects=True)
        if response.status_code != 200:
            print(f"❌ Failed to load article page: {response.status_code}")
            return False
        
        html_content = response.text
        
        print("🔍 Testing Speed Reader and Quiz Integration...")
        print()
        
        # Check if speed reader elements exist
        speed_reader_elements = [
            'id="start-pause-btn"',
            'id="word-display"',
            'id="progress-bar"',
            'id="speed-reader-section"'
        ]
        
        for element in speed_reader_elements:
            if element in html_content:
                print(f"✅ Speed Reader: {element} found")
            else:
                print(f"❌ Speed Reader: {element} missing")
                return False
        
        print()
        
        # Check if quiz elements exist
        quiz_elements = [
            'id="start-quiz-btn"',
            'id="quiz-overlay"',
            'class="quiz-section"'
        ]
        
        for element in quiz_elements:
            if element in html_content:
                print(f"✅ Quiz: {element} found")
            else:
                print(f"❌ Quiz: {element} missing")
                return False
        
        print()
        
        # Check if quiz enabling logic is present
        quiz_logic_checks = [
            'function enableQuiz',
            'function disableQuiz',
            'enableQuiz(); // Enable quiz when reading is finished',
            'external-link'
        ]
        
        for check in quiz_logic_checks:
            if check in html_content:
                print(f"✅ Quiz Logic: {check} found")
            else:
                print(f"❌ Quiz Logic: {check} missing")
                return False
        
        print()
        
        # Check if speed reader initialization is present
        speed_reader_logic = [
            'Speed Reader: Starting implementation',
            'function showNextWord',
            'function startReading',
            'function stopReading'
        ]
        
        for check in speed_reader_logic:
            if check in html_content:
                print(f"✅ Speed Reader Logic: {check} found")
            else:
                print(f"❌ Speed Reader Logic: {check} missing")
                return False
        
        print()
        print("🎯 All components found! The implementation looks correct.")
        print()
        print("📝 Manual Testing Instructions:")
        print("   1. Open http://localhost:8000/articles/4/ in browser")
        print("   2. Notice the quiz button should be disabled initially")
        print("   3. Click 'Start Reading' to begin speed reading")
        print("   4. Wait for reading to complete (or click 'View Original Article')")
        print("   5. Quiz button should become enabled")
        print("   6. Click 'Start Quiz' to test quiz functionality")
        print()
        print("🔧 If it's still not working, check browser console for JavaScript errors")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing functionality: {e}")
        return False

if __name__ == "__main__":
    test_speed_reader_and_quiz()