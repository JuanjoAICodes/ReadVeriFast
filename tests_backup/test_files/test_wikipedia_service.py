#!/usr/bin/env python
"""
Test script for Wikipedia service functionality.
Run this to test Wikipedia integration without Django management commands.
"""

import os
import django
from verifast_app.wikipedia_service import WikipediaService, validate_tag

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()


def test_wikipedia_validation():
    """Test Wikipedia tag validation."""
    print("Testing Wikipedia tag validation...")
    
    # Test valid tags
    test_tags = [
        "Python",
        "Machine Learning", 
        "Django",
        "Artificial Intelligence",
        "Speed Reading"
    ]
    
    for tag_name in test_tags:
        print(f"\nTesting tag: '{tag_name}'")
        is_valid, data = validate_tag(tag_name)
        
        if is_valid and data:
            print(f"✅ Valid! Title: {data['title']}")
            print(f"   URL: {data['url']}")
            print(f"   Summary: {data['summary'][:100]}...")
        else:
            print("❌ Invalid or not found")

def test_wikipedia_service():
    """Test Wikipedia service class."""
    print("\n" + "="*50)
    print("Testing Wikipedia Service Class")
    print("="*50)
    
    service = WikipediaService()
    
    # Test with a known good tag
    tag_name = "Python"
    print(f"\nTesting service with tag: '{tag_name}'")
    
    is_valid, data = service.validate_tag_with_wikipedia(tag_name)
    
    if is_valid and data:
        print("✅ Service validation successful!")
        print(f"   Title: {data['title']}")
        print(f"   Content length: {len(data['content'])} characters")
        
        # Test content processing
        processed = service.process_wikipedia_content(data['content'])
        print(f"   Processed content length: {len(processed)} characters")
        print(f"   First 200 chars: {processed[:200]}...")
        
    else:
        print("❌ Service validation failed")

if __name__ == "__main__":
    print("Wikipedia Service Test")
    print("=" * 50)
    
    try:
        test_wikipedia_validation()
        test_wikipedia_service()
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()