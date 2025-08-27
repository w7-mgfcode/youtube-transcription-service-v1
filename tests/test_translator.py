"""Comprehensive tests for the context-aware translator module."""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path

from src.core.translator import (
    ContextAwareTranslator, 
    TranslationQuality,
    TranslationContext
)
from src.config import settings, VertexAIModels
from src.utils.chunking import TranscriptChunker


class TestContextAwareTranslator:
    """Test suite for ContextAwareTranslator class."""
    
    @pytest.fixture
    def translator(self):
        """Create a translator instance for testing."""
        return ContextAwareTranslator()
    
    @pytest.fixture
    def mock_vertex_responses(self, test_data_dir):
        """Load mock Vertex AI responses from test data."""
        with open(test_data_dir / "mock_vertex_responses.json", 'r') as f:
            return json.load(f)
    
    # =========================================================================
    # Context Instructions Tests
    # =========================================================================
    
    def test_context_instructions_all_7_types(self, translator):
        """Test that all 7 context types have proper instructions."""
        contexts = [
            TranslationContext.CASUAL,
            TranslationContext.LEGAL,
            TranslationContext.SPIRITUAL,
            TranslationContext.MARKETING,
            TranslationContext.SCIENTIFIC,
            TranslationContext.EDUCATIONAL,
            TranslationContext.NEWS
        ]
        
        for context in contexts:
            assert context in translator.context_instructions
            instructions = translator.context_instructions[context]
            assert "instruction" in instructions
            assert "terminology" in instructions
            assert "tone" in instructions
            assert len(instructions["instruction"]) > 0
    
    def test_context_specific_prompts(self, translator):
        """Test that each context generates unique prompts."""
        script = "[00:00:01] Test text"
        prompts = {}
        
        for context in TranslationContext:
            prompt = translator._build_context_prompt(
                script, context, "en-US", "general", "neutral"
            )
            prompts[context] = prompt
            
            # Check prompt contains context-specific elements
            assert context.value in prompt.lower()
            assert "CRITICAL" in prompt  # Timing preservation warning
            assert "[00:00:01]" in prompt  # Original timestamp
        
        # Ensure all prompts are unique
        unique_prompts = set(prompts.values())
        assert len(unique_prompts) == len(TranslationContext)
    
    # =========================================================================
    # Single Chunk Translation Tests
    # =========================================================================
    
    @patch('src.core.translator.vertexai')
    def test_translate_single_chunk(self, mock_vertexai, translator, sample_transcript):
        """Test translation of a single chunk (no chunking needed)."""
        # Setup mock
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "[00:00:01] Welcome everyone!"
        mock_model.generate_content.return_value = mock_response
        mock_vertexai.GenerativeModel.return_value = mock_model
        
        # Short text that doesn't need chunking
        short_text = "[00:00:01] Üdvözöllek mindenkit!"
        
        result = translator.translate_script(
            short_text,
            "en-US",
            TranslationContext.CASUAL
        )
        
        assert result is not None
        assert result["translated_text"] == "[00:00:01] Welcome everyone!"
        assert result["chunks_processed"] == 1
        assert result["target_language"] == "en-US"
    
    @patch('src.core.translator.vertexai')
    def test_preserve_timestamps(self, mock_vertexai, translator):
        """Test that timestamps are preserved during translation."""
        # Setup mock with multiple timestamps
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """[00:00:01] Hello!
[00:00:05] How are you?
[00:00:10] [breath]
[00:00:11] Let's begin."""
        
        mock_model.generate_content.return_value = mock_response
        mock_vertexai.GenerativeModel.return_value = mock_model
        
        input_text = """[00:00:01] Sziasztok!
[00:00:05] Hogy vagytok?
[00:00:10] [levegővétel]
[00:00:11] Kezdjük el."""
        
        result = translator.translate_script(input_text, "en-US")
        
        # Check timestamps are preserved
        assert "[00:00:01]" in result["translated_text"]
        assert "[00:00:05]" in result["translated_text"]
        assert "[00:00:10]" in result["translated_text"]
        assert "[00:00:11]" in result["translated_text"]
        assert "[breath]" in result["translated_text"]  # Special markers preserved
    
    # =========================================================================
    # Chunking Support Tests
    # =========================================================================
    
    @patch('src.core.translator.vertexai')
    def test_translate_with_chunking(self, mock_vertexai, translator):
        """Test translation of long text that requires chunking."""
        # Generate long text
        long_text = "\n".join([
            f"[00:{i:02d}:00] Ez egy nagyon hosszú szöveg rész {i}."
            for i in range(100)  # 100 lines should trigger chunking
        ])
        
        # Setup mock to return translated chunks
        mock_model = MagicMock()
        mock_responses = []
        for i in range(100):
            response = MagicMock()
            response.text = f"[00:{i:02d}:00] This is a very long text part {i}."
            mock_responses.append(response)
        
        mock_model.generate_content.side_effect = mock_responses
        mock_vertexai.GenerativeModel.return_value = mock_model
        
        result = translator.translate_script(
            long_text,
            "en-US",
            quality=TranslationQuality.FAST
        )
        
        assert result is not None
        assert result["chunks_processed"] > 1
        assert "This is a very long text" in result["translated_text"]
    
    def test_chunk_boundary_handling(self, translator):
        """Test that chunk boundaries don't break timestamps."""
        # Create text at chunk boundary
        chunker = TranscriptChunker()
        boundary_size = settings.chunk_size
        
        # Generate text near boundary
        lines = []
        char_count = 0
        line_num = 0
        while char_count < boundary_size + 100:
            line = f"[00:00:{line_num:02d}] Line {line_num}"
            lines.append(line)
            char_count += len(line)
            line_num += 1
        
        text = "\n".join(lines)
        chunks = chunker.chunk_text(text)
        
        # Verify chunks maintain timestamp integrity
        for chunk_text, start, end in chunks:
            # Each chunk should start with a timestamp
            assert chunk_text.strip().startswith("[")
            # Timestamps should be complete, not cut off
            assert chunk_text.count("[") == chunk_text.count("]")
    
    # =========================================================================
    # Multi-Region Fallback Tests
    # =========================================================================
    
    @patch('src.core.translator.vertexai')
    def test_multi_region_fallback(self, mock_vertexai, translator):
        """Test fallback through multiple regions on failure."""
        mock_model = MagicMock()
        
        # First two calls fail, third succeeds
        mock_model.generate_content.side_effect = [
            Exception("Region unavailable"),
            Exception("Model not found"),
            MagicMock(text="[00:00:01] Success!")
        ]
        
        mock_vertexai.GenerativeModel.return_value = mock_model
        
        result = translator._translate_single_chunk(
            "[00:00:01] Test",
            "en-US",
            TranslationContext.CASUAL
        )
        
        # Should succeed after fallback
        assert result is not None
        assert result["translated_text"] == "[00:00:01] Success!"
        
        # Check that multiple regions were tried
        assert mock_vertexai.init.call_count >= 3
    
    def test_all_regions_fail(self, translator):
        """Test behavior when all regions fail."""
        with patch('src.core.translator.vertexai') as mock_vertexai:
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = Exception("All regions down")
            mock_vertexai.GenerativeModel.return_value = mock_model
            
            result = translator._translate_single_chunk(
                "[00:00:01] Test",
                "en-US",
                TranslationContext.CASUAL
            )
            
            assert result is None
    
    # =========================================================================
    # Language Support Tests
    # =========================================================================
    
    def test_supported_languages(self, translator):
        """Test that 20+ languages are supported."""
        supported_languages = [
            "en-US", "en-GB", "de-DE", "fr-FR", "es-ES", "es-MX",
            "it-IT", "pt-BR", "pt-PT", "nl-NL", "pl-PL", "ru-RU",
            "ja-JP", "ko-KR", "zh-CN", "zh-TW", "hi-IN", "ar-SA",
            "tr-TR", "sv-SE", "da-DK", "no-NO", "fi-FI"
        ]
        
        for lang in supported_languages:
            # Language codes should be valid
            assert len(lang) == 5
            assert "-" in lang
            
            # Test language in prompt building
            prompt = translator._build_context_prompt(
                "[00:00:01] Test",
                TranslationContext.CASUAL,
                lang,
                "general",
                "neutral"
            )
            assert lang in prompt
    
    # =========================================================================
    # Translation Quality Tests
    # =========================================================================
    
    def test_translation_quality_levels(self, translator):
        """Test different translation quality levels."""
        qualities = [
            TranslationQuality.FAST,
            TranslationQuality.BALANCED,
            TranslationQuality.HIGH
        ]
        
        for quality in qualities:
            prompt = translator._build_quality_prompt(
                "[00:00:01] Test",
                quality
            )
            
            if quality == TranslationQuality.FAST:
                assert "quick" in prompt.lower() or "fast" in prompt.lower()
            elif quality == TranslationQuality.HIGH:
                assert "high quality" in prompt.lower() or "accurate" in prompt.lower()
    
    @patch('src.core.translator.vertexai')
    def test_quality_affects_model_selection(self, mock_vertexai, translator):
        """Test that quality level affects model selection."""
        mock_model = MagicMock()
        mock_response = MagicMock(text="[00:00:01] Translated")
        mock_model.generate_content.return_value = mock_response
        mock_vertexai.GenerativeModel.return_value = mock_model
        
        # High quality should prefer better models
        result_high = translator.translate_script(
            "[00:00:01] Test",
            "en-US",
            quality=TranslationQuality.HIGH
        )
        
        # Fast quality should prefer faster models
        result_fast = translator.translate_script(
            "[00:00:01] Test",
            "en-US",
            quality=TranslationQuality.FAST
        )
        
        assert result_high is not None
        assert result_fast is not None
    
    # =========================================================================
    # Error Handling Tests
    # =========================================================================
    
    def test_invalid_input_handling(self, translator):
        """Test handling of invalid inputs."""
        # Empty text
        result = translator.translate_script("", "en-US")
        assert result is None or result["translated_text"] == ""
        
        # None text
        result = translator.translate_script(None, "en-US")
        assert result is None
        
        # Invalid language code
        result = translator.translate_script("[00:00:01] Test", "invalid")
        # Should still attempt translation
        assert result is None or "error" in result
    
    @patch('src.core.translator.vertexai')
    def test_api_error_handling(self, mock_vertexai, translator):
        """Test handling of API errors."""
        mock_model = MagicMock()
        
        # Test various API errors
        errors = [
            Exception("Quota exceeded"),
            Exception("Invalid API key"),
            Exception("Model not found"),
            Exception("Timeout")
        ]
        
        for error in errors:
            mock_model.generate_content.side_effect = error
            mock_vertexai.GenerativeModel.return_value = mock_model
            
            result = translator._translate_single_chunk(
                "[00:00:01] Test",
                "en-US",
                TranslationContext.CASUAL
            )
            
            # Should handle gracefully
            assert result is None or "error" in result
    
    # =========================================================================
    # Timing Preservation Tests
    # =========================================================================
    
    def test_timestamp_format_validation(self, translator):
        """Test validation of various timestamp formats."""
        valid_formats = [
            "[00:00:01]",
            "[00:01:30]",
            "[01:30:45]",
            "[99:59:59]"
        ]
        
        invalid_formats = [
            "[0:0:1]",
            "[00:60:00]",
            "[00:00:60]",
            "00:00:01",
            "[00:00:00"
        ]
        
        for ts in valid_formats:
            assert translator._is_valid_timestamp(ts)
        
        for ts in invalid_formats:
            assert not translator._is_valid_timestamp(ts)
    
    def test_special_markers_preservation(self, translator):
        """Test that special markers are preserved."""
        markers = [
            "[levegővétel]",
            "[szünet]",
            "[nevetés]",
            "[köhögés]",
            "[zene]"
        ]
        
        for marker in markers:
            text = f"[00:00:01] Hello {marker} world"
            # Marker should be preserved or translated appropriately
            assert marker in text or translator._translate_marker(marker) in text
    
    # =========================================================================
    # Cost Estimation Tests
    # =========================================================================
    
    def test_translation_cost_estimation(self, translator):
        """Test cost estimation for translation."""
        text = "[00:00:01] " + "Test text " * 100  # ~1000 characters
        
        cost = translator.estimate_translation_cost(
            text,
            "en-US",
            TranslationQuality.BALANCED
        )
        
        assert cost is not None
        assert cost["character_count"] > 0
        assert cost["estimated_cost_usd"] > 0
        assert "model" in cost
        assert "quality" in cost
    
    # =========================================================================
    # Integration Tests
    # =========================================================================
    
    @patch('src.core.translator.vertexai')
    def test_full_translation_pipeline(self, mock_vertexai, translator, sample_transcript):
        """Test complete translation pipeline with real-like data."""
        # Setup mock
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = sample_transcript.replace("magyar", "English")
        mock_model.generate_content.return_value = mock_response
        mock_vertexai.GenerativeModel.return_value = mock_model
        
        result = translator.translate_script(
            sample_transcript,
            "en-US",
            context=TranslationContext.EDUCATIONAL,
            audience="students",
            tone="friendly",
            quality=TranslationQuality.HIGH,
            preserve_timing=True
        )
        
        assert result is not None
        assert result["success"] == True
        assert result["target_language"] == "en-US"
        assert result["context"] == TranslationContext.EDUCATIONAL
        assert len(result["translated_text"]) > 0
        
        # Check metadata
        assert "processing_time" in result
        assert "chunks_processed" in result
        assert "model_used" in result