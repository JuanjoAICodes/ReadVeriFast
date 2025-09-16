#!/usr/bin/env python
"""
Test script to verify article processing works without database locks.
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from verifast_app.models import Article
from verifast_app.tasks import process_article
from django.db import transaction
import time


def test_article_processing():
    """Test that article processing works without database locks."""
    print("🧪 Testing Article Processing")
    print("=" * 40)
    
    # Find articles that need processing
    pending_articles = Article.objects.filter(
        processing_status__in=['pending', 'failed', 'failed_quota']
    )[:3]
    
    print(f"Found {len(pending_articles)} articles that need processing")
    
    if not pending_articles:
        print("No articles need processing. Creating a test article...")
        
        # Create a test article
        test_article = Article.objects.create(
            title="Test Article for Database Lock Testing",
            content="This is a test article to verify that database lock handling works correctly. " * 20,
            url="https://example.com/test-article",
            processing_status="pending",
            article_type="regular"
        )
        pending_articles = [test_article]
        print(f"Created test article with ID: {test_article.id}")
    
    # Test processing articles one by one
    results = []
    for article in pending_articles:
        print(f"\n📝 Processing article {article.id}: {article.title[:50]}...")
        
        try:
            # Call the task directly (synchronously for testing)
            result = process_article(article.id)
            results.append((article.id, result))
            print(f"✅ Article {article.id} processed successfully")
            print(f"   Result: {result}")
            
        except Exception as e:
            results.append((article.id, {"success": False, "error": str(e)}))
            print(f"❌ Article {article.id} failed: {e}")
    
    # Summary
    successful = len([r for r in results if r[1].get('success', False)])
    total = len(results)
    
    print(f"\n📊 Processing Results: {successful}/{total} articles processed successfully")
    
    if successful == total:
        print("🎉 All articles processed without database lock errors!")
        return True
    else:
        print("⚠️  Some articles failed to process.")
        return False


def check_database_status():
    """Check current database status."""
    from verifast_app.database_utils import get_database_status
    
    print("🔍 Current Database Status:")
    status = get_database_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    return not status.get('locked', True)


def main():
    """Run the article processing test."""
    print("🚀 Article Processing Test Suite")
    print("=" * 50)
    
    # Check database status first
    if not check_database_status():
        print("❌ Database is locked or has issues. Aborting test.")
        return False
    
    # Test article processing
    return test_article_processing()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)