#!/usr/bin/env python3
"""
External API Test Script for VeriFast Content Motor
Tests all external news APIs (NewsData.io, GNews, NewsAPI.org) and RSS feeds
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from verifast_app.services.newsdata_service import NewsDataService
from verifast_app.services.gnews_service import GNewsService
from verifast_app.services.newsapi_service import NewsAPIService
from verifast_app.services.rss_service import RSSProcessor
from verifast_app.models_content_acquisition import ContentSource


class ExternalAPITester:
    def __init__(self):
        self.results = {
            'newsdata': {'available': False, 'working': False, 'articles': 0, 'error': ''},
            'gnews': {'available': False, 'working': False, 'articles': 0, 'error': ''},
            'newsapi': {'available': False, 'working': False, 'articles': 0, 'error': ''},
            'rss': {'available': True, 'working': False, 'articles': 0, 'error': ''}
        }
    
    def test_newsdata_api(self):
        """Test NewsData.io API"""
        print("🔍 Testing NewsData.io API...")
        
        api_key = getattr(settings, 'NEWSDATA_API_KEY', '')
        if not api_key:
            self.results['newsdata']['error'] = 'API key not configured'
            print("  ❌ NewsData.io API key not found in settings")
            return
        
        self.results['newsdata']['available'] = True
        
        try:
            # Create a test source
            test_source = ContentSource(
                name='Test NewsData Source',
                source_type='newsdata_api',
                url='https://newsdata.io/api/1/news',
                language='en',
                requests_per_hour=20,
                requests_per_day=200,
                is_active=True
            )
            
            service = NewsDataService(api_key)
            success, message = service.test_connection(test_source)
            
            if success:
                print(f"  ✅ Connection successful: {message}")
                
                # Try to fetch a few articles
                articles = service.fetch_latest_articles(
                    source=test_source,
                    language='en',
                    max_articles=3
                )
                
                self.results['newsdata']['working'] = True
                self.results['newsdata']['articles'] = len(articles)
                print(f"  ✅ Fetched {len(articles)} articles")
                
                if articles:
                    print(f"  📰 Sample article: {articles[0].title[:60]}...")
            else:
                self.results['newsdata']['error'] = message
                print(f"  ❌ Connection failed: {message}")
                
        except Exception as e:
            self.results['newsdata']['error'] = str(e)
            print(f"  ❌ Error: {str(e)}")
    
    def test_gnews_api(self):
        """Test GNews API"""
        print("\n🔍 Testing GNews API...")
        
        api_key = getattr(settings, 'GNEWS_API_KEY', '')
        if not api_key:
            self.results['gnews']['error'] = 'API key not configured'
            print("  ❌ GNews API key not found in settings")
            return
        
        self.results['gnews']['available'] = True
        
        try:
            # Create a test source
            test_source = ContentSource(
                name='Test GNews Source',
                source_type='gnews_api',
                url='https://gnews.io/api/v4',
                language='en',
                requests_per_hour=10,
                requests_per_day=100,
                is_active=True
            )
            
            service = GNewsService(api_key)
            success, message = service.test_connection(test_source)
            
            if success:
                print(f"  ✅ Connection successful: {message}")
                
                # Try to fetch a few articles
                articles = service.fetch_top_headlines(
                    source=test_source,
                    language='en',
                    max_articles=3
                )
                
                self.results['gnews']['working'] = True
                self.results['gnews']['articles'] = len(articles)
                print(f"  ✅ Fetched {len(articles)} articles")
                
                if articles:
                    print(f"  📰 Sample article: {articles[0].title[:60]}...")
            else:
                self.results['gnews']['error'] = message
                print(f"  ❌ Connection failed: {message}")
                
        except Exception as e:
            self.results['gnews']['error'] = str(e)
            print(f"  ❌ Error: {str(e)}")
    
    def test_newsapi(self):
        """Test NewsAPI.org"""
        print("\n🔍 Testing NewsAPI.org...")
        
        api_key = getattr(settings, 'NEWSAPI_KEY', '')
        if not api_key:
            self.results['newsapi']['error'] = 'API key not configured'
            print("  ❌ NewsAPI key not found in settings")
            return
        
        self.results['newsapi']['available'] = True
        
        try:
            # Create a test source
            test_source = ContentSource(
                name='Test NewsAPI Source',
                source_type='newsapi',
                url='https://newsapi.org/v2',
                language='en',
                requests_per_hour=50,
                requests_per_day=1000,
                is_active=True
            )
            
            service = NewsAPIService(api_key)
            success, message = service.test_connection(test_source)
            
            if success:
                print(f"  ✅ Connection successful: {message}")
                
                # Try to fetch a few articles
                articles = service.fetch_top_headlines(
                    source=test_source,
                    language='en',
                    max_articles=3
                )
                
                self.results['newsapi']['working'] = True
                self.results['newsapi']['articles'] = len(articles)
                print(f"  ✅ Fetched {len(articles)} articles")
                
                if articles:
                    print(f"  📰 Sample article: {articles[0].title[:60]}...")
            else:
                self.results['newsapi']['error'] = message
                print(f"  ❌ Connection failed: {message}")
                
        except Exception as e:
            self.results['newsapi']['error'] = str(e)
            print(f"  ❌ Error: {str(e)}")
    
    def test_rss_feeds(self):
        """Test RSS feed processing"""
        print("\n🔍 Testing RSS Feed Processing...")
        
        try:
            # Create a test RSS source
            test_source = ContentSource(
                name='Test RSS Source',
                source_type='rss',
                url='http://feeds.bbci.co.uk/news/rss.xml',
                language='en',
                requests_per_hour=12,
                requests_per_day=100,
                is_active=True
            )
            
            processor = RSSProcessor()
            
            # Test feed connection
            try:
                success, message = processor.test_feed_connection(test_source)
                
                if success:
                    print(f"  ✅ RSS connection successful: {message}")
                    
                    # Try to fetch a few articles
                    articles = processor.fetch_feed_articles(
                        source=test_source,
                        max_articles=3,
                        extract_full_content=False  # Just test feed parsing
                    )
                    
                    self.results['rss']['working'] = True
                    self.results['rss']['articles'] = len(articles)
                    print(f"  ✅ Fetched {len(articles)} RSS items")
                    
                    if articles:
                        print(f"  📰 Sample article: {articles[0].title[:60]}...")
                else:
                    self.results['rss']['error'] = message
                    print(f"  ❌ RSS connection failed: {message}")
                    
            except Exception as e:
                self.results['rss']['error'] = str(e)
                print(f"  ❌ RSS Error: {str(e)}")
                
        except Exception as e:
            self.results['rss']['error'] = str(e)
            print(f"  ❌ Error: {str(e)}")
    
    def test_content_sources_in_db(self):
        """Test existing content sources in database"""
        print("\n🔍 Testing Existing Content Sources in Database...")
        
        sources = ContentSource.objects.filter(is_active=True)
        
        if not sources.exists():
            print("  ⚠️  No active content sources found in database")
            print("  💡 Run: python manage.py setup_content_sources --create-sample-rss")
            return
        
        print(f"  📊 Found {sources.count()} active content sources:")
        
        for source in sources:
            health_score = source.get_health_score()
            can_request, reason = source.can_make_request()
            
            status_icon = "✅" if can_request else "⚠️"
            health_color = "🟢" if health_score >= 80 else "🟡" if health_score >= 60 else "🔴"
            
            print(f"    {status_icon} {source.name} ({source.get_source_type_display()})")
            print(f"      Health: {health_color} {health_score}/100")
            print(f"      Status: {reason}")
            print(f"      Articles fetched: {source.total_articles_fetched}")
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 VeriFast External API Test Suite")
        print("=" * 60)
        
        # Test individual APIs
        self.test_newsdata_api()
        self.test_gnews_api()
        self.test_newsapi()
        self.test_rss_feeds()
        
        # Test database sources
        self.test_content_sources_in_db()
        
        # Summary
        print("\n📊 Test Results Summary")
        print("=" * 60)
        
        total_working = 0
        total_available = 0
        
        for api_name, result in self.results.items():
            if result['available']:
                total_available += 1
                
            if result['working']:
                total_working += 1
                status = f"✅ Working ({result['articles']} articles)"
            elif result['available']:
                status = f"❌ Failed: {result['error']}"
            else:
                status = f"⚠️  Not configured: {result['error']}"
            
            api_display = {
                'newsdata': 'NewsData.io API',
                'gnews': 'GNews API',
                'newsapi': 'NewsAPI.org',
                'rss': 'RSS Feeds'
            }
            
            print(f"  {api_display[api_name]:<20} {status}")
        
        print(f"\n🎯 Overall Status: {total_working}/{total_available} APIs working")
        
        # Recommendations
        print("\n💡 Recommendations:")
        
        if total_working == 0:
            print("  🔧 No APIs are working. Check your configuration:")
            print("     1. Add API keys to your .env file")
            print("     2. Run: python manage.py setup_content_sources --create-sample-rss")
            print("     3. Restart Django server to load new environment variables")
        
        elif total_working < total_available:
            print("  🔧 Some APIs need attention:")
            for api_name, result in self.results.items():
                if result['available'] and not result['working']:
                    print(f"     - Fix {api_name}: {result['error']}")
        
        else:
            print("  🎉 All configured APIs are working!")
            print("  🚀 You can now start the content motor:")
            print("     python manage.py start_content_motor --orchestrate")
        
        return total_working > 0


def main():
    """Main test function"""
    print("🔍 Checking Django configuration...")
    
    try:
        # Test Django setup
        print("✅ Django configuration loaded successfully")
        
        # Run API tests
        tester = ExternalAPITester()
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 At least one API is working - Content Motor is ready!")
            sys.exit(0)
        else:
            print("\n⚠️  No APIs are working - Please check configuration")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Django configuration error: {str(e)}")
        print("\n💡 Make sure you're in the correct directory and Django is properly set up")
        sys.exit(1)


if __name__ == "__main__":
    main()