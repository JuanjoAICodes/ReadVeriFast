"""
Model selection service with fallback logic for LLM quiz generation.
"""

import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """Model tiers based on capability and cost."""
    PREMIUM = "premium"      # Best quality, highest cost
    STANDARD = "standard"    # Good quality, moderate cost  
    FALLBACK = "fallback"    # Basic quality, lowest cost


class ModelConfig:
    """Configuration for individual models."""
    
    def __init__(self, name: str, tier: ModelTier, max_tokens: int, 
                 temperature: float = 0.9, supports_languages: List[str] = None):
        self.name = name
        self.tier = tier
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.supports_languages = supports_languages or ['en', 'es']
        self.failure_count = 0
        self.last_failure = None


class ModelSelector:
    """Intelligent model selection with fallback logic."""
    
    def __init__(self):
        self.models = {
            # Premium models - best quality
            "gemini-1.5-pro": ModelConfig(
                name="gemini-1.5-pro", 
                tier=ModelTier.PREMIUM,
                max_tokens=8192,
                temperature=0.9,
                supports_languages=['en', 'es']
            ),
            
            # Standard models - good balance
            "gemini-1.5-flash": ModelConfig(
                name="gemini-1.5-flash",
                tier=ModelTier.STANDARD, 
                max_tokens=8192,
                temperature=0.9,
                supports_languages=['en', 'es']
            ),
            
            # Fallback models - basic but reliable
            "gemma-3-27b-it": ModelConfig(
                name="gemma-3-27b-it", # corrected name
                tier=ModelTier.FALLBACK,
                max_tokens=4096,
                temperature=0.8,
                supports_languages=['en', 'es']
            ),
            "gemma-3-27b-it": ModelConfig(
                name="gemma-3-27b-it", # corrected name
                tier=ModelTier.FALLBACK,
                max_tokens=4096,
                temperature=0.8,
                supports_languages=['en', 'es']
            )
        }
        
        # Model selection order by preference
        self.selection_order = [
            "gemini-1.5-pro", 
            "gemini-1.5-flash",
            "gemma-3-27b-it",
            "gemma-3-27b-it"
        ]
    
    def select_model(self, reading_level: float, word_count: int, 
                    language: str = 'en', source: str = 'user_submission') -> Tuple[str, ModelConfig]:
        """
        Select the best available model based on content characteristics.
        
        Args:
            reading_level: Flesch-Kincaid reading level (lower = more complex)
            word_count: Number of words in the article
            language: Article language ('en' or 'es')
            source: Article source (affects model selection)
            
        Returns:
            Tuple of (model_name, model_config)
        """
        
        # Special handling for different sources
        if source == "gutenberg":
            # Gutenberg texts are often complex, prefer premium models
            preferred_tiers = [ModelTier.PREMIUM, ModelTier.STANDARD, ModelTier.FALLBACK]
        elif word_count > 2000:
            # Long articles need premium models
            preferred_tiers = [ModelTier.PREMIUM, ModelTier.STANDARD, ModelTier.FALLBACK]
        elif reading_level < 30:
            # Complex content (low reading level score) needs better models
            preferred_tiers = [ModelTier.PREMIUM, ModelTier.STANDARD, ModelTier.FALLBACK]
        else:
            # Standard content can use any model
            preferred_tiers = [ModelTier.STANDARD, ModelTier.PREMIUM, ModelTier.FALLBACK]
        
        # Try models in order of preference and availability
        for model_name in self.selection_order:
            model_config = self.models[model_name]
            
            # Check if model supports the language
            if language not in model_config.supports_languages:
                continue
                
            # Check if model tier is preferred for this content
            if model_config.tier not in preferred_tiers:
                continue
                
            # Check if model has too many recent failures
            if model_config.failure_count > 3:
                logger.warning(f"Skipping model {model_name} due to recent failures ({model_config.failure_count})")
                continue
            
            # Test model availability
            if self._test_model_availability(model_name):
                logger.info(f"Selected model {model_name} (tier: {model_config.tier.value}) for content: "
                           f"reading_level={reading_level}, word_count={word_count}, language={language}")
                return model_name, model_config
            else:
                self._record_model_failure(model_name, "Model unavailable")
        
        # If no preferred model is available, try any working model
        logger.warning("No preferred models available, trying fallback models")
        for model_name in self.selection_order:
            model_config = self.models[model_name]
            
            if language in model_config.supports_languages and self._test_model_availability(model_name):
                logger.info(f"Using fallback model {model_name}")
                return model_name, model_config
        
        # Last resort - return the most basic model
        fallback_model = "gemma-3-27b-it"
        logger.error(f"All models failed, using last resort: {fallback_model}")
        return fallback_model, self.models[fallback_model]
    
    def _test_model_availability(self, model_name: str) -> bool:
        """
        Test if a model is currently available.
        
        Args:
            model_name: Name of the model to test
            
        Returns:
            True if model is available, False otherwise
        """
        try:
            # Try to create a model instance
            model = genai.GenerativeModel(model_name)
            
            # Test with a minimal request
            response = model.generate_content(
                "Test",
                generation_config={
                    "max_output_tokens": 10,
                    "temperature": 0.1
                }
            )
            
            # If we get here, model is working
            return True
            
        except google_exceptions.ResourceExhausted:
            # Quota exceeded - model exists but unavailable
            logger.warning(f"Model {model_name} quota exceeded")
            return False
        except google_exceptions.NotFound:
            # Model doesn't exist
            logger.error(f"Model {model_name} not found")
            return False
        except Exception as e:
            # Other errors
            logger.error(f"Error testing model {model_name}: {e}")
            return False
    
    def _record_model_failure(self, model_name: str, error: str):
        """Record a model failure for future selection decisions."""
        if model_name in self.models:
            self.models[model_name].failure_count += 1
            self.models[model_name].last_failure = error
            logger.warning(f"Recorded failure for model {model_name}: {error} "
                          f"(total failures: {self.models[model_name].failure_count})")
    
    def record_model_success(self, model_name: str):
        """Record a successful model usage to reset failure count."""
        if model_name in self.models:
            self.models[model_name].failure_count = 0
            self.models[model_name].last_failure = None
            logger.debug(f"Reset failure count for successful model {model_name}")
    
    def get_generation_config(self, model_config: ModelConfig, question_count: int) -> Dict:
        """
        Get generation configuration for a specific model.
        
        Args:
            model_config: Configuration for the selected model
            question_count: Number of questions to generate
            
        Returns:
            Generation configuration dictionary
        """
        # Calculate required tokens based on question count
        estimated_tokens_per_question = 150  # Question + 4 options + answer
        estimated_total_tokens = question_count * estimated_tokens_per_question + 200  # Buffer
        
        max_output_tokens = min(estimated_total_tokens, model_config.max_tokens)
        
        return {
            "temperature": model_config.temperature,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": max_output_tokens,
            "response_mime_type": "text/plain",
        }
    
    def get_model_stats(self) -> Dict:
        """Get statistics about model usage and failures."""
        stats = {}
        for name, config in self.models.items():
            stats[name] = {
                "tier": config.tier.value,
                "failure_count": config.failure_count,
                "last_failure": config.last_failure,
                "max_tokens": config.max_tokens,
                "supports_languages": config.supports_languages
            }
        return stats


# Global model selector instance
model_selector = ModelSelector()