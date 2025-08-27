"""End-to-end integration tests for the complete dubbing system."""

import os
import json
import pytest
import tempfile
import threading
import time
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from fastapi.testclient import TestClient

from src.api import app
from src.core.dubbing_service import DubbingService
from src.models.dubbing import (
    DubbingRequest, TranslationContextEnum, 
    AudioQuality, VideoFormat, DubbingJobStatus
)


class TestIntegration:
    """End-to-end integration tests."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    @pytest.fixture
    def temp_files_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    # =========================================================================
    # Complete Pipeline Integration Tests
    # =========================================================================
    
    @patch('src.core.dubbing_service.TranscriptionService')
    @patch('src.core.dubbing_service.ContextAwareTranslator') 
    @patch('src.core.dubbing_service.ElevenLabsSynthesizer')
    @patch('src.core.dubbing_service.VideoMuxer')
    def test_complete_dubbing_flow_mock(
        self, mock_muxer_class, mock_synth_class, 
        mock_trans_class, mock_transcr_class, 
        temp_files_dir
    ):
        """Test complete end-to-end dubbing flow with mocked services."""
        
        # Create mock files
        transcript_file = f"{temp_files_dir}/transcript.txt"
        translation_file = f"{temp_files_dir}/translation.txt"
        audio_file = f"{temp_files_dir}/audio.mp3"
        video_file = f"{temp_files_dir}/video.mp4"
        
        for file_path, content in [
            (transcript_file, "[00:00:01] Magyar szöveg\n[00:00:05] Második sor"),
            (translation_file, "[00:00:01] English text\n[00:00:05] Second line"),
            (audio_file, b"FAKE_AUDIO_DATA"),
            (video_file, b"FAKE_VIDEO_DATA")
        ]:
            with open(file_path, 'w' if isinstance(content, str) else 'wb') as f:
                f.write(content)
        
        # Setup mocks
        mock_transcr = mock_transcr_class.return_value
        mock_transcr.process_request.return_value = {
            "success": True,
            "transcript_file": transcript_file,
            "transcript_text": "[00:00:01] Magyar szöveg\n[00:00:05] Második sor",
            "processing_time": 15.2
        }
        
        mock_trans = mock_trans_class.return_value
        mock_trans.translate_script.return_value = {
            "success": True,
            "translated_text": "[00:00:01] English text\n[00:00:05] Second line",
            "translation_file": translation_file,
            "processing_time": 8.5,
            "cost_usd": 0.85
        }
        
        mock_synth = mock_synth_class.return_value
        mock_synth.synthesize_script.return_value = {
            "success": True,
            "audio_file": audio_file,
            "duration_seconds": 12.5,
            "processing_time": 25.0,
            "cost_usd": 3.75
        }
        
        mock_muxer = mock_muxer_class.return_value
        mock_muxer.replace_audio_in_video.return_value = {
            "success": True,
            "output_file": video_file,
            "processing_time": 18.3
        }
        
        # Create service and run pipeline
        service = DubbingService()
        request = DubbingRequest(
            url="https://youtube.com/watch?v=integration_test",
            test_mode=True,
            enable_translation=True,
            target_language="en-US",
            translation_context=TranslationContextEnum.CASUAL,
            enable_synthesis=True,
            voice_id="test_voice_id",
            audio_quality=AudioQuality.HIGH,
            enable_video_muxing=True,
            video_format=VideoFormat.MP4
        )
        
        result = service.process_dubbing_job(request)
        
        # Verify complete pipeline execution
        assert result.status == DubbingJobStatus.COMPLETED
        assert result.progress_percentage == 100
        assert result.transcript_file == transcript_file
        assert result.translation_file == translation_file
        assert result.audio_file == audio_file
        assert result.video_file == video_file
        
        # Verify cost tracking
        assert result.cost_breakdown is not None
        assert result.cost_breakdown["translation_cost"] == 0.85
        assert result.cost_breakdown["synthesis_cost"] == 3.75
        assert result.cost_breakdown["total_cost"] == 4.60
        
        # Verify all files exist
        for file_path in [transcript_file, translation_file, audio_file, video_file]:
            assert os.path.exists(file_path)
    
    @patch('src.api.DubbingService')
    def test_api_workflow_simulation(self, mock_service_class, client, temp_files_dir):
        """Test complete API workflow simulation."""
        
        # Create mock service with realistic progression
        mock_service = MagicMock()
        
        # Simulate job progression over multiple status checks
        job_states = [
            {"status": DubbingJobStatus.TRANSCRIBING, "progress": 10},
            {"status": DubbingJobStatus.TRANSLATING, "progress": 40},  
            {"status": DubbingJobStatus.SYNTHESIZING, "progress": 70},
            {"status": DubbingJobStatus.MUXING, "progress": 90},
            {"status": DubbingJobStatus.COMPLETED, "progress": 100}
        ]
        
        current_state = [0]  # Mutable reference for closure
        
        def mock_get_job_status(job_id):
            state_idx = min(current_state[0], len(job_states) - 1)
            state = job_states[state_idx]
            current_state[0] += 1
            
            result = {
                "job_id": job_id,
                "status": state["status"].value,
                "progress": state["progress"]
            }
            
            if state["status"] == DubbingJobStatus.COMPLETED:
                result.update({
                    "transcript_file": f"{temp_files_dir}/transcript.txt",
                    "translation_file": f"{temp_files_dir}/translation.txt",
                    "audio_file": f"{temp_files_dir}/audio.mp3",
                    "video_file": f"{temp_files_dir}/final.mp4",
                    "cost_breakdown": {"total_cost": 12.50}
                })
            
            return result
        
        # Initial job creation
        mock_job_result = MagicMock()
        mock_job_result.job_id = "integration-test-job"
        mock_job_result.status = DubbingJobStatus.PENDING
        mock_job_result.progress_percentage = 0
        mock_service.process_dubbing_job.return_value = mock_job_result
        mock_service_class.return_value = mock_service
        
        # Mock job storage access
        with patch('src.api.jobs', {}) as mock_jobs:
            # Step 1: Submit dubbing job
            request_data = {
                "url": "https://youtube.com/watch?v=integration_test",
                "enable_translation": True,
                "target_language": "en-US",
                "enable_synthesis": True,
                "voice_id": "test_voice",
                "enable_video_muxing": True,
                "async_processing": True
            }
            
            response = client.post("/v1/dub", json=request_data)
            assert response.status_code in [200, 202]
            job_data = response.json()
            job_id = job_data["job_id"]
            
            # Add job to mock storage
            mock_jobs[job_id] = {
                "job_id": job_id,
                "job_type": "dubbing",
                "status": "pending",
                "progress": 0
            }
            
            # Step 2: Monitor job progress
            for expected_state in job_states:
                # Update mock storage
                status_data = mock_get_job_status(job_id)
                mock_jobs[job_id].update(status_data)
                
                response = client.get(f"/v1/dubbing/{job_id}")
                assert response.status_code == 200
                
                data = response.json()
                assert data["job_id"] == job_id
                assert data["status"] == expected_state["status"].value
                assert data["progress"] == expected_state["progress"]
                
                if expected_state["status"] == DubbingJobStatus.COMPLETED:
                    assert "video_file" in data
                    assert "cost_breakdown" in data
                    break
                
                time.sleep(0.1)  # Simulate polling delay
    
    # =========================================================================
    # CLI Workflow Integration Tests  
    # =========================================================================
    
    @patch('src.core.dubbing_service.DubbingService')
    @patch('builtins.input')
    def test_cli_workflow_simulation(self, mock_input, mock_service_class):
        """Test CLI workflow with user interactions."""
        # Mock user inputs for CLI flow
        mock_inputs = [
            "https://youtube.com/watch?v=cli_test",  # Video URL
            "y",  # Enable translation
            "2",  # English language selection
            "3",  # Educational context
            "y",  # Enable synthesis
            "1",  # Voice selection
            "y",  # Enable video muxing
            "y"   # Confirm processing
        ]
        mock_input.side_effect = mock_inputs
        
        # Mock service
        mock_service = MagicMock()
        mock_job_result = MagicMock()
        mock_job_result.status = DubbingJobStatus.COMPLETED
        mock_job_result.transcript_file = "/tmp/cli_transcript.txt"
        mock_job_result.translation_file = "/tmp/cli_translation.txt"
        mock_job_result.audio_file = "/tmp/cli_audio.mp3"
        mock_job_result.video_file = "/tmp/cli_video.mp4"
        mock_service.process_dubbing_job.return_value = mock_job_result
        mock_service_class.return_value = mock_service
        
        # Import and test CLI
        from src.cli import InteractiveCLI
        
        cli = InteractiveCLI()
        
        with patch('builtins.print') as mock_print:
            # This would normally run the interactive flow
            # For testing, we simulate the key method calls
            cli.get_video_url = lambda: "https://youtube.com/watch?v=cli_test"
            cli.get_translation_settings = lambda: {
                "enable": True,
                "language": "en-US",
                "context": "educational"
            }
            cli.get_synthesis_settings = lambda: {
                "enable": True,
                "voice_id": "test_voice"
            }
            cli.get_video_settings = lambda: {"enable": True, "format": "mp4"}
            
            # Run simulated CLI flow
            result = cli.run_dubbing_workflow()
            
            # Verify CLI completed successfully
            assert result is not None
    
    # =========================================================================
    # Long Content Processing Tests
    # =========================================================================
    
    @patch('src.core.dubbing_service.TranscriptionService')
    @patch('src.core.dubbing_service.ContextAwareTranslator')
    def test_long_content_processing(
        self, mock_trans_class, mock_transcr_class, temp_files_dir
    ):
        """Test processing of long content requiring chunking."""
        
        # Generate long transcript (30 minutes worth)
        long_transcript_lines = []
        for i in range(450):  # 30 min * 15 lines/min = 450 lines
            minutes = i // 15
            seconds = (i % 15) * 4
            timestamp = f"[{minutes:02d}:{seconds:02d}:00]"
            long_transcript_lines.append(f"{timestamp} Ez a {i+1}. mondat a hosszú videóban.")
        
        long_transcript = "\n".join(long_transcript_lines)
        
        # Setup mocks for chunked processing
        mock_transcr = mock_transcr_class.return_value
        mock_transcr.process_request.return_value = {
            "success": True,
            "transcript_text": long_transcript,
            "processing_time": 180.0  # 3 minutes for long video
        }
        
        mock_trans = mock_trans_class.return_value
        mock_trans.translate_script.return_value = {
            "success": True,
            "translated_text": long_transcript.replace("mondat", "sentence"),
            "chunks_processed": 8,  # Should be chunked
            "processing_time": 45.0,
            "cost_usd": 12.50
        }
        
        service = DubbingService()
        request = DubbingRequest(
            url="https://youtube.com/watch?v=long_video_test",
            enable_translation=True,
            target_language="en-US",
            translation_context=TranslationContextEnum.EDUCATIONAL,
            enable_synthesis=False,  # Skip synthesis for this test
            enable_video_muxing=False
        )
        
        result = service.process_dubbing_job(request)
        
        assert result.status == DubbingJobStatus.COMPLETED
        
        # Verify chunking was used
        mock_trans.translate_script.assert_called_once()
        call_args = mock_trans.translate_script.call_args
        # Should have received the long text
        assert len(call_args[0][0]) > 5000  # Long content
    
    # =========================================================================
    # Concurrent Job Handling Tests
    # =========================================================================
    
    @patch('src.api.DubbingService')
    def test_concurrent_job_handling(self, mock_service_class, client):
        """Test handling of multiple concurrent dubbing jobs."""
        
        # Create mock service that simulates different job durations
        mock_services = []
        job_results = []
        
        for i in range(5):
            mock_service = MagicMock()
            mock_result = MagicMock()
            mock_result.job_id = f"concurrent-job-{i}"
            mock_result.status = DubbingJobStatus.COMPLETED
            mock_result.progress_percentage = 100
            
            # Simulate varying processing times
            processing_time = 1 + (i * 0.5)
            
            def delayed_return(result=mock_result, delay=processing_time):
                time.sleep(delay)
                return result
            
            mock_service.process_dubbing_job.side_effect = lambda req, cb=None: delayed_return()
            mock_services.append(mock_service)
            job_results.append(mock_result)
        
        mock_service_class.side_effect = mock_services
        
        # Submit multiple jobs concurrently
        threads = []
        responses = []
        
        def submit_job(job_index):
            request_data = {
                "url": f"https://youtube.com/watch?v=concurrent{job_index}",
                "enable_translation": True,
                "target_language": "en-US",
                "async_processing": True
            }
            
            response = client.post("/v1/dub", json=request_data)
            responses.append(response)
        
        # Start 5 concurrent jobs
        for i in range(5):
            thread = threading.Thread(target=submit_job, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all jobs to complete
        for thread in threads:
            thread.join()
        
        # Verify all jobs were handled
        successful_responses = [r for r in responses if r.status_code in [200, 202]]
        assert len(successful_responses) >= 3  # At least some should succeed
        
        # Some might be rejected due to concurrent limits
        rejected_responses = [r for r in responses if r.status_code == 429]
        assert len(successful_responses) + len(rejected_responses) == 5
    
    # =========================================================================
    # Memory Management Tests
    # =========================================================================
    
    @patch('src.core.dubbing_service.DubbingService')
    def test_memory_management(self, mock_service_class, temp_files_dir):
        """Test memory management during large file processing."""
        
        # Create large mock files
        large_transcript = f"{temp_files_dir}/large_transcript.txt"
        large_audio = f"{temp_files_dir}/large_audio.mp3"
        
        # Generate large transcript file (simulate 2MB file)
        with open(large_transcript, 'w') as f:
            for i in range(10000):
                f.write(f"[00:{i//60:02d}:{i%60:02d}] Line {i} with substantial content " * 10 + "\n")
        
        # Generate large audio file (simulate 50MB file)
        with open(large_audio, 'wb') as f:
            f.write(b'AUDIO_DATA' * 6250000)  # ~50MB
        
        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.status = DubbingJobStatus.COMPLETED
        mock_result.transcript_file = large_transcript
        mock_result.audio_file = large_audio
        
        def monitor_memory(result=mock_result):
            import psutil
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Simulate processing
            time.sleep(1.0)
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Memory usage should not grow excessively (less than 100MB increase)
            memory_growth = final_memory - initial_memory
            assert memory_growth < 100, f"Memory grew by {memory_growth}MB"
            
            return result
        
        mock_service.process_dubbing_job.side_effect = monitor_memory
        mock_service_class.return_value = mock_service
        
        service = DubbingService()
        request = DubbingRequest(
            url="https://youtube.com/watch?v=memory_test",
            enable_translation=True,
            target_language="en-US"
        )
        
        result = service.process_dubbing_job(request)
        assert result.status == DubbingJobStatus.COMPLETED
    
    # =========================================================================
    # Error Recovery Integration Tests
    # =========================================================================
    
    @patch('src.core.dubbing_service.TranscriptionService')
    @patch('src.core.dubbing_service.ContextAwareTranslator')
    @patch('src.core.dubbing_service.ElevenLabsSynthesizer')
    def test_error_recovery_integration(
        self, mock_synth_class, mock_trans_class, mock_transcr_class
    ):
        """Test error recovery across the entire pipeline."""
        
        # Setup mocks with realistic failure/recovery pattern
        mock_transcr = mock_transcr_class.return_value
        mock_transcr.process_request.return_value = {
            "success": True,
            "transcript_text": "Test transcript"
        }
        
        # Translation fails twice then succeeds (network issues)
        mock_trans = mock_trans_class.return_value
        mock_trans.translate_script.side_effect = [
            Exception("Network timeout"),
            Exception("Service unavailable"),
            {
                "success": True,
                "translated_text": "Translated text",
                "cost_usd": 1.25
            }
        ]
        
        # Synthesis fails once then succeeds (voice not available)
        mock_synth = mock_synth_class.return_value
        mock_synth.synthesize_script.side_effect = [
            Exception("Voice temporarily unavailable"),
            {
                "success": True,
                "audio_file": "/tmp/recovered_audio.mp3",
                "cost_usd": 2.75
            }
        ]
        
        service = DubbingService()
        request = DubbingRequest(
            url="https://youtube.com/watch?v=error_recovery_test",
            enable_translation=True,
            target_language="en-US",
            enable_synthesis=True,
            voice_id="test_voice",
            enable_video_muxing=False,
            max_retries=3  # Allow retries
        )
        
        result = service.process_dubbing_job(request)
        
        # Should eventually succeed after retries
        assert result.status == DubbingJobStatus.COMPLETED
        
        # Verify retry attempts
        assert mock_trans.translate_script.call_count == 3  # 2 failures + 1 success
        assert mock_synth.synthesize_script.call_count == 2  # 1 failure + 1 success
    
    # =========================================================================
    # Performance Integration Tests
    # =========================================================================
    
    def test_end_to_end_performance_benchmark(self, temp_files_dir):
        """Benchmark complete end-to-end performance with mocks."""
        
        with patch.multiple(
            'src.core.dubbing_service',
            TranscriptionService=MagicMock(),
            ContextAwareTranslator=MagicMock(), 
            ElevenLabsSynthesizer=MagicMock(),
            VideoMuxer=MagicMock()
        ) as mocks:
            
            # Setup fast mocks
            for mock_class in mocks.values():
                mock_instance = mock_class.return_value
                for method in ['process_request', 'translate_script', 'synthesize_script', 'replace_audio_in_video']:
                    if hasattr(mock_instance, method):
                        setattr(mock_instance, method, lambda *args, **kwargs: {
                            "success": True,
                            "processing_time": 0.1
                        })
            
            service = DubbingService()
            request = DubbingRequest(
                url="https://youtube.com/watch?v=perf_test",
                enable_translation=True,
                target_language="en-US",
                enable_synthesis=True,
                voice_id="test_voice",
                enable_video_muxing=True
            )
            
            start_time = time.time()
            result = service.process_dubbing_job(request)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            assert result.status == DubbingJobStatus.COMPLETED
            # With mocks, should complete very quickly
            assert processing_time < 5.0, f"Processing took {processing_time:.2f}s, expected < 5.0s"