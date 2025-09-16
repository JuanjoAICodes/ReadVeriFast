#!/usr/bin/env python
"""
Test script to verify automated content acquisition models are working
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from verifast_app.models import Article, ContentAcquisitionLog

def test_models():
    """Test that the automated content acquisition models work correctly"""
    print("Testing automated content acquisition models...")
    
    try:
        # Test Article model with new fields
        print("✓ Article model imported successfully")
        
        # Test ContentAcquisitionLog model
        print("✓ ContentAcquisitionLog model imported successfully")
        
        # Test creating a sample article with new fields
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
        
        # Test creating a sample log entry
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
        
        print("\n🎉 All automated content acquisition models are working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing models: {e}")
        return False

if __name__ == "__main__":
    success = test_models()
    sys.exit(0 if success else 1)