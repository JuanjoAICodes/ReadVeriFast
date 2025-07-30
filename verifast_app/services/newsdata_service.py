"""
NewsData.io API Integration Service
Handles content acquisition from NewsData.io API with rate limiting and error handling
"""

import requests
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from django.conf import settings

from ..models_content_acquisition import ContentSource, ContentFingerprint
from ..pydantic_models.dto import ContentAcquisitionDTO

logger = logging.getLogger(__name__)


class NewsDataService:
    """Service for interacting with NewsData.io API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'NEWSDATA_API_KEY', '')
        self.base_url = "https://newsdata.io/api/1/news"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VeriFast/1.0 (Educational Content Platform)'
        })
        
        # Rate limiting (NewsData.io free tier: 200 requests/day)
        self.requests_per_day = 200
        self.requests_per_hour = 20  # Conservative limit
        self.min_request_interval = 3  # Seconds between requests
        
        self.last_request_time = None
    
    def _can_make_request(self, source: ContentSource) -> Tuple[bool, str]:
        """Check if we can make a request based on rate limits"""
        return source.can_make_request()
    
    def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                wait_time = self.min_request_interval - elapsed
                logger.info(f"Rate limiting: waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
    
    def _make_api_request(self, params: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Make API request with error handling and rate limiting"""
        self._wait_for_rate_limit()
        
        # Add API key to parameters
        params['apikey'] = self.api_key
        
        try:
            self.last_request_time = time.time()
            response = self.session.get(self.base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return True, data
                else:
                    error_msg = data.get('message', 'Unknown API error')
                    logger.error(f"NewsData API error: {error_msg}")
                    return False, {'error': error_msg}
            
            elif response.status_code == 429:
                # Rate limit exceeded
                logger.warning("NewsData API rate limit exceeded")
                return False, {'error': 'Rate limit exceeded', 'retry_after': 3600}
            
            elif response.status_code == 401:
                logger.error("NewsData API authentication failed")
                return False, {'error': 'Authentication failed'}
            
            else:
                logger.error(f"NewsData API HTTP error: {response.status_code}")
                return False, {'error': f'HTTP {response.status_code}'}
                
        except requests.exceptions.Timeout:
            logger.error("NewsData API request timeout")
            return False, {'error': 'Request timeout'}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"NewsData API request error: {str(e)}")
            return False, {'error': str(e)}
    
    def fetch_latest_articles(
        self, 
        source: ContentSource,
        language: str = 'en',
        category: Optional[str] = None,
        country: Optional[str] = None,
        max_articles: int = 10
    ) -> List[ContentAcquisitionDTO]:
        """Fetch latest articles from NewsData.io API"""
        
        # Check if we can make request
        can_request, reason = self._can_make_request(source)
        if not can_request:
            logger.warning(f"Cannot make request to {source.name}: {reason}")
            return []
        
        # Build API parameters
        params = {
            'language': language,
            'size': min(max_articles, 10),  # API limit is 10 per request
            'removeduplicate': 1,
            'full_content': 1
        }
        
        if category:
            params['category'] = category
        
        if country:
            params['country'] = country
        
        # Make API request
        success, response_data = self._make_api_request(params)
        
        # Record request attempt
        source.record_request(
            success=success,
            error_message=response_data.get('error', '') if not success else ''
        )
        
        if not success:
            return []
        
        # Process articles
        articles = []
        raw_articles = response_data.get('results', [])
        
        for article_data in raw_articles:
            try:
                # Extract article information
                title = article_data.get('title', '').strip()
                content = article_data.get('content') or article_data.get('description', '')
                url = article_data.get('link', '')
                
                if not title or not content or not url:
                    logger.warning("Skipping article with missing required fields")
                    continue
                
                # Check for duplicates
                is_duplicate, duplicate_reason = ContentFingerprint.is_duplicate(
                    url=url,
                    title=title,
                    content=content,
                    language=language,
                    topic_category=category or 'general'
                )
                
                if is_duplicate:
                    logger.info(f"Skipping duplicate article: {duplicate_reason}")
                    continue
                
                # Create DTO
                dto = ContentAcquisitionDTO(
                    source_id=source.name,
                    source_type='api',
                    url=url,
                    title=title,
                    content=content,
                    language=language,
                    publication_date=self._parse_date(article_data.get('pubDate')),
                    author=article_data.get('creator', [None])[0] if article_data.get('creator') else None,
                    tags=article_data.get('keywords', []) or [],
                    priority=source.priority
                )
                
                articles.append(dto)
                
            except Exception as e:
                logger.error(f"Error processing article from NewsData: {str(e)}")
                continue
        
        logger.info(f"Fetched {len(articles)} articles from NewsData.io for {source.name}")
        return articles
    
    def fetch_articles_by_query(
        self,
        source: ContentSource,
        query: str,
        language: str = 'en',
        max_articles: int = 10
    ) -> List[ContentAcquisitionDTO]:
        """Fetch articles by search query"""
        
        can_request, reason = self._can_make_request(source)
        if not can_request:
            logger.warning(f"Cannot make request to {source.name}: {reason}")
            return []
        
        params = {
            'q': query,
            'language': language,
            'size': min(max_articles, 10),
            'removeduplicate': 1,
            'full_content': 1
        }
        
        success, response_data = self._make_api_request(params)
        
        source.record_request(
            success=success,
            error_message=response_data.get('error', '') if not success else ''
        )
        
        if not success:
            return []
        
        # Process results similar to fetch_latest_articles
        articles = []
        raw_articles = response_data.get('results', [])
        
        for article_data in raw_articles:
            try:
                title = article_data.get('title', '').strip()
                content = article_data.get('content') or article_data.get('description', '')
                url = article_data.get('link', '')
                
                if not title or not content or not url:
                    continue
                
                is_duplicate, _ = ContentFingerprint.is_duplicate(
                    url=url,
                    title=title,
                    content=content,
                    language=language,
                    topic_category='search_result'
                )
                
                if is_duplicate:
                    continue
                
                dto = ContentAcquisitionDTO(
                    source_id=source.name,
                    source_type='api',
                    url=url,
                    title=title,
                    content=content,
                    language=language,
                    publication_date=self._parse_date(article_data.get('pubDate')),
                    author=article_data.get('creator', [None])[0] if article_data.get('creator') else None,
                    tags=article_data.get('keywords', []) or [],
                    priority=source.priority
                )
                
                articles.append(dto)
                
            except Exception as e:
                logger.error(f"Error processing search result: {str(e)}")
                continue
        
        return articles
    
    def _parse_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """Parse date string from API response"""
        if not date_string:
            return None
        
        try:
            # NewsData.io uses ISO format
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse date: {date_string}")
            return None
    
    def get_available_categories(self) -> List[str]:
        """Get list of available categories from NewsData.io"""
        return [
            'business', 'entertainment', 'environment', 'food', 'health',
            'politics', 'science', 'sports', 'technology', 'top', 'world'
        ]
    
    def get_available_countries(self) -> Dict[str, str]:
        """Get list of available countries for content filtering"""
        return {
            'us': 'United States',
            'gb': 'United Kingdom',
            'ca': 'Canada',
            'au': 'Australia',
            'es': 'Spain',
            'mx': 'Mexico',
            'ar': 'Argentina',
            'co': 'Colombia',
            'pe': 'Peru',
            'cl': 'Chile'
        }
    
    def test_connection(self, source: ContentSource) -> Tuple[bool, str]:
        """Test API connection and authentication"""
        can_request, reason = self._can_make_request(source)
        if not can_request:
            return False, reason
        
        # Make a minimal test request
        params = {
            'language': 'en',
            'size': 1
        }
        
        success, response_data = self._make_api_request(params)
        
        if success:
            return True, "Connection successful"
        else:
            error_msg = response_data.get('error', 'Unknown error')
            return False, f"Connection failed: {error_msg}"