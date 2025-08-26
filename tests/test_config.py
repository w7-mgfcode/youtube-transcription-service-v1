"""Tests for configuration management."""

import pytest
from src.config import VertexAIModels, settings


class TestVertexAIModels:
    """Test Vertex AI model configuration."""
    
    def test_all_models_list(self):
        """Test that all models are returned."""
        models = VertexAIModels.get_all_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert VertexAIModels.GEMINI_2_0_FLASH in models
        assert VertexAIModels.AUTO_DETECT in models
    
    def test_model_descriptions(self):
        """Test that all models have descriptions."""
        models = VertexAIModels.get_all_models()
        
        for model in models:
            description = VertexAIModels.get_model_description(model)
            assert isinstance(description, str)
            assert len(description) > 0
            assert description != "Ismeretlen modell"
    
    def test_auto_detect_order(self):
        """Test auto-detect fallback order."""
        order = VertexAIModels.get_auto_detect_order()
        
        assert isinstance(order, list)
        assert len(order) > 0
        assert VertexAIModels.GEMINI_2_0_FLASH in order
        # Should not include AUTO_DETECT in the order
        assert VertexAIModels.AUTO_DETECT not in order


class TestSettings:
    """Test application settings."""
    
    def test_settings_instance(self):
        """Test that settings can be accessed."""
        assert settings is not None
        assert hasattr(settings, 'mode')
        assert hasattr(settings, 'vertex_ai_model')
        assert hasattr(settings, 'language_code')
    
    def test_default_values(self):
        """Test default configuration values."""
        assert settings.language_code == "hu-HU"
        assert settings.mode in ["api", "cli"]
        assert settings.vertex_ai_model in VertexAIModels.get_all_models()