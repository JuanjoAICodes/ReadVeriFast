"""
Content Acquisition Orchestrator
Coordinates multi-source content fetching with prioritization and fallback logic
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count

from ..models_content_acquisition import ContentSource, ContentAcquisitionJob, AcquisitionMetrics
from ..models import Article
from ..services.newsdata_service import NewsDataService
from ..services.rss_service import RSSProcessor
from ..services.content_deduplicator import ContentDeduplicator
from ..services.language_processor import LanguageProcessor
from ..pydantic_models.dto import ContentAcquisitionDTO

logger = logging.getLogger(__name__)


class ContentAcquisitionOrchestrator:
    """Orchestrates content acquisition from multiple sources"""
    
    def __init__(self):
        self.newsdata_service = NewsDataService()
        self.rss_processor = RSSProcessor()
        self.deduplicator = ContentDeduplicator()
        self.language_processor = LanguageProcessor()
        
        # Acquisition settings
        self.max_articles_per_run = 50
        self.max_sources_per_run = 10
        self.source_timeout = 30  # seconds
        
        # Priority weights for source selection
        self.priority_weights = {
            'critical': 4,
            'high': 3,
            'normal': 2,
            'low': 1
        }
    
    def orchestrate_acquisition(
        self,
        languages: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        max_articles: Optional[int] = None,
        force_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main orchestration method for content acquisition
        
        Args:
            languages: List of languages to acquire ('en', 'es')
            categories: List of categories to focus on
            max_articles: Maximum articles to acquire
            force_sources: Force acquisition from specific sources
            
        Returns:
            Dictionary with acquisition results and statistics
        """
        start_time = timezone.now()
        
        # Set defaults
        languages = languages or ['en', 'es']
        max_articles = max_articles or self.max_articles_per_run
        
        logger.info(f"Starting orchestrated content acquisition: "
                   f"languages={languages}, max_articles={max_articles}")
        
        # Initialize results tracking
        results = {
            'start_time': start_time,
            'languages': languages,
            'categories': categories,
            'max_articles': max_articles,
            'sources_processed': 0,
            'sources_successful': 0,
            'sources_failed': 0,
            'total_articles_found': 0,
            'total_articles_processed': 0,
            'total_articles_duplicated': 0,
            'total_articles_rejected': 0,
            'source_results': [],
            'errors': []
        }
        
        try:
            # Get prioritized sources
            sources = self._get_prioritized_sources(languages, force_sources)
            
            if not sources:
                results['errors'].append("No active sources available")
                return results
            
            # Process each source
            articles_acquired = 0
            
            for source in sources[:self.max_sources_per_run]:
                if articles_acquired >= max_articles:
                    logger.info(f"Reached max articles limit ({max_articles})")
                    break
                
                try:
                    # Calculate articles to fetch from this source
                    remaining_articles = max_articles - articles_acquired
                    source_max_articles = min(remaining_articles, 
                                            self._calculate_source_quota(source))
                    
                    # Acquire content from source
                    source_result = self._acquire_from_source(
                        source, 
                        languages, 
                        categories, 
                        source_max_articles
                    )
                    
                    # Update results
                    results['sources_processed'] += 1
                    results['source_results'].append(source_result)
                    
                    if source_result['success']:
                        results['sources_successful'] += 1
                        results['total_articles_found'] += source_result['articles_found']
                        results['total_articles_processed'] += source_result['articles_processed']
                        results['total_articles_duplicated'] += source_result['articles_duplicated']
                        results['total_articles_rejected'] += source_result['articles_rejected']
                        
                        articles_acquired += source_result['articles_processed']
                    else:
                        results['sources_failed'] += 1
                        results['errors'].append(f"{source.name}: {source_result['error']}")
                    
                except Exception as e:
                    logger.error(f"Error processing source {source.name}: {str(e)}")
                    results['sources_failed'] += 1
                    results['errors'].append(f"{source.name}: {str(e)}")
                    continue
            
            # Calculate final statistics
            results['end_time'] = timezone.now()
            results['duration_seconds'] = (results['end_time'] - start_time).total_seconds()
            results['success_rate'] = (results['sources_successful'] / results['sources_processed'] * 100) if results['sources_processed'] > 0 else 0
            results['articles_per_minute'] = (results['total_articles_processed'] / (results['duration_seconds'] / 60)) if results['duration_seconds'] > 0 else 0
            
            logger.info(f"Orchestrated acquisition completed: "
                       f"{results['total_articles_processed']} articles processed "
                       f"from {results['sources_successful']}/{results['sources_processed']} sources "
                       f"in {results['duration_seconds']:.1f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Orchestration failed: {str(e)}", exc_info=True)
            results['errors'].append(f"Orchestration error: {str(e)}")
            results['end_time'] = timezone.now()
            results['duration_seconds'] = (results['end_time'] - start_time).total_seconds()
            return results
    
    def _get_prioritized_sources(
        self, 
        languages: List[str], 
        force_sources: Optional[List[str]] = None
    ) -> List[ContentSource]:
        """Get sources prioritized by health, priority, and recent performance"""
        
        # Base query for active sources
        queryset = ContentSource.objects.filter(
            is_active=True,
            status__in=['active', 'rate_limited']
        )
        
        # Filter by language support
        language_filter = Q()
        for lang in languages:
            language_filter |= Q(language=lang) | Q(language='both')
        queryset = queryset.filter(language_filter)
        
        # Force specific sources if requested
        if force_sources:
            queryset = queryset.filter(name__in=force_sources)
        
        # Get sources with health scores
        sources = list(queryset)
        
        # Calculate priority scores
        for source in sources:
            # Base priority score
            priority_score = self.priority_weights.get(source.priority, 1)
            
            # Health score (0-100)
            health_score = source.get_health_score()
            
            # Recent performance score
            performance_score = self._calculate_performance_score(source)
            
            # Combined score (weighted average)
            source.orchestration_score = (
                priority_score * 0.3 +
                health_score * 0.4 +
                performance_score * 0.3
            )
        
        # Sort by orchestration score (highest first)
        sources.sort(key=lambda s: s.orchestration_score, reverse=True)
        
        logger.info(f"Prioritized {len(sources)} sources for acquisition")
        return sources
    
    def _calculate_performance_score(self, source: ContentSource) -> float:
        """Calculate recent performance score for a source (0-100)"""
        try:
            # Get recent metrics (last 7 days)
            recent_date = timezone.now().date() - timedelta(days=7)
            
            metrics = AcquisitionMetrics.objects.filter(
                source=source,
                date__gte=recent_date
            ).aggregate(
                total_found=Count('articles_found'),
                total_processed=Count('articles_processed'),
                total_requests=Count('total_requests'),
                successful_requests=Count('successful_requests')
            )
            
            # Calculate success rates
            processing_rate = 0
            if metrics['total_found'] > 0:
                processing_rate = (metrics['total_processed'] / metrics['total_found']) * 100
            
            request_success_rate = 0
            if metrics['total_requests'] > 0:
                request_success_rate = (metrics['successful_requests'] / metrics['total_requests']) * 100
            
            # Combined performance score
            performance_score = (processing_rate * 0.6 + request_success_rate * 0.4)
            
            return min(performance_score, 100)
            
        except Exception as e:
            logger.warning(f"Could not calculate performance score for {source.name}: {str(e)}")
            return 50  # Default neutral score
    
    def _calculate_source_quota(self, source: ContentSource) -> int:
        """Calculate how many articles to fetch from a source"""
        base_quota = {
            'critical': 15,
            'high': 12,
            'normal': 8,
            'low': 5
        }.get(source.priority, 8)
        
        # Adjust based on health score
        health_score = source.get_health_score()
        health_multiplier = health_score / 100
        
        # Adjust based on recent success rate
        performance_score = self._calculate_performance_score(source)
        performance_multiplier = performance_score / 100
        
        # Calculate final quota
        quota = int(base_quota * health_multiplier * performance_multiplier)
        
        return max(quota, 2)  # Minimum 2 articles per source
    
    def _acquire_from_source(
        self,
        source: ContentSource,
        languages: List[str],
        categories: Optional[List[str]],
        max_articles: int
    ) -> Dict[str, Any]:
        """Acquire content from a single source"""
        
        result = {
            'source_name': source.name,
            'source_type': source.source_type,
            'success': False,
            'articles_found': 0,
            'articles_processed': 0,
            'articles_duplicated': 0,
            'articles_rejected': 0,
            'error': None,
            'duration_seconds': 0
        }
        
        start_time = timezone.now()
        
        try:
            # Check if source can make requests
            can_request, reason = source.can_make_request()
            if not can_request:
                result['error'] = reason
                return result
            
            # Create acquisition job
            job = ContentAcquisitionJob.objects.create(
                job_type='manual',
                source=source,
                config_data={
                    'languages': languages,
                    'categories': categories,
                    'max_articles': max_articles
                }
            )
            job.start_job()
            
            # Acquire content based on source type
            articles = []
            
            if source.source_type == 'newsdata_api':
                articles = self._fetch_from_newsdata(source, languages, categories, max_articles)
            elif source.source_type == 'rss':
                articles = self._fetch_from_rss(source, max_articles)
            else:
                result['error'] = f"Unsupported source type: {source.source_type}"
                job.fail_job(result['error'])
                return result
            
            result['articles_found'] = len(articles)
            
            # Process each article
            for dto in articles:
                try:
                    processed_result = self._process_single_article(dto)
                    
                    if processed_result == 'processed':
                        result['articles_processed'] += 1
                    elif processed_result == 'duplicate':
                        result['articles_duplicated'] += 1
                    else:
                        result['articles_rejected'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing article: {str(e)}")
                    result['articles_rejected'] += 1
                    continue
            
            # Complete the job
            job.complete_job(
                articles_found=result['articles_found'],
                articles_processed=result['articles_processed'],
                articles_duplicated=result['articles_duplicated'],
                articles_rejected=result['articles_rejected']
            )
            
            result['success'] = True
            result['duration_seconds'] = (timezone.now() - start_time).total_seconds()
            
            logger.info(f"Acquired from {source.name}: "
                       f"{result['articles_processed']}/{result['articles_found']} processed")
            
            return result
            
        except Exception as e:
            error_msg = f"Acquisition error: {str(e)}"
            result['error'] = error_msg
            result['duration_seconds'] = (timezone.now() - start_time).total_seconds()
            
            # Mark job as failed
            try:
                job.fail_job(error_msg)
            except Exception:
                pass
            
            logger.error(f"Failed to acquire from {source.name}: {error_msg}")
            return result
    
    def _fetch_from_newsdata(
        self,
        source: ContentSource,
        languages: List[str],
        categories: Optional[List[str]],
        max_articles: int
    ) -> List[ContentAcquisitionDTO]:
        """Fetch articles from NewsData.io API"""
        articles = []
        
        # Filter languages based on source support
        supported_languages = []
        if source.language == 'both':
            supported_languages = [lang for lang in languages if lang in ['en', 'es']]
        elif source.language in languages:
            supported_languages = [source.language]
        
        articles_per_language = max_articles // len(supported_languages) if supported_languages else 0
        
        for language in supported_languages:
            try:
                if categories:
                    # Fetch by category
                    for category in categories:
                        lang_articles = self.newsdata_service.fetch_latest_articles(
                            source=source,
                            language=language,
                            category=category,
                            max_articles=articles_per_language // len(categories)
                        )
                        articles.extend(lang_articles)
                else:
                    # Fetch general articles
                    lang_articles = self.newsdata_service.fetch_latest_articles(
                        source=source,
                        language=language,
                        max_articles=articles_per_language
                    )
                    articles.extend(lang_articles)
                    
            except Exception as e:
                logger.error(f"Error fetching NewsData articles for {language}: {str(e)}")
                continue
        
        return articles[:max_articles]  # Ensure we don't exceed limit
    
    def _fetch_from_rss(self, source: ContentSource, max_articles: int) -> List[ContentAcquisitionDTO]:
        """Fetch articles from RSS feed"""
        try:
            return self.rss_processor.fetch_feed_articles(
                source=source,
                max_articles=max_articles,
                extract_full_content=True
            )
        except Exception as e:
            logger.error(f"Error fetching RSS articles: {str(e)}")
            return []
    
    def _process_single_article(self, dto: ContentAcquisitionDTO) -> str:
        """
        Process a single article DTO
        Returns: 'processed', 'duplicate', or 'rejected'
        """
        try:
            # Check for duplicates
            is_duplicate, reason, details = self.deduplicator.check_duplicate(dto)
            if is_duplicate:
                return 'duplicate'
            
            # Process language-specific content
            dto = self.language_processor.process_content_for_language(dto)
            
            # Validate content quality
            is_valid, validation_reason, validation_details = self.language_processor.validate_language_content(dto)
            if not is_valid:
                return 'rejected'
            
            # Always fetch full content from the URL using newspaper3k
            from .scraper import fetch_full_article
            success, full_text = fetch_full_article(dto.url, language=dto.language)
            # Minimum content length enforcement
            MIN_WORDS = 300
            if not success or not full_text or len(full_text.split()) < MIN_WORDS:
                return 'rejected'

            # Create article in database with scraped content
            with transaction.atomic():
                article = Article.objects.create(
                    title=dto.title,
                    url=dto.url,
                    content=full_text,
                    language=dto.language,
                    publication_date=dto.publication_date,
                    image_url=getattr(dto, 'image_url', None),
                    processing_status='pending',
                    word_count=len(full_text.split()),
                    acquisition_source=dto.source_id,
                    acquisition_timestamp=timezone.now()
                )
                
                # Create fingerprint
                self.deduplicator.create_fingerprint(dto, article)
                
                # Add tags if provided
                if dto.tags:
                    from ..models import Tag
                    for tag_name in dto.tags[:5]:  # Limit to 5 tags
                        tag, created = Tag.objects.get_or_create(
                            name=tag_name.strip()
                        )
                        article.tags.add(tag)
                
                # Trigger async processing for quiz generation
                from ..tasks import process_article_async
                process_article_async.delay(article.id)
                
                return 'processed'
                
        except Exception as e:
            logger.error(f"Error processing article: {str(e)}")
            return 'rejected'
    
    def get_acquisition_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get acquisition statistics for the specified period"""
        start_date = timezone.now().date() - timedelta(days=days)
        
        # Get metrics
        metrics = AcquisitionMetrics.objects.filter(
            date__gte=start_date,
            hour__isnull=True  # Daily metrics only
        ).aggregate(
            total_found=Count('articles_found'),
            total_processed=Count('articles_processed'),
            total_duplicated=Count('articles_duplicated'),
            total_rejected=Count('articles_rejected'),
            total_requests=Count('total_requests'),
            successful_requests=Count('successful_requests')
        )
        
        # Get source performance
        source_stats = AcquisitionMetrics.objects.filter(
            date__gte=start_date,
            hour__isnull=True
        ).values('source__name', 'source__source_type').annotate(
            articles_found=Count('articles_found'),
            articles_processed=Count('articles_processed'),
            success_rate=Count('successful_requests') * 100.0 / Count('total_requests')
        ).order_by('-articles_processed')
        
        # Get language distribution
        language_stats = AcquisitionMetrics.objects.filter(
            date__gte=start_date,
            hour__isnull=True
        ).exclude(language='').values('language').annotate(
            articles_processed=Count('articles_processed')
        ).order_by('-articles_processed')
        
        return {
            'period_days': days,
            'overall_metrics': metrics,
            'source_performance': list(source_stats),
            'language_distribution': list(language_stats),
            'success_rate': (metrics['successful_requests'] / metrics['total_requests'] * 100) if metrics['total_requests'] > 0 else 0,
            'processing_rate': (metrics['total_processed'] / metrics['total_found'] * 100) if metrics['total_found'] > 0 else 0
        }