"""
GNews API Integration Service
Handles content acquisition from GNews API with rate limiting and error handling
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


class GNewsService:
    """Service for interacting with GNews API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'GNEWS_API_KEY', '')
        self.base_url = "https://gnews.io/api/v4"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VeriFast/1.0 (Educational Content Platform)'
        })
        
        # Rate limiting (GNews free tier: 100 requests/day)
        self.requests_per_day = 100
        self.requests_per_hour = 10  # Conservative limit
        self.min_request_interval = 6  # Seconds between requests
        
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
                logger.info(f"GNews rate limiting: waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
    
    def _make_api_request(self, endpoint: str, params: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Make API request with error handling and rate limiting"""
        self._wait_for_rate_limit()
        
        # Add API key to parameters
        params['apikey'] = self.api_key
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            self.last_request_time = time.time()
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return True, data
            
            elif response.status_code == 429:
                # Rate limit exceeded
                logger.warning("GNews API rate limit exceeded")
                return False, {'error': 'Rate limit exceeded', 'retry_after': 3600}
            
            elif response.status_code == 401:
                logger.error("GNews API authentication failed")
                return False, {'error': 'Authentication failed'}
            
            elif response.status_code == 403:
                logger.error("GNews API access forbidden - check API key")
                return False, {'error': 'Access forbidden'}
            
            else:
                logger.error(f"GNews API HTTP error: {response.status_code}")
                return False, {'error': f'HTTP {response.status_code}'}
                
        except requests.exceptions.Timeout:
            logger.error("GNews API request timeout")
            return False, {'error': 'Request timeout'}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"GNews API request error: {str(e)}")
            return False, {'error': str(e)}
    
    def fetch_top_headlines(
        self, 
        source: ContentSource,
        language: str = 'en',
        country: Optional[str] = None,
        category: Optional[str] = None,
        max_articles: int = 10
    ) -> List[ContentAcquisitionDTO]:
        """Fetch top headlines from GNews API"""
        
        # Check if we can make request
        can_request, reason = self._can_make_request(source)
        if not can_request:
            logger.warning(f"Cannot make request to {source.name}: {reason}")
            return []
        
        # Build API parameters
        params = {
            'lang': language,
            'max': min(max_articles, 10),  # API limit is 10 per request
            'expand': 'content'  # Get full content
        }
        
        if country:
            params['country'] = country
        
        if category:
            params['category'] = category
        
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
                    logger.warning("Skipping GNews article with missing required fields")
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
                    logger.info(f"Skipping duplicate GNews article: {duplicate_reason}")
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
                    author=article_data.get('source', {}).get('name'),
                    tags=[],  # GNews doesn't provide tags
                    image_url=article_data.get('image'),
                    priority=source.priority
                )
                
                articles.append(dto)
                
            except Exception as e:
                logger.error(f"Error processing GNews article: {str(e)}")
                continue
        
        logger.info(f"Fetched {len(articles)} articles from GNews for {source.name}")
        return articles
    
    def search_articles(
        self,
        source: ContentSource,
        query: str,
        language: str = 'en',
        max_articles: int = 10,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[ContentAcquisitionDTO]:
        """Search articles by query using GNews API"""
        
        can_request, reason = self._can_make_request(source)
        if not can_request:
            logger.warning(f"Cannot make request to {source.name}: {reason}")
            return []
        
        params = {
            'q': query,
            'lang': language,
            'max': min(max_articles, 10),
            'expand': 'content'
        }
        
        if from_date:
            params['from'] = from_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        if to_date:
            params['to'] = to_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        success, response_data = self._make_api_request('search', params)
        
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
                    author=article_data.get('source', {}).get('name'),
                    tags=[],
                    image_url=article_data.get('image'),
                    priority=source.priority
                )
                
                articles.append(dto)
                
            except Exception as e:
                logger.error(f"Error processing GNews search result: {str(e)}")
                continue
        
        return articles
    
    def _parse_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """Parse date string from API response"""
        if not date_string:
            return None
        
        try:
            # GNews uses ISO format
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse GNews date: {date_string}")
            return None
    
    def get_available_categories(self) -> List[str]:
        """Get list of available categories from GNews"""
        return [
            'general', 'world', 'nation', 'business', 'technology', 
            'entertainment', 'sports', 'science', 'health'
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
            'lang': 'en',
            'max': 1
        }
        
        success, response_data = self._make_api_request('top-headlines', params)
        
        if success:
            return True, "GNews connection successful"
        else:
            error_msg = response_data.get('error', 'Unknown error')
            return False, f"GNews connection failed: {error_msg}"