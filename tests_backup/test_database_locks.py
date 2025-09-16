#!/usr/bin/env python
"""
Test script to verify database lock handling improvements.
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from verifast_app.database_utils import with_database_retry, DatabaseLockManager, get_database_status
from verifast_app.models import Article
from django.db import transaction
import time
import threading


def test_database_status():
    """Test database status reporting."""
    print("🔍 Testing database status...")
    status = get_database_status()
    print(f"Database status: {status}")
    return status.get('locked', False) == False


@with_database_retry(max_retries=2, base_delay=0.5)
def test_retry_decorator():
    """Test the retry decorator."""
    print("🔄 Testing retry decorator...")
    with transaction.atomic():
        articles = Article.objects.all()[:5]
        print(f"Found {len(articles)} articles")
    return True


def test_lock_manager():
    """Test the database lock manager."""
    print("🔒 Testing database lock manager...")
    try:
        with DatabaseLockManager(timeout=30):
            with transaction.atomic():
                articles = Article.objects.all()[:3]
                print(f"Lock manager test: Found {len(articles)} articles")
        return True
    except Exception as e:
        print(f"Lock manager test failed: {e}")
        return False


def test_concurrent_access():
    """Test concurrent database access."""
    print("🚀 Testing concurrent database access...")
    
    results = []
    
    def worker(worker_id):
        try:
            with DatabaseLockManager():
                with transaction.atomic():
                    articles = Article.objects.all()[:2]
                    time.sleep(0.1)  # Simulate some work
                    results.append(f"Worker {worker_id}: {len(articles)} articles")
        except Exception as e:
            results.append(f"Worker {worker_id}: ERROR - {e}")
    
    # Start multiple threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    print("Concurrent access results:")
    for result in results:
        print(f"  {result}")
    
    return len([r for r in results if "ERROR" not in r]) == 3


def main():
    """Run all database lock tests."""
    print("🧪 Database Lock Handling Test Suite")
    print("=" * 50)
    
    tests = [
        ("Database Status", test_database_status),
        ("Retry Decorator", test_retry_decorator),
        ("Lock Manager", test_lock_manager),
        ("Concurrent Access", test_concurrent_access),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database lock handling is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Database lock handling may need attention.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)