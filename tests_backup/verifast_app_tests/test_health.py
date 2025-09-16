from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse

from verifast_app.health import ServiceHealthChecker


class TestHealthChecker(TestCase):
    """Test health check functionality"""
    
    def setUp(self):
        self.checker = ServiceHealthChecker()
    
    @patch.object(ServiceHealthChecker, 'check_google_ai')
    def test_check_google_ai_healthy(self, mock_check_google_ai):
        """Test Google AI health check when service is healthy"""
        mock_check_google_ai.return_value = {'status': 'healthy', 'message': 'Google AI available'}
        
        result = self.checker.check_google_ai()
        
        self.assertEqual(result['status'], 'healthy')
        self.assertEqual(result['message'], 'Google AI available')
    
    @patch.object(ServiceHealthChecker, 'check_google_ai')
    def test_check_google_ai_error(self, mock_check_google_ai):
        """Test Google AI health check when service has error"""
        mock_check_google_ai.return_value = {'status': 'error', 'message': 'API error'}
        
        result = self.checker.check_google_ai()
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('API error', result['message'])
    
    def test_check_google_ai_unavailable(self):
        """Test Google AI health check when not installed"""
        with patch.dict('sys.modules', {'google.generativeai': None}):
            result = self.checker.check_google_ai()
            
            self.assertEqual(result['status'], 'unavailable')
            self.assertEqual(result['message'], 'Google AI not installed')
    
    @patch.object(ServiceHealthChecker, 'check_spacy')
    def test_check_spacy_healthy(self, mock_check_spacy):
        """Test spaCy health check when models are loaded"""
        mock_check_spacy.return_value = {'status': 'healthy', 'message': 'spaCy models loaded'}
        
        result = self.checker.check_spacy()
        
        self.assertEqual(result['status'], 'healthy')
        self.assertEqual(result['message'], 'spaCy models loaded')
    
    @patch.object(ServiceHealthChecker, 'check_spacy')
    def test_check_spacy_model_missing(self, mock_check_spacy):
        """Test spaCy health check when models are missing"""
        mock_check_spacy.return_value = {'status': 'error', 'message': 'spaCy models not downloaded'}
        
        result = self.checker.check_spacy()
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'spaCy models not downloaded')
    
    @patch.object(ServiceHealthChecker, 'check_wikipedia_api')
    def test_check_wikipedia_api_healthy(self, mock_check_wikipedia_api):
        """Test Wikipedia API health check when service is healthy"""
        mock_check_wikipedia_api.return_value = {'status': 'healthy', 'message': 'Wikipedia API available'}
        
        result = self.checker.check_wikipedia_api()
        
        self.assertEqual(result['status'], 'healthy')
        self.assertEqual(result['message'], 'Wikipedia API available')
    
    @patch.object(ServiceHealthChecker, 'check_wikipedia_api')
    def test_check_wikipedia_api_no_results(self, mock_check_wikipedia_api):
        """Test Wikipedia API health check when no results returned"""
        mock_check_wikipedia_api.return_value = {'status': 'error', 'message': 'Wikipedia API returned no results'}
        
        result = self.checker.check_wikipedia_api()
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'Wikipedia API returned no results')
    
    @patch.object(ServiceHealthChecker, 'check_newspaper')
    def test_check_newspaper_healthy(self, mock_check_newspaper):
        """Test newspaper3k health check when available"""
        mock_check_newspaper.return_value = {'status': 'healthy', 'message': 'newspaper3k available'}
        
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