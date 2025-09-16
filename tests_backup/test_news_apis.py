from django.core.management.base import BaseCommand
import os
import requests
import json


class Command(BaseCommand):
    help = 'Test news API connections and diagnose authentication issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api',
            type=str,
            choices=['newsdata', 'newsapi', 'gnews', 'all'],
            default='all',
            help='Which API to test (default: all)'
        )

    def handle(self, *args, **options):
        api_choice = options['api']
        
        self.stdout.write("News API Connection Test")
        self.stdout.write("=" * 50)
        
        if api_choice in ['newsdata', 'all']:
            self.test_newsdata_api()
        
        if api_choice in ['newsapi', 'all']:
            self.test_newsapi()
        
        if api_choice in ['gnews', 'all']:
            self.test_gnews_api()

    def test_newsdata_api(self):
        """Test NewsData.io API"""
        self.stdout.write("\n📰 Testing NewsData.io API...")
        
        api_key = os.environ.get('NEWSDATA_API_KEY')
        if not api_key:
            self.stdout.write(self.style.ERROR("❌ NEWSDATA_API_KEY not found"))
            return
        
        # Test with a simple request (NewsData.io doesn't support 'general' category)
        url = "https://newsdata.io/api/1/news"
        params = {
            'apikey': api_key,
            'language': 'en',
            'category': 'top',  # Use 'top' instead of 'general'
            'size': 1  # Just get 1 article for testing
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            self.stdout.write(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    results_count = len(data.get('results', []))
                    self.stdout.write(self.style.SUCCESS(f"✅ NewsData.io API working! Found {results_count} articles"))
                    if results_count > 0:
                        sample = data['results'][0]
                        self.stdout.write(f"   Sample: {sample.get('title', 'No title')[:60]}...")
                else:
                    self.stdout.write(self.style.ERROR(f"❌ API Error: {data}"))
            elif response.status_code == 401:
                self.stdout.write(self.style.ERROR("❌ Authentication failed - Invalid API key"))
            elif response.status_code == 429:
                self.stdout.write(self.style.WARNING("⚠️ Rate limit exceeded"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ HTTP Error {response.status_code}: {response.text[:200]}"))
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"❌ Connection error: {str(e)}"))

    def test_newsapi(self):
        """Test NewsAPI.org"""
        self.stdout.write("\n📰 Testing NewsAPI.org...")
        
        api_key = os.environ.get('NEWSAPI_KEY')
        if not api_key:
            self.stdout.write(self.style.ERROR("❌ NEWSAPI_KEY not found"))
            return
        
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            'apiKey': api_key,
            'language': 'en',
            'pageSize': 1
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            self.stdout.write(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    total_results = data.get('totalResults', 0)
                    articles_count = len(data.get('articles', []))
                    self.stdout.write(self.style.SUCCESS(f"✅ NewsAPI working! {total_results} total, got {articles_count} articles"))
                    if articles_count > 0:
                        sample = data['articles'][0]
                        self.stdout.write(f"   Sample: {sample.get('title', 'No title')[:60]}...")
                else:
                    self.stdout.write(self.style.ERROR(f"❌ API Error: {data}"))
            elif response.status_code == 401:
                self.stdout.write(self.style.ERROR("❌ Authentication failed - Invalid API key"))
            elif response.status_code == 429:
                self.stdout.write(self.style.WARNING("⚠️ Rate limit exceeded"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ HTTP Error {response.status_code}: {response.text[:200]}"))
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"❌ Connection error: {str(e)}"))

    def test_gnews_api(self):
        """Test GNews API"""
        self.stdout.write("\n📰 Testing GNews API...")
        
        api_key = os.environ.get('GNEWS_API_KEY')
        if not api_key:
            self.stdout.write(self.style.ERROR("❌ GNEWS_API_KEY not found"))
            return
        
        url = "https://gnews.io/api/v4/top-headlines"
        params = {
            'token': api_key,
            'lang': 'en',
            'max': 1
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            self.stdout.write(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                total_articles = data.get('totalArticles', 0)
                self.stdout.write(self.style.SUCCESS(f"✅ GNews API working! {total_articles} total, got {len(articles)} articles"))
                if articles:
                    sample = articles[0]
                    self.stdout.write(f"   Sample: {sample.get('title', 'No title')[:60]}...")
            elif response.status_code == 401:
                self.stdout.write(self.style.ERROR("❌ Authentication failed - Invalid API key"))
            elif response.status_code == 429:
                self.stdout.write(self.style.WARNING("⚠️ Rate limit exceeded"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ HTTP Error {response.status_code}: {response.text[:200]}"))
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"❌ Connection error: {str(e)}"))

    def test_rss_feeds(self):
        """Test a few RSS feeds"""
        self.stdout.write("\n📡 Testing RSS Feeds...")
        
        feeds_to_test = [
            ("BBC News", "http://feeds.bbci.co.uk/news/rss.xml"),
            ("NPR", "https://feeds.npr.org/1001/rss.xml"),
            ("El País", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada")
        ]
        
        for name, url in feeds_to_test:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    # Simple check for RSS content
                    if '<rss' in response.text.lower() or '<feed' in response.text.lower():
                        self.stdout.write(self.style.SUCCESS(f"✅ {name} RSS feed working"))
                    else:
                        self.stdout.write(self.style.WARNING(f"⚠️ {name} returned content but not RSS format"))
                else:
                    self.stdout.write(self.style.ERROR(f"❌ {name} HTTP {response.status_code}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ {name} error: {str(e)}"))