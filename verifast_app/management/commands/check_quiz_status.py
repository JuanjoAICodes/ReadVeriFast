from django.core.management.base import BaseCommand
from verifast_app.models import Article
import json


class Command(BaseCommand):
    help = 'Check the status of quiz generation for articles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--article-id',
            type=int,
            help='Check specific article ID'
        )
        parser.add_argument(
            '--show-quiz',
            action='store_true',
            help='Show quiz content for articles'
        )

    def handle(self, *args, **options):
        article_id = options.get('article_id')
        show_quiz = options['show_quiz']
        
        if article_id:
            try:
                article = Article.objects.get(id=article_id)
                self.show_article_status(article, show_quiz)
            except Article.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Article with ID {article_id} not found")
                )
        else:
            self.stdout.write("Quiz Generation Status Report")
            self.stdout.write("=" * 50)
            
            # Overall statistics
            total_articles = Article.objects.count()
            complete_articles = Article.objects.filter(processing_status='complete').count()
            articles_with_quiz = Article.objects.filter(
                processing_status='complete',
                quiz_data__isnull=False
            ).count()
            
            self.stdout.write(f"Total articles: {total_articles}")
            self.stdout.write(f"Complete articles: {complete_articles}")
            self.stdout.write(f"Articles with quiz: {articles_with_quiz}")
            
            if complete_articles > 0:
                success_rate = (articles_with_quiz / complete_articles) * 100
                self.stdout.write(f"Quiz success rate: {success_rate:.1f}%")
            
            # Status breakdown
            self.stdout.write("\nStatus breakdown:")
            statuses = Article.objects.values_list('processing_status', flat=True).distinct()
            for status in statuses:
                count = Article.objects.filter(processing_status=status).count()
                self.stdout.write(f"  {status}: {count}")
            
            # Recent articles
            self.stdout.write("\nRecent articles:")
            recent_articles = Article.objects.order_by('-id')[:10]
            for article in recent_articles:
                self.show_article_status(article, show_quiz, brief=True)

    def show_article_status(self, article, show_quiz=False, brief=False):
        """Show detailed status for a single article"""
        quiz_status = "HAS QUIZ" if article.quiz_data else "NO QUIZ"
        
        if brief:
            self.stdout.write(
                f"  ID {article.id}: {article.processing_status} - {quiz_status} - {article.title[:40]}..."
            )
        else:
            self.stdout.write(f"\nArticle ID: {article.id}")
            self.stdout.write(f"Title: {article.title}")
            self.stdout.write(f"Status: {article.processing_status}")
            self.stdout.write(f"Language: {article.language}")
            self.stdout.write(f"Source: {article.source}")
            self.stdout.write(f"Word count: {len(article.content.split()) if article.content else 0}")
            self.stdout.write(f"Reading level: {article.reading_level}")
            self.stdout.write(f"LLM model used: {article.llm_model_used}")
            
            if article.quiz_data:
                if isinstance(article.quiz_data, list):
                    quiz_count = len(article.quiz_data)
                elif isinstance(article.quiz_data, dict) and 'quiz' in article.quiz_data:
                    quiz_count = len(article.quiz_data['quiz'])
                else:
                    quiz_count = "Unknown format"
                
                self.stdout.write(f"Quiz questions: {quiz_count}")
                
                if show_quiz and isinstance(article.quiz_data, list):
                    self.stdout.write("\nQuiz content:")
                    for i, question in enumerate(article.quiz_data[:3], 1):  # Show first 3
                        self.stdout.write(f"  Q{i}: {question.get('question', 'No question')}")
                        if len(article.quiz_data) > 3:
                            self.stdout.write(f"  ... and {len(article.quiz_data) - 3} more questions")
                            break
            else:
                self.stdout.write("Quiz: Not generated")
            
            # Tags
            tags = list(article.tags.values_list('name', flat=True))
            if tags:
                self.stdout.write(f"Tags: {', '.join(tags[:5])}")
                if len(tags) > 5:
                    self.stdout.write(f"  ... and {len(tags) - 5} more tags")
            else:
                self.stdout.write("Tags: None")