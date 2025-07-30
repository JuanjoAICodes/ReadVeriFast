from unittest.mock import patch, MagicMock
from django.test import TestCase

from verifast_app.tasks import scrape_and_save_article, process_article
from verifast_app.models import Article


class TestTasks(TestCase):
    """Test Celery tasks"""
    
    @patch('verifast_app.tasks.newspaper.Article')
    @patch('verifast_app.tasks.Article.objects.filter')
    @patch('verifast_app.tasks.Article.objects.create')
    @patch('verifast_app.tasks.process_article.delay')
    def test_scrape_and_save_article_success(self, mock_process, mock_create, mock_filter, mock_newspaper):
        """Test successful article scraping"""
        # Setup mocks
        mock_filter.return_value.exists.return_value = False
        
        mock_article = MagicMock()
        mock_article.title = "Test Title"
        mock_article.text = "Test content"
        mock_article.publish_date = None
        mock_article.top_image = ""
        mock_newspaper.return_value = mock_article
        
        mock_db_article = MagicMock()
        mock_db_article.id = 1
        mock_create.return_value = mock_db_article
        
        # Call function
        result = scrape_and_save_article("https://example.com")
        
        # Verify results
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['article_id'], 1)
        mock_newspaper.assert_called_once_with("https://example.com")
        mock_article.download.assert_called_once()
        mock_article.parse.assert_called_once()
        mock_create.assert_called_once()
        mock_process.assert_called_once_with(1)
    
    @patch('verifast_app.tasks.Article.objects.filter')
    def test_scrape_and_save_article_duplicate(self, mock_filter):
        """Test handling of duplicate URLs"""
        # Setup mock
        mock_filter.return_value.exists.return_value = True
        
        # Call function
        result = scrape_and_save_article("https://example.com")
        
        # Verify results
        self.assertEqual(result['status'], 'duplicate')
        self.assertEqual(result['url'], "https://example.com")
    
    @patch('verifast_app.tasks.newspaper.Article')
    @patch('verifast_app.tasks.Article.objects.filter')
    def test_scrape_and_save_article_error(self, mock_filter, mock_newspaper):
        """Test handling of scraping errors"""
        # Setup mocks
        mock_filter.return_value.exists.return_value = False
        mock_newspaper.side_effect = Exception("Network error")
        
        # Call function
        result = scrape_and_save_article("https://example.com")
        
        # Verify results
        self.assertEqual(result['status'], 'error')
        self.assertIn('Network error', result['message'])
    
    def setUp(self):
        """Set up test data"""
        self.test_article = Article.objects.create(
            title="Test Article",
            content="This is test content with entities like John Doe and Google.",
            processing_status="pending",
            language="en"
        )
    
    @patch('verifast_app.tasks.analyze_text_content')
    @patch('verifast_app.tasks.generate_master_analysis')
    @patch('verifast_app.tasks.get_valid_wikipedia_tags')
    def test_process_article_success(self, mock_tags, mock_analysis, mock_nlp):
        """Test successful article processing"""
        # Setup mocks
        mock_nlp.return_value = {
            'reading_score': 8.5,
            'people': ['John Doe'],
            'organizations': ['Google'],
            'money_mentions': []
        }
        
        mock_analysis.return_value = {
            'quiz': [{'question': 'Test?', 'options': ['A', 'B'], 'answer': 'A'}],
            'tags': ['Technology', 'Programming']
        }
        
        mock_tag1 = MagicMock()
        mock_tag1.name = 'Technology'
        mock_tag2 = MagicMock()
        mock_tag2.name = 'Programming'
        mock_tags.return_value = [mock_tag1, mock_tag2]
        
        # Call function
        process_article(self.test_article.id)
        
        # Refresh article from database
        self.test_article.refresh_from_db()
        
        # Verify results
        self.assertEqual(self.test_article.processing_status, 'complete')
        self.assertEqual(self.test_article.reading_level, 8.5)
        self.assertIsNotNone(self.test_article.quiz_data)
        self.assertIn('models/gemini-2.5-pro', self.test_article.llm_model_used)
    
    @patch('verifast_app.tasks.analyze_text_content')
    def test_process_article_nonexistent(self, mock_nlp):
        """Test processing of non-existent article"""
        # Call function with non-existent ID
        result = process_article(99999)
        
        # Function should return without error
        self.assertIsNone(result)
        mock_nlp.assert_not_called()
    
    @patch('verifast_app.tasks.analyze_text_content')
    @patch('verifast_app.tasks.generate_master_analysis')
    def test_process_article_api_error(self, mock_analysis, mock_nlp):
        """Test handling of API errors during processing"""
        # Setup mocks
        mock_nlp.return_value = {
            'reading_score': 8.5,
            'people': ['John Doe'],
            'organizations': ['Google'],
            'money_mentions': []
        }
        
        mock_analysis.side_effect = Exception("API quota exceeded")
        
        # Call function
        process_article(self.test_article.id)
        
        # Refresh article from database
        self.test_article.refresh_from_db()
        
        # Verify error handling
        self.assertEqual(self.test_article.processing_status, 'failed_quota')
    
    @patch('verifast_app.tasks.analyze_text_content')
    @patch('verifast_app.tasks.generate_master_analysis')
    def test_process_article_no_llm_data(self, mock_analysis, mock_nlp):
        """Test handling when LLM returns no data"""
        # Setup mocks
        mock_nlp.return_value = {
            'reading_score': 8.5,
            'people': ['John Doe'],
            'organizations': ['Google'],
            'money_mentions': []
        }
        
        mock_analysis.return_value = None
        
        # Call function
        process_article(self.test_article.id)
        
        # Refresh article from database
        self.test_article.refresh_from_db()
        
        # Verify error handling
        self.assertEqual(self.test_article.processing_status, 'failed')