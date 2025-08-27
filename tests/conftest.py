"""Pytest configuration and shared fixtures for all tests."""

import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

# Import application components
from src.api import app
from src.config import settings, TranslationContext, VertexAIModels
from src.models.dubbing import (
    DubbingRequest, TranslationRequest, SynthesisRequest,
    DubbingJob, DubbingJobStatus, AudioQuality, VideoFormat
)


# =============================================================================
# Test Client Fixtures
# =============================================================================

@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def async_test_client():
    """Create an async test client for the FastAPI app."""
    from httpx import AsyncClient
    return AsyncClient(app=app, base_url="http://test")


# =============================================================================
# Directory and File Management Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_data_dir():
    """Get the test data directory path."""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def sample_transcript():
    """Return a sample Hungarian transcript with timestamps."""
    return """[00:00:01] Üdvözöllek mindenkit a mai videóban!
[00:00:04] Ma egy nagyon érdekes témáról fogunk beszélni.
[00:00:08] A mesterséges intelligencia fejlődéséről.
[00:00:12] Kezdjük is el rögtön az alapokkal.
[00:00:15] [levegővétel]
[00:00:16] Az MI története az 1950-es évekre nyúlik vissza.
[00:00:20] Alan Turing volt az egyik úttörő ezen a területen.
[00:00:24] [szünet]
[00:00:25] Ma már mindenhol találkozunk MI alkalmazásokkal.
[00:00:29] A telefonunktól kezdve az autókig.
[00:00:32] De mi is pontosan az MI?"""


@pytest.fixture
def sample_translation():
    """Return a sample English translation with timestamps."""
    return """[00:00:01] Welcome everyone to today's video!
[00:00:04] Today we'll be talking about a very interesting topic.
[00:00:08] The development of artificial intelligence.
[00:00:12] Let's start right away with the basics.
[00:00:15] [breath]
[00:00:16] The history of AI goes back to the 1950s.
[00:00:20] Alan Turing was one of the pioneers in this field.
[00:00:24] [pause]
[00:00:25] Today we encounter AI applications everywhere.
[00:00:29] From our phones to cars.
[00:00:32] But what exactly is AI?"""


# =============================================================================
# Mock Service Fixtures
# =============================================================================

@pytest.fixture
def mock_vertex_ai():
    """Mock Vertex AI client and responses."""
    with patch('src.core.translator.vertexai') as mock_vertexai:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Translated text with timestamps"
        mock_model.generate_content.return_value = mock_response
        
        mock_vertexai.init.return_value = None
        mock_vertexai.GenerativeModel.return_value = mock_model
        
        yield mock_vertexai


@pytest.fixture
def mock_elevenlabs_api():
    """Mock ElevenLabs API responses."""
    with patch('src.core.synthesizer.httpx.Client') as mock_client:
        mock_instance = MagicMock()
        
        # Mock successful synthesis response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake_audio_data"
        mock_response.json.return_value = {
            "audio_url": "https://api.elevenlabs.io/v1/audio/sample.mp3",
            "duration_seconds": 32.5,
            "character_count": 450
        }
        
        mock_instance.post.return_value = mock_response
        mock_client.return_value = mock_instance
        
        yield mock_instance


@pytest.fixture
def mock_ffmpeg():
    """Mock FFmpeg subprocess calls."""
    with patch('subprocess.run') as mock_run:
        # Mock successful FFmpeg execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "FFmpeg output"
        mock_result.stderr = ""
        
        mock_run.return_value = mock_result
        yield mock_run


@pytest.fixture
def mock_yt_dlp():
    """Mock yt-dlp download functionality."""
    with patch('yt_dlp.YoutubeDL') as mock_ytdl:
        mock_instance = MagicMock()
        
        # Mock video info
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'formats': [
                {'format_id': 'best', 'ext': 'mp4'}
            ]
        }
        
        # Mock download
        mock_instance.download.return_value = 0  # Success
        
        mock_ytdl.return_value.__enter__.return_value = mock_instance
        yield mock_instance


# =============================================================================
# Request Model Fixtures
# =============================================================================

@pytest.fixture
def sample_dubbing_request():
    """Create a sample dubbing request."""
    return DubbingRequest(
        url="https://youtube.com/watch?v=test123",
        test_mode=True,
        enable_translation=True,
        target_language="en-US",
        translation_context=TranslationContext.EDUCATIONAL,
        enable_synthesis=True,
        voice_id="test_voice_id",
        enable_video_muxing=True,
        video_format=VideoFormat.MP4
    )


@pytest.fixture
def sample_translation_request():
    """Create a sample translation request."""
    return TranslationRequest(
        transcript_text="[00:00:01] Magyar szöveg teszt.",
        target_language="en-US",
        translation_context=TranslationContext.CASUAL,
        target_audience="general public",
        desired_tone="friendly"
    )


@pytest.fixture
def sample_synthesis_request():
    """Create a sample synthesis request."""
    return SynthesisRequest(
        script_text="[00:00:01] English text test.",
        voice_id="test_voice_id",
        audio_quality=AudioQuality.HIGH
    )


# =============================================================================
# Mock Response Data Fixtures
# =============================================================================

@pytest.fixture
def mock_vertex_responses():
    """Load mock Vertex AI responses."""
    return {
        "casual": {
            "translated_text": "[00:00:01] Welcome everyone!\n[00:00:04] Today we discuss AI.",
            "confidence_score": 0.95,
            "model_used": "gemini-2.0-flash"
        },
        "legal": {
            "translated_text": "[00:00:01] Parties hereby acknowledge.\n[00:00:04] Terms and conditions apply.",
            "confidence_score": 0.98,
            "model_used": "gemini-2.0-flash"
        },
        "spiritual": {
            "translated_text": "[00:00:01] Blessed are those who seek.\n[00:00:04] The journey begins within.",
            "confidence_score": 0.92,
            "model_used": "gemini-2.0-flash"
        }
    }


@pytest.fixture
def mock_elevenlabs_voices():
    """Mock ElevenLabs available voices."""
    return [
        {
            "voice_id": "pNInz6obpgDQGcFmaJgB",
            "name": "Adam",
            "labels": {"accent": "american", "gender": "male"},
            "preview_url": "https://example.com/preview1.mp3"
        },
        {
            "voice_id": "21m00Tcm4TlvDq8ikWAM",
            "name": "Rachel",
            "labels": {"accent": "american", "gender": "female"},
            "preview_url": "https://example.com/preview2.mp3"
        }
    ]


# =============================================================================
# Job and Status Fixtures
# =============================================================================

@pytest.fixture
def sample_dubbing_job():
    """Create a sample dubbing job."""
    job = DubbingJob(
        job_id="test-job-123",
        status=DubbingJobStatus.PENDING,
        progress_percentage=0,
        created_at=datetime.now()
    )
    return job


@pytest.fixture
def mock_job_storage():
    """Mock job storage for testing."""
    jobs = {}
    
    def add_job(job_id: str, job_data: Dict[str, Any]):
        jobs[job_id] = job_data
    
    def get_job(job_id: str) -> Optional[Dict[str, Any]]:
        return jobs.get(job_id)
    
    def update_job(job_id: str, updates: Dict[str, Any]):
        if job_id in jobs:
            jobs[job_id].update(updates)
    
    return {
        "jobs": jobs,
        "add_job": add_job,
        "get_job": get_job,
        "update_job": update_job
    }


# =============================================================================
# Performance Testing Fixtures
# =============================================================================

@pytest.fixture
def performance_timer():
    """Simple timer for performance testing."""
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = datetime.now()
        
        def stop(self):
            self.end_time = datetime.now()
        
        def elapsed_seconds(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time).total_seconds()
            return 0
    
    return Timer()


# =============================================================================
# Test Data Generators
# =============================================================================

def generate_long_transcript(duration_seconds: int = 1800) -> str:
    """Generate a long transcript for testing chunking."""
    lines = []
    for i in range(0, duration_seconds, 4):
        minutes = i // 60
        seconds = i % 60
        timestamp = f"[{minutes:02d}:{seconds:02d}]"
        lines.append(f"{timestamp} Ez a {i//4 + 1}. mondat a tesztben.")
    return "\n".join(lines)


def generate_mock_audio_file(path: str, duration_seconds: float = 10.0):
    """Generate a fake audio file for testing."""
    # Create a simple WAV header (44 bytes) + fake data
    sample_rate = 44100
    num_samples = int(sample_rate * duration_seconds)
    
    # This is a simplified WAV file structure
    with open(path, 'wb') as f:
        # RIFF header
        f.write(b'RIFF')
        f.write((36 + num_samples * 2).to_bytes(4, 'little'))
        f.write(b'WAVE')
        
        # fmt chunk
        f.write(b'fmt ')
        f.write((16).to_bytes(4, 'little'))
        f.write((1).to_bytes(2, 'little'))  # PCM
        f.write((1).to_bytes(2, 'little'))  # Mono
        f.write(sample_rate.to_bytes(4, 'little'))
        f.write((sample_rate * 2).to_bytes(4, 'little'))
        f.write((2).to_bytes(2, 'little'))  # Block align
        f.write((16).to_bytes(2, 'little'))  # Bits per sample
        
        # data chunk
        f.write(b'data')
        f.write((num_samples * 2).to_bytes(4, 'little'))
        
        # Fake audio data (silence)
        f.write(b'\x00' * (num_samples * 2))


def generate_mock_video_file(path: str, duration_seconds: float = 10.0):
    """Generate a minimal fake video file for testing."""
    # Create a very simple file that FFmpeg would recognize
    # This is just for testing file operations, not actual video processing
    with open(path, 'wb') as f:
        # Write some fake data
        f.write(b'FAKE_VIDEO_DATA' * 1000)


# =============================================================================
# Cleanup Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_files(request):
    """Automatically cleanup test files after each test."""
    created_files = []
    
    def register_file(filepath):
        created_files.append(filepath)
    
    request.addfinalizer(lambda: [
        os.remove(f) for f in created_files if os.path.exists(f)
    ])
    
    return register_file


# =============================================================================
# Environment Variable Fixtures
# =============================================================================

@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    original_env = os.environ.copy()
    
    test_env = {
        "VERTEX_PROJECT_ID": "test-project",
        "GCS_BUCKET_NAME": "test-bucket",
        "ELEVENLABS_API_KEY": "test-api-key",
        "VERTEX_AI_MODEL": "gemini-2.0-flash"
    }
    
    os.environ.update(test_env)
    
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)