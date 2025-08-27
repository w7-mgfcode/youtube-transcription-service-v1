"""Performance and benchmarking tests for the dubbing system."""

import time
import pytest
import threading
import psutil
import os
from unittest.mock import Mock, MagicMock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile

from src.core.translator import ContextAwareTranslator
from src.core.synthesizer import ElevenLabsSynthesizer  
from src.core.video_muxer import VideoMuxer
from src.core.dubbing_service import DubbingService
from src.utils.chunking import TranscriptChunker
from src.models.dubbing import DubbingRequest, AudioQuality, VideoFormat


class TestPerformance:
    """Performance benchmarking and load testing suite."""
    
    @pytest.fixture
    def performance_timer(self):
        """Performance timer fixture."""
        class Timer:
            def __init__(self):
                self.start_time = None
                self.end_time = None
                self.checkpoints = []
            
            def start(self):
                self.start_time = time.time()
                return self
            
            def checkpoint(self, name):
                if self.start_time:
                    elapsed = time.time() - self.start_time
                    self.checkpoints.append((name, elapsed))
            
            def stop(self):
                self.end_time = time.time()
                return self.elapsed()
            
            def elapsed(self):
                if self.start_time and self.end_time:
                    return self.end_time - self.start_time
                return 0
        
        return Timer()
    
    @pytest.fixture
    def memory_monitor(self):
        """Memory usage monitoring fixture."""
        class MemoryMonitor:
            def __init__(self):
                self.process = psutil.Process()
                self.initial_memory = None
                self.peak_memory = 0
                self.measurements = []
            
            def start(self):
                self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
                self.peak_memory = self.initial_memory
                return self
            
            def checkpoint(self, name):
                current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
                self.peak_memory = max(self.peak_memory, current_memory)
                self.measurements.append((name, current_memory))
                return current_memory
            
            def growth(self):
                if self.initial_memory:
                    return self.peak_memory - self.initial_memory
                return 0
        
        return MemoryMonitor()
    
    # =========================================================================
    # Chunking Performance Tests
    # =========================================================================
    
    def test_chunking_performance(self, performance_timer, memory_monitor):
        """Test chunking performance with various content sizes."""
        chunker = TranscriptChunker()
        
        # Test different content sizes
        sizes = [1000, 5000, 25000, 100000, 500000]  # Characters
        results = {}
        
        for size in sizes:
            # Generate content of specific size
            lines_needed = size // 50  # ~50 chars per line
            content_lines = []
            for i in range(lines_needed):
                timestamp = f"[{i//60:02d}:{i%60:02d}:00]"
                line = f"{timestamp} This is line {i} with some content to reach target size."
                content_lines.append(line)
            
            content = "\n".join(content_lines)[:size]  # Trim to exact size
            
            # Benchmark chunking
            timer = performance_timer.start()
            monitor = memory_monitor.start()
            
            chunks = chunker.chunk_text(content)
            
            processing_time = timer.stop()
            memory_used = monitor.growth()
            
            results[size] = {
                "chunks": len(chunks),
                "time": processing_time,
                "memory_mb": memory_used,
                "chars_per_second": size / processing_time if processing_time > 0 else 0
            }
            
            # Verify chunking is efficient
            assert processing_time < 5.0, f"Chunking {size} chars took {processing_time:.2f}s"
            assert memory_used < 50, f"Chunking used {memory_used:.1f}MB memory"
        
        # Verify performance scales reasonably
        small_rate = results[1000]["chars_per_second"]
        large_rate = results[100000]["chars_per_second"] 
        
        # Large content should still process at reasonable rate
        assert large_rate > small_rate * 0.1, "Performance degrades too much with size"
    
    def test_chunking_memory_efficiency(self, memory_monitor):
        """Test that chunking doesn't cause memory leaks."""
        chunker = TranscriptChunker()
        
        # Generate very large content
        large_content = ""
        for i in range(50000):
            large_content += f"[{i//3600:02d}:{(i%3600)//60:02d}:{i%60:02d}] Line {i} content.\n"
        
        monitor = memory_monitor.start()
        initial_memory = monitor.checkpoint("start")
        
        # Process multiple times to detect memory leaks
        for iteration in range(10):
            chunks = chunker.chunk_text(large_content)
            assert len(chunks) > 1
            
            # Force garbage collection
            import gc
            gc.collect()
            
            current_memory = monitor.checkpoint(f"iteration_{iteration}")
            
            # Memory should not grow significantly between iterations
            if iteration > 2:  # Allow some warmup
                memory_growth = current_memory - initial_memory
                assert memory_growth < 100, f"Memory leak detected: {memory_growth:.1f}MB"
    
    # =========================================================================
    # Translation Performance Tests
    # =========================================================================
    
    @patch('src.core.translator.vertexai')
    def test_translation_speed_benchmark(self, mock_vertexai, performance_timer):
        """Benchmark translation speed across different content sizes."""
        translator = ContextAwareTranslator()
        
        # Setup mock
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Translated text"
        mock_model.generate_content.return_value = mock_response
        mock_vertexai.GenerativeModel.return_value = mock_model
        
        sizes = [500, 2000, 10000, 50000]  # Characters
        results = {}
        
        for size in sizes:
            # Generate content
            content = f"[00:00:01] " + "Test content " * (size // 13)
            content = content[:size]
            
            timer = performance_timer.start()
            
            result = translator.translate_script(
                content, 
                "en-US",
                context="casual"
            )
            
            processing_time = timer.stop()
            
            results[size] = {
                "time": processing_time,
                "chars_per_second": size / processing_time if processing_time > 0 else 0
            }
            
            # Verify reasonable performance
            assert processing_time < 10.0, f"Translation of {size} chars took {processing_time:.2f}s"
        
        # Log performance results
        print("\nTranslation Performance Results:")
        for size, metrics in results.items():
            print(f"  {size:6} chars: {metrics['time']:.2f}s ({metrics['chars_per_second']:.0f} chars/s)")
    
    @patch('src.core.translator.vertexai')  
    def test_concurrent_translation_performance(self, mock_vertexai):
        """Test translation performance under concurrent load."""
        translator = ContextAwareTranslator()
        
        # Setup mock with slight delay to simulate network
        mock_model = MagicMock()
        def mock_translate(*args, **kwargs):
            time.sleep(0.1)  # Simulate 100ms API call
            response = MagicMock()
            response.text = "Translated content"
            return response
        
        mock_model.generate_content.side_effect = mock_translate
        mock_vertexai.GenerativeModel.return_value = mock_model
        
        # Test concurrent translations
        content = "[00:00:01] Test content for concurrent processing."
        num_threads = 10
        
        start_time = time.time()
        
        def translate_worker(thread_id):
            return translator.translate_script(content, "en-US", context="casual")
        
        # Execute concurrent translations
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(translate_worker, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Verify all translations completed
        successful_results = [r for r in results if r is not None]
        assert len(successful_results) == num_threads
        
        # Verify reasonable concurrency performance
        expected_sequential_time = num_threads * 0.1  # 10 threads * 100ms each
        efficiency = expected_sequential_time / total_time
        
        # Should be at least somewhat concurrent (>2x speedup)
        assert efficiency > 2.0, f"Concurrency efficiency: {efficiency:.1f}x"
    
    # =========================================================================
    # Synthesis Performance Tests
    # =========================================================================
    
    @patch('src.core.synthesizer.httpx.Client')
    def test_synthesis_throughput_benchmark(self, mock_client, performance_timer):
        """Benchmark synthesis throughput with different content lengths."""
        synthesizer = ElevenLabsSynthesizer()
        
        # Setup mock
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"AUDIO_DATA"
        
        def mock_synthesis(*args, **kwargs):
            # Simulate processing time proportional to content length
            json_data = kwargs.get('json', {})
            text_segments = json_data.get('text_segments', [])
            total_chars = sum(len(seg.get('text', '')) for seg in text_segments)
            processing_time = total_chars / 10000  # 10k chars per second
            time.sleep(processing_time)
            return mock_response
        
        mock_instance.post.side_effect = mock_synthesis
        mock_client.return_value = mock_instance
        
        # Test different script lengths
        lengths = [100, 500, 2000, 10000]  # Characters
        results = {}
        
        for length in lengths:
            # Generate timed script
            lines = []
            chars_used = 0
            line_num = 0
            
            while chars_used < length:
                timestamp = f"[00:{line_num//60:02d}:{line_num%60:02d}]"
                line = f"{timestamp} Line {line_num} content."
                lines.append(line)
                chars_used += len(line)
                line_num += 1
            
            script = "\n".join(lines)[:length]
            
            timer = performance_timer.start()
            
            result = synthesizer.synthesize_script(
                script,
                "test_voice",
                f"/tmp/test_{length}.mp3"
            )
            
            processing_time = timer.stop()
            
            results[length] = {
                "time": processing_time,
                "chars_per_second": length / processing_time if processing_time > 0 else 0,
                "success": result.get("success", False)
            }
            
            # Verify synthesis completed successfully
            assert result["success"] == True
        
        # Log synthesis performance
        print("\nSynthesis Performance Results:")
        for length, metrics in results.items():
            print(f"  {length:5} chars: {metrics['time']:.2f}s ({metrics['chars_per_second']:.0f} chars/s)")
    
    @patch('src.core.synthesizer.httpx.Client')
    def test_chunked_synthesis_efficiency(self, mock_client, performance_timer, memory_monitor):
        """Test efficiency of chunked synthesis for long content."""
        synthesizer = ElevenLabsSynthesizer()
        
        # Setup mock for chunked processing
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"CHUNK_AUDIO_DATA"
        
        call_count = [0]
        
        def mock_chunked_synthesis(*args, **kwargs):
            call_count[0] += 1
            time.sleep(0.05)  # 50ms per chunk
            return mock_response
        
        mock_instance.post.side_effect = mock_chunked_synthesis
        mock_client.return_value = mock_instance
        
        # Generate very long script (should trigger chunking)
        long_script_lines = []
        for i in range(200):  # 200 lines should definitely trigger chunking
            timestamp = f"[00:{i//60:02d}:{i%60:02d}:00]"
            long_script_lines.append(f"{timestamp} This is line {i} with substantial content for chunking test.")
        
        long_script = "\n".join(long_script_lines)
        
        timer = performance_timer.start()
        monitor = memory_monitor.start()
        
        result = synthesizer.synthesize_script(
            long_script,
            "test_voice",
            "/tmp/long_synthesis.mp3"
        )
        
        processing_time = timer.stop()
        memory_used = monitor.growth()
        
        # Verify chunking occurred
        assert call_count[0] > 1, f"Expected chunking, but only {call_count[0]} API calls made"
        
        # Verify reasonable performance despite chunking
        assert processing_time < 30.0, f"Chunked synthesis took {processing_time:.2f}s"
        assert memory_used < 200, f"Chunked synthesis used {memory_used:.1f}MB"
        assert result["success"] == True
        
        print(f"\nChunked Synthesis: {call_count[0]} chunks in {processing_time:.2f}s")
    
    # =========================================================================
    # Video Muxing Performance Tests
    # =========================================================================
    
    @patch('subprocess.run')
    @patch('yt_dlp.YoutubeDL')
    def test_video_muxing_performance(self, mock_ytdl, mock_run, performance_timer, temp_dir):
        """Benchmark video muxing performance."""
        muxer = VideoMuxer()
        
        # Setup mocks
        mock_ytdl_instance = MagicMock()
        mock_ytdl_instance.download.return_value = 0
        mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance
        
        def mock_ffmpeg_run(*args, **kwargs):
            # Simulate FFmpeg processing time
            time.sleep(0.5)  # 500ms for muxing
            result = MagicMock()
            result.returncode = 0
            return result
        
        mock_run.side_effect = mock_ffmpeg_run
        
        # Create test files
        video_file = f"{temp_dir}/test_video.mp4"
        audio_file = f"{temp_dir}/test_audio.mp3"
        output_file = f"{temp_dir}/output.mp4"
        
        # Create mock files
        with open(video_file, 'wb') as f:
            f.write(b'VIDEO_DATA' * 1000)  # ~10KB
        with open(audio_file, 'wb') as f:
            f.write(b'AUDIO_DATA' * 1000)  # ~10KB
        
        timer = performance_timer.start()
        
        with patch.object(muxer, '_download_video_only', return_value=video_file):
            result = muxer.replace_audio_in_video(
                "https://youtube.com/watch?v=test",
                audio_file,
                output_file
            )
        
        processing_time = timer.stop()
        
        assert result["success"] == True
        assert processing_time < 5.0, f"Video muxing took {processing_time:.2f}s"
        
        print(f"\nVideo Muxing: {processing_time:.2f}s")
    
    # =========================================================================
    # End-to-End Performance Tests
    # =========================================================================
    
    def test_complete_pipeline_performance(self, performance_timer, memory_monitor):
        """Benchmark complete dubbing pipeline performance."""
        
        with patch.multiple(
            'src.core.dubbing_service',
            TranscriptionService=MagicMock(),
            ContextAwareTranslator=MagicMock(),
            ElevenLabsSynthesizer=MagicMock(),
            VideoMuxer=MagicMock()
        ) as mocks:
            
            # Setup mocks with realistic timing
            stage_times = {
                'transcription': 3.0,
                'translation': 2.0,
                'synthesis': 8.0,
                'muxing': 2.0
            }
            
            def create_timed_mock(stage_name):
                def timed_operation(*args, **kwargs):
                    time.sleep(stage_times[stage_name])
                    return {"success": True, "processing_time": stage_times[stage_name]}
                return timed_operation
            
            # Setup each service mock
            mocks['TranscriptionService'].return_value.process_request.side_effect = create_timed_mock('transcription')
            mocks['ContextAwareTranslator'].return_value.translate_script.side_effect = create_timed_mock('translation')
            mocks['ElevenLabsSynthesizer'].return_value.synthesize_script.side_effect = create_timed_mock('synthesis')
            mocks['VideoMuxer'].return_value.replace_audio_in_video.side_effect = create_timed_mock('muxing')
            
            service = DubbingService()
            request = DubbingRequest(
                url="https://youtube.com/watch?v=perf_test",
                enable_translation=True,
                target_language="en-US",
                enable_synthesis=True,
                voice_id="test_voice",
                enable_video_muxing=True
            )
            
            timer = performance_timer.start()
            monitor = memory_monitor.start()
            
            result = service.process_dubbing_job(request)
            
            total_time = timer.stop()
            memory_used = monitor.growth()
            
            # Verify performance
            expected_time = sum(stage_times.values())
            assert result.status.value == "completed"
            
            # Allow some overhead but should be close to expected time
            assert total_time <= expected_time * 1.2, f"Pipeline took {total_time:.2f}s, expected ~{expected_time:.2f}s"
            assert memory_used < 300, f"Pipeline used {memory_used:.1f}MB memory"
            
            print(f"\nComplete Pipeline: {total_time:.2f}s (expected: {expected_time:.2f}s)")
    
    # =========================================================================
    # Load Testing
    # =========================================================================
    
    def test_concurrent_job_performance(self, performance_timer):
        """Test performance under concurrent job load."""
        
        with patch.multiple(
            'src.core.dubbing_service',
            TranscriptionService=MagicMock(),
            ContextAwareTranslator=MagicMock(),
            ElevenLabsSynthesizer=MagicMock(),
            VideoMuxer=MagicMock()
        ) as mocks:
            
            # Setup fast mocks for load testing
            for mock_class in mocks.values():
                mock_instance = mock_class.return_value
                for method in ['process_request', 'translate_script', 'synthesize_script', 'replace_audio_in_video']:
                    if hasattr(mock_instance, method):
                        setattr(mock_instance, method, lambda *args, **kwargs: {
                            "success": True,
                            "processing_time": 0.1
                        })
            
            # Test with multiple concurrent jobs
            num_jobs = 5
            jobs = []
            
            timer = performance_timer.start()
            
            def process_job(job_id):
                service = DubbingService()
                request = DubbingRequest(
                    url=f"https://youtube.com/watch?v=load_test_{job_id}",
                    enable_translation=True,
                    target_language="en-US"
                )
                return service.process_dubbing_job(request)
            
            # Run concurrent jobs
            with ThreadPoolExecutor(max_workers=num_jobs) as executor:
                futures = [executor.submit(process_job, i) for i in range(num_jobs)]
                results = [future.result() for future in as_completed(futures)]
            
            total_time = timer.stop()
            
            # Verify all jobs completed successfully  
            successful_jobs = [r for r in results if r.status.value == "completed"]
            assert len(successful_jobs) == num_jobs
            
            # Should complete faster than sequential processing
            sequential_time = num_jobs * 0.4  # ~400ms per job
            speedup = sequential_time / total_time
            
            assert speedup > 1.5, f"Concurrent processing speedup: {speedup:.1f}x"
            
            print(f"\nConcurrent Jobs: {num_jobs} jobs in {total_time:.2f}s (speedup: {speedup:.1f}x)")
    
    # =========================================================================
    # Memory Stress Tests
    # =========================================================================
    
    def test_memory_stress_large_files(self, memory_monitor, temp_dir):
        """Test memory usage with large file processing."""
        
        # Create large mock transcript file
        large_transcript = f"{temp_dir}/large_transcript.txt"
        with open(large_transcript, 'w') as f:
            for i in range(100000):  # 100k lines
                f.write(f"[{i//3600:02d}:{(i%3600)//60:02d}:{i%60:02d}] Line {i} content.\n")
        
        chunker = TranscriptChunker()
        
        monitor = memory_monitor.start()
        initial_memory = monitor.checkpoint("start")
        
        # Read and process large file
        with open(large_transcript, 'r') as f:
            content = f.read()
        
        monitor.checkpoint("file_loaded")
        
        # Process with chunker
        chunks = chunker.chunk_text(content)
        
        final_memory = monitor.checkpoint("chunks_created")
        
        # Memory growth should be reasonable
        memory_growth = final_memory - initial_memory
        
        # Should not use more than 500MB for this test
        assert memory_growth < 500, f"Memory usage: {memory_growth:.1f}MB (too high)"
        assert len(chunks) > 10, "Large file should be chunked"
        
        print(f"\nLarge File Processing: {len(chunks)} chunks, {memory_growth:.1f}MB memory")
    
    # =========================================================================
    # Performance Regression Tests  
    # =========================================================================
    
    def test_performance_regression_baseline(self, performance_timer):
        """Establish performance baseline for regression testing."""
        
        baselines = {}
        
        # Test chunking performance
        chunker = TranscriptChunker()
        content = "Test content " * 5000  # ~65k chars
        
        timer = performance_timer.start()
        chunks = chunker.chunk_text(content)
        chunking_time = timer.stop()
        
        baselines['chunking_5k_words'] = chunking_time
        
        # Test mock translation performance  
        with patch('src.core.translator.vertexai') as mock_vertexai:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = MagicMock(text="translated")
            mock_vertexai.GenerativeModel.return_value = mock_model
            
            translator = ContextAwareTranslator()
            
            timer = performance_timer.start()
            result = translator.translate_script(content[:2000], "en-US")
            translation_time = timer.stop()
            
            baselines['translation_2k_chars'] = translation_time
        
        # Performance baselines (these may need adjustment based on hardware)
        expected_baselines = {
            'chunking_5k_words': 1.0,      # 1 second
            'translation_2k_chars': 2.0,   # 2 seconds
        }
        
        print("\nPerformance Baselines:")
        for test_name, actual_time in baselines.items():
            expected_time = expected_baselines[test_name]
            ratio = actual_time / expected_time
            status = "✓" if ratio <= 2.0 else "✗"  # Allow 2x slower than baseline
            
            print(f"  {test_name}: {actual_time:.3f}s (expected: {expected_time:.3f}s) {status}")
            
            # Fail if more than 3x slower than baseline
            assert ratio <= 3.0, f"{test_name} is {ratio:.1f}x slower than baseline"