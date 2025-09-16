"""
Content Deduplication Service
Handles duplicate detection and content diversity management
"""

import hashlib
import logging
from typing import List, Dict, Any, Tuple, Set
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count
from difflib import SequenceMatcher

from ..models_content_acquisition import ContentSource, ContentFingerprint
from ..models import Article
from ..pydantic_models.dto import ContentAcquisitionDTO

logger = logging.getLogger(__name__)


class ContentDeduplicator:
    """Service for detecting and managing content duplicates"""
    
    def __init__(self):
        # Similarity thresholds
        self.title_similarity_threshold = 0.8
        self.content_similarity_threshold = 0.7
        self.url_similarity_threshold = 0.9
        
        # Topic limits (4 articles per topic per day per language)
        self.max_articles_per_topic_per_day = 4
        
        # Content quality thresholds
        self.min_content_length = 200
        self.max_content_length = 50000
    
    def _create_hash(self, text: str) -> str:
        """Create SHA-256 hash of text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using SequenceMatcher (fast lexical)."""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _feature_hash_vector(self, text: str, dim: int = 256) -> list:
        """Compute a lightweight hashed feature vector for text (bag-of-words hashing).
        This approximates a semantic vector without external dependencies.
        """
        import re
        vec = [0.0] * dim
        # tokenize simple words (>=3 chars) and downcase
        tokens = re.findall(r"[a-zA-Z]{3,}", text.lower())
        if not tokens:
            return vec
        for tok in tokens:
            # simple hashing trick
            h = hash(tok) % dim
            vec[h] += 1.0
        # L2 normalize
        norm = sum(v*v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def _cosine(self, v1: list, v2: list) -> float:
        """Cosine similarity between two equal-length lists."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        return float(sum(a*b for a, b in zip(v1, v2)))
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        import re
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common punctuation
        text = re.sub(r'[^\w\s]', '', text)
        
        return text
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> Set[str]:
        """Extract keywords from text for similarity comparison"""
        import re
        
        # Simple keyword extraction (in production, consider using NLP libraries)
        words = re.findall(r'\b\w{4,}\b', text.lower())
        
        # Remove common stop words
        stop_words = {
            'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been',
            'were', 'said', 'each', 'which', 'their', 'time', 'would', 'there',
            'could', 'other', 'more', 'very', 'what', 'know', 'just', 'first',
            'into', 'over', 'think', 'also', 'your', 'work', 'life', 'only',
            'can', 'still', 'should', 'after', 'being', 'now', 'made', 'before'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Return most frequent keywords
        from collections import Counter
        return set(dict(Counter(keywords).most_common(max_keywords)).keys())
    
    def _categorize_content(self, title: str, content: str) -> str:
        """Categorize content based on keywords and patterns"""
        text = f"{title} {content}".lower()
        
        # Enhanced category detection
        categories = {
            'technology': {
                'keywords': ['tech', 'software', 'ai', 'artificial intelligence', 'computer', 
                           'digital', 'internet', 'app', 'programming', 'code', 'data', 'algorithm'],
                'weight': 1.0
            },
            'science': {
                'keywords': ['science', 'research', 'study', 'discovery', 'experiment', 
                           'scientific', 'biology', 'physics', 'chemistry', 'medical', 'clinical'],
                'weight': 1.0
            },
            'health': {
                'keywords': ['health', 'medical', 'medicine', 'doctor', 'hospital', 
                           'disease', 'treatment', 'wellness', 'fitness', 'nutrition'],
                'weight': 1.0
            },
            'business': {
                'keywords': ['business', 'economy', 'market', 'finance', 'company', 
                           'corporate', 'investment', 'startup', 'entrepreneur', 'revenue'],
                'weight': 1.0
            },
            'politics': {
                'keywords': ['politics', 'government', 'election', 'policy', 'political', 
                           'congress', 'senate', 'president', 'minister', 'law', 'legal'],
                'weight': 1.0
            },
            'education': {
                'keywords': ['education', 'school', 'university', 'student', 'teacher', 
                           'learning', 'academic', 'course', 'curriculum', 'degree'],
                'weight': 1.2  # Slightly favor educational content
            },
            'environment': {
                'keywords': ['environment', 'climate', 'green', 'sustainable', 'ecology', 
                           'renewable', 'carbon', 'pollution', 'conservation', 'nature'],
                'weight': 1.1
            }
        }
        
        # Calculate weighted scores
        category_scores = {}
        for category, config in categories.items():
            keywords = config['keywords']
            weight = config['weight']
            
            score = sum(1 for keyword in keywords if keyword in text) * weight
            if score > 0:
                category_scores[category] = score
        
        # Return category with highest score
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return 'general'
    
    def check_duplicate(self, dto: ContentAcquisitionDTO) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Check if content is a duplicate
        Returns: (is_duplicate, reason, details)
        """
        details = {
            'url_hash': self._create_hash(dto.url),
            'title_hash': self._create_hash(dto.title),
            'content_hash': self._create_hash(dto.content),
            'category': self._categorize_content(dto.title, dto.content),
            'checks_performed': []
        }
        
        # 1. Exact URL duplicate check
        url_hash = details['url_hash']
        existing_url = ContentFingerprint.objects.filter(url_hash=url_hash).first()
        if existing_url:
            details['checks_performed'].append('exact_url_match')
            return True, f"Exact URL duplicate found (ID: {existing_url.id})", details
        
        # 2. Exact content hash duplicate check
        content_hash = details['content_hash']
        existing_content = ContentFingerprint.objects.filter(content_hash=content_hash).first()
        if existing_content:
            details['checks_performed'].append('exact_content_match')
            return True, f"Exact content duplicate found (ID: {existing_content.id})", details
        
        # 3. Title similarity check
        title_hash = details['title_hash']
        similar_titles = ContentFingerprint.objects.filter(
            language=dto.language,
            first_seen__gte=timezone.now() - timedelta(days=7)  # Check last 7 days
        ).exclude(title_hash=title_hash)
        
        for fingerprint in similar_titles:
            # Get the associated article to compare titles
            if fingerprint.article:
                similarity = self._calculate_similarity(dto.title, fingerprint.article.title)
                if similarity >= self.title_similarity_threshold:
                    details['checks_performed'].append('title_similarity')
                    details['title_similarity'] = similarity
                    return True, f"Similar title found (similarity: {similarity:.2f})", details
        
        # 4. Topic saturation check
        category = details['category']
        today = timezone.now().date()
        
        topic_count = ContentFingerprint.objects.filter(
            topic_category=category,
            language=dto.language,
            first_seen__date=today
        ).count()
        
        details['checks_performed'].append('topic_saturation')
        details['topic_count_today'] = topic_count
        
        if topic_count >= self.max_articles_per_topic_per_day:
            return True, f"Topic saturation: {topic_count} articles for '{category}' today", details
        
        # 5. Content length validation
        content_length = len(dto.content)
        details['content_length'] = content_length
        
        if content_length < self.min_content_length:
            details['checks_performed'].append('content_too_short')
            return True, f"Content too short: {content_length} characters (min: {self.min_content_length})", details
        
        if content_length > self.max_content_length:
            details['checks_performed'].append('content_too_long')
            return True, f"Content too long: {content_length} characters (max: {self.max_content_length})", details
        
        # 6. Source diversity check (ensure variety from different sources)
        source_articles_today = ContentFingerprint.objects.filter(
            source__name=dto.source_id,
            topic_category=category,
            language=dto.language,
            first_seen__date=today
        ).count()
        
        details['checks_performed'].append('source_diversity')
        details['source_articles_today'] = source_articles_today
        
        # Allow max 2 articles per source per topic per day
        if source_articles_today >= 2:
            return True, f"Source diversity limit: {source_articles_today} articles from {dto.source_id} for '{category}' today", details
        
        # 7. Lightweight semantic similarity (for near-duplicates)
        # Compare hashed feature vectors of title+lead content (first 600 chars)
        title_lead_new = f"{dto.title} {(dto.content or '')[:600]}"
        vec_new = self._feature_hash_vector(title_lead_new)
        
        recent_fingerprints = ContentFingerprint.objects.filter(
            language=dto.language,
            topic_category=category,
            first_seen__gte=timezone.now() - timedelta(days=3)
        ).select_related('article')
        
        best_cos = 0.0
        for fingerprint in recent_fingerprints:
            if fingerprint.article:
                title_lead_old = f"{fingerprint.article.title} {(fingerprint.article.content or '')[:600]}"
                vec_old = self._feature_hash_vector(title_lead_old)
                cos = self._cosine(vec_new, vec_old)
                if cos > best_cos:
                    best_cos = cos
                if cos >= 0.90:  # near-duplicate threshold
                    details['checks_performed'].append('semantic_hash_similarity')
                    details['semantic_cosine'] = cos
                    return True, f"High semantic similarity: {cos:.2f}", details
        details['semantic_cosine_max'] = best_cos
        
        # Content passed all duplicate checks
        details['checks_performed'].append('all_checks_passed')
        return False, "Content is unique", details
    
    def create_fingerprint(self, dto: ContentAcquisitionDTO, article=None) -> ContentFingerprint:
        """Create content fingerprint for tracking"""
        category = self._categorize_content(dto.title, dto.content)
        
        # Get or create source
        try:
            source = ContentSource.objects.get(name=dto.source_id)
        except ContentSource.DoesNotExist:
            logger.warning(f"Source {dto.source_id} not found, creating placeholder")
            source = ContentSource.objects.create(
                name=dto.source_id,
                description=f"Auto-created source for {dto.source_id}",
                source_type=dto.source_type,
                url=dto.url,
                language=dto.language
            )
        
        fingerprint = ContentFingerprint.objects.create(
            url_hash=self._create_hash(dto.url),
            title_hash=self._create_hash(dto.title),
            content_hash=self._create_hash(dto.content),
            language=dto.language,
            topic_category=category,
            source=source,
            article=article
        )
        
        logger.info(f"Created fingerprint {fingerprint.id} for {category} article in {dto.language}")
        return fingerprint
    
    def get_topic_statistics(self, language: str = None, days: int = 7) -> Dict[str, Any]:
        """Get statistics about topic distribution and saturation"""
        start_date = timezone.now() - timedelta(days=days)
        
        queryset = ContentFingerprint.objects.filter(first_seen__gte=start_date)
        if language:
            queryset = queryset.filter(language=language)
        
        # Topic distribution
        topic_stats = queryset.values('topic_category', 'language').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Daily breakdown
        daily_stats = queryset.extra(
            select={'day': 'date(first_seen)'}
        ).values('day', 'topic_category', 'language').annotate(
            count=Count('id')
        ).order_by('-day', 'topic_category')
        
        # Source diversity
        source_stats = queryset.values('source__name', 'topic_category', 'language').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'period_days': days,
            'total_articles': queryset.count(),
            'topic_distribution': list(topic_stats),
            'daily_breakdown': list(daily_stats),
            'source_diversity': list(source_stats),
            'languages': list(queryset.values_list('language', flat=True).distinct())
        }
    
    def cleanup_old_fingerprints(self, days_to_keep: int = 30) -> int:
        """Clean up old fingerprints to prevent database bloat"""
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        old_fingerprints = ContentFingerprint.objects.filter(
            first_seen__lt=cutoff_date,
            article__isnull=True  # Only delete fingerprints not associated with articles
        )
        
        count = old_fingerprints.count()
        old_fingerprints.delete()
        
        logger.info(f"Cleaned up {count} old content fingerprints")
        return count
    
    def get_duplicate_candidates(self, dto: ContentAcquisitionDTO, limit: int = 5) -> List[Dict[str, Any]]:
        """Get potential duplicate candidates for manual review"""
        candidates = []
        
        # Find articles with similar titles
        recent_articles = Article.objects.filter(
            language=dto.language,
            timestamp__gte=timezone.now() - timedelta(days=7)
        )
        
        for article in recent_articles[:20]:  # Limit to recent articles
            title_similarity = self._calculate_similarity(dto.title, article.title)
            
            if title_similarity >= 0.5:  # Lower threshold for candidates
                content_similarity = 0
                if len(article.content) > 100:
                    content_similarity = self._calculate_similarity(
                        dto.content[:1000],  # Compare first 1000 chars
                        article.content[:1000]
                    )
                
                candidates.append({
                    'article_id': article.id,
                    'title': article.title,
                    'url': article.url,
                    'title_similarity': title_similarity,
                    'content_similarity': content_similarity,
                    'overall_similarity': (title_similarity + content_similarity) / 2,
                    'timestamp': article.timestamp
                })
        
        # Sort by overall similarity
        candidates.sort(key=lambda x: x['overall_similarity'], reverse=True)
        
        return candidates[:limit]