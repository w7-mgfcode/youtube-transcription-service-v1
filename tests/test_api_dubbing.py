"""Comprehensive tests for the dubbing API endpoints."""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
import tempfile
import os

from src.api import app
from src.models.dubbing import (
    DubbingRequest, TranslationRequest, SynthesisRequest,
    TranslationContextEnum, AudioQuality, VideoFormat,
    DubbingJobStatus
)


class TestDubbingAPIEndpoints:
    """Test suite for all dubbing-related API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the API."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_job_storage(self):
        """Mock the global jobs storage."""
        with patch('src.api.jobs', {}) as mock_jobs:
            yield mock_jobs
    
    # =========================================================================
    # POST /v1/dub - Full Dubbing Pipeline Tests
    # =========================================================================
    
    @patch('src.api.DubbingService')
    def test_dub_endpoint_full_pipeline(self, mock_service_class, client, mock_job_storage):
        """Test full dubbing pipeline endpoint."""
        mock_service = MagicMock()
        mock_service.process_dubbing_job.return_value = MagicMock(
            job_id="test-job-123",
            status=DubbingJobStatus.COMPLETED,
            progress_percentage=100,
            transcript_file="/tmp/transcript.txt",
            translation_file="/tmp/translation.txt",
            audio_file="/tmp/audio.mp3",
            video_file="/tmp/video.mp4",
            cost_breakdown={"total_cost": 12.50}
        )
        mock_service_class.return_value = mock_service
        
        request_data = {
            "url": "https://youtube.com/watch?v=test123",
            "test_mode": True,
            "enable_translation": True,
            "target_language": "en-US",
            "translation_context": "educational",
            "enable_synthesis": True,
            "voice_id": "pNInz6obpgDQGcFmaJgB",
            "enable_video_muxing": True,
            "video_format": "mp4"
        }
        
        response = client.post("/v1/dub", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-123"
        assert data["status"] == "completed"
        assert data["progress"] == 100
        assert "transcript_file" in data
        assert "video_file" in data
        assert "cost_breakdown" in data
    
    @patch('src.api.DubbingService')
    def test_dub_endpoint_async_processing(self, mock_service_class, client, mock_job_storage):
        """Test asynchronous dubbing job processing."""
        mock_service = MagicMock()
        # Simulate job in progress
        mock_service.process_dubbing_job.return_value = MagicMock(
            job_id="async-job-456",
            status=DubbingJobStatus.TRANSLATING,
            progress_percentage=45,
            transcript_file="/tmp/transcript.txt"
        )
        mock_service_class.return_value = mock_service
        
        request_data = {
            "url": "https://youtube.com/watch?v=long_video",
            "enable_translation": True,
            "target_language": "de-DE",
            "enable_synthesis": True,
            "async_processing": True
        }
        
        response = client.post("/v1/dub", json=request_data)
        
        assert response.status_code == 202  # Accepted for async processing
        data = response.json()
        assert data["job_id"] == "async-job-456"
        assert data["status"] == "translating"
        assert data["progress"] == 45
        assert "transcript_file" in data
    
    def test_dub_endpoint_validation_errors(self, client):
        """Test validation errors in dub endpoint."""
        # Missing required URL
        response = client.post("/v1/dub", json={})
        assert response.status_code == 422
        
        # Invalid URL format
        response = client.post("/v1/dub", json={"url": "not-a-valid-url"})
        assert response.status_code == 422
        
        # Invalid language code
        response = client.post("/v1/dub", json={
            "url": "https://youtube.com/watch?v=test",
            "target_language": "invalid-lang"
        })
        assert response.status_code == 422
    
    # =========================================================================
    # POST /v1/translate - Translation Only Tests
    # =========================================================================
    
    @patch('src.api.ContextAwareTranslator')
    def test_translate_endpoint(self, mock_translator_class, client, mock_job_storage):
        """Test standalone translation endpoint."""
        mock_translator = MagicMock()
        mock_translator.translate_script.return_value = {
            "success": True,
            "translated_text": "[00:00:01] Welcome to the test!",
            "processing_time": 2.5,
            "context": "educational",
            "model_used": "gemini-2.0-flash"
        }
        mock_translator_class.return_value = mock_translator
        
        request_data = {
            "transcript_text": "[00:00:01] Üdvözöllek a tesztben!",
            "target_language": "en-US",
            "translation_context": "educational",
            "target_audience": "students",
            "desired_tone": "friendly"
        }
        
        response = client.post("/v1/translate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["translated_text"] == "[00:00:01] Welcome to the test!"
        assert data["processing_time"] == 2.5
        assert data["context"] == "educational"
        assert "job_id" in data
    
    @patch('src.api.ContextAwareTranslator')
    def test_translate_endpoint_context_variations(self, mock_translator_class, client):
        """Test translation endpoint with different contexts."""
        contexts = ["legal", "spiritual", "marketing", "scientific", "casual", "educational", "news"]
        
        mock_translator = MagicMock()
        mock_translator_class.return_value = mock_translator
        
        for context in contexts:
            mock_translator.translate_script.return_value = {
                "success": True,
                "translated_text": f"[00:00:01] {context.title()} translation",
                "context": context
            }
            
            request_data = {
                "transcript_text": "[00:00:01] Test text",
                "target_language": "en-US",
                "translation_context": context
            }
            
            response = client.post("/v1/translate", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["context"] == context
            assert context.title() in data["translated_text"]
    
    # =========================================================================
    # POST /v1/synthesize - Speech Synthesis Tests
    # =========================================================================
    
    @patch('src.api.ElevenLabsSynthesizer')
    def test_synthesize_endpoint(self, mock_synthesizer_class, client, mock_job_storage):
        """Test standalone speech synthesis endpoint."""
        mock_synthesizer = MagicMock()
        mock_synthesizer.synthesize_script.return_value = {
            "success": True,
            "audio_file": "/tmp/synthesized_audio.mp3",
            "duration_seconds": 25.5,
            "character_count": 150,
            "cost_usd": 0.45,
            "voice_id": "test_voice_id"
        }
        mock_synthesizer_class.return_value = mock_synthesizer
        
        request_data = {
            "script_text": "[00:00:01] This is a test synthesis.",
            "voice_id": "test_voice_id",
            "audio_quality": "high",
            "model": "eleven_multilingual_v2"
        }
        
        response = client.post("/v1/synthesize", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["audio_file"].endswith(".mp3")
        assert data["duration_seconds"] == 25.5
        assert data["voice_id"] == "test_voice_id"
        assert "job_id" in data
    
    @patch('src.api.ElevenLabsSynthesizer')
    def test_synthesize_endpoint_voice_validation(self, mock_synthesizer_class, client):
        """Test voice validation in synthesis endpoint."""
        mock_synthesizer = MagicMock()
        mock_synthesizer.validate_voice_id.return_value = False
        mock_synthesizer_class.return_value = mock_synthesizer
        
        request_data = {
            "script_text": "[00:00:01] Test",
            "voice_id": "invalid_voice_id"
        }
        
        response = client.post("/v1/synthesize", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "voice" in data["detail"].lower()
    
    # =========================================================================
    # GET /v1/voices - Available Voices Tests
    # =========================================================================
    
    @patch('src.api.ElevenLabsSynthesizer')
    def test_voices_endpoint(self, mock_synthesizer_class, client):
        """Test getting available voices."""
        mock_synthesizer = MagicMock()
        mock_synthesizer.get_available_voices.return_value = [
            {
                "voice_id": "voice1",
                "name": "Adam",
                "labels": {"gender": "male", "accent": "american"}
            },
            {
                "voice_id": "voice2", 
                "name": "Rachel",
                "labels": {"gender": "female", "accent": "american"}
            }
        ]
        mock_synthesizer_class.return_value = mock_synthesizer
        
        response = client.get("/v1/voices")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["voices"]) == 2
        assert data["voices"][0]["name"] == "Adam"
        assert data["voices"][1]["name"] == "Rachel"
    
    @patch('src.api.ElevenLabsSynthesizer')
    def test_voices_endpoint_with_filters(self, mock_synthesizer_class, client):
        """Test voices endpoint with gender and language filters."""
        mock_synthesizer = MagicMock()
        mock_synthesizer.get_available_voices.return_value = [
            {
                "voice_id": "female1",
                "name": "Rachel",
                "labels": {"gender": "female", "accent": "american", "language": "en"}
            }
        ]
        mock_synthesizer_class.return_value = mock_synthesizer
        
        response = client.get("/v1/voices?gender=female&language=en")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["voices"]) == 1
        assert data["voices"][0]["labels"]["gender"] == "female"
    
    # =========================================================================
    # GET /v1/dubbing/{job_id} - Job Status Tests
    # =========================================================================
    
    def test_dubbing_job_status(self, client, mock_job_storage):
        """Test getting dubbing job status."""
        # Add a test job to storage
        job_id = "test-status-job"
        mock_job_storage[job_id] = {
            "job_id": job_id,
            "job_type": "dubbing",
            "status": "completed",
            "progress": 100,
            "result": {
                "transcript_file": "/tmp/transcript.txt",
                "translation_file": "/tmp/translation.txt",
                "audio_file": "/tmp/audio.mp3",
                "video_file": "/tmp/video.mp4",
                "cost_breakdown": {"total_cost": 15.75},
                "processing_time_seconds": 125
            }
        }
        
        response = client.get(f"/v1/dubbing/{job_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "completed"
        assert data["progress"] == 100
        assert data["video_file"] == "/tmp/video.mp4"
        assert data["cost_breakdown"]["total_cost"] == 15.75
    
    def test_dubbing_job_status_not_found(self, client, mock_job_storage):
        """Test getting status for non-existent job."""
        response = client.get("/v1/dubbing/nonexistent-job")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_dubbing_job_status_wrong_type(self, client, mock_job_storage):
        """Test getting dubbing status for non-dubbing job."""
        job_id = "transcription-job"
        mock_job_storage[job_id] = {
            "job_id": job_id,
            "job_type": "transcription",  # Not dubbing
            "status": "completed"
        }
        
        response = client.get(f"/v1/dubbing/{job_id}")
        
        assert response.status_code == 400
        data = response.json()
        assert "not a dubbing job" in data["detail"].lower()
    
    # =========================================================================
    # GET /v1/cost-estimate - Cost Estimation Tests
    # =========================================================================
    
    def test_cost_estimate_endpoint(self, client):
        """Test cost estimation endpoint."""
        params = {
            "transcript_length": 2000,
            "target_language": "en-US", 
            "enable_synthesis": True,
            "enable_video_muxing": True,
            "audio_quality": "high"
        }
        
        response = client.get("/v1/cost-estimate", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert "translation_cost" in data
        assert "synthesis_cost" in data
        assert "total_cost" in data
        assert "character_count" in data
        assert data["total_cost"] > 0
    
    def test_cost_estimate_translation_only(self, client):
        """Test cost estimation for translation-only job."""
        params = {
            "transcript_length": 1500,
            "target_language": "de-DE",
            "enable_synthesis": False,
            "enable_video_muxing": False
        }
        
        response = client.get("/v1/cost-estimate", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert data["synthesis_cost"] == 0
        assert data["video_muxing_cost"] == 0
        assert data["total_cost"] == data["translation_cost"]
    
    # =========================================================================
    # File Download Tests
    # =========================================================================
    
    def test_download_completed_files(self, client, mock_job_storage, temp_dir):
        """Test downloading files from completed dubbing jobs."""
        # Create test files
        transcript_file = f"{temp_dir}/transcript.txt"
        audio_file = f"{temp_dir}/audio.mp3"
        video_file = f"{temp_dir}/video.mp4"
        
        for file_path, content in [
            (transcript_file, b"Transcript content"),
            (audio_file, b"Audio content"), 
            (video_file, b"Video content")
        ]:
            with open(file_path, 'wb') as f:
                f.write(content)
        
        job_id = "download-test-job"
        mock_job_storage[job_id] = {
            "job_id": job_id,
            "job_type": "dubbing",
            "status": "completed",
            "result": {
                "transcript_file": transcript_file,
                "audio_file": audio_file,
                "video_file": video_file
            }
        }
        
        # Test transcript download
        response = client.get(f"/v1/dubbing/{job_id}/download?file_type=transcript")
        assert response.status_code == 200
        assert response.content == b"Transcript content"
        
        # Test audio download
        response = client.get(f"/v1/dubbing/{job_id}/download?file_type=audio")
        assert response.status_code == 200
        assert response.content == b"Audio content"
        
        # Test video download
        response = client.get(f"/v1/dubbing/{job_id}/download?file_type=video")
        assert response.status_code == 200
        assert response.content == b"Video content"
    
    # =========================================================================
    # Error Handling Tests
    # =========================================================================
    
    @patch('src.api.DubbingService')
    def test_service_error_handling(self, mock_service_class, client):
        """Test proper error handling from dubbing service."""
        mock_service = MagicMock()
        mock_service.process_dubbing_job.side_effect = Exception("Service unavailable")
        mock_service_class.return_value = mock_service
        
        request_data = {
            "url": "https://youtube.com/watch?v=test",
            "enable_translation": True,
            "target_language": "en-US"
        }
        
        response = client.post("/v1/dub", json=request_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data["detail"].lower()
    
    def test_malformed_json_handling(self, client):
        """Test handling of malformed JSON requests."""
        response = client.post(
            "/v1/dub",
            data="invalid json{",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    # =========================================================================
    # Enhanced /v1/transcribe Endpoint Tests
    # =========================================================================
    
    @patch('src.api.DubbingService')
    def test_enhanced_transcribe_with_dubbing(self, mock_service_class, client):
        """Test enhanced transcribe endpoint with dubbing parameters."""
        mock_service = MagicMock()
        mock_service.process_dubbing_job.return_value = MagicMock(
            job_id="transcribe-dub-job",
            status=DubbingJobStatus.COMPLETED,
            transcript_file="/tmp/transcript.txt",
            translation_file="/tmp/translation.txt",
            audio_file="/tmp/audio.mp3"
        )
        mock_service_class.return_value = mock_service
        
        request_data = {
            "url": "https://youtube.com/watch?v=test",
            "enable_translation": True,
            "target_language": "en-US",
            "translation_context": "casual",
            "enable_synthesis": True,
            "voice_id": "test_voice",
            "enable_video_muxing": False  # Transcribe + translate + synthesize only
        }
        
        response = client.post("/v1/transcribe", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "transcribe-dub-job"
        assert "transcript_file" in data
        assert "translation_file" in data
        assert "audio_file" in data
    
    # =========================================================================
    # Rate Limiting and Security Tests
    # =========================================================================
    
    def test_request_size_limits(self, client):
        """Test handling of oversized requests."""
        # Create a very large transcript
        large_transcript = "[00:00:01] " + "Very long text " * 10000
        
        request_data = {
            "transcript_text": large_transcript,
            "target_language": "en-US"
        }
        
        response = client.post("/v1/translate", json=request_data)
        
        # Should either succeed or return appropriate error for large content
        assert response.status_code in [200, 413, 422]
    
    def test_concurrent_request_handling(self, client):
        """Test handling of multiple concurrent requests."""
        import threading
        import time
        
        responses = []
        
        def make_request():
            response = client.get("/v1/voices")
            responses.append(response.status_code)
        
        # Make 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All requests should succeed or fail gracefully
        assert all(status in [200, 429, 503] for status in responses)
    
    # =========================================================================
    # API Documentation Tests
    # =========================================================================
    
    def test_openapi_schema_generation(self, client):
        """Test that OpenAPI schema is generated correctly."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        
        # Check that dubbing endpoints are included
        paths = schema.get("paths", {})
        assert "/v1/dub" in paths
        assert "/v1/translate" in paths
        assert "/v1/synthesize" in paths
        assert "/v1/voices" in paths
        assert "/v1/cost-estimate" in paths
    
    def test_swagger_ui_accessibility(self, client):
        """Test that Swagger UI is accessible."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()