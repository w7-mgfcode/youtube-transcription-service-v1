"""Tests for input validation utilities."""

import pytest
from src.utils.validators import is_valid_youtube_url


class TestYouTubeURLValidator:
    """Test YouTube URL validation."""
    
    def test_valid_youtube_urls(self):
        """Test valid YouTube URL formats."""
        valid_urls = [
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://youtube.com/watch?v=dQw4w9WgXcQ",
        ]
        
        for url in valid_urls:
            assert is_valid_youtube_url(url), f"Should be valid: {url}"
    
    def test_invalid_youtube_urls(self):
        """Test invalid YouTube URL formats."""
        invalid_urls = [
            "not-a-url",
            "https://google.com",
            "https://youtube.com/",
            "https://youtube.com/watch",
            "https://youtube.com/watch?v=",
            "https://vimeo.com/123456789",
            "",
            None,
        ]
        
        for url in invalid_urls:
            assert not is_valid_youtube_url(url), f"Should be invalid: {url}"