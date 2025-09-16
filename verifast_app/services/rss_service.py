"""
RSS Feed Processing Service
Handles content acquisition from RSS feeds with validation and error handling
"""

import feedparser
import requests
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ..models_content_acquisition import ContentSource, ContentFingerprint
from ..pydantic_models.dto import ContentAcquisitionDTO

logger = logging.getLogger(__name__)


class RSSProcessor:
    """Service for processing RSS feeds"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VeriFast/1.0 RSS Reader (Educational Content Platform)'
        })
        
        # Rate limiting for RSS feeds
        self.min_request_interval = 2  # Seconds between requests
        self.last_request_time = None
        
        # Feed parsing settings
        feedparser.USER_AGENT = 'VeriFast/1.0 RSS Reader'
    
    def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                wait_time = self.min_request_interval - elapsed
                logger.debug(f"RSS rate limiting: waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
    
    def _detect_language(self, text: str) -> str:
        """Detect language of text content"""
        try:
            import langdetect
            detected = langdetect.detect(text)
            
            # Map detected languages to our supported languages
            if detected in ['en']:
                return 'en'
            elif detected in ['es']:
                return 'es'
            else:
                # Default to English for unsupported languages
                return 'en'
                
        except ImportError:
            logger.warning("Language detection failed: langdetect package not available")
            return 'en'  # Default to English
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}")
            return 'en'  # Default to English
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content text"""
        if not content:
            return ""
        
        # Remove HTML tags
        import re
        content = re.sub(r'<[^>]+>', '', content)
        
        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Remove common RSS artifacts
        content = re.sub(r'\[…\]|\[...\]|\[more\]', '', content, flags=re.IGNORECASE)
        
        return content
    
    def _extract_full_content(self, url: str) -> Optional[str]:
        """Extract full content from article URL using newspaper3k"""
        try:
            from newspaper import Article
            
            article = Article(url)
            article.download()
            article.parse()
            
            if article.text and len(article.text) > 200:
                return article.text
            
        except Exception as e:
            logger.debug(f"Could not extract full content from {url}: {str(e)}")
        
        return None
    
    def _extract_image(self, entry: Any, content: str, url: str) -> Optional[str]:
        """Extract representative image URL from RSS entry or content."""
        try:
            # 1) media_content
            media_content = getattr(entry, 'media_content', []) or []
            for m in media_content:
                if isinstance(m, dict):
                    mtype = str(m.get('type', '')).lower()
                    if m.get('medium') == 'image' or mtype.startswith('image'):
                        if m.get('url'):
                            return m.get('url')
                    # Some feeds embed URL directly
                    if m.get('url') and (m.get('url').endswith(('.jpg', '.jpeg', '.png', '.webp'))):
                        return m.get('url')
            
            # 2) media_thumbnail
            media_thumb = getattr(entry, 'media_thumbnail', []) or []
            for t in media_thumb:
                if isinstance(t, dict) and t.get('url'):
                    return t.get('url')
            
            # 3) enclosures
            enclosures = getattr(entry, 'enclosures', []) or []
            for e in enclosures:
                if isinstance(e, dict):
                    etype = str(e.get('type', '')).lower()
                    href = e.get('href') or e.get('url')
                    if etype.startswith('image') and href:
                        return href
                    if href and href.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        return href
            
            # 4) HTML img in content/summary
            import re
            html = (content or '')
            m = re.search(r'<img[^>]+src=[\"\\\']([^\"\
\']+)[\"\\\']', html, flags=re.IGNORECASE)
            if m:
                return m.group(1)
        except Exception:
            return None
        return None
        """Extract full content from article URL using newspaper3k"""
        try:
            from newspaper import Article
            
            article = Article(url)
            article.download()
            article.parse()
            
            if article.text and len(article.text) > 200:
                return article.text
            
        except Exception as e:
            logger.debug(f"Could not extract full content from {url}: {str(e)}")
        
        return None
    
    def _parse_date(self, date_tuple) -> Optional[datetime]:
        """Parse date from feedparser date tuple"""
        if not date_tuple:
            return None
        
        try:
            # Convert time tuple to datetime
            from datetime import timezone as dt_timezone
            return datetime(*date_tuple[:6], tzinfo=dt_timezone.utc)
        except (ValueError, TypeError):
            return None
    
    def _is_video_entry(self, entry: Any, content: str, url: str) -> bool:
        """Heuristics to detect video-only items to avoid processing as articles."""
        try:
            url_l = (url or "").lower()
            title_l = (getattr(entry, 'title', '') or '').lower()
            content_l = (content or '').lower()

            # Known video platforms or URL markers
            video_domains = [
                'youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com',
                'facebook.com/watch', 'tiktok.com', 'instagram.com/reel',
                'instagram.com/tv', 'player.vimeo'
            ]
            if any(d in url_l for d in video_domains):
                return True

            # Common video path segments
            path_markers = ['/video/', '/videos/', '/watch/']
            if any(m in url_l for m in path_markers):
                return True

            # RSS media fields (feedparser)
            media_content = getattr(entry, 'media_content', []) or []
            enclosures = getattr(entry, 'enclosures', []) or []
            try:
                # Some feeds store tuples, ensure dict access safely
                if any((isinstance(m, dict) and (m.get('medium') == 'video' or str(m.get('type', '')).startswith('video'))) for m in media_content):
                    return True
            except Exception:
                pass
            try:
                if any((isinstance(e, dict) and str(e.get('type', '')).startswith('video')) for e in enclosures):
                    return True
            except Exception:
                pass

            # Content markers
            content_markers = [
                '<iframe', 'video/mp4', 'application/x-mpegurl', '.m3u8', '.mp4',
                'watch the video', 'ver video', 'ver el video', 'mire el video',
                'see video', 'play video'
            ]
            if any(marker in content_l for marker in content_markers):
                return True

            # Title markers
            title_markers = ['video:', '[video]', '(video)']
            if any(marker in title_l for marker in title_markers):
                return True
        except Exception:
            return False
        return False

    def fetch_feed_articles(
        self,
        source: ContentSource,
        max_articles: int = 20,
        extract_full_content: bool = True
    ) -> List[ContentAcquisitionDTO]:
        """Fetch articles from RSS feed"""
        
        # Check if we can make request
        can_request, reason = source.can_make_request()
        if not can_request:
            logger.warning(f"Cannot fetch from {source.name}: {reason}")
            return []
        
        self._wait_for_rate_limit()
        
        try:
            self.last_request_time = time.time()
            
            # Parse RSS feed
            logger.info(f"Fetching RSS feed: {source.url}")
            feed = feedparser.parse(source.url)
            
            # Check for feed errors
            if hasattr(feed, 'bozo') and feed.bozo:
                logger.warning(f"RSS feed has parsing issues: {source.url}")
            
            if not hasattr(feed, 'entries') or not feed.entries:
                error_msg = "No entries found in RSS feed"
                source.record_request(success=False, error_message=error_msg)
                return []
            
            # Record successful request
            source.record_request(success=True)
            
            articles = []
            processed_count = 0
            
            for entry in feed.entries[:max_articles]:
                try:
                    # Extract basic information
                    title = entry.get('title', '').strip()
                    url = entry.get('link', '').strip()
                    
                    if not title or not url:
                        logger.debug("Skipping entry with missing title or URL")
                        continue
                    
                    # Get content (try multiple fields)
                    content = ""
                    if hasattr(entry, 'content') and entry.content:
                        content = entry.content[0].value if isinstance(entry.content, list) else entry.content
                    elif hasattr(entry, 'summary'):
                        content = entry.summary
                    elif hasattr(entry, 'description'):
                        content = entry.description
                    
                    content = self._clean_content(content)
                    
                    # Try to extract full content if content is too short
                    if extract_full_content and len(content) < 300:
                        full_content = self._extract_full_content(url)
                        if full_content:
                            content = full_content
                    
                    # Reject known video-only entries
                    if self._is_video_entry(entry, content, url):
                        logger.debug(f"Skipping video-only entry: {title}")
                        continue
                    
                    # Skip if content is still too short
                    if len(content) < 150:
                        logger.debug(f"Skipping article with insufficient content: {title}")
                        continue
                    
                    # Detect language
                    language = self._detect_language(f"{title} {content}")
                    
                    # Filter by source language preference
                    if source.language != 'both' and source.language != language:
                        logger.debug(f"Skipping article in {language}, source expects {source.language}")
                        continue
                    
                    # Check for duplicates
                    is_duplicate, duplicate_reason = ContentFingerprint.is_duplicate(
                        url=url,
                        title=title,
                        content=content,
                        language=language,
                        topic_category=self._categorize_content(title, content)
                    )
                    
                    if is_duplicate:
                        logger.debug(f"Skipping duplicate: {duplicate_reason}")
                        continue
                    
                    # Extract publication date
                    pub_date = None
                    if hasattr(entry, 'published_parsed'):
                        pub_date = self._parse_date(entry.published_parsed)
                    elif hasattr(entry, 'updated_parsed'):
                        pub_date = self._parse_date(entry.updated_parsed)
                    
                    # Extract author
                    author = None
                    if hasattr(entry, 'author'):
                        author = entry.author
                    elif hasattr(entry, 'authors') and entry.authors:
                        author = entry.authors[0].get('name', '') if isinstance(entry.authors[0], dict) else str(entry.authors[0])
                    
                    # Extract tags
                    tags = []
                    if hasattr(entry, 'tags') and entry.tags:
                        tags = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
                    
                    # Create DTO
                    dto = ContentAcquisitionDTO(
                        source_id=source.name,
                        source_type='rss',
                        url=url,
                        title=title,
                        content=content,
                        language=language,
                        publication_date=pub_date,
                        author=author,
                        tags=tags,
                        image_url=self._extract_image(entry, content, url),
                        priority=source.priority
                    )
                    
                    articles.append(dto)
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing RSS entry: {str(e)}")
                    continue
            
            logger.info(f"Processed {processed_count} articles from RSS feed {source.name}")
            return articles
            
        except Exception as e:
            error_msg = f"RSS feed processing error: {str(e)}"
            logger.error(error_msg)
            source.record_request(success=False, error_message=error_msg)
            return []
    
    def _categorize_content(self, title: str, content: str) -> str:
        """Simple content categorization based on keywords"""
        text = f"{title} {content}".lower()
        
        # Define category keywords
        categories = {
            'technology': ['tech', 'software', 'ai', 'artificial intelligence', 'computer', 'digital', 'internet', 'app', 'programming'],
            'science': ['science', 'research', 'study', 'discovery', 'experiment', 'scientific', 'biology', 'physics', 'chemistry'],
            'health': ['health', 'medical', 'medicine', 'doctor', 'hospital', 'disease', 'treatment', 'wellness', 'fitness'],
            'business': ['business', 'economy', 'market', 'finance', 'company', 'corporate', 'investment', 'startup', 'entrepreneur'],
            'politics': ['politics', 'government', 'election', 'policy', 'political', 'congress', 'senate', 'president', 'minister'],
            'sports': ['sports', 'football', 'basketball', 'soccer', 'baseball', 'tennis', 'olympics', 'athlete', 'game', 'match'],
            'entertainment': ['entertainment', 'movie', 'film', 'music', 'celebrity', 'actor', 'actress', 'concert', 'show', 'tv'],
            'education': ['education', 'school', 'university', 'student', 'teacher', 'learning', 'academic', 'study', 'course']
        }
        
        # Count keyword matches for each category
        category_scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                category_scores[category] = score
        
        # Return category with highest score, or 'general' if no matches
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return 'general'
    
    def validate_feed(self, url: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate RSS feed URL and return feed information"""
        try:
            feed = feedparser.parse(url)
            
            if hasattr(feed, 'bozo') and feed.bozo:
                if hasattr(feed, 'bozo_exception'):
                    return False, f"Feed parsing error: {feed.bozo_exception}", {}
            
            if not hasattr(feed, 'feed') or not feed.feed:
                return False, "Invalid RSS feed format", {}
            
            if not hasattr(feed, 'entries') or not feed.entries:
                return False, "No entries found in feed", {}
            
            # Extract feed information
            feed_info = {
                'title': feed.feed.get('title', 'Unknown'),
                'description': feed.feed.get('description', ''),
                'link': feed.feed.get('link', ''),
                'language': feed.feed.get('language', 'unknown'),
                'entry_count': len(feed.entries),
                'last_updated': feed.feed.get('updated', ''),
                'generator': feed.feed.get('generator', ''),
            }
            
            return True, "Valid RSS feed", feed_info
            
        except Exception as e:
            return False, f"Feed validation error: {str(e)}", {}
    
    def get_feed_info(self, source: ContentSource) -> Dict[str, Any]:
        """Get detailed information about RSS feed"""
        try:
            feed = feedparser.parse(source.url)
            
            info = {
                'title': feed.feed.get('title', 'Unknown'),
                'description': feed.feed.get('description', ''),
                'link': feed.feed.get('link', ''),
                'language': feed.feed.get('language', 'unknown'),
                'entry_count': len(feed.entries) if hasattr(feed, 'entries') else 0,
                'last_updated': feed.feed.get('updated', ''),
                'generator': feed.feed.get('generator', ''),
                'categories': [],
                'recent_entries': []
            }
            
            # Get categories if available
            if hasattr(feed.feed, 'tags') and feed.feed.tags:
                info['categories'] = [tag.term for tag in feed.feed.tags if hasattr(tag, 'term')]
            
            # Get recent entry titles
            if hasattr(feed, 'entries'):
                info['recent_entries'] = [
                    {
                        'title': entry.get('title', 'No title'),
                        'published': entry.get('published', ''),
                        'link': entry.get('link', '')
                    }
                    for entry in feed.entries[:5]
                ]
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting feed info: {str(e)}")
            return {'error': str(e)}
    
    def test_feed_connection(self, source: ContentSource) -> Tuple[bool, str]:
        """Test RSS feed connection and accessibility"""
        try:
            # Check if we can make request
            can_request, reason = source.can_make_request()
            if not can_request:
                return False, reason
            
            # Try to fetch and parse feed
            response = self.session.get(source.url, timeout=30)
            
            if response.status_code != 200:
                return False, f"HTTP {response.status_code}: {response.reason}"
            
            # Try to parse the feed
            feed = feedparser.parse(response.content)
            
            if hasattr(feed, 'bozo') and feed.bozo:
                if hasattr(feed, 'bozo_exception'):
                    return False, f"Feed parsing error: {feed.bozo_exception}"
            
            if not hasattr(feed, 'entries') or not feed.entries:
                return False, "No entries found in feed"
            
            return True, f"Connection successful, found {len(feed.entries)} entries"
            
        except requests.exceptions.Timeout:
            return False, "Connection timeout"
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"