from django.core.management.base import BaseCommand
from verifast_app.models import Article
from verifast_app.tasks import process_article
import json


class Command(BaseCommand):
    help = 'Retry quiz generation for articles that are complete but have no quiz data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--article-id',
            type=int,
            help='Retry specific article ID'
        )
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Process articles synchronously instead of using Celery'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum number of articles to retry (default: 10)'
        )

    def handle(self, *args, **options):
        article_id = options.get('article_id')
        sync_mode = options['sync']
        limit = options['limit']
        
        if article_id:
            try:
                article = Article.objects.get(id=article_id)
                self.retry_article(article, sync_mode)
            except Article.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Article with ID {article_id} not found")
                )
        else:
            # Find articles that need quiz retry
            articles_needing_retry = Article.objects.filter(
                processing_status='complete',
                quiz_data__isnull=True
            ).order_by('-id')[:limit]
            
            # Also include articles with empty quiz arrays
            articles_with_empty_quiz = Article.objects.filter(
                processing_status='complete',
                quiz_data__exact=[]
            ).order_by('-id')[:limit]
            
            # Combine and deduplicate
            all_articles = list(articles_needing_retry) + list(articles_with_empty_quiz)
            unique_articles = {article.id: article for article in all_articles}.values()
            
            if not unique_articles:
                self.stdout.write("No articles found that need quiz retry")
                return
            
            self.stdout.write(f"Found {len(unique_articles)} articles needing quiz retry")
            
            for article in unique_articles:
                self.retry_article(article, sync_mode)

    def retry_article(self, article, sync_mode=False):
        """Retry quiz generation for a single article"""
        self.stdout.write(f"Retrying quiz generation for article {article.id}: {article.title}")
        
        # Reset status to trigger reprocessing
        article.processing_status = 'pending'
        article.save()
        
        if sync_mode:
            try:
                result = process_article(article.id)
                if result.get('success'):
                    # Refresh from database
                    article.refresh_from_db()
                    if article.quiz_data and len(article.quiz_data) > 0:
                        self.stdout.write(
                            self.style.SUCCESS(f"✓ Article {article.id} quiz generated successfully ({len(article.quiz_data)} questions)")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"⚠ Article {article.id} processed but no quiz generated")
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"✗ Article {article.id} processing failed: {result.get('error')}")
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Article {article.id} processing error: {str(e)}")
                )
        else:
            process_article.delay(article.id)
            self.stdout.write(f"Queued article {article.id} for async retry")