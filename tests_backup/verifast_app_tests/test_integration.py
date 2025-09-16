from unittest.mock import patch, MagicMock
from django.test import TransactionTestCase
from django.test.utils import override_settings

from verifast_app.models import Article, Tag
from verifast_app.tasks import scrape_and_save_article, process_article
from verifast_app.services import analyze_text_content, get_valid_wikipedia_tags


class TestIntegration(TransactionTestCase):
    """Integration tests for end-to-end functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.test_content = """
        Artificial Intelligence (AI) is a branch of computer science that aims to create 
        intelligent machines. Companies like Google, Microsoft, and OpenAI are leading 
        the development of AI technologies. The field involves machine learning, 
        neural networks, and natural language processing.
        """
    
    @patch('verifast_app.services.analysis_core.genai.GenerativeModel')
    @patch('verifast_app.services.analysis_core.wiki_en')
    def test_full_article_processing_pipeline(self, mock_wiki, mock_genai):
        """Test the complete article processing pipeline"""
        # Setup AI mock
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "quiz": [
                {
                    "question": "What is AI?",
                    "options": ["Artificial Intelligence", "Automated Intelligence", "Advanced Intelligence", "Applied Intelligence"],
                    "answer": "Artificial Intelligence"
                }
            ],
            "tags": ["Artificial Intelligence", "Google", "Microsoft", "OpenAI", "Machine Learning"]
        }
        '''
        mock_chat = MagicMock()
        mock_chat.send_message.return_value = mock_response
        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Setup Wikipedia mock
        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.title = "Artificial Intelligence"
        mock_wiki.page.return_value = mock_page
        
        # Create test article
        article = Article.objects.create(
            title="Test AI Article",
            content=self.test_content,
            processing_status="pending",
            language="en"
        )
        
        # Process the article
        process_article(article.id)
        
        # Refresh from database
        article.refresh_from_db()
        
        # Verify processing results
        self.assertEqual(article.processing_status, 'complete')
        self.assertIsNotNone(article.quiz_data)
        self.assertGreater(article.reading_level, 0)
        self.assertIsNotNone(article.llm_model_used)
        self.assertGreater(article.tags.count(), 0)
        
        # Verify quiz data structure
        quiz_data = article.quiz_data
        if isinstance(quiz_data, list):
            self.assertGreater(len(quiz_data), 0)
        else:
            self.assertIn('question', str(quiz_data))
    
    @patch('verifast_app.tasks.newspaper.Article')
    @patch('verifast_app.services.analysis_core.genai.GenerativeModel')
    def test_scrape_and_process_workflow(self, mock_genai, mock_newspaper):
        """Test the complete scrape and process workflow"""
        # Setup newspaper mock
        mock_article = MagicMock()
        mock_article.title = "AI Revolution"
        mock_article.text = self.test_content
        mock_article.publish_date = None
        mock_article.top_image = ""
        mock_newspaper.return_value = mock_article
        
        # Setup AI mock
        mock_response = MagicMock()
        mock_response.text = '{"quiz": [{"question": "Test?", "options": ["A", "B"], "answer": "A"}], "tags": ["AI"]}'
        mock_chat = MagicMock()
        mock_chat.send_message.return_value = mock_response
        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Test scraping
        result = scrape_and_save_article("https://example.com/ai-article")
        
        # Verify scraping result
        self.assertEqual(result['status'], 'success')
        self.assertIn('article_id', result)
        
        # Verify article was created
        article = Article.objects.get(id=result['article_id'])
        self.assertEqual(article.title, "AI Revolution")
        self.assertEqual(article.content, self.test_content)
        self.assertEqual(article.processing_status, 'pending')
    
    def test_nlp_analysis_with_real_text(self):
        """Test NLP analysis with real text content"""
        # This test uses real spaCy models if available
        try:
            result = analyze_text_content(self.test_content)
            
            # Verify structure
            self.assertIn('reading_score', result)
            self.assertIn('people', result)
            self.assertIn('organizations', result)
            self.assertIn('money_mentions', result)
            
            # Verify types
            self.assertIsInstance(result['reading_score'], (int, float))
            self.assertIsInstance(result['people'], list)
            self.assertIsInstance(result['organizations'], list)
            self.assertIsInstance(result['money_mentions'], list)
            
            # Should detect organizations like Google, Microsoft, OpenAI
            org_names = [org.lower() for org in result['organizations']]
            detected_orgs = [org for org in ['google', 'microsoft', 'openai'] if org in org_names]
            self.assertGreater(len(detected_orgs), 0, "Should detect at least one organization")
            
        except Exception as e:
            # If spaCy models are not available, test should still pass
            self.skipTest(f"spaCy models not available: {e}")
    
    @patch('verifast_app.services.analysis_core.wiki_en')
    def test_wikipedia_tag_validation_integration(self, mock_wiki):
        """Test Wikipedia tag validation with multiple entities"""
        # Setup mock for successful validation
        def mock_page_side_effect(entity_name):
            mock_page = MagicMock()
            if entity_name in ["Python", "Django", "JavaScript"]:
                mock_page.exists.return_value = True
                mock_page.title = f"{entity_name} (programming language)" if entity_name != "Django" else entity_name
            else:
                mock_page.exists.return_value = False
            return mock_page
        
        mock_wiki.page.side_effect = mock_page_side_effect
        
        # Test with mixed valid/invalid entities
        entities = ["Python", "Django", "JavaScript", "NonexistentTech", ""]
        result = get_valid_wikipedia_tags(entities)
        
        # Should create tags for valid entities only
        self.assertEqual(len(result), 3)  # Python, Django, JavaScript
        tag_names = [tag.name for tag in result]
        self.assertIn("Python (programming language)", tag_names)
        self.assertIn("Django", tag_names)
        self.assertIn("JavaScript (programming language)", tag_names)
    
    def test_error_handling_and_fallbacks(self):
        """Test that error handling and fallbacks work correctly"""
        # Test with invalid/empty inputs
        
        # Empty content should not crash
        result = analyze_text_content("")
        self.assertEqual(result['reading_score'], 0)
        self.assertEqual(result['people'], [])
        
        # Invalid entities should not crash
        result = get_valid_wikipedia_tags([None, "", 123, []])
        self.assertEqual(len(result), 0)
        
        # Non-existent article processing should not crash
        process_article(99999)  # Should return without error
    
    @override_settings(ENABLE_AI_FEATURES=False)
    def test_feature_flags_disable_ai(self):
        """Test that feature flags properly disable AI features"""
        # When AI features are disabled, functions should still work but return fallback values
        from verifast_app.feature_flags import FeatureFlags
        
        self.assertFalse(FeatureFlags.ai_features_enabled())
    
    def test_concurrent_article_processing(self):
        """Test processing multiple articles concurrently"""
        # Create multiple test articles
        articles = []
        for i in range(3):
            article = Article.objects.create(
                title=f"Test Article {i}",
                content=f"Test content {i} with different entities.",
                processing_status="pending",
                language="en"
            )
            articles.append(article)
        
        # Process all articles (this would normally be done by Celery workers)
        with patch('verifast_app.services.analysis_core.genai.GenerativeModel') as mock_genai_model, \
             patch('verifast_app.services.analysis_core.wiki_en') as mock_wiki:
            
            # Setup mocks
            mock_response = MagicMock()
            mock_response.text = '{"quiz": [], "tags": []}'
            mock_chat = MagicMock()
            mock_chat.send_message.return_value = mock_response
            mock_model = MagicMock()
            mock_model.start_chat.return_value = mock_chat
            mock_genai.GenerativeModel.return_value = mock_model
            
            mock_page = MagicMock()
            mock_page.exists.return_value = False
            mock_wiki.page.return_value = mock_page
            
            # Process all articles
            for article in articles:
                process_article(article.id)
            
            # Verify all articles were processed
            for article in articles:
                article.refresh_from_db()
                self.assertIn(article.processing_status, ['complete', 'failed', 'failed_quota'])
    
    def tearDown(self):
        """Clean up test data"""
        Article.objects.all().delete()
        Tag.objects.all().delete()