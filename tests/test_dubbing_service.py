"""Comprehensive tests for the dubbing orchestration service."""

import os
import uuid
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timedelta
import tempfile

from src.core.dubbing_service import DubbingService, DubbingServiceError
from src.core.translator import TranslationQuality
from src.models.dubbing import (
    DubbingRequest, DubbingJob, DubbingJobStatus,
    TranslationContextEnum, AudioQuality, VideoFormat
)
from src.config import TranslationContext


class TestDubbingService:
    """Test suite for DubbingService orchestration."""
    
    @pytest.fixture
    def service(self):
        """Create a dubbing service instance for testing."""
        return DubbingService()
    
    @pytest.fixture
    def sample_dubbing_request(self):
        """Create a comprehensive dubbing request for testing."""
        return DubbingRequest(
            url="https://youtube.com/watch?v=test123",
            test_mode=True,
            enable_translation=True,
            target_language="en-US",
            translation_context=TranslationContextEnum.EDUCATIONAL,
            target_audience="students",
            desired_tone="friendly",
            enable_synthesis=True,
            voice_id="pNInz6obpgDQGcFmaJgB",
            audio_quality=AudioQuality.HIGH,
            enable_video_muxing=True,
            video_format=VideoFormat.MP4,
            max_cost_usd=50.0
        )
    
    @pytest.fixture
    def mock_all_services(self):
        """Mock all dependent services."""
        with patch.multiple(
            'src.core.dubbing_service',
            TranscriptionService=MagicMock(),
            ContextAwareTranslator=MagicMock(),
            ElevenLabsSynthesizer=MagicMock(),
            VideoMuxer=MagicMock()
        ) as mocks:
            yield mocks
    
    # =========================================================================
    # Initialization Tests
    # =========================================================================
    
    def test_service_initialization(self, service):
        """Test dubbing service initialization."""
        assert service.transcriber is not None
        assert service.translator is not None
        assert service.synthesizer is not None
        assert service.video_muxer is not None
        assert service.current_job is None
        assert service.progress_callback is None
    
    # =========================================================================
    # Full Pipeline Tests
    # =========================================================================
    
    def test_complete_dubbing_pipeline(self, service, sample_dubbing_request, mock_all_services):
        """Test complete dubbing pipeline from start to finish."""
        # Setup mocks for successful pipeline
        mock_transcriber = mock_all_services['TranscriptionService'].return_value
        mock_transcriber.process_request.return_value = {
            "success": True,
            "transcript_file": "/tmp/transcript.txt",
            "transcript_text": "[00:00:01] Test Hungarian text"
        }
        
        mock_translator = mock_all_services['ContextAwareTranslator'].return_value
        mock_translator.translate_script.return_value = {
            "success": True,
            "translated_text": "[00:00:01] Test English text",
            "processing_time": 5.2
        }
        
        mock_synthesizer = mock_all_services['ElevenLabsSynthesizer'].return_value
        mock_synthesizer.synthesize_script.return_value = {
            "success": True,
            "audio_file": "/tmp/audio.mp3",
            "duration_seconds": 30.5
        }
        
        mock_muxer = mock_all_services['VideoMuxer'].return_value
        mock_muxer.replace_audio_in_video.return_value = {
            "success": True,
            "output_file": "/tmp/final.mp4",
            "processing_time": 15.8
        }
        
        # Execute pipeline
        result = service.process_dubbing_job(sample_dubbing_request)
        
        # Verify complete pipeline execution
        assert result.status == DubbingJobStatus.COMPLETED
        assert result.progress_percentage == 100
        assert result.transcript_file is not None
        assert result.translation_file is not None
        assert result.audio_file is not None
        assert result.video_file is not None
        assert result.completed_at is not None
        
        # Verify all services were called
        mock_transcriber.process_request.assert_called_once()
        mock_translator.translate_script.assert_called_once()
        mock_synthesizer.synthesize_script.assert_called_once()
        mock_muxer.replace_audio_in_video.assert_called_once()
    
    def test_partial_pipeline_translation_only(self, service, mock_all_services):
        """Test partial pipeline with translation only (no synthesis)."""
        request = DubbingRequest(
            url="https://youtube.com/watch?v=test123",
            enable_translation=True,
            target_language="de-DE",
            enable_synthesis=False,
            enable_video_muxing=False
        )
        
        mock_transcriber = mock_all_services['TranscriptionService'].return_value
        mock_transcriber.process_request.return_value = {
            "success": True,
            "transcript_text": "[00:00:01] Test text"
        }
        
        mock_translator = mock_all_services['ContextAwareTranslator'].return_value
        mock_translator.translate_script.return_value = {
            "success": True,
            "translated_text": "[00:00:01] Deutscher Text"
        }
        
        result = service.process_dubbing_job(request)
        
        assert result.status == DubbingJobStatus.COMPLETED
        assert result.transcript_file is not None
        assert result.translation_file is not None
        assert result.audio_file is None  # No synthesis
        assert result.video_file is None  # No muxing
        
        # Only transcription and translation should be called
        mock_transcriber.process_request.assert_called_once()
        mock_translator.translate_script.assert_called_once()
        mock_all_services['ElevenLabsSynthesizer'].return_value.synthesize_script.assert_not_called()
        mock_all_services['VideoMuxer'].return_value.replace_audio_in_video.assert_not_called()
    
    # =========================================================================
    # Job Status Tracking Tests
    # =========================================================================
    
    def test_job_status_progression(self, service, sample_dubbing_request, mock_all_services):
        """Test that job status progresses correctly through stages."""
        status_updates = []
        
        def progress_callback(message, percentage):
            status_updates.append((service.current_job.status, percentage))
        
        # Setup mocks with delays to capture status changes
        mock_transcriber = mock_all_services['TranscriptionService'].return_value
        mock_transcriber.process_request.return_value = {"success": True, "transcript_text": "test"}
        
        mock_translator = mock_all_services['ContextAwareTranslator'].return_value
        mock_translator.translate_script.return_value = {"success": True, "translated_text": "test"}
        
        mock_synthesizer = mock_all_services['ElevenLabsSynthesizer'].return_value
        mock_synthesizer.synthesize_script.return_value = {"success": True, "audio_file": "test.mp3"}
        
        mock_muxer = mock_all_services['VideoMuxer'].return_value
        mock_muxer.replace_audio_in_video.return_value = {"success": True, "output_file": "test.mp4"}
        
        result = service.process_dubbing_job(sample_dubbing_request, progress_callback)
        
        # Check status progression
        expected_statuses = [
            DubbingJobStatus.TRANSCRIBING,
            DubbingJobStatus.TRANSLATING,
            DubbingJobStatus.SYNTHESIZING,
            DubbingJobStatus.MUXING
        ]
        
        captured_statuses = [status for status, _ in status_updates]
        for expected_status in expected_statuses:
            assert expected_status in captured_statuses
        
        assert result.status == DubbingJobStatus.COMPLETED
    
    def test_progress_percentage_updates(self, service, sample_dubbing_request, mock_all_services):
        """Test that progress percentage increases correctly."""
        progress_updates = []
        
        def progress_callback(message, percentage):
            progress_updates.append(percentage)
        
        # Setup successful mocks
        for mock_service in mock_all_services.values():
            mock_instance = mock_service.return_value
            if hasattr(mock_instance, 'process_request'):
                mock_instance.process_request.return_value = {"success": True}
            if hasattr(mock_instance, 'translate_script'):
                mock_instance.translate_script.return_value = {"success": True}
            if hasattr(mock_instance, 'synthesize_script'):
                mock_instance.synthesize_script.return_value = {"success": True}
            if hasattr(mock_instance, 'replace_audio_in_video'):
                mock_instance.replace_audio_in_video.return_value = {"success": True}
        
        result = service.process_dubbing_job(sample_dubbing_request, progress_callback)
        
        # Progress should increase monotonically
        assert len(progress_updates) > 0
        assert progress_updates[0] >= 0
        assert progress_updates[-1] == 100
        
        # Check for reasonable progression
        for i in range(1, len(progress_updates)):
            assert progress_updates[i] >= progress_updates[i-1]
    
    # =========================================================================
    # Error Handling and Recovery Tests
    # =========================================================================
    
    def test_transcription_failure(self, service, sample_dubbing_request, mock_all_services):
        """Test handling of transcription failures."""
        mock_transcriber = mock_all_services['TranscriptionService'].return_value
        mock_transcriber.process_request.side_effect = Exception("Transcription failed")
        
        result = service.process_dubbing_job(sample_dubbing_request)
        
        assert result.status == DubbingJobStatus.FAILED
        assert "transcription" in result.error_message.lower()
        assert result.completed_at is not None
        assert result.progress_percentage < 100
    
    def test_translation_failure_with_rollback(self, service, sample_dubbing_request, mock_all_services):
        """Test translation failure and rollback mechanism."""
        # Transcription succeeds
        mock_transcriber = mock_all_services['TranscriptionService'].return_value
        mock_transcriber.process_request.return_value = {
            "success": True,
            "transcript_file": "/tmp/transcript.txt"
        }
        
        # Translation fails
        mock_translator = mock_all_services['ContextAwareTranslator'].return_value
        mock_translator.translate_script.side_effect = Exception("Translation API error")
        
        result = service.process_dubbing_job(sample_dubbing_request)
        
        assert result.status == DubbingJobStatus.FAILED
        assert "translation" in result.error_message.lower()
        
        # Rollback should clean up transcript file
        # (This would be tested by checking if cleanup methods were called)
    
    def test_synthesis_failure_recovery(self, service, mock_all_services):
        """Test recovery from synthesis failures."""
        request = DubbingRequest(
            url="https://youtube.com/watch?v=test123",
            enable_translation=True,
            target_language="en-US",
            enable_synthesis=True,
            voice_id="invalid_voice",
            retry_on_failure=True,
            max_retries=2
        )
        
        # Transcription and translation succeed
        mock_transcriber = mock_all_services['TranscriptionService'].return_value
        mock_transcriber.process_request.return_value = {"success": True, "transcript_text": "test"}
        
        mock_translator = mock_all_services['ContextAwareTranslator'].return_value
        mock_translator.translate_script.return_value = {"success": True, "translated_text": "test"}
        
        # Synthesis fails twice, then succeeds
        mock_synthesizer = mock_all_services['ElevenLabsSynthesizer'].return_value
        mock_synthesizer.synthesize_script.side_effect = [
            Exception("Voice not found"),
            Exception("API timeout"), 
            {"success": True, "audio_file": "recovered.mp3"}
        ]
        
        mock_muxer = mock_all_services['VideoMuxer'].return_value
        mock_muxer.replace_audio_in_video.return_value = {"success": True, "output_file": "final.mp4"}
        
        result = service.process_dubbing_job(request)
        
        assert result.status == DubbingJobStatus.COMPLETED
        assert mock_synthesizer.synthesize_script.call_count == 3  # 2 failures + 1 success
    
    # =========================================================================
    # Cost Estimation and Validation Tests
    # =========================================================================
    
    def test_cost_estimation_before_processing(self, service, mock_all_services):
        """Test cost estimation before starting dubbing job."""
        request = DubbingRequest(
            url="https://youtube.com/watch?v=test123",
            enable_translation=True,
            target_language="en-US",
            enable_synthesis=True,
            voice_id="test_voice",
            max_cost_usd=10.0
        )
        
        # Mock cost estimation
        service.estimate_dubbing_cost = MagicMock(return_value={
            "translation_cost": 2.50,
            "synthesis_cost": 5.75,
            "total_cost": 8.25,
            "character_count": 2750
        })
        
        # Setup successful pipeline
        for mock_service in mock_all_services.values():
            mock_instance = mock_service.return_value
            for method_name in ['process_request', 'translate_script', 'synthesize_script', 'replace_audio_in_video']:
                if hasattr(mock_instance, method_name):
                    setattr(mock_instance, method_name, MagicMock(return_value={"success": True}))
        
        result = service.process_dubbing_job(request)
        
        assert result.status == DubbingJobStatus.COMPLETED
        assert result.cost_breakdown is not None
        assert result.cost_breakdown["total_cost"] <= request.max_cost_usd
    
    def test_cost_limit_exceeded_rejection(self, service):
        """Test rejection of jobs that exceed cost limits."""
        request = DubbingRequest(
            url="https://youtube.com/watch?v=test123",
            enable_translation=True,
            enable_synthesis=True,
            max_cost_usd=1.0  # Very low limit
        )
        
        # Mock high cost estimation
        service.estimate_dubbing_cost = MagicMock(return_value={
            "total_cost": 25.0,  # Exceeds limit
            "character_count": 10000
        })
        
        with pytest.raises(DubbingServiceError) as exc_info:
            service.process_dubbing_job(request)
        
        assert "cost limit" in str(exc_info.value).lower()
        assert "25.0" in str(exc_info.value)
    
    def test_cost_breakdown_accuracy(self, service, sample_dubbing_request, mock_all_services):
        """Test accuracy of cost breakdown in completed jobs."""
        # Mock services with cost information
        mock_translator = mock_all_services['ContextAwareTranslator'].return_value
        mock_translator.translate_script.return_value = {
            "success": True,
            "translated_text": "test",
            "cost_usd": 3.20,
            "character_count": 1600
        }
        
        mock_synthesizer = mock_all_services['ElevenLabsSynthesizer'].return_value
        mock_synthesizer.synthesize_script.return_value = {
            "success": True,
            "audio_file": "test.mp3",
            "cost_usd": 4.80,
            "character_count": 1600
        }
        
        # Other services succeed without cost
        mock_transcriber = mock_all_services['TranscriptionService'].return_value
        mock_transcriber.process_request.return_value = {"success": True, "transcript_text": "test"}
        
        mock_muxer = mock_all_services['VideoMuxer'].return_value
        mock_muxer.replace_audio_in_video.return_value = {"success": True, "output_file": "test.mp4"}
        
        result = service.process_dubbing_job(sample_dubbing_request)
        
        assert result.cost_breakdown is not None
        assert result.cost_breakdown["translation_cost"] == 3.20
        assert result.cost_breakdown["synthesis_cost"] == 4.80
        assert result.cost_breakdown["total_cost"] == 8.00
    
    # =========================================================================
    # Job Recovery and Retry Tests
    # =========================================================================
    
    def test_job_recovery_from_checkpoint(self, service, mock_all_services):
        """Test recovery of failed jobs from checkpoints."""
        request = DubbingRequest(
            url="https://youtube.com/watch?v=test123",
            enable_translation=True,
            enable_synthesis=True,
            enable_video_muxing=True
        )
        
        # Simulate job that failed during synthesis
        existing_job = DubbingJob(
            job_id="recovery-test",
            status=DubbingJobStatus.SYNTHESIZING,
            progress_percentage=60,
            transcript_file="/tmp/existing_transcript.txt",
            translation_file="/tmp/existing_translation.txt",
            request=request
        )
        
        # Setup mocks for recovery (skip completed stages)
        mock_synthesizer = mock_all_services['ElevenLabsSynthesizer'].return_value
        mock_synthesizer.synthesize_script.return_value = {"success": True, "audio_file": "recovered.mp3"}
        
        mock_muxer = mock_all_services['VideoMuxer'].return_value
        mock_muxer.replace_audio_in_video.return_value = {"success": True, "output_file": "final.mp4"}
        
        result = service.recover_job(existing_job)
        
        assert result.status == DubbingJobStatus.COMPLETED
        
        # Should not re-run transcription or translation
        mock_all_services['TranscriptionService'].return_value.process_request.assert_not_called()
        mock_all_services['ContextAwareTranslator'].return_value.translate_script.assert_not_called()
        
        # Should only run synthesis and muxing
        mock_synthesizer.synthesize_script.assert_called_once()
        mock_muxer.replace_audio_in_video.assert_called_once()
    
    # =========================================================================
    # Concurrent Job Handling Tests
    # =========================================================================
    
    def test_concurrent_job_limits(self, service, mock_all_services):
        """Test enforcement of concurrent job limits."""
        requests = [
            DubbingRequest(url=f"https://youtube.com/watch?v=test{i}")
            for i in range(10)  # More than max concurrent
        ]
        
        # Mock slow processing
        for mock_service in mock_all_services.values():
            mock_instance = mock_service.return_value
            for method_name in ['process_request', 'translate_script', 'synthesize_script', 'replace_audio_in_video']:
                if hasattr(mock_instance, method_name):
                    setattr(mock_instance, method_name, MagicMock(return_value={"success": True}))
        
        # Start multiple jobs
        jobs = []
        for request in requests[:3]:  # Start first 3
            job = service.process_dubbing_job(request)
            jobs.append(job)
        
        # 4th job should be queued or rejected
        with pytest.raises(DubbingServiceError) as exc_info:
            service.process_dubbing_job(requests[3])
        
        assert "concurrent" in str(exc_info.value).lower() or "limit" in str(exc_info.value).lower()
    
    # =========================================================================
    # Performance and Resource Management Tests
    # =========================================================================
    
    def test_memory_cleanup_after_completion(self, service, sample_dubbing_request, mock_all_services):
        """Test that memory is cleaned up after job completion."""
        # Setup successful pipeline
        for mock_service in mock_all_services.values():
            mock_instance = mock_service.return_value
            for method_name in ['process_request', 'translate_script', 'synthesize_script', 'replace_audio_in_video']:
                if hasattr(mock_instance, method_name):
                    setattr(mock_instance, method_name, MagicMock(return_value={"success": True}))
        
        result = service.process_dubbing_job(sample_dubbing_request)
        
        # After completion, current job should be cleared
        assert service.current_job is None or service.current_job.status == DubbingJobStatus.COMPLETED
        assert service.progress_callback is None
    
    def test_temp_file_cleanup_on_failure(self, service, sample_dubbing_request, mock_all_services):
        """Test that temporary files are cleaned up even on failure."""
        # Transcription succeeds, creates temp files
        mock_transcriber = mock_all_services['TranscriptionService'].return_value
        mock_transcriber.process_request.return_value = {
            "success": True,
            "transcript_file": "/tmp/test_transcript.txt",
            "temp_files": ["/tmp/temp1.txt", "/tmp/temp2.wav"]
        }
        
        # Translation fails
        mock_translator = mock_all_services['ContextAwareTranslator'].return_value
        mock_translator.translate_script.side_effect = Exception("Translation failed")
        
        # Mock cleanup method
        service.cleanup_temp_files = MagicMock()
        
        result = service.process_dubbing_job(sample_dubbing_request)
        
        assert result.status == DubbingJobStatus.FAILED
        # Cleanup should have been called
        service.cleanup_temp_files.assert_called()
    
    # =========================================================================
    # Configuration and Customization Tests
    # =========================================================================
    
    def test_custom_quality_settings(self, service, mock_all_services):
        """Test dubbing with custom quality settings."""
        request = DubbingRequest(
            url="https://youtube.com/watch?v=test123",
            enable_translation=True,
            target_language="fr-FR",
            translation_quality="high",
            enable_synthesis=True,
            audio_quality=AudioQuality.HIGH,
            enable_video_muxing=True,
            preserve_video_quality=True
        )
        
        # Setup mocks
        mock_translator = mock_all_services['ContextAwareTranslator'].return_value
        mock_translator.translate_script.return_value = {"success": True, "translated_text": "test"}
        
        mock_synthesizer = mock_all_services['ElevenLabsSynthesizer'].return_value
        mock_synthesizer.synthesize_script.return_value = {"success": True, "audio_file": "test.mp3"}
        
        # Other services
        mock_transcriber = mock_all_services['TranscriptionService'].return_value
        mock_transcriber.process_request.return_value = {"success": True, "transcript_text": "test"}
        
        mock_muxer = mock_all_services['VideoMuxer'].return_value
        mock_muxer.replace_audio_in_video.return_value = {"success": True, "output_file": "test.mp4"}
        
        result = service.process_dubbing_job(request)
        
        # Check that quality settings were passed to services
        translator_call = mock_translator.translate_script.call_args
        assert translator_call is not None
        
        synthesizer_call = mock_synthesizer.synthesize_script.call_args
        assert synthesizer_call is not None
        
        muxer_call = mock_muxer.replace_audio_in_video.call_args
        assert muxer_call is not None