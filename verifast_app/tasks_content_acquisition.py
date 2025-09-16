"""
Celery Tasks for Automated Content Acquisition
Background tasks for scheduled content fetching and processing
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.db import transaction
import time

from .models_content_acquisition import (
    ContentSource,
    ContentAcquisitionJob,
    AcquisitionMetrics,
)
from .models import Article
from .services.newsdata_service import NewsDataService
from .services.gnews_service import GNewsService
from .services.newsapi_service import NewsAPIService
from .services.rss_service import RSSProcessor
from .services.content_deduplicator import ContentDeduplicator
from .services.language_processor import LanguageProcessor
from .pydantic_models.dto import ContentAcquisitionDTO

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300, queue='acquisition')
def acquire_content_from_source(
    self, source_id: int, job_type: str = "scheduled", max_articles: int = 10
):
    """
    Acquire content from a specific source
    """
    try:
        # Get the content source
        source = ContentSource.objects.get(id=source_id, is_active=True)

        # Create acquisition job
        job = ContentAcquisitionJob.objects.create(
            job_type=job_type,
            source=source,
            config_data={"max_articles": max_articles, "task_id": self.request.id},
        )

        job.start_job()
        logger.info(f"Starting content acquisition from {source.name}")

        # Initialize services
        deduplicator = ContentDeduplicator()
        language_processor = LanguageProcessor()

        articles_found = 0
        articles_processed = 0
        articles_duplicated = 0
        articles_rejected = 0

        # Acquire content based on source type
        if source.source_type == "newsdata_api":
            newsdata_service = NewsDataService()

            # Fetch articles for both languages if source supports both
            languages = ["en", "es"] if source.language == "both" else [source.language]

            for lang in languages:
                try:
                    articles = newsdata_service.fetch_latest_articles(
                        source=source,
                        language=lang,
                        max_articles=max_articles // len(languages),
                    )

                    articles_found += len(articles)

                    for dto in articles:
                        processed = _process_article_dto(
                            dto, deduplicator, language_processor
                        )
                        if processed == "processed":
                            articles_processed += 1
                        elif processed == "duplicate":
                            articles_duplicated += 1
                        else:
                            articles_rejected += 1

                except Exception as e:
                    logger.error(
                        f"Error fetching from NewsData API for {lang}: {str(e)}"
                    )
                    continue

        elif source.source_type == "gnews_api":
            gnews_service = GNewsService()

            # Fetch articles for both languages if source supports both
            languages = ["en", "es"] if source.language == "both" else [source.language]

            for lang in languages:
                try:
                    # Get category from config_data if available
                    # Map 'general' to 'top' for NewsData.io compatibility
                    category = source.config_data.get('category', 'general')
                    if category == 'general':
                        category = 'top'  # NewsData.io uses 'top' instead of 'general'
                    country = source.config_data.get('country')
                    
                    articles = gnews_service.fetch_top_headlines(
                        source=source,
                        language=lang,
                        category=category,
                        country=country,
                        max_articles=max_articles // len(languages),
                    )

                    articles_found += len(articles)

                    for dto in articles:
                        processed = _process_article_dto(
                            dto, deduplicator, language_processor
                        )
                        if processed == "processed":
                            articles_processed += 1
                        elif processed == "duplicate":
                            articles_duplicated += 1
                        else:
                            articles_rejected += 1

                except Exception as e:
                    logger.error(
                        f"Error fetching from GNews API for {lang}: {str(e)}"
                    )
                    continue

        elif source.source_type == "newsapi":
            newsapi_service = NewsAPIService()

            # Fetch articles for both languages if source supports both
            languages = ["en", "es"] if source.language == "both" else [source.language]

            for lang in languages:
                try:
                    # Get configuration from config_data
                    category = source.config_data.get('category', 'general')
                    country = source.config_data.get('country')
                    sources = source.config_data.get('sources')
                    
                    articles = newsapi_service.fetch_top_headlines(
                        source=source,
                        language=lang,
                        category=category,
                        country=country,
                        sources=sources,
                        max_articles=max_articles // len(languages),
                    )

                    articles_found += len(articles)

                    for dto in articles:
                        processed = _process_article_dto(
                            dto, deduplicator, language_processor
                        )
                        if processed == "processed":
                            articles_processed += 1
                        elif processed == "duplicate":
                            articles_duplicated += 1
                        else:
                            articles_rejected += 1

                except Exception as e:
                    logger.error(
                        f"Error fetching from NewsAPI for {lang}: {str(e)}"
                    )
                    continue

        elif source.source_type == "rss":
            rss_processor = RSSProcessor()

            try:
                articles = rss_processor.fetch_feed_articles(
                    source=source, max_articles=max_articles, extract_full_content=True
                )

                articles_found = len(articles)

                for dto in articles:
                    processed = _process_article_dto(
                        dto, deduplicator, language_processor
                    )
                    if processed == "processed":
                        articles_processed += 1
                    elif processed == "duplicate":
                        articles_duplicated += 1
                    else:
                        articles_rejected += 1

            except Exception as e:
                logger.error(f"Error processing RSS feed {source.url}: {str(e)}")
                job.fail_job(f"RSS processing error: {str(e)}")
                return {"success": False, "error": str(e)}

        else:
            error_msg = f"Unsupported source type: {source.source_type}"
            logger.error(error_msg)
            job.fail_job(error_msg)
            return {"success": False, "error": error_msg}

        # Complete the job
        job.complete_job(
            articles_found=articles_found,
            articles_processed=articles_processed,
            articles_duplicated=articles_duplicated,
            articles_rejected=articles_rejected,
        )

        # Update metrics
        _update_acquisition_metrics(
            source,
            articles_found,
            articles_processed,
            articles_duplicated,
            articles_rejected,
        )

        logger.info(
            f"Completed acquisition from {source.name}: "
            f"{articles_processed}/{articles_found} articles processed"
        )

        return {
            "success": True,
            "source_name": source.name,
            "articles_found": articles_found,
            "articles_processed": articles_processed,
            "articles_duplicated": articles_duplicated,
            "articles_rejected": articles_rejected,
            "job_id": job.id,
        }

    except ContentSource.DoesNotExist:
        error_msg = f"Content source {source_id} not found or inactive"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

    except Exception as e:
        logger.error(
            f"Unexpected error in content acquisition: {str(e)}", exc_info=True
        )

        # Retry the task if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task in {self.default_retry_delay} seconds...")
            raise self.retry(countdown=self.default_retry_delay, exc=e)

        # Mark job as failed if it exists
        try:
            job = ContentAcquisitionJob.objects.get(
                config_data__task_id=self.request.id, status="running"
            )
            job.fail_job(str(e))
        except ContentAcquisitionJob.DoesNotExist:
            pass

        return {"success": False, "error": str(e)}


@shared_task(queue='acquisition')
def scheduled_content_acquisition():
    """
    Main scheduled task that runs every 4 hours to acquire content from all active sources
    """
    logger.info("Starting scheduled content acquisition")

    # Get all active sources
    active_sources = ContentSource.objects.filter(
        is_active=True, status__in=["active", "rate_limited"]
    ).order_by("priority", "last_successful_fetch")

    if not active_sources.exists():
        logger.warning("No active content sources found")
        return {"success": True, "message": "No active sources"}

    # Track overall results
    total_sources = active_sources.count()
    failed_sources = 0

    # Process each source
    for source in active_sources:
        try:
            # Check if source can make requests
            can_request, reason = source.can_make_request()
            if not can_request:
                logger.info(f"Skipping {source.name}: {reason}")
                continue

            # Determine max articles based on source priority
            max_articles = {"critical": 20, "high": 15, "normal": 10, "low": 5}.get(
                source.priority, 10
            )

            # Launch acquisition task
            result = acquire_content_from_source.delay(
                source_id=source.id, job_type="scheduled", max_articles=max_articles
            )

            # Wait a bit between sources to avoid overwhelming APIs
            time.sleep(2)

            logger.info(
                f"Launched acquisition task for {source.name} (task: {result.id})"
            )

        except Exception as e:
            logger.error(f"Error launching acquisition for {source.name}: {str(e)}")
            failed_sources += 1
            continue

    logger.info(
        f"Scheduled content acquisition completed: "
        f"launched tasks for {total_sources} sources"
    )

    return {
        "success": True,
        "total_sources": total_sources,
        "message": f"Launched acquisition tasks for {total_sources} sources",
    }


@shared_task(queue='maintenance')
def cleanup_old_acquisition_data():
    """
    Clean up old acquisition data to prevent database bloat
    """
    logger.info("Starting acquisition data cleanup")

    # Clean up old fingerprints
    deduplicator = ContentDeduplicator()
    cleaned_fingerprints = deduplicator.cleanup_old_fingerprints(days_to_keep=30)

    # Clean up old failed jobs (keep for 7 days)
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=7)

    old_jobs = ContentAcquisitionJob.objects.filter(
        status="failed", completed_at__lt=cutoff_date
    )
    old_job_count = old_jobs.count()
    old_jobs.delete()

    # Clean up old metrics (keep daily metrics for 90 days, hourly for 7 days)
    daily_cutoff = timezone.now() - timedelta(days=90)
    hourly_cutoff = timezone.now() - timedelta(days=7)

    old_daily_metrics = AcquisitionMetrics.objects.filter(
        hour__isnull=True, date__lt=daily_cutoff.date()
    )
    old_daily_count = old_daily_metrics.count()
    old_daily_metrics.delete()

    old_hourly_metrics = AcquisitionMetrics.objects.filter(
        hour__isnull=False, date__lt=hourly_cutoff.date()
    )
    old_hourly_count = old_hourly_metrics.count()
    old_hourly_metrics.delete()

    logger.info(
        f"Cleanup completed: {cleaned_fingerprints} fingerprints, "
        f"{old_job_count} jobs, {old_daily_count} daily metrics, "
        f"{old_hourly_count} hourly metrics"
    )

    return {
        "success": True,
        "cleaned_fingerprints": cleaned_fingerprints,
        "cleaned_jobs": old_job_count,
        "cleaned_daily_metrics": old_daily_count,
        "cleaned_hourly_metrics": old_hourly_count,
    }


@shared_task(queue='monitoring')
def health_check_sources():
    """
    Perform health checks on all content sources
    """
    logger.info("Starting source health checks")

    sources = ContentSource.objects.all()
    health_results = {}

    for source in sources:
        try:
            if source.source_type == "newsdata_api":
                newsdata_service = NewsDataService()
                is_healthy, message = newsdata_service.test_connection(source)
            elif source.source_type == "rss":
                rss_processor = RSSProcessor()
                is_healthy, message = rss_processor.test_feed_connection(source)
            elif source.source_type == "gnews_api":
                from .services.gnews_service import GNewsService
                gnews_service = GNewsService()
                is_healthy, message = gnews_service.test_connection(source)
            elif source.source_type == "newsapi":
                from .services.newsapi_service import NewsAPIService
                newsapi_service = NewsAPIService()
                is_healthy, message = newsapi_service.test_connection(source)
            else:
                is_healthy, message = (
                    False,
                    f"Unknown source type: {source.source_type}",
                )

            # Update source status based on health check
            if is_healthy:
                if source.status in ["error", "maintenance"]:
                    source.status = "active"
                    source.consecutive_failures = 0
                    source.save(
                        update_fields=["status", "consecutive_failures", "updated_at"]
                    )
            else:
                source.consecutive_failures += 1
                if source.consecutive_failures >= 3:
                    source.status = "error"
                source.last_error = message
                source.save(
                    update_fields=[
                        "consecutive_failures",
                        "status",
                        "last_error",
                        "updated_at",
                    ]
                )

            health_results[source.name] = {
                "healthy": is_healthy,
                "message": message,
                "health_score": source.get_health_score(),
            }

        except Exception as e:
            logger.error(f"Health check failed for {source.name}: {str(e)}")
            health_results[source.name] = {
                "healthy": False,
                "message": f"Health check error: {str(e)}",
                "health_score": 0,
            }

    # Calculate overall health
    healthy_sources = sum(1 for result in health_results.values() if result["healthy"])
    total_sources = len(health_results)
    overall_health = (healthy_sources / total_sources * 100) if total_sources > 0 else 0

    logger.info(
        f"Health check completed: {healthy_sources}/{total_sources} sources healthy "
        f"({overall_health:.1f}%)"
    )

    return {
        "success": True,
        "overall_health_percentage": overall_health,
        "healthy_sources": healthy_sources,
        "total_sources": total_sources,
        "source_details": health_results,
    }


def _process_article_dto(
    dto: ContentAcquisitionDTO,
    deduplicator: ContentDeduplicator,
    language_processor: LanguageProcessor,
) -> str:
    """
    Process a single article DTO
    Returns: 'processed', 'duplicate', or 'rejected'
    """
    try:
        # Check for duplicates
        is_duplicate, reason, details = deduplicator.check_duplicate(dto)
        if is_duplicate:
            logger.debug(f"Skipping duplicate article: {reason}")
            return "duplicate"

        # Process language-specific content
        dto = language_processor.process_content_for_language(dto)

        # Validate content quality
        is_valid, validation_reason, validation_details = (
            language_processor.validate_language_content(dto)
        )
        if not is_valid:
            logger.debug(f"Rejecting article: {validation_reason}")
            return "rejected"

        # Create article in database
        with transaction.atomic():
            article = Article.objects.create(
                title=dto.title,
                url=dto.url,
                content=dto.content,
                language=dto.language,
                publication_date=dto.publication_date,
                image_url=getattr(dto, 'image_url', None),
                processing_status="pending",
                word_count=len(dto.content.split()),
                acquisition_source=dto.source_id,
                acquisition_timestamp=timezone.now(),
            )

            # Create fingerprint
            deduplicator.create_fingerprint(dto, article)

            # Add tags if provided
            if dto.tags:
                from .models import Tag

                for tag_name in dto.tags[:5]:  # Limit to 5 tags
                    tag, created = Tag.objects.get_or_create(
                        name=tag_name.strip()
                    )
                    article.tags.add(tag)

            # Trigger async processing for quiz generation
            from .tasks import process_article

            process_article.delay(article.id)

            logger.info(f"Created article {article.id}: {article.title[:50]}...")
            return "processed"

    except Exception as e:
        logger.error(f"Error processing article DTO: {str(e)}")
        return "rejected"


def _update_acquisition_metrics(
    source: ContentSource,
    articles_found: int,
    articles_processed: int,
    articles_duplicated: int,
    articles_rejected: int,
):
    """Update acquisition metrics for reporting"""
    try:
        now = timezone.now()
        today = now.date()
        current_hour = now.hour

        # Update daily metrics
        daily_metrics, created = AcquisitionMetrics.objects.get_or_create(
            date=today,
            source=source,
            language="",  # Aggregate across languages
            hour=None,
            defaults={
                "articles_found": 0,
                "articles_processed": 0,
                "articles_duplicated": 0,
                "articles_rejected": 0,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
            },
        )

        daily_metrics.articles_found += articles_found
        daily_metrics.articles_processed += articles_processed
        daily_metrics.articles_duplicated += articles_duplicated
        daily_metrics.articles_rejected += articles_rejected
        daily_metrics.total_requests += 1
        daily_metrics.successful_requests += 1 if articles_found > 0 else 0
        daily_metrics.failed_requests += 0 if articles_found > 0 else 1
        daily_metrics.save()

        # Update hourly metrics
        hourly_metrics, created = AcquisitionMetrics.objects.get_or_create(
            date=today,
            hour=current_hour,
            source=source,
            language="",
            defaults={
                "articles_found": 0,
                "articles_processed": 0,
                "articles_duplicated": 0,
                "articles_rejected": 0,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
            },
        )

        hourly_metrics.articles_found += articles_found
        hourly_metrics.articles_processed += articles_processed
        hourly_metrics.articles_duplicated += articles_duplicated
        hourly_metrics.articles_rejected += articles_rejected
        hourly_metrics.total_requests += 1
        hourly_metrics.successful_requests += 1 if articles_found > 0 else 0
        hourly_metrics.failed_requests += 0 if articles_found > 0 else 1
        hourly_metrics.save()

    except Exception as e:
        logger.error(f"Error updating acquisition metrics: {str(e)}")


# Periodic task configuration (add to Django settings)
CELERY_BEAT_SCHEDULE = {
    "scheduled-content-acquisition": {
        "task": "verifast_app.tasks_content_acquisition.scheduled_content_acquisition",
        "schedule": 4 * 60 * 60,  # Every 4 hours
        "options": {"queue": "content_acquisition"},
    },
    "cleanup-acquisition-data": {
        "task": "verifast_app.tasks_content_acquisition.cleanup_old_acquisition_data",
        "schedule": 24 * 60 * 60,  # Daily
        "options": {"queue": "maintenance"},
    },
    "health-check-sources": {
        "task": "verifast_app.tasks_content_acquisition.health_check_sources",
        "schedule": 60 * 60,  # Every hour
        "options": {"queue": "monitoring"},
    },
}
