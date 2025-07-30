from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ServiceHealthChecker:
    """Monitor health of external services"""
    
    def check_google_ai(self) -> Dict[str, Any]:
        """Check Google AI service availability"""
        try:
            import google.generativeai as genai
            # Simple test call - just check if we can import and configure
            genai.configure(api_key="test")  # This won't make actual calls
            return {'status': 'healthy', 'message': 'Google AI available'}
        except ImportError:
            return {'status': 'unavailable', 'message': 'Google AI not installed'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def check_spacy(self) -> Dict[str, Any]:
        """Check spaCy service availability"""
        try:
            import spacy
            try:
                spacy.load("en_core_web_sm")
                return {'status': 'healthy', 'message': 'spaCy models loaded'}
            except OSError:
                return {'status': 'error', 'message': 'spaCy models not downloaded'}
        except ImportError:
            return {'status': 'unavailable', 'message': 'spaCy not installed'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
            
    def check_wikipedia_api(self) -> Dict[str, Any]:
        """Check Wikipedia API availability"""
        try:
            import wikipediaapi
            wiki = wikipediaapi.Wikipedia(language='en', user_agent='VeriFastApp/1.0')
            # Try to fetch a known page
            page = wiki.page('Wikipedia')
            if page.exists():
                return {'status': 'healthy', 'message': 'Wikipedia API available'}
            else:
                return {'status': 'error', 'message': 'Wikipedia API returned no results'}
        except ImportError:
            return {'status': 'unavailable', 'message': 'Wikipedia API not installed'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
            
    def check_newspaper(self) -> Dict[str, Any]:
        """Check newspaper3k availability"""
        try:
            # Test if newspaper3k can be imported and used
            from newspaper import Article
            # Create a test article object to verify functionality
            Article('')  # Just test instantiation
            return {'status': 'healthy', 'message': 'newspaper3k available'}
        except ImportError:
            return {'status': 'unavailable', 'message': 'newspaper3k not installed'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def check_all_services(self) -> Dict[str, Dict[str, Any]]:
        """Check all services and return their status"""
        return {
            'google_ai': self.check_google_ai(),
            'spacy': self.check_spacy(),
            'wikipedia_api': self.check_wikipedia_api(),
            'newspaper': self.check_newspaper()
        }