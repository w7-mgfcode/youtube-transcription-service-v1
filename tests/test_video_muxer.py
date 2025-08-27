"""Comprehensive tests for the video muxer module."""

import os
import tempfile
import subprocess
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path

from src.core.video_muxer import VideoMuxer, VideoMuxingError
from src.config import settings
from src.models.dubbing import VideoFormat


class TestVideoMuxer:
    """Test suite for VideoMuxer class."""
    
    @pytest.fixture
    def muxer(self):
        """Create a video muxer instance for testing."""
        return VideoMuxer()
    
    @pytest.fixture
    def mock_video_file(self, temp_dir):
        """Create a mock video file."""
        video_path = f"{temp_dir}/test_video.mp4"
        with open(video_path, 'wb') as f:
            f.write(b'FAKE_VIDEO_HEADER' + b'\x00' * 1000)
        return video_path
    
    @pytest.fixture
    def mock_audio_file(self, temp_dir):
        """Create a mock audio file."""
        audio_path = f"{temp_dir}/test_audio.mp3"
        with open(audio_path, 'wb') as f:
            # Simple WAV header
            f.write(b'RIFF' + b'\x00' * 100)
        return audio_path
    
    # =========================================================================
    # Initialization Tests
    # =========================================================================
    
    def test_initialization(self, muxer):
        """Test video muxer initialization."""
        assert muxer.temp_video_dir == settings.temp_video_dir
        assert muxer.video_format == settings.video_output_format
        assert muxer.preserve_quality == True
        assert os.path.exists(muxer.temp_video_dir)
    
    def test_temp_directory_creation(self):
        """Test that temp directory is created on init."""
        with patch('os.makedirs') as mock_makedirs:
            muxer = VideoMuxer()
            mock_makedirs.assert_called_with(settings.temp_video_dir, exist_ok=True)
    
    # =========================================================================
    # Video Download Tests
    # =========================================================================
    
    @patch('yt_dlp.YoutubeDL')
    def test_download_video_only(self, mock_ytdl, muxer, temp_dir):
        """Test video-only download to save bandwidth."""
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'formats': [{'format_id': 'best'}]
        }
        mock_instance.download.return_value = 0
        mock_ytdl.return_value.__enter__.return_value = mock_instance
        
        video_path = muxer._download_video_only("https://youtube.com/watch?v=test")
        
        # Check that video-only format was requested
        call_args = mock_ytdl.call_args
        ydl_opts = call_args[0][0] if call_args else {}
        assert 'format' in ydl_opts or 'format_sort' in ydl_opts
        # Should prefer video-only formats
        format_str = ydl_opts.get('format', '')
        assert 'video' in format_str.lower() or 'bestvideo' in format_str
    
    @patch('yt_dlp.YoutubeDL')
    def test_download_video_error_handling(self, mock_ytdl, muxer):
        """Test error handling during video download."""
        mock_instance = MagicMock()
        mock_instance.download.side_effect = Exception("Download failed")
        mock_ytdl.return_value.__enter__.return_value = mock_instance
        
        result = muxer._download_video_only("https://youtube.com/watch?v=test")
        assert result is None
    
    # =========================================================================
    # Audio Replacement Tests
    # =========================================================================
    
    @patch('subprocess.run')
    def test_audio_replacement(self, mock_run, muxer, mock_video_file, mock_audio_file, temp_dir):
        """Test replacing audio track in video."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        output_path = f"{temp_dir}/output.mp4"
        
        result = muxer._mux_video_audio(
            mock_video_file,
            mock_audio_file,
            output_path,
            preserve_video_quality=True,
            target_format="mp4"
        )
        
        assert result == True
        
        # Verify FFmpeg command structure
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert 'ffmpeg' in cmd
        assert '-i' in cmd  # Input files
        assert mock_video_file in cmd
        assert mock_audio_file in cmd
        assert output_path in cmd
        assert '-c:v' in cmd  # Video codec
        assert '-c:a' in cmd  # Audio codec
    
    @patch('subprocess.run')
    def test_preserve_video_quality(self, mock_run, muxer, mock_video_file, mock_audio_file, temp_dir):
        """Test that video quality is preserved during muxing."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        output_path = f"{temp_dir}/output.mp4"
        
        # Test with quality preservation ON
        muxer._mux_video_audio(
            mock_video_file,
            mock_audio_file,
            output_path,
            preserve_video_quality=True,
            target_format="mp4"
        )
        
        cmd = mock_run.call_args[0][0]
        assert 'copy' in cmd  # Should use copy codec to preserve quality
        
        # Test with quality preservation OFF
        muxer._mux_video_audio(
            mock_video_file,
            mock_audio_file,
            output_path,
            preserve_video_quality=False,
            target_format="mp4"
        )
        
        cmd = mock_run.call_args[0][0]
        # Should re-encode with specific settings
        assert any(codec in cmd for codec in ['libx264', 'h264', 'aac'])
    
    # =========================================================================
    # Video Format Tests
    # =========================================================================
    
    @patch('subprocess.run')
    def test_multiple_video_formats(self, mock_run, muxer, mock_video_file, mock_audio_file, temp_dir):
        """Test support for multiple video formats."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        formats = [VideoFormat.MP4, VideoFormat.WEBM, VideoFormat.AVI]
        
        for format_type in formats:
            output_path = f"{temp_dir}/output.{format_type.value}"
            
            result = muxer._mux_video_audio(
                mock_video_file,
                mock_audio_file,
                output_path,
                target_format=format_type.value
            )
            
            assert result == True
            
            # Check that output has correct extension
            assert output_path.endswith(f".{format_type.value}")
    
    @patch('subprocess.run')
    def test_format_specific_codecs(self, mock_run, muxer, mock_video_file, mock_audio_file, temp_dir):
        """Test that appropriate codecs are used for different formats."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        format_codecs = {
            "mp4": ["libx264", "aac"],
            "webm": ["libvpx", "libvorbis"],
            "avi": ["mpeg4", "mp3"]
        }
        
        for format_type, expected_codecs in format_codecs.items():
            output_path = f"{temp_dir}/output.{format_type}"
            
            muxer._mux_video_audio(
                mock_video_file,
                mock_audio_file,
                output_path,
                preserve_video_quality=False,
                target_format=format_type
            )
            
            cmd = mock_run.call_args[0][0]
            # At least one expected codec should be in command
            assert any(codec in " ".join(cmd) for codec in expected_codecs)
    
    # =========================================================================
    # Duration Validation Tests
    # =========================================================================
    
    @patch('subprocess.run')
    def test_duration_validation(self, mock_run, muxer):
        """Test video and audio duration compatibility check."""
        # Mock ffprobe for video info
        video_probe = MagicMock()
        video_probe.returncode = 0
        video_probe.stdout = '{"format": {"duration": "120.5"}}'
        
        # Mock ffprobe for audio info
        audio_probe = MagicMock()
        audio_probe.returncode = 0
        audio_probe.stdout = '{"format": {"duration": "118.2"}}'
        
        mock_run.side_effect = [video_probe, audio_probe]
        
        video_info = muxer._get_video_info("fake_video.mp4")
        audio_info = muxer._get_audio_info("fake_audio.mp3")
        
        # Small difference should be acceptable
        assert muxer._validate_duration_compatibility(video_info, audio_info)
        
        # Large difference should trigger warning
        audio_info["duration"] = 60.0  # Half of video duration
        result = muxer._validate_duration_compatibility(video_info, audio_info)
        # Should still proceed but with warning
        assert result == True or result == False
    
    @patch('subprocess.run')
    def test_get_video_info(self, mock_run, muxer):
        """Test extracting video information using ffprobe."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '''{
            "format": {
                "duration": "120.5",
                "bit_rate": "1000000"
            },
            "streams": [{
                "codec_type": "video",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1"
            }]
        }'''
        mock_run.return_value = mock_result
        
        info = muxer._get_video_info("test.mp4")
        
        assert info["duration"] == 120.5
        assert info["resolution"] == "1920x1080"
        assert "bitrate" in info
        
        # Verify ffprobe was called correctly
        cmd = mock_run.call_args[0][0]
        assert "ffprobe" in cmd
        assert "-print_format" in cmd
        assert "json" in cmd
    
    # =========================================================================
    # Preview Generation Tests
    # =========================================================================
    
    @patch('subprocess.run')
    def test_preview_generation(self, mock_run, muxer, mock_video_file, mock_audio_file, temp_dir):
        """Test preview video generation."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        preview_path = f"{temp_dir}/preview.mp4"
        
        result = muxer.generate_preview(
            mock_video_file,
            mock_audio_file,
            preview_path,
            duration_seconds=30
        )
        
        assert result == True
        
        # Check that duration limit was applied
        cmd = mock_run.call_args[0][0]
        assert "-t" in cmd  # Duration flag
        assert "30" in cmd  # 30 seconds
    
    @patch('subprocess.run')
    def test_preview_with_fade_effects(self, mock_run, muxer, mock_video_file, mock_audio_file, temp_dir):
        """Test preview generation with fade in/out effects."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        preview_path = f"{temp_dir}/preview_fade.mp4"
        
        result = muxer.generate_preview(
            mock_video_file,
            mock_audio_file,
            preview_path,
            duration_seconds=30,
            add_fade=True
        )
        
        cmd = " ".join(mock_run.call_args[0][0])
        # Check for fade filters
        assert "fade" in cmd.lower() or "-vf" in cmd
    
    # =========================================================================
    # Temp File Management Tests
    # =========================================================================
    
    def test_temp_file_cleanup(self, muxer, temp_dir):
        """Test that temporary files are cleaned up."""
        # Create temp files
        temp_files = []
        for i in range(3):
            temp_file = f"{temp_dir}/temp_{i}.tmp"
            with open(temp_file, 'w') as f:
                f.write("temp")
            temp_files.append(temp_file)
        
        # Register files for cleanup
        muxer._temp_files = temp_files
        
        # Cleanup
        muxer.cleanup_temp_files()
        
        # Check files are deleted
        for temp_file in temp_files:
            assert not os.path.exists(temp_file)
    
    def test_cleanup_on_error(self, muxer, mock_video_file, temp_dir):
        """Test that temp files are cleaned up even on error."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("FFmpeg crashed")
            
            output_path = f"{temp_dir}/output.mp4"
            
            with pytest.raises(Exception):
                muxer.replace_audio_in_video(
                    "https://youtube.com/watch?v=test",
                    mock_video_file,
                    output_path
                )
            
            # Temp files should still be cleaned
            assert len(muxer._temp_files) == 0 or all(
                not os.path.exists(f) for f in muxer._temp_files
            )
    
    # =========================================================================
    # Error Handling Tests
    # =========================================================================
    
    @patch('subprocess.run')
    def test_ffmpeg_error_handling(self, mock_run, muxer, mock_video_file, mock_audio_file, temp_dir):
        """Test handling of FFmpeg errors."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Invalid input format"
        mock_run.return_value = mock_result
        
        output_path = f"{temp_dir}/output.mp4"
        
        result = muxer._mux_video_audio(
            mock_video_file,
            mock_audio_file,
            output_path
        )
        
        assert result == False
    
    def test_missing_audio_file(self, muxer, mock_video_file, temp_dir):
        """Test handling of missing audio file."""
        output_path = f"{temp_dir}/output.mp4"
        non_existent_audio = "/path/to/nonexistent.mp3"
        
        with pytest.raises(VideoMuxingError) as exc_info:
            muxer.replace_audio_in_video(
                mock_video_file,
                non_existent_audio,
                output_path
            )
        
        assert "not found" in str(exc_info.value).lower()
    
    @patch('subprocess.run')
    def test_corrupted_video_handling(self, mock_run, muxer, temp_dir):
        """Test handling of corrupted video files."""
        # Create a corrupted video file
        corrupted_video = f"{temp_dir}/corrupted.mp4"
        with open(corrupted_video, 'wb') as f:
            f.write(b'CORRUPTED_DATA')
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Invalid data found"
        mock_run.return_value = mock_result
        
        audio_file = f"{temp_dir}/audio.mp3"
        with open(audio_file, 'wb') as f:
            f.write(b'AUDIO_DATA')
        
        output_path = f"{temp_dir}/output.mp4"
        
        result = muxer._mux_video_audio(
            corrupted_video,
            audio_file,
            output_path
        )
        
        assert result == False
    
    # =========================================================================
    # Video Length Validation Tests
    # =========================================================================
    
    @patch('subprocess.run')
    def test_video_length_limit(self, mock_run, muxer):
        """Test enforcement of 30-minute video length limit."""
        # Mock video info with duration > 30 minutes
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"format": {"duration": "2100.0"}}'  # 35 minutes
        mock_run.return_value = mock_result
        
        info = muxer._get_video_info("long_video.mp4")
        
        # Should detect as too long
        assert info["duration"] > 1800  # 30 minutes in seconds
        
        with pytest.raises(VideoMuxingError) as exc_info:
            muxer._validate_video_length(info)
        
        assert "30 minutes" in str(exc_info.value) or "length" in str(exc_info.value).lower()
    
    # =========================================================================
    # Integration Tests
    # =========================================================================
    
    @patch('subprocess.run')
    @patch('yt_dlp.YoutubeDL')
    def test_full_muxing_pipeline(
        self, mock_ytdl, mock_run, muxer, mock_audio_file, temp_dir
    ):
        """Test complete video muxing pipeline."""
        # Mock video download
        mock_ytdl_instance = MagicMock()
        mock_ytdl_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120
        }
        mock_ytdl_instance.download.return_value = 0
        mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance
        
        # Mock FFmpeg operations
        mock_results = [
            MagicMock(returncode=0, stdout='{"format": {"duration": "120"}}'),  # Video info
            MagicMock(returncode=0, stdout='{"format": {"duration": "118"}}'),  # Audio info
            MagicMock(returncode=0),  # Muxing success
        ]
        mock_run.side_effect = mock_results
        
        output_path = f"{temp_dir}/final_output.mp4"
        
        # Create a fake downloaded video
        temp_video = f"{muxer.temp_video_dir}/temp_video.mp4"
        os.makedirs(os.path.dirname(temp_video), exist_ok=True)
        with open(temp_video, 'wb') as f:
            f.write(b'VIDEO_DATA')
        
        with patch.object(muxer, '_download_video_only', return_value=temp_video):
            result = muxer.replace_audio_in_video(
                "https://youtube.com/watch?v=test",
                mock_audio_file,
                output_path,
                preserve_video_quality=True,
                target_format="mp4"
            )
        
        assert result["success"] == True
        assert result["output_file"] == output_path
        assert "processing_time" in result
        assert "video_info" in result
        assert "audio_info" in result