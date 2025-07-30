"""
Wikipedia Integration Service

This module provides Wikipedia API integration for tag validation and content processing.
It handles Wikipedia article retrieval, content cleaning, and integration with VeriFast's
article processing pipeline.
"""

import logging
import re
from typing import Optional, Dict, Any, Tuple
import wikipediaapi # type: ignore
from .models import Tag, Article

logger = logging.getLogger(__name__)


class WikipediaService:
    """
    Service class for Wikipedia API integration and content processing.
    
    Handles tag validation, content retrieval, and article creation from Wikipedia.
    """
    
    def __init__(self, language='en'):
        """
        Initialize Wikipedia service with specified language.
        
        Args:
            language (str): Wikipedia language code (default: 'en')
        """
        self.language = language
        self.wiki = wikipediaapi.Wikipedia(
            language=language,
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent='VeriFast/1.0 (https://verifast.app) Educational Speed Reading Platform'
        )
    
    def validate_tag_with_wikipedia(self, tag_name: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate if a tag has a corresponding Wikipedia article.
        
        Args:
            tag_name (str): The tag name to validate
            
        Returns:
            Tuple[bool, Optional[Dict]]: (is_valid, wikipedia_data)
            wikipedia_data contains: url, title, summary, content
        """
        try:
            # Clean and format tag name for Wikipedia search
            search_term = self._clean_tag_name(tag_name)
            
            logger.info(f"Validating tag '{tag_name}' with Wikipedia search term '{search_term}'")
            
            # Get Wikipedia page
            page = self.wiki.page(search_term)
            
            if not page.exists():
                logger.info(f"Wikipedia page does not exist for '{search_term}'")
                return False, None
            
            # Check if it's a disambiguation page
            if self._is_disambiguation_page(page):
                logger.info(f"Wikipedia page '{search_term}' is a disambiguation page")
                # Try to get the first non-disambiguation option
                disambiguated_page = self._handle_disambiguation(page)
                if disambiguated_page:
                    page = disambiguated_page
                else:
                    return False, None
            
            # Extract Wikipedia data
            wikipedia_data = {
                'url': page.fullurl,
                'title': page.title,
                'summary': page.summary[:500] if page.summary else '',
                'content': page.text,
                'categories': list(page.categories.keys())[:10],  # Limit categories
                'links': list(page.links.keys())[:20]  # Limit links
            }
            
            logger.info(f"Successfully validated tag '{tag_name}' with Wikipedia article '{page.title}'")
            return True, wikipedia_data
            
        except Exception as e:
            logger.error(f"Error validating tag '{tag_name}' with Wikipedia: {str(e)}")
            return False, None
    
    def process_wikipedia_content(self, content: str) -> str:
        """
        Clean and process Wikipedia content for VeriFast article format.
        
        Args:
            content (str): Raw Wikipedia content
            
        Returns:
            str: Cleaned content suitable for VeriFast processing
        """
        if not content:
            return ""
        
        # Remove Wikipedia-specific markup
        cleaned_content = self._remove_wikipedia_markup(content)
        
        # Clean up formatting
        cleaned_content = self._clean_text_formatting(cleaned_content)
        
        # Limit content length for better reading experience
        cleaned_content = self._limit_content_length(cleaned_content)
        
        return cleaned_content
    
    def create_wikipedia_article(self, tag: Tag, wikipedia_data: Dict[str, Any]) -> Optional[Article]:
        """
        Create a VeriFast Article from Wikipedia data.
        
        Args:
            tag (Tag): The tag associated with this Wikipedia article
            wikipedia_data (Dict): Wikipedia data from validate_tag_with_wikipedia
            
        Returns:
            Optional[Article]: Created article or None if failed
        """
        try:
            # Process content
            processed_content = self.process_wikipedia_content(wikipedia_data['content'])
            
            if not processed_content or len(processed_content) < 100:
                logger.warning(f"Wikipedia content too short for tag '{tag.name}'")
                return None
            
            # Create article
            article: Article = Article.objects.create(
                title=f"Wikipedia: {wikipedia_data['title']}",
                content=processed_content,
                url=wikipedia_data['url'],
                source='Wikipedia',
                article_type='wikipedia',
                processing_status='pending',  # Will be processed through pipeline
                reading_level=8.0,  # Default reading level for Wikipedia
                word_count=len(processed_content.split()),
                letter_count=len(processed_content.replace(' ', '')),
                summary=wikipedia_data['summary']
            )
            
            # Associate with tag
            article.tags.add(tag)
            
            # Update tag with Wikipedia data
            tag.wikipedia_url = wikipedia_data['url']
            tag.wikipedia_content = processed_content
            tag.description = wikipedia_data['summary']
            tag.is_validated = True
            tag.save()
            
            # Queue for processing through the NLP pipeline
            from .tasks import process_wikipedia_article
            process_wikipedia_article.delay(article.id) # type: ignore
            
            logger.info(f"Created Wikipedia article '{article.title}' for tag '{tag.name}' and queued for processing")
            return article
            
        except Exception as e:
            logger.error(f"Error creating Wikipedia article for tag '{tag.name}': {str(e)}")
            return None
    
    def update_tag_with_wikipedia(self, tag: Tag) -> bool:
        """
        Update an existing tag with Wikipedia validation and content.
        
        Args:
            tag (Tag): The tag to update
            
        Returns:
            bool: True if successfully updated, False otherwise
        """
        is_valid, wikipedia_data = self.validate_tag_with_wikipedia(tag.name)
        
        if not is_valid or not wikipedia_data:
            logger.info(f"Tag '{tag.name}' could not be validated with Wikipedia")
            tag.is_validated = False
            tag.save()
            return False
        
        # Update tag with Wikipedia data
        tag.wikipedia_url = wikipedia_data['url']
        tag.wikipedia_content = self.process_wikipedia_content(wikipedia_data['content'])
        tag.description = wikipedia_data['summary']
        tag.is_validated = True
        tag.save()
        
        # Create Wikipedia article if it doesn't exist
        wikipedia_articles = tag.article_set.filter(article_type='wikipedia')
        if not wikipedia_articles.exists():
            self.create_wikipedia_article(tag, wikipedia_data)
        
        return True
    
    def _clean_tag_name(self, tag_name: str) -> str:
        """Clean tag name for Wikipedia search."""
        # Remove special characters and normalize
        cleaned = re.sub(r'[^\w\s-]', '', tag_name)
        # Replace underscores and multiple spaces with single spaces
        cleaned = re.sub(r'[_\s]+', ' ', cleaned)
        # Capitalize first letter of each word
        cleaned = cleaned.title().strip()
        return cleaned
    
    def _is_disambiguation_page(self, page) -> bool:
        """Check if Wikipedia page is a disambiguation page."""
        return 'disambiguation' in page.title.lower() or \
               'may refer to' in page.text[:500].lower()
    
    def _handle_disambiguation(self, page) -> Optional[Any]:
        """Handle disambiguation pages by finding the most relevant option."""
        try:
            # Look for links in the disambiguation page
            links = list(page.links.keys())[:5]  # Check first 5 links
            
            for link_title in links:
                link_page = self.wiki.page(link_title)
                if link_page.exists() and not self._is_disambiguation_page(link_page):
                    logger.info(f"Found disambiguation target: {link_title}")
                    return link_page
            
            return None
        except Exception as e:
            logger.error(f"Error handling disambiguation: {str(e)}")
            return None
    
    def _remove_wikipedia_markup(self, content: str) -> str:
        """Remove Wikipedia-specific markup from content."""
        # Remove section headers with multiple equals signs
        content = re.sub(r'={2,}.*?={2,}', '', content)
        
        # Remove references and citations
        content = re.sub(r'\[\d+\]', '', content)
        content = re.sub(r'\[citation needed\]', '', content)
        
        # Remove template markup
        content = re.sub(r'\{\{.*?\}\}', '', content, flags=re.DOTALL)
        
        # Remove file and image references
        content = re.sub(r'\[\[File:.*?\]\]', '', content, flags=re.DOTALL)
        content = re.sub(r'\[\[Image:.*?\]\]', '', content, flags=re.DOTALL)
        
        # Clean up links - keep the display text
        content = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', r'\2', content)
        content = re.sub(r'\[\[([^\]]+)\]\]', r'\1', content)
        
        return content
    
    def _clean_text_formatting(self, content: str) -> str:
        """Clean up text formatting."""
        # Remove multiple newlines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Remove multiple spaces
        content = re.sub(r' {2,}', ' ', content)
        
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in content.split('\n')]
        content = '\n'.join(line for line in lines if line)
        
        return content.strip()
    
    def _limit_content_length(self, content: str, max_words: int = 2000) -> str:
        """Limit content length for better reading experience."""
        words = content.split()
        if len(words) <= max_words:
            return content
        
        # Find a good breaking point near the limit
        limited_words = words[:max_words]
        
        # Try to end at a sentence
        text = ' '.join(limited_words)
        sentences = text.split('.')
        if len(sentences) > 1:
            # Remove the last incomplete sentence
            text = '.'.join(sentences[:-1]) + '.'
        
        return text


# Convenience functions for easy access
def validate_tag(tag_name: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Validate a tag name with Wikipedia."""
    service = WikipediaService()
    return service.validate_tag_with_wikipedia(tag_name)


def update_tag_wikipedia_data(tag: Tag) -> bool:
    """Update a tag with Wikipedia data."""
    service = WikipediaService()
    return service.update_tag_with_wikipedia(tag)


def create_wikipedia_article_for_tag(tag: Tag) -> Optional[Article]:
    """Create a Wikipedia article for a tag."""
    service = WikipediaService()
    is_valid, wikipedia_data = service.validate_tag_with_wikipedia(tag.name)
    
    if is_valid and wikipedia_data:
        return service.create_wikipedia_article(tag, wikipedia_data)
    
    return None