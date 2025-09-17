from celery import shared_task
from celery.utils.log import get_task_logger  # type: ignore
import json
import time
import random
from django.utils import timezone
from django.db import transaction, OperationalError
from django.db import connection

import newspaper # type: ignore
from .models import Article, Tag
from .decorators import with_fallback

# Import from the services.py file, not the services package
from . import services

# Import Pydantic models for serialization
from .pydantic_models.dto import ArticleAnalysisDTO, XPTransactionDTO
from .pydantic_models.llm import MasterAnalysisResponse
from .validation.pipeline import ValidationPipeline

logger = get_task_logger(__name__)
validation_pipeline = ValidationPipeline(logger_name=__name__)


from .database_utils import with_database_retry, DatabaseLockManager, ensure_connection_closed


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
@with_database_retry(max_retries=3, base_delay=2, max_delay=30)
def process_article(self, article_id):
    """
    Orchestrates the full analysis pipeline with Pydantic validation and serialization.
    This task now also acts as a dispatcher for different article types.
    """
    logger.info(f"Starting processing for article ID: {article_id}")
    
    try:
        with DatabaseLockManager(timeout=60):
            # Check if article exists and is in correct state
            try:
                article = Article.objects.get(id=article_id)
            except Article.DoesNotExist:
                logger.error(f"Article {article_id} not found in database. Task aborted.")
                return {"success": False, "error": "Article not found"}
            
            # Check if article is in correct state for processing
            if article.processing_status not in ["pending", "failed", "failed_quota"]:
                logger.info(f"Article {article_id} status is '{article.processing_status}', skipping processing.")
                return {"success": False, "error": f"Article status is {article.processing_status}"}
            
            # Lock article for processing with retry logic
            try:
                with transaction.atomic():
                    article = Article.objects.select_for_update(nowait=False).get(
                        id=article_id, 
                        processing_status__in=["pending", "failed", "failed_quota"]
                    )
                    article.processing_status = "processing"
                    article.save()
            except Article.DoesNotExist:
                logger.warning(f"Article {article_id} was modified by another process. Task aborted.")
                return {"success": False, "error": "Article state changed"}
            except OperationalError as e:
                if 'database is locked' in str(e).lower():
                    logger.warning(f"Database locked while trying to lock article {article_id}, will retry")
                    # Let the decorator handle the retry
                    raise
                else:
                    logger.error(f"Database error while locking article {article_id}: {e}")
                    raise

            # --- Dispatch based on article type ---
            if article.article_type == "wikipedia":
                logger.info(
                    f"Article {article_id} is a Wikipedia article. Delegating to process_wikipedia_article."
                )
                result = process_wikipedia_article.delay(article.id)
                return {"success": True, "delegated_to": "process_wikipedia_article", "task_id": result.id}

            # --- Continue with regular article processing ---
            return _process_regular_article(article, article_id)
            
    except Exception as e:
        logger.error(f"Critical error in process_article for ID {article_id}: {e}")
        ensure_connection_closed()
        raise


def _process_regular_article(article, article_id):
    """Helper function to process regular (non-Wikipedia) articles."""
    try:
        # --- 0. Ensure correct language before analysis ---
        try:
            from .services.language_processor import LanguageProcessor
            lp = LanguageProcessor()
            detected_lang, confidence = lp.detect_language(article.content or "", article.title or "")
            if detected_lang in ['en', 'es'] and detected_lang != article.language and confidence >= 0.7:
                article.language = detected_lang
                article.save(update_fields=['language'])
                logger.info(f"Language corrected to {detected_lang} (confidence={confidence:.2f}) for Article ID {article.id}")
        except Exception as e:
            logger.warning(f"Language re-detection failed for Article ID {article_id}: {e}")

        # --- 1. Create ArticleAnalysisDTO for structured processing ---
        analysis_dto = ArticleAnalysisDTO(
            article_id=article.id,
            content=article.content,
            language=article.language,
            entities=[],  # Will be populated by NLP analysis
            reading_level=None,  # Will be calculated
            word_count=len(article.content.split()),
            processing_time=0.0,
            confidence_score=None
        )

        # --- 2. Perform initial NLP Analysis with validation ---
        import time
        start_time = time.time()
        
        analysis_data = services.analyze_text_content(article.content, article.language)
        all_entities = analysis_data.get("people", []) + analysis_data.get("organizations", [])
        
        # Update DTO with analysis results
        analysis_dto.entities = all_entities[:20]  # Limit entities as per DTO validation
        analysis_dto.reading_level = analysis_data.get("reading_score", 0)
        analysis_dto.processing_time = time.time() - start_time
        analysis_dto.confidence_score = analysis_data.get("confidence", 0.8)

        # Validate the analysis DTO
        validated_analysis = validation_pipeline.validate_and_parse(
            ArticleAnalysisDTO,
            analysis_dto.dict(),
            context=f"Article {article_id} analysis",
            raise_on_error=True
        )

        # --- 3. Set Reading Level ---
        article.reading_level = validated_analysis.reading_level
        logger.info(
            f"Calculated reading level for Article ID {article.id}: {article.reading_level}"
        )

        # --- 4. Dynamic Model Selection ---
        selected_model = ""
        # Prefer flash by default; only use pro for very complex texts
        if article.source == "gutenberg":
            selected_model = "models/gemini-2.5-flash"
        else:
            if article.reading_level < 20:  # Very difficult text
                selected_model = "models/gemini-2.5-pro"
            elif 20 <= article.reading_level < 60:  # Standard text
                selected_model = "models/gemini-2.5-flash"
            else:  # Easy text (reading_level >= 60)
                selected_model = "models/gemini-2.5-flash-lite-preview-06-17"

        logger.info(
            f"Selected model '{selected_model}' for Article ID: {article_id} with reading level: {article.reading_level}"
        )
        article.llm_model_used = selected_model
        article.save()  # Save reading_level and llm_model_used immediately

        # --- 5. The Single Master Call with Pydantic validation ---
        try:
            time.sleep(2)  # Add a delay to avoid hitting rate limits
            llm_response = services.generate_master_analysis(
                model_name=selected_model,
                entity_list=validated_analysis.entities,
                article_text=article.content,
                language=article.language,
                source=article.source
            )
            
            # Validate LLM response using Pydantic
            if llm_response:
                validated_llm_response = validation_pipeline.validate_llm_response(
                    MasterAnalysisResponse,
                    json.dumps(llm_response) if isinstance(llm_response, dict) else llm_response,
                    model_name=selected_model,
                    raise_on_error=True
                )
                
                if validated_llm_response:
                    llm_data = validated_llm_response.dict()
                    logger.info(f"Successfully validated LLM response for Article ID: {article_id}")
                else:
                    logger.warning(f"LLM response validation failed for Article ID: {article_id}, using raw data")
                    llm_data = llm_response
            else:
                llm_data = None
                
        except Exception as e:
            # Treat LLM/API errors as retryable: backoff and retry until max_retries
            logger.error(f"API error for Article ID: {article_id}. Error: {e}")
            if self.request.retries < self.max_retries:
                countdown = min(60 * (self.request.retries + 1), 300)  # 60s,120s,180s,240s,300s
                logger.info(f"Retrying article {article_id} after {countdown}s (attempt {self.request.retries + 1})")
                raise self.retry(countdown=countdown)
            article.processing_status = "failed_quota"
            article.save()
            return {"success": False, "error": f"API error: {str(e)}", "article_id": article_id}

        # --- 6. Process the Unified Response and Finalize ---
        if llm_data:
            article.quiz_data = llm_data.get("quiz")

            # Get clean, canonical tags from LLM and validate/cache them
            llm_canonical_tags = llm_data.get("tags", [])
            final_tag_objects = services.get_valid_wikipedia_tags(
                llm_canonical_tags, article.language
            )

            article.tags.set(list(set(final_tag_objects)))
            article.processing_status = "complete"
            article.save()
            
            logger.info(f"Successfully processed Article ID: {article.id}")
            
            return {
                "success": True,
                "article_id": article.id,
                "processing_time": validated_analysis.processing_time,
                "reading_level": validated_analysis.reading_level,
                "entities_found": len(validated_analysis.entities),
                "tags_assigned": len(llm_canonical_tags),
                "quiz_questions": len(llm_data.get("quiz", [])),
                "model_used": selected_model
            }
        else:
            article.processing_status = "failed"
            article.save()
            logger.error(f"Failed to get LLM data for Article ID: {article.id}")
            return {"success": False, "error": "Failed to get LLM data", "article_id": article_id}
            
    except Exception as e:
        logger.error(f"Unexpected error processing Article ID: {article_id}. Error: {e}")
        article.processing_status = "failed"
        article.save()
        return {"success": False, "error": str(e), "article_id": article_id}


@shared_task(bind=True, max_retries=3)
def ensure_article_has_quiz(self, article_id):
    """
    Ensure article has quiz data, retry if generation fails.
    This task helps with reliability for regular articles.
    """
    try:
        article = Article.objects.get(id=article_id)
        
        if not article.quiz_data and article.can_generate_quiz():
            logger.info(f"Article {article_id} missing quiz data, triggering regeneration")
            
            # Retry quiz generation based on article type
            if article.article_type == "wikipedia":
                process_wikipedia_article.delay(article_id)
            else:
                process_article.delay(article_id)
                
        elif article.quiz_data:
            logger.info(f"Article {article_id} already has quiz data with {len(article.quiz_data)} questions")
        else:
            logger.warning(f"Article {article_id} cannot generate quiz: status={article.processing_status}, content_length={len(article.content) if article.content else 0}")
            
    except Article.DoesNotExist:
        logger.error(f"Article {article_id} not found for quiz generation")
    except Exception as e:
        logger.error(f"Failed to ensure quiz for article {article_id}: {e}")
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying quiz generation for article {article_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))


@shared_task
@with_fallback(fallback_return={'status': 'error', 'message': 'Article scraping failed with an unexpected error'})
def scrape_and_save_article(url):
    """
    Scrapes an article from a URL and saves a new Article object.
    Returns a dictionary indicating the result.
    """
    try:
        # Check if URL already exists to avoid duplicates
        if Article.objects.filter(url=url).exists():
            return {'status': 'duplicate', 'url': url}

        article = newspaper.Article(url)
        article.download()
        article.parse()

        # Detect language via LanguageProcessor (robust fallback inside)
        try:
            from .services.language_processor import LanguageProcessor
            lp = LanguageProcessor()
            detected_lang, confidence = lp.detect_language(article.text or "", article.title or "")
            lang = detected_lang if detected_lang in ['en', 'es'] else 'en'
        except Exception:
            lang = 'en'
        
        # Create but don't process yet. Save with 'pending' status.
        new_article = Article.objects.create(
            url=url,
            title=article.title or "Title not found",
            content=article.text or "Content not found",
            publication_date=article.publish_date,
            image_url=article.top_image,
            source="user_submission",
            processing_status='pending', # IMPORTANT
            language=lang
        )
        # Now, trigger the processing task for the new article
        process_article.delay(new_article.id)
        return {'status': 'success', 'article_id': new_article.id}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task(bind=True)
def process_wikipedia_article(self, article_id):
    """
    Process Wikipedia articles through the same NLP pipeline as regular articles.

    Wikipedia articles have some special handling:
    - They're already validated and cleaned
    - They may have different complexity patterns
    - They should get quiz generation
    """
    logger.info(f"Starting Wikipedia article processing for article ID: {article_id}")

    try:
        article = Article.objects.get(
            id=article_id,
            article_type="wikipedia",
            processing_status__in=["pending", "complete"],
        )
    except Article.DoesNotExist:
        logger.warning(f"Wikipedia article {article_id} not found. Task aborted.")
        return

    # If already processed, skip unless forced reprocessing
    if article.processing_status == "complete" and article.quiz_data:
        logger.info(f"Wikipedia article {article_id} already processed. Skipping.")
        return

    try:
        # Set processing status
        article.processing_status = "processing"
        article.save()

        # --- 1. Perform NLP Analysis ---
        analysis_data = services.analyze_text_content(article.content, article.language)
        all_entities = analysis_data.get("people", []) + analysis_data.get(
            "organizations", []
        )

        # --- 2. Set Reading Level ---
        article.reading_level = analysis_data.get(
            "reading_score", 8.0
        )  # Default for Wikipedia
        logger.info(
            f"Calculated reading level for Wikipedia Article ID {article.id}: {article.reading_level}"
        )

        # --- 3. Update word and letter counts ---
        article.word_count = len(article.content.split())
        article.letter_count = len(article.content.replace(" ", ""))

        # --- 4. Dynamic Model Selection (Wikipedia tends to be more complex) ---
        selected_model = ""
        if article.reading_level < 25:  # Very complex Wikipedia content
            selected_model = "models/gemini-2.5-pro"
        elif 25 <= article.reading_level < 50:  # Standard Wikipedia content
            selected_model = "models/gemini-2.5-flash"
        else:  # Simpler Wikipedia content
            selected_model = "models/gemini-2.5-flash"

        logger.info(
            f"Selected model '{selected_model}' for Wikipedia Article ID: {article_id}"
        )
        article.llm_model_used = selected_model
        article.save()

        # --- 5. Generate Quiz and Analysis ---
        try:
            llm_data = services.generate_master_analysis(
                model_name=selected_model,
                entity_list=all_entities,
                article_text=article.content,
            )
        except Exception as e:
            logger.error(
                f"API error for Wikipedia Article ID: {article_id}. Error: {e}"
            )
            article.processing_status = "failed_quota"
            article.save()
            return

        # --- 6. Process Results ---
        if llm_data:
            article.quiz_data = llm_data.get("quiz")

            # For Wikipedia articles, we already have the main tag, but we can add related tags
            llm_canonical_tags = llm_data.get("tags", [])
            if llm_canonical_tags:
                # Get additional tags but preserve existing ones
                existing_tags = list(article.tags.all())
                additional_tags = services.get_valid_wikipedia_tags(
                    llm_canonical_tags, article.language
                )

                # Combine existing and new tags
                all_tags = existing_tags + [
                    tag for tag in additional_tags if tag not in existing_tags
                ]
                article.tags.set(all_tags)

            article.processing_status = "complete"
            article.save()

            # Update tag article counts
            for tag in article.tags.all():
                tag.update_article_count()

            logger.info(f"Successfully processed Wikipedia Article ID: {article.id}")
        else:
            article.processing_status = "failed"
            article.save()
            logger.error(
                f"Failed to get LLM data for Wikipedia Article ID: {article.id}"
            )

    except Exception as e:
        logger.error(f"Error processing Wikipedia article {article_id}: {str(e)}")
        article.processing_status = "failed"
        article.save()
        raise


@shared_task
def process_wikipedia_articles_batch(article_ids):
    """
    Process multiple Wikipedia articles in batch.

    Args:
        article_ids (list): List of Wikipedia article IDs to process
    """
    logger.info(f"Starting batch processing of {len(article_ids)} Wikipedia articles")

    results = {"processed": 0, "failed": 0, "skipped": 0}

    for article_id in article_ids:
        try:
            process_wikipedia_article.delay(article_id)
            results["processed"] += 1
        except Exception as e:
            logger.error(f"Failed to queue Wikipedia article {article_id}: {str(e)}")
            results["failed"] += 1

    logger.info(f"Batch processing queued: {results}")
    return results


@shared_task
def create_wikipedia_articles_for_tags():
    """
    Create Wikipedia articles for all validated tags that don't have them yet.
    """
    from .wikipedia_service import WikipediaService

    logger.info("Starting Wikipedia article creation for validated tags")

    # Get tags that are validated but don't have Wikipedia articles
    tags_without_articles = Tag.objects.filter(
        is_validated=True, wikipedia_url__isnull=False
    ).exclude(article__article_type="wikipedia")

    service = WikipediaService()
    created_count = 0
    failed_count = 0

    for tag in tags_without_articles:
        try:
            # Validate and get Wikipedia data
            is_valid, wikipedia_data = service.validate_tag_with_wikipedia(tag.name)

            if is_valid and wikipedia_data:
                # Create Wikipedia article
                article = service.create_wikipedia_article(tag, wikipedia_data)

                if article:
                    # Queue for processing
                    process_wikipedia_article.delay(article.id)
                    created_count += 1
                    logger.info(f"Created Wikipedia article for tag '{tag.name}'")
                else:
                    failed_count += 1
            else:
                failed_count += 1

        except Exception as e:
            logger.error(
                f"Error creating Wikipedia article for tag '{tag.name}': {str(e)}"
            )
            failed_count += 1

    logger.info(
        f"Wikipedia article creation completed: {created_count} created, {failed_count} failed"
    )
    return {
        "created": created_count,
        "failed": failed_count,
        "total_processed": len(tags_without_articles),
    }


@shared_task
def update_tag_statistics():
    """
    Update cached statistics for all tags.
    """
    from .tag_analytics import refresh_tag_cache

    logger.info("Starting tag statistics update")

    try:
        # Clear all caches to force refresh
        refresh_tag_cache()

        # Update article counts for all tags
        tags = Tag.objects.filter(is_validated=True)
        updated_count = 0

        for tag in tags:
            try:
                tag.update_article_count()
                updated_count += 1
            except Exception as e:
                logger.error(
                    f"Error updating statistics for tag '{tag.name}': {str(e)}"
                )

        logger.info(f"Tag statistics update completed: {updated_count} tags updated")
        return {"updated": updated_count, "total_tags": tags.count()}

    except Exception as e:
        logger.error(f"Error updating tag statistics: {str(e)}")
        raise

@shared_task(bind=True)
def process_article_async(self, article_id, processing_options=None):
    """
    Async article processing with full Pydantic serialization support.
    
    Args:
        article_id: ID of the article to process
        processing_options: Optional dict with processing configuration
        
    Returns:
        Serialized result using Pydantic models
    """
    logger.info(f"Starting async processing for article ID: {article_id}")
    
    try:
        # Validate processing options if provided
        if processing_options:
            # You could create a ProcessingOptionsDTO here if needed
            validated_options = validation_pipeline.validate_and_parse(
                dict,  # Simple dict validation for now
                processing_options,
                context=f"Processing options for article {article_id}",
                raise_on_error=False
            )
            processing_options = validated_options or {}
        else:
            processing_options = {}
        
        # Call the main processing function
        result = process_article(article_id)
        
        # Ensure result is properly serialized
        if isinstance(result, dict):
            # Add task metadata
            result.update({
                "task_id": self.request.id,
                "processing_options": processing_options,
                "timestamp": timezone.now().isoformat()
            })
            
            # Validate the result structure
            validated_result = validation_pipeline.validate_and_parse(
                dict,  # Could create a TaskResultDTO for this
                result,
                context=f"Task result for article {article_id}",
                raise_on_error=False
            )
            
            return validated_result or result
        
        return result
        
    except Exception as e:
        logger.error(f"Async processing failed for article {article_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "article_id": article_id,
            "task_id": self.request.id,
            "timestamp": timezone.now().isoformat()
        }


@shared_task(bind=True)
def process_xp_transaction(self, transaction_data):
    """
    Process XP transactions with Pydantic validation.
    
    Args:
        transaction_data: Dictionary containing transaction information
        
    Returns:
        Validated transaction result
    """
    logger.info(f"Processing XP transaction: {transaction_data}")
    
    try:
        # Validate transaction data using Pydantic DTO
        validated_transaction = validation_pipeline.validate_and_parse(
            XPTransactionDTO,
            transaction_data,
            context="XP Transaction Processing",
            raise_on_error=True
        )
        
        # Process the transaction using the XP system
        from .xp_system import XPTransactionManager
        
        transaction_manager = XPTransactionManager()
        
        if validated_transaction.transaction_type == "EARN":
            result = transaction_manager.award_xp(
                user_id=validated_transaction.user_id,
                amount=validated_transaction.amount,
                source=validated_transaction.source,
                description=validated_transaction.description,
                metadata=validated_transaction.metadata
            )
        else:  # SPEND
            result = transaction_manager.spend_xp(
                user_id=validated_transaction.user_id,
                amount=abs(validated_transaction.amount),  # Ensure positive for spending
                source=validated_transaction.source,
                description=validated_transaction.description,
                metadata=validated_transaction.metadata
            )
        
        # Return validated result
        return {
            "success": True,
            "transaction_id": result.get("transaction_id"),
            "user_id": validated_transaction.user_id,
            "amount": validated_transaction.amount,
            "new_balance": result.get("new_balance"),
            "transaction_type": validated_transaction.transaction_type,
            "timestamp": timezone.now().isoformat(),
            "task_id": self.request.id
        }
        
    except Exception as e:
        logger.error(f"XP transaction processing failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "transaction_data": transaction_data,
            "task_id": self.request.id,
            "timestamp": timezone.now().isoformat()
        }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def validate_and_retry_failed_articles(self):
    """
    Find articles with failed processing and retry them with validation.
    """
    logger.info("Starting validation and retry of failed articles")
    
    try:
        # Get articles that failed processing
        failed_articles = Article.objects.filter(
            processing_status__in=['failed', 'failed_quota']
        ).order_by('-timestamp')[:10]  # Limit to 10 most recent
        
        results = {
            "total_found": failed_articles.count(),
            "retry_attempts": 0,
            "successful_retries": 0,
            "failed_retries": 0,
            "articles_processed": []
        }
        
        for article in failed_articles:
            try:
                # Create analysis DTO for validation
                analysis_dto = ArticleAnalysisDTO(
                    article_id=article.id,
                    content=article.content,
                    language=article.language,
                    entities=[],
                    reading_level=article.reading_level or 0,
                    word_count=len(article.content.split()) if article.content else 0
                )
                
                # Validate the article data
                validated_analysis = validation_pipeline.validate_and_parse(
                    ArticleAnalysisDTO,
                    analysis_dto.dict(),
                    context=f"Retry validation for article {article.id}",
                    raise_on_error=False
                )
                
                if validated_analysis:
                    # Reset status and retry processing
                    article.processing_status = 'pending'
                    article.save()
                    
                    # Queue for reprocessing
                    process_article_async.delay(article.id)
                    
                    results["retry_attempts"] += 1
                    results["successful_retries"] += 1
                    results["articles_processed"].append({
                        "article_id": article.id,
                        "status": "queued_for_retry",
                        "word_count": validated_analysis.word_count
                    })
                    
                    logger.info(f"Queued article {article.id} for retry processing")
                else:
                    results["failed_retries"] += 1
                    results["articles_processed"].append({
                        "article_id": article.id,
                        "status": "validation_failed",
                        "error": "Article data validation failed"
                    })
                    
            except Exception as e:
                logger.error(f"Error processing failed article {article.id}: {str(e)}")
                results["failed_retries"] += 1
                results["articles_processed"].append({
                    "article_id": article.id,
                    "status": "error",
                    "error": str(e)
                })
        
        logger.info(f"Retry validation completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Failed article retry process error: {str(e)}")
        
        # Retry the task if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying failed article validation (attempt {self.request.retries + 1})")
            raise self.retry(countdown=self.default_retry_delay)
        
        return {
            "success": False,
            "error": str(e),
            "task_id": self.request.id,
            "timestamp": timezone.now().isoformat()
        }