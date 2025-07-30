"""
Simple tests that don't require database access.
"""
import pytest
from unittest.mock import patch, MagicMock


def test_basic_functionality():
    """Test basic Python functionality"""
    assert 1 + 1 == 2
    assert "hello".upper() == "HELLO"


@patch('verifast_app.services.genai')
def test_mock_functionality(mock_genai):
    """Test that mocking works correctly"""
    mock_genai.GenerativeModel.return_value = MagicMock()
    
    # Import here to avoid Django setup issues
    from verifast_app.services import generate_master_analysis
    
    # This should use the fallback decorator
    result = generate_master_analysis("test-model", [], "")
    
    # Should return fallback values for empty content
    assert result == {'quiz': {}, 'tags': []}


def test_environment_variables():
    """Test environment variable handling"""
    import os
    
    # Test setting and getting environment variables
    test_key = "TEST_VERIFAST_VAR"
    test_value = "test_value"
    
    os.environ[test_key] = test_value
    assert os.environ.get(test_key) == test_value
    
    # Clean up
    del os.environ[test_key]


def test_imports():
    """Test that critical modules can be imported"""
    import importlib.util
    
    critical_modules = [
        'spacy',
        'newspaper',
        'google.generativeai',
        'wikipediaapi',
        'textstat'
    ]
    
    for module_name in critical_modules:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            pytest.fail(f"Critical module not available: {module_name}")
    
    assert True  # All modules are available


def test_feature_flags():
    """Test feature flags functionality"""
    from verifast_app.feature_flags import FeatureFlags
    
    # Test default values
    assert isinstance(FeatureFlags.ai_features_enabled(), bool)
    assert isinstance(FeatureFlags.nlp_features_enabled(), bool)
    assert isinstance(FeatureFlags.wikipedia_validation_enabled(), bool)
    assert isinstance(FeatureFlags.article_scraping_enabled(), bool)


def test_decorators():
    """Test the with_fallback decorator"""
    from verifast_app.decorators import with_fallback
    
    @with_fallback(fallback_return="fallback")
    def test_function():
        raise Exception("Test error")
    
    result = test_function()
    assert result == "fallback"
    
    @with_fallback(fallback_return="fallback")
    def working_function():
        return "success"
    
    result = working_function()
    assert result == "success"