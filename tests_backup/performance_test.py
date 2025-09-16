#!/usr/bin/env python
"""
Performance testing script for article processing.
"""

import os
import sys
import time
import django
import statistics
from datetime import datetime

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from verifast_app.models import Article
from verifast_app.services import analyze_text_content, generate_master_analysis

def test_nlp_performance(iterations=5):
    """Test NLP performance"""
    print("\nTesting NLP Performance...")
    
    # Sample text of different lengths
    texts = [
        "This is a short test sentence.",  # Short
        "This is a medium length paragraph that contains multiple sentences. It should be processed by the NLP pipeline to extract entities and calculate reading level. The paragraph mentions people like John Smith and organizations like Google.",  # Medium
        "This is a long text that would be typical of an article. " * 20  # Long
    ]
    
    for i, text in enumerate(texts):
        print(f"\nText {i+1} (length: {len(text)} chars):")
        times = []
        
        for j in range(iterations):
            start_time = time.time()
            result = analyze_text_content(text)
            end_time = time.time()
            elapsed = end_time - start_time
            times.append(elapsed)
            print(f"  Run {j+1}: {elapsed:.4f}s")
        
        avg_time = statistics.mean(times)
        print(f"  Average: {avg_time:.4f}s")
        print(f"  Entities found: {len(result['people']) + len(result['organizations'])}")

def test_ai_performance(iterations=3):
    """Test AI performance"""
    print("\nTesting AI Performance...")
    
    # Sample text and entities
    text = "This is a test article about artificial intelligence and machine learning. " * 10
    entities = ["Artificial Intelligence", "Machine Learning", "Neural Networks"]
    
    times = []
    for i in range(iterations):
        print(f"\nRun {i+1}:")
        start_time = time.time()
        result = generate_master_analysis("models/gemini-2.5-flash", entities, text)
        end_time = time.time()
        elapsed = end_time - start_time
        times.append(elapsed)
        print(f"  Time: {elapsed:.4f}s")
        print(f"  Quiz questions: {len(result.get('quiz', []))}")
        print(f"  Tags: {result.get('tags', [])}")
    
    if times:
        avg_time = statistics.mean(times)
        print(f"\nAverage AI processing time: {avg_time:.4f}s")

def test_database_performance():
    """Test database query performance"""
    print("\nTesting Database Performance...")
    
    # Create test articles if needed
    if Article.objects.count() < 10:
        for i in range(10):
            Article.objects.create(
                title=f"Test Article {i}",
                content=f"This is test content for article {i}. " * 20,
                processing_status='complete'
            )
    
    # Test query performance
    start_time = time.time()
    articles = list(Article.objects.all()[:100])
    end_time = time.time()
    print(f"Query time for {len(articles)} articles: {end_time - start_time:.4f}s")
    
    # Test filtering performance
    start_time = time.time()
    filtered = list(Article.objects.filter(processing_status='complete')[:100])
    end_time = time.time()
    print(f"Filtered query time for {len(filtered)} articles: {end_time - start_time:.4f}s")

def test_memory_usage():
    """Test memory usage during processing"""
    print("\nTesting Memory Usage...")
    
    try:
        import psutil
        process = psutil.Process()
        
        # Get initial memory usage
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"Initial memory usage: {initial_memory:.2f} MB")
        
        # Process a large text
        large_text = "This is a large text for memory testing. " * 1000
        
        start_memory = process.memory_info().rss / 1024 / 1024
        analyze_text_content(large_text)
        end_memory = process.memory_info().rss / 1024 / 1024
        
        print(f"Memory before NLP: {start_memory:.2f} MB")
        print(f"Memory after NLP: {end_memory:.2f} MB")
        print(f"Memory increase: {end_memory - start_memory:.2f} MB")
        
    except ImportError:
        print("psutil not available, skipping memory test")

def test_concurrent_processing():
    """Test concurrent processing simulation"""
    print("\nTesting Concurrent Processing Simulation...")
    
    # Simulate processing multiple articles
    test_texts = [
        "Article about technology and innovation.",
        "Article about science and research.",
        "Article about business and economics.",
        "Article about health and medicine.",
        "Article about education and learning."
    ]
    
    start_time = time.time()
    results = []
    
    for i, text in enumerate(test_texts):
        print(f"Processing article {i+1}...")
        result = analyze_text_content(text)
        results.append(result)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Total time for {len(test_texts)} articles: {total_time:.4f}s")
    print(f"Average time per article: {total_time/len(test_texts):.4f}s")

def validate_performance_thresholds():
    """Validate that performance meets acceptable thresholds"""
    print("\nValidating Performance Thresholds...")
    
    # Define acceptable thresholds
    thresholds = {
        'nlp_processing': 2.0,  # seconds
        'ai_processing': 30.0,  # seconds
        'database_query': 0.1,  # seconds
    }
    
    results = {}
    
    # Test NLP processing time
    start_time = time.time()
    analyze_text_content("This is a test sentence for performance validation.")
    nlp_time = time.time() - start_time
    results['nlp_processing'] = nlp_time
    
    # Test database query time
    start_time = time.time()
    list(Article.objects.all()[:10])
    db_time = time.time() - start_time
    results['database_query'] = db_time
    
    # Check thresholds
    print("\nPerformance Validation Results:")
    all_passed = True
    
    for metric, time_taken in results.items():
        threshold = thresholds.get(metric, float('inf'))
        status = "PASS" if time_taken <= threshold else "FAIL"
        if status == "FAIL":
            all_passed = False
        
        print(f"  {metric}: {time_taken:.4f}s (threshold: {threshold}s) - {status}")
    
    print(f"\nOverall Performance: {'PASS' if all_passed else 'FAIL'}")
    return all_passed

def main():
    """Main function"""
    print(f"Performance Test Started: {datetime.now()}")
    
    try:
        test_nlp_performance()
        test_ai_performance()
        test_database_performance()
        test_memory_usage()
        test_concurrent_processing()
        
        # Final validation
        performance_ok = validate_performance_thresholds()
        
        print(f"\nPerformance Test Completed: {datetime.now()}")
        
        if performance_ok:
            print("✅ All performance tests passed!")
            return 0
        else:
            print("❌ Some performance tests failed!")
            return 1
            
    except Exception as e:
        print(f"❌ Performance test failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())