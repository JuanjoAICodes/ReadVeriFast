"""
NewsAPI.org Integration Service
Handles content acquisition from NewsAPI.org with rate limiting and error handling
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


class NewsAPIService:
    """Service for interacting with NewsAPI.org"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'NEWSAPI_KEY', '')
        self.base_url = "https://newsapi.org/v2"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VeriFast/1.0 (Educational Content Platform)',
            'X-API-Key': self.api_key
        })
        
        # Rate limiting (NewsAPI free tier: 1000 requests/day)
        self.requests_per_day = 1000
        self.requests_per_hour = 50  # Conservative limit
        self.min_request_interval = 1  # Seconds between requests
        
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
                logger.info(f"NewsAPI rate limiting: waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
    
    def _make_api_request(self, endpoint: str, params: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Make API request with error handling and rate limiting"""
        self._wait_for_rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            self.last_request_time = time.time()
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    return True, data
                else:
                    error_msg = data.get('message', 'Unknown API error')
                    logger.error(f"NewsAPI error: {error_msg}")
                    return False, {'error': error_msg}
            
            elif response.status_code == 429:
                # Rate limit exceeded
                logger.warning("NewsAPI rate limit exceeded")
                return False, {'error': 'Rate limit exceeded', 'retry_after': 3600}
            
            elif response.status_code == 401:
                logger.error("NewsAPI authentication failed")
                return False, {'error': 'Authentication failed'}
            
            elif response.status_code == 426:
                logger.error("NewsAPI upgrade required")
                return False, {'error': 'Upgrade required'}
            
            else:
                logger.error(f"NewsAPI HTTP error: {response.status_code}")
                return False, {'error': f'HTTP {response.status_code}'}
                
        except requests.exceptions.Timeout:
            logger.error("NewsAPI request timeout")
            return False, {'error': 'Request timeout'}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"NewsAPI request error: {str(e)}")
            return False, {'error': str(e)}
    
    def fetch_top_headlines(
        self, 
        source: ContentSource,
        language: str = 'en',
        country: Optional[str] = None,
        category: Optional[str] = None,
        sources: Optional[str] = None,
        max_articles: int = 20
    ) -> List[ContentAcquisitionDTO]:
        """Fetch top headlines from NewsAPI"""
        
        # Check if we can make request
        can_request, reason = self._can_make_request(source)
        if not can_request:
            logger.warning(f"Cannot make request to {source.name}: {reason}")
            return []
        
        # Build API parameters
        params = {
            'language': language,
            'pageSize': min(max_articles, 100),  # API limit is 100 per request
        }
        
        if country:
            params['country'] = country
        
        if category:
            params['category'] = category
            
        if sources:
            params['sources'] = sources
        
        # Make API request
        success, response_data = self._make_api_request('top-headlines', params)
        
        # Record request attempt
        source.record_request(
            success=success,
            error_message=response_data.get('error', '') if not success else ''
        )
        
        if not success:
            return []
        
        # Process articles
        articles = []
        raw_articles = response_data.get('articles', [])
        
        for article_data in raw_articles:
            try:
                # Extract article information
                title = article_data.get('title', '').strip()
                content = article_data.get('content') or article_data.get('description', '')
                url = article_data.get('url', '')
                
                if not title or not content or not url:
                    logger.warning("Skipping NewsAPI article with missing required fields")
                    continue
                
                # Skip articles with [Removed] content
                if content and '[Removed]' in content:
                    logger.info("Skipping NewsAPI article with removed content")
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
                    logger.info(f"Skipping duplicate NewsAPI article: {duplicate_reason}")
                    continue
                
                # Create DTO
                dto = ContentAcquisitionDTO(
                    source_id=source.name,
                    source_type='api',
                    url=url,
                    title=title,
                    content=content,
                    language=language,
                    publication_date=self._parse_date(article_data.get('publishedAt')),
                    author=article_data.get('author'),
                    tags=[],  # NewsAPI doesn't provide tags directly
                    image_url=article_data.get('urlToImage'),
                    priority=source.priority
                )
                
                articles.append(dto)
                
            except Exception as e:
                logger.error(f"Error processing NewsAPI article: {str(e)}")
                continue
        
        logger.info(f"Fetched {len(articles)} articles from NewsAPI for {source.name}")
        return articles
    
    def search_everything(
        self,
        source: ContentSource,
        query: str,
        language: str = 'en',
        max_articles: int = 20,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        sort_by: str = 'publishedAt'
    ) -> List[ContentAcquisitionDTO]:
        """Search everything using NewsAPI"""
        
        can_request, reason = self._can_make_request(source)
        if not can_request:
            logger.warning(f"Cannot make request to {source.name}: {reason}")
            return []
        
        params = {
            'q': query,
            'language': language,
            'pageSize': min(max_articles, 100),
            'sortBy': sort_by
        }
        
        if from_date:
            params['from'] = from_date.strftime('%Y-%m-%d')
        
        if to_date:
            params['to'] = to_date.strftime('%Y-%m-%d')
        
        success, response_data = self._make_api_request('everything', params)
        
        source.record_request(
            success=success,
            error_message=response_data.get('error', '') if not success else ''
        )
        
        if not success:
            return []
        
        # Process results similar to fetch_top_headlines
        articles = []
        raw_articles = response_data.get('articles', [])
        
        for article_data in raw_articles:
            try:
                title = article_data.get('title', '').strip()
                content = article_data.get('content') or article_data.get('description', '')
                url = article_data.get('url', '')
                
                if not title or not content or not url:
                    continue
                
                # Skip articles with [Removed] content
                if content and '[Removed]' in content:
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
                    publication_date=self._parse_date(article_data.get('publishedAt')),
                    author=article_data.get('author'),
                    tags=[],
                    priority=source.priority
                )
                
                articles.append(dto)
                
            except Exception as e:
                logger.error(f"Error processing NewsAPI search result: {str(e)}")
                continue
        
        return articles
    
    def get_sources(self, language: str = 'en', country: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available news sources from NewsAPI"""
        params = {
            'language': language
        }
        
        if country:
            params['country'] = country
        
        success, response_data = self._make_api_request('sources', params)
        
        if success:
            return response_data.get('sources', [])
        
        return []
    
    def _parse_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """Parse date string from API response"""
        if not date_string:
            return None
        
        try:
            # NewsAPI uses ISO format
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse NewsAPI date: {date_string}")
            return None
    
    def get_available_categories(self) -> List[str]:
        """Get list of available categories from NewsAPI"""
        return [
            'business', 'entertainment', 'general', 'health', 
            'science', 'sports', 'technology'
        ]
    
    def get_available_countries(self) -> Dict[str, str]:
        """Get list of available countries for content filtering"""
        return {
            'us': 'United States',
            'gb': 'United Kingdom',
            'ca': 'Canada',
            'au': 'Australia',
            'ar': 'Argentina',
            'mx': 'Mexico'
        }
    
    def test_connection(self, source: ContentSource) -> Tuple[bool, str]:
        """Test API connection and authentication"""
        can_request, reason = self._can_make_request(source)
        if not can_request:
            return False, reason
        
        # Make a minimal test request
        params = {
            'language': 'en',
            'pageSize': 1
        }
        
        success, response_data = self._make_api_request('top-headlines', params)
        
        if success:
            return True, "NewsAPI connection successful"
        else:
            error_msg = response_data.get('error', 'Unknown error')
            return False, f"NewsAPI connection failed: {error_msg}"