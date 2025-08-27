"""Comprehensive tests for the ElevenLabs synthesizer module."""

import json
import base64
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
import tempfile
import os

from src.core.synthesizer import (
    ElevenLabsSynthesizer,
    VoiceNotFoundError,
    SynthesisError
)
from src.config import settings
from src.models.dubbing import AudioQuality


class TestElevenLabsSynthesizer:
    """Test suite for ElevenLabsSynthesizer class."""
    
    @pytest.fixture
    def synthesizer(self):
        """Create a synthesizer instance for testing."""
        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test-key'}):
            return ElevenLabsSynthesizer()
    
    @pytest.fixture
    def mock_elevenlabs_data(self, test_data_dir):
        """Load mock ElevenLabs responses from test data."""
        with open(test_data_dir / "mock_elevenlabs_responses.json", 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def timed_script(self):
        """Sample timed script for testing."""
        return """[00:00:01] Welcome to this test video!
[00:00:05] This is the second line.
[00:00:10] [breath]
[00:00:11] And here's the third line.
[00:00:15] Thank you for watching!"""
    
    # =========================================================================
    # Initialization Tests
    # =========================================================================
    
    def test_initialization_with_api_key(self):
        """Test synthesizer initialization with API key."""
        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test-api-key'}):
            synth = ElevenLabsSynthesizer()
            assert synth.api_key == 'test-api-key'
            assert synth.base_url == settings.elevenlabs_base_url
            assert synth.model == settings.elevenlabs_model
    
    def test_initialization_without_api_key(self, capsys):
        """Test synthesizer initialization without API key."""
        with patch.dict(os.environ, {}, clear=True):
            synth = ElevenLabsSynthesizer()
            captured = capsys.readouterr()
            assert "ElevenLabs API key not configured" in captured.out
    
    # =========================================================================
    # Script to ElevenLabs Format Tests
    # =========================================================================
    
    def test_script_to_elevenlabs_format(self, synthesizer, timed_script):
        """Test conversion of timed script to ElevenLabs format."""
        segments = synthesizer._script_to_elevenlabs_format(timed_script)
        
        assert len(segments) == 4  # Excluding [breath] marker
        
        # Check first segment
        assert segments[0]["text"] == "Welcome to this test video!"
        assert segments[0]["start_time"] == 1.0
        assert "end_time" in segments[0]
        
        # Check second segment
        assert segments[1]["text"] == "This is the second line."
        assert segments[1]["start_time"] == 5.0
        
        # Check timing continuity
        for i in range(len(segments) - 1):
            assert segments[i]["end_time"] <= segments[i + 1]["start_time"]
    
    def test_timestamp_extraction(self, synthesizer):
        """Test extraction of timestamps from various formats."""
        test_cases = [
            ("[00:00:01] Text", 1.0),
            ("[00:01:30] Text", 90.0),
            ("[01:00:00] Text", 3600.0),
            ("[10:30:45] Text", 37845.0)
        ]
        
        for script, expected_time in test_cases:
            segments = synthesizer._script_to_elevenlabs_format(script)
            assert segments[0]["start_time"] == expected_time
    
    def test_special_markers_handling(self, synthesizer):
        """Test that special markers are handled correctly."""
        script = """[00:00:01] First line
[00:00:05] [breath]
[00:00:06] [pause]
[00:00:07] Second line
[00:00:10] [laughter]
[00:00:11] Third line"""
        
        segments = synthesizer._script_to_elevenlabs_format(script)
        
        # Special markers should be filtered out
        texts = [seg["text"] for seg in segments]
        assert "First line" in texts
        assert "Second line" in texts
        assert "Third line" in texts
        assert "[breath]" not in " ".join(texts)
        assert "[pause]" not in " ".join(texts)
    
    # =========================================================================
    # Single Call Synthesis Tests
    # =========================================================================
    
    @patch('src.core.synthesizer.httpx.Client')
    def test_single_call_synthesis(self, mock_client, synthesizer, timed_script, temp_dir):
        """Test single API call synthesis for short content."""
        # Setup mock
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake_audio_data"
        mock_response.json.return_value = {
            "duration_seconds": 15.0,
            "character_count": 100
        }
        mock_instance.post.return_value = mock_response
        mock_client.return_value = mock_instance
        
        output_path = f"{temp_dir}/test_output.mp3"
        
        result = synthesizer.synthesize_script(
            timed_script,
            "test_voice_id",
            output_path
        )
        
        assert result["success"] == True
        assert result["audio_file"] == output_path
        assert result["duration_seconds"] == 15.0
        assert os.path.exists(output_path)
        
        # Verify API call
        mock_instance.post.assert_called_once()
        call_args = mock_instance.post.call_args
        assert "test_voice_id" in str(call_args)
    
    # =========================================================================
    # Chunked Synthesis Tests
    # =========================================================================
    
    @patch('src.core.synthesizer.httpx.Client')
    def test_chunked_synthesis(self, mock_client, synthesizer, temp_dir):
        """Test chunked synthesis for long content."""
        # Generate long script (>50 segments)
        long_script = "\n".join([
            f"[00:{i:02d}:00] This is line number {i}"
            for i in range(60)
        ])
        
        # Setup mock for multiple chunks
        mock_instance = MagicMock()
        mock_responses = []
        for i in range(3):  # Expect 3 chunks
            response = MagicMock()
            response.status_code = 200
            response.content = b"chunk_audio_data_" + str(i).encode()
            response.json.return_value = {
                "duration_seconds": 20.0,
                "character_count": 400
            }
            mock_responses.append(response)
        
        mock_instance.post.side_effect = mock_responses
        mock_client.return_value = mock_instance
        
        output_path = f"{temp_dir}/test_chunked.mp3"
        
        result = synthesizer.synthesize_script(
            long_script,
            "test_voice_id",
            output_path,
            audio_quality="high"
        )
        
        assert result["success"] == True
        assert result["chunks_processed"] > 1
        assert "processing_time" in result
    
    # =========================================================================
    # Voice Profile Tests
    # =========================================================================
    
    @patch('src.core.synthesizer.httpx.Client')
    def test_voice_profile_validation(self, mock_client, synthesizer):
        """Test voice profile validation and fetching."""
        # Setup mock for voice list
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "voices": [
                {"voice_id": "voice1", "name": "Adam"},
                {"voice_id": "voice2", "name": "Rachel"}
            ]
        }
        mock_instance.get.return_value = mock_response
        mock_client.return_value = mock_instance
        
        # Test getting available voices
        voices = synthesizer.get_available_voices()
        assert len(voices) == 2
        assert voices[0]["voice_id"] == "voice1"
        
        # Test voice validation
        assert synthesizer.validate_voice_id("voice1") == True
        assert synthesizer.validate_voice_id("invalid_voice") == False
    
    @patch('src.core.synthesizer.httpx.Client')
    def test_voice_not_found_error(self, mock_client, synthesizer, timed_script, temp_dir):
        """Test handling of invalid voice ID."""
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "error": "Voice not found"
        }
        mock_instance.post.return_value = mock_response
        mock_client.return_value = mock_instance
        
        output_path = f"{temp_dir}/test.mp3"
        
        with pytest.raises(VoiceNotFoundError):
            synthesizer.synthesize_script(
                timed_script,
                "invalid_voice_id",
                output_path
            )
    
    # =========================================================================
    # Audio Quality Settings Tests
    # =========================================================================
    
    @patch('src.core.synthesizer.httpx.Client')
    def test_audio_quality_settings(self, mock_client, synthesizer, timed_script, temp_dir):
        """Test different audio quality settings."""
        qualities = [
            (AudioQuality.LOW, "mp3_22050_32"),
            (AudioQuality.MEDIUM, "mp3_44100_64"),
            (AudioQuality.HIGH, "mp3_44100_128")
        ]
        
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"audio_data"
        mock_instance.post.return_value = mock_response
        mock_client.return_value = mock_instance
        
        for quality, expected_format in qualities:
            output_path = f"{temp_dir}/test_{quality.value}.mp3"
            
            result = synthesizer.synthesize_script(
                timed_script,
                "test_voice",
                output_path,
                audio_quality=quality.value
            )
            
            # Check that the correct format was requested
            call_args = mock_instance.post.call_args
            assert expected_format in str(call_args) or quality.value in str(call_args)
    
    # =========================================================================
    # Error Handling and Retry Logic Tests
    # =========================================================================
    
    @patch('src.core.synthesizer.httpx.Client')
    def test_retry_logic(self, mock_client, synthesizer, timed_script, temp_dir):
        """Test retry logic on temporary failures."""
        mock_instance = MagicMock()
        
        # First call fails, second succeeds
        mock_responses = [
            MagicMock(status_code=500),  # Server error
            MagicMock(status_code=200, content=b"audio_data")  # Success
        ]
        mock_instance.post.side_effect = mock_responses
        mock_client.return_value = mock_instance
        
        output_path = f"{temp_dir}/test_retry.mp3"
        
        result = synthesizer.synthesize_script(
            timed_script,
            "test_voice",
            output_path
        )
        
        assert result["success"] == True
        assert mock_instance.post.call_count == 2  # Retried once
    
    @patch('src.core.synthesizer.httpx.Client')
    def test_quota_exceeded_error(self, mock_client, synthesizer, timed_script, temp_dir):
        """Test handling of quota exceeded errors."""
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "error": "Quota exceeded"
        }
        mock_instance.post.return_value = mock_response
        mock_client.return_value = mock_instance
        
        output_path = f"{temp_dir}/test.mp3"
        
        with pytest.raises(SynthesisError) as exc_info:
            synthesizer.synthesize_script(
                timed_script,
                "test_voice",
                output_path
            )
        
        assert "quota" in str(exc_info.value).lower()
    
    @patch('src.core.synthesizer.httpx.Client')
    def test_unauthorized_error(self, mock_client, synthesizer, timed_script, temp_dir):
        """Test handling of authentication errors."""
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": "Unauthorized"
        }
        mock_instance.post.return_value = mock_response
        mock_client.return_value = mock_instance
        
        output_path = f"{temp_dir}/test.mp3"
        
        with pytest.raises(SynthesisError) as exc_info:
            synthesizer.synthesize_script(
                timed_script,
                "test_voice",
                output_path
            )
        
        assert "unauthorized" in str(exc_info.value).lower() or "401" in str(exc_info.value)
    
    # =========================================================================
    # Cost Estimation Tests
    # =========================================================================
    
    def test_synthesis_cost_estimation(self, synthesizer, mock_elevenlabs_data):
        """Test cost estimation for synthesis."""
        script = "[00:00:01] " + "Test text " * 100  # ~900 characters
        
        cost = synthesizer.estimate_synthesis_cost(
            script,
            audio_quality=AudioQuality.HIGH.value
        )
        
        assert cost["character_count"] > 0
        assert cost["estimated_cost_usd"] > 0
        assert cost["estimated_cost_usd"] == pytest.approx(
            cost["character_count"] / 1000 * mock_elevenlabs_data["cost_estimates"]["per_1000_chars"],
            rel=0.1
        )
    
    def test_model_based_cost_estimation(self, synthesizer, mock_elevenlabs_data):
        """Test that different models have different costs."""
        script = "[00:00:01] Test script with 100 characters."
        
        models = mock_elevenlabs_data["cost_estimates"]["models"]
        costs = {}
        
        for model_name, model_info in models.items():
            cost = synthesizer.estimate_synthesis_cost(
                script,
                model=model_name
            )
            costs[model_name] = cost["estimated_cost_usd"]
        
        # Different models should have different costs
        unique_costs = set(costs.values())
        assert len(unique_costs) > 1 or len(models) == 1
    
    # =========================================================================
    # Progress Tracking Tests
    # =========================================================================
    
    @patch('src.core.synthesizer.httpx.Client')
    def test_synthesis_progress_tracking(self, mock_client, synthesizer, timed_script, temp_dir):
        """Test progress tracking during synthesis."""
        progress_updates = []
        
        def progress_callback(message, percentage):
            progress_updates.append((message, percentage))
        
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"audio_data"
        mock_instance.post.return_value = mock_response
        mock_client.return_value = mock_instance
        
        output_path = f"{temp_dir}/test.mp3"
        
        result = synthesizer.synthesize_script(
            timed_script,
            "test_voice",
            output_path,
            progress_callback=progress_callback
        )
        
        assert len(progress_updates) > 0
        assert any("synthesis" in msg.lower() for msg, _ in progress_updates)
        assert progress_updates[-1][1] == 100  # Should end at 100%
    
    # =========================================================================
    # File Output Tests
    # =========================================================================
    
    @patch('src.core.synthesizer.httpx.Client')
    def test_audio_file_creation(self, mock_client, synthesizer, timed_script, temp_dir):
        """Test that audio files are created correctly."""
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"RIFF____WAVEfmt audio_data"  # Fake WAV header
        mock_instance.post.return_value = mock_response
        mock_client.return_value = mock_instance
        
        output_path = f"{temp_dir}/test_audio.mp3"
        
        result = synthesizer.synthesize_script(
            timed_script,
            "test_voice",
            output_path
        )
        
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
        
        # Verify content was written
        with open(output_path, 'rb') as f:
            content = f.read()
            assert content == mock_response.content
    
    def test_output_directory_creation(self, synthesizer, timed_script, temp_dir):
        """Test that output directories are created if they don't exist."""
        nested_path = f"{temp_dir}/nested/deep/path/audio.mp3"
        
        with patch('src.core.synthesizer.httpx.Client') as mock_client:
            mock_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"audio_data"
            mock_instance.post.return_value = mock_response
            mock_client.return_value = mock_instance
            
            result = synthesizer.synthesize_script(
                timed_script,
                "test_voice",
                nested_path
            )
            
            assert os.path.exists(os.path.dirname(nested_path))
    
    # =========================================================================
    # Integration Tests
    # =========================================================================
    
    @patch('src.core.synthesizer.httpx.Client')
    def test_full_synthesis_pipeline(
        self, mock_client, synthesizer, sample_transcript, temp_dir
    ):
        """Test complete synthesis pipeline with real-like data."""
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"complete_audio_data"
        mock_response.json.return_value = {
            "duration_seconds": 32.5,
            "character_count": len(sample_transcript)
        }
        mock_instance.post.return_value = mock_response
        mock_client.return_value = mock_instance
        
        output_path = f"{temp_dir}/complete_audio.mp3"
        
        result = synthesizer.synthesize_script(
            sample_transcript,
            "pNInz6obpgDQGcFmaJgB",  # Adam voice
            output_path,
            model="eleven_multilingual_v2",
            audio_quality=AudioQuality.HIGH.value
        )
        
        assert result["success"] == True
        assert result["audio_file"] == output_path
        assert result["duration_seconds"] == 32.5
        assert result["voice_id"] == "pNInz6obpgDQGcFmaJgB"
        assert os.path.exists(output_path)