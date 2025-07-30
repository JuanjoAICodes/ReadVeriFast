from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse

from verifast_app.health import ServiceHealthChecker


class TestHealthChecker(TestCase):
    """Test health check functionality"""
    
    def setUp(self):
        self.checker = ServiceHealthChecker()
    
    @patch('verifast_app.health.ServiceHealthChecker.genai')
    def test_check_google_ai_healthy(self, mock_genai):
        """Test Google AI health check when service is healthy"""
        mock_genai.list_models.return_value = []
        
        result = self.checker.check_google_ai()
        
        self.assertEqual(result['status'], 'healthy')
        self.assertEqual(result['message'], 'Google AI available')
    
    @patch('verifast_app.health.ServiceHealthChecker.genai')
    def test_check_google_ai_error(self, mock_genai):
        """Test Google AI health check when service has error"""
        mock_genai.list_models.side_effect = Exception("API error")
        
        result = self.checker.check_google_ai()
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('API error', result['message'])
    
    def test_check_google_ai_unavailable(self):
        """Test Google AI health check when not installed"""
        with patch.dict('sys.modules', {'google.generativeai': None}):
            result = self.checker.check_google_ai()
            
            self.assertEqual(result['status'], 'unavailable')
            self.assertEqual(result['message'], 'Google AI not installed')
    
    @patch('verifast_app.health.ServiceHealthChecker.spacy')
    def test_check_spacy_healthy(self, mock_spacy):
        """Test spaCy health check when models are loaded"""
        mock_nlp = MagicMock()
        mock_spacy.load.return_value = mock_nlp
        
        result = self.checker.check_spacy()
        
        self.assertEqual(result['status'], 'healthy')
        self.assertEqual(result['message'], 'spaCy models loaded')
    
    @patch('verifast_app.health.ServiceHealthChecker.spacy')
    def test_check_spacy_model_missing(self, mock_spacy):
        """Test spaCy health check when models are missing"""
        mock_spacy.load.side_effect = OSError("Model not found")
        
        result = self.checker.check_spacy()
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'spaCy models not downloaded')
    
    @patch('verifast_app.health.ServiceHealthChecker.wikipediaapi')
    def test_check_wikipedia_api_healthy(self, mock_wiki_module):
        """Test Wikipedia API health check when service is healthy"""
        mock_wiki = MagicMock()
        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_wiki.page.return_value = mock_page
        mock_wiki_module.Wikipedia.return_value = mock_wiki
        
        result = self.checker.check_wikipedia_api()
        
        self.assertEqual(result['status'], 'healthy')
        self.assertEqual(result['message'], 'Wikipedia API available')
    
    @patch('verifast_app.health.ServiceHealthChecker.wikipediaapi')
    def test_check_wikipedia_api_no_results(self, mock_wiki_module):
        """Test Wikipedia API health check when no results returned"""
        mock_wiki = MagicMock()
        mock_page = MagicMock()
        mock_page.exists.return_value = False
        mock_wiki.page.return_value = mock_page
        mock_wiki_module.Wikipedia.return_value = mock_wiki
        
        result = self.checker.check_wikipedia_api()
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'Wikipedia API returned no results')
    
    @patch('verifast_app.health.ServiceHealthChecker.newspaper')
    def test_check_newspaper_healthy(self, mock_newspaper):
        """Test newspaper3k health check when available"""
        result = self.checker.check_newspaper()
        
        self.assertEqual(result['status'], 'healthy')
        self.assertEqual(result['message'], 'newspaper3k available')
    
    def test_check_all_services(self):
        """Test checking all services at once"""
        with patch.object(self.checker, 'check_google_ai') as mock_ai, \
             patch.object(self.checker, 'check_spacy') as mock_spacy, \
             patch.object(self.checker, 'check_wikipedia_api') as mock_wiki, \
             patch.object(self.checker, 'check_newspaper') as mock_news:
            
            mock_ai.return_value = {'status': 'healthy', 'message': 'OK'}
            mock_spacy.return_value = {'status': 'healthy', 'message': 'OK'}
            mock_wiki.return_value = {'status': 'healthy', 'message': 'OK'}
            mock_news.return_value = {'status': 'healthy', 'message': 'OK'}
            
            result = self.checker.check_all_services()
            
            self.assertIn('google_ai', result)
            self.assertIn('spacy', result)
            self.assertIn('wikipedia_api', result)
            self.assertIn('newspaper', result)
            self.assertEqual(len(result), 4)


class TestHealthEndpoint(TestCase):
    """Test health check HTTP endpoint"""
    
    def setUp(self):
        self.client = Client()
    
    @patch('verifast_app.views_health.ServiceHealthChecker')
    def test_health_endpoint_healthy(self, mock_checker_class):
        """Test health endpoint when all services are healthy"""
        mock_checker = MagicMock()
        mock_checker.check_all_services.return_value = {
            'google_ai': {'status': 'healthy', 'message': 'Google AI available'},
            'spacy': {'status': 'healthy', 'message': 'spaCy models loaded'},
            'wikipedia_api': {'status': 'healthy', 'message': 'Wikipedia API available'},
            'newspaper': {'status': 'healthy', 'message': 'newspaper3k available'}
        }
        mock_checker_class.return_value = mock_checker
        
        response = self.client.get(reverse('verifast_app:health_check'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('services', data)
        self.assertEqual(len(data['services']), 4)
    
    @patch('verifast_app.views_health.ServiceHealthChecker')
    def test_health_endpoint_degraded(self, mock_checker_class):
        """Test health endpoint when some services are down"""
        mock_checker = MagicMock()
        mock_checker.check_all_services.return_value = {
            'google_ai': {'status': 'error', 'message': 'API key missing'},
            'spacy': {'status': 'healthy', 'message': 'spaCy models loaded'},
            'wikipedia_api': {'status': 'healthy', 'message': 'Wikipedia API available'},
            'newspaper': {'status': 'healthy', 'message': 'newspaper3k available'}
        }
        mock_checker_class.return_value = mock_checker
        
        response = self.client.get(reverse('verifast_app:health_check'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'degraded')
        self.assertIn('services', data)
    
    def test_health_endpoint_method_not_allowed(self):
        """Test health endpoint with wrong HTTP method"""
        response = self.client.post(reverse('verifast_app:health_check'))
        
        self.assertEqual(response.status_code, 405)  # Method Not Allowed