
from django.test import TestCase
from unittest.mock import patch
from verifast_app.models import Article
from verifast_app.tasks import process_article

class ProcessArticleDispatcherTest(TestCase):

    def setUp(self):
        self.regular_article = Article.objects.create(
            title="Regular Article",
            content="This is a regular article.",
            article_type='regular',
            processing_status='pending'
        )
        self.wikipedia_article = Article.objects.create(
            title="Wikipedia Article",
            content="This is a Wikipedia article.",
            article_type='wikipedia',
            processing_status='pending'
        )

    @patch('verifast_app.tasks.process_wikipedia_article.delay')
    def test_process_article_delegates_wikipedia_articles(self, mock_delay):
        """Test that process_article correctly delegates Wikipedia articles."""
        process_article(self.wikipedia_article.id)
        mock_delay.assert_called_once_with(self.wikipedia_article.id)

    @patch('verifast_app.tasks.services.analyze_text_content')
    def test_process_article_processes_regular_articles(self, mock_analyze):
        """Test that process_article processes regular articles directly."""
        mock_analyze.return_value = {
            'reading_score': 50,
            'people': [],
            'organizations': []
        }
        process_article(self.regular_article.id)
        mock_analyze.assert_called_once()
