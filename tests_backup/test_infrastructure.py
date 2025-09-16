#!/usr/bin/env python
"""
Test script to verify automated content acquisition infrastructure
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
    print("✓ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

def test_models():
    """Test that the automated content acquisition models work correctly"""
    try:
        from verifast_app.models import Article, ContentAcquisitionLog
        
        # Test Article model with new fields
        print("✓ Article model imported successfully")
        
        # Test ContentAcquisitionLog model
        print("✓ ContentAcquisitionLog model imported successfully")
        
        # Test creating instances (without saving to DB)
        Article(
            title="Test Article",
            content="This is test content for automated acquisition.",
            acquisition_source="rss",
            source_url="https://example.com/test-article",
            topic_category="technology",
            geographic_focus="global",
            content_quality_score=0.85,
            duplicate_check_hash="test_hash_123"
        )
        print("✓ Article instance created with automated acquisition fields")
        
        ContentAcquisitionLog(
            acquisition_type="rss",
            source_name="Test RSS Feed",
            articles_acquired=5,
            articles_processed=4,
            articles_rejected=1,
            processing_time_seconds=30.5,
            language_distribution={"en": 3, "es": 1},
            topic_distribution={"technology": 2, "politics": 2}
        )
        print("✓ ContentAcquisitionLog instance created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def test_configuration():
    """Test configuration imports"""
    try:
        from verifast_app.content_acquisition_config import (
            RSS_SOURCES, TOPIC_CATEGORIES, 
            get_acquisition_enabled
        )
        
        print("✓ Configuration imported successfully")
        print(f"  - RSS sources: {len(RSS_SOURCES['english'])} English, {len(RSS_SOURCES['spanish'])} Spanish")
        print(f"  - Topic categories: {len(TOPIC_CATEGORIES)}")
        print(f"  - Acquisition enabled: {get_acquisition_enabled()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_cache_utils():
    """Test cache utilities"""
    try:
        from verifast_app.cache_utils import ContentAcquisitionCache
        
        print("✓ Cache utilities imported successfully")
        
        # Test basic cache operations (without Redis connection)
        print("  - Cache methods available:")
        methods = [method for method in dir(ContentAcquisitionCache) if not method.startswith('_')]
        for method in methods[:5]:  # Show first 5 methods
            print(f"    - {method}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache utilities test failed: {e}")
        return False

def test_settings():
    """Test Django settings for automated content acquisition"""
    try:
        from django.conf import settings
        
        # Check if our new settings are available
        acquisition_settings = [
            'ENABLE_AUTOMATED_CONTENT_ACQUISITION',
            'MAX_CONCURRENT_ACQUISITIONS',
            'CONTENT_ACQUISITION_INTERVAL_HOURS',
            'MAX_ARTICLES_PER_CYCLE'
        ]
        
        print("✓ Settings configuration:")
        for setting in acquisition_settings:
            value = getattr(settings, setting, 'NOT_SET')
            print(f"  - {setting}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Settings test failed: {e}")
        return False

def main():
    """Run all infrastructure tests"""
    print("=== Automated Content Acquisition Infrastructure Test ===\n")
    
    tests = [
        ("Models", test_models),
        ("Configuration", test_configuration),
        ("Cache Utils", test_cache_utils),
        ("Settings", test_settings)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- Testing {test_name} ---")
        if test_func():
            passed += 1
            print(f"✅ {test_name} test passed")
        else:
            print(f"❌ {test_name} test failed")
    
    print("\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All infrastructure tests passed!")
        print("\nNext steps:")
        print("1. Ensure Redis is running: redis-server")
        print("2. Apply migrations: python manage.py migrate")
        print("3. Continue with Content Acquisition Manager implementation")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)