from django.conf import settings

class FeatureFlags:
    """Centralized feature flag management"""
    
    @staticmethod
    def ai_features_enabled() -> bool:
        """Check if AI features are enabled"""
        return getattr(settings, 'ENABLE_AI_FEATURES', True)
    
    @staticmethod
    def nlp_features_enabled() -> bool:
        """Check if NLP features are enabled"""
        return getattr(settings, 'ENABLE_NLP_FEATURES', True)
    
    @staticmethod
    def wikipedia_validation_enabled() -> bool:
        """Check if Wikipedia validation is enabled"""
        return getattr(settings, 'ENABLE_WIKIPEDIA_VALIDATION', True)
    
    @staticmethod
    def article_scraping_enabled() -> bool:
        """Check if article scraping is enabled"""
        return getattr(settings, 'ENABLE_ARTICLE_SCRAPING', True)