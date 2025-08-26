"""Input validation utilities."""

import re
from typing import Tuple, Optional
from .colors import Colors


def is_valid_bucket_name(name: str) -> bool:
    """
    Validate GCS bucket name format.
    
    Args:
        name: Bucket name to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not name or len(name) < 3 or len(name) > 63:
        return False
    
    # Check pattern: lowercase letters, numbers, dashes, dots
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", name):
        return False
    
    # Additional restrictions
    if ".." in name or name.startswith("goog"):
        return False
    
    return True


def is_valid_youtube_url(url: str) -> bool:
    """
    Validate YouTube URL format.
    
    Args:
        url: URL to validate
    
    Returns:
        True if valid YouTube URL, False otherwise
    """
    if not url:
        return False
    
    # Check for common YouTube URL patterns
    youtube_patterns = [
        r'youtube\.com/watch',
        r'youtu\.be/',
        r'youtube\.com/embed/',
        r'youtube\.com/v/',
    ]
    
    return any(re.search(pattern, url) for pattern in youtube_patterns)


def get_user_inputs() -> Tuple[str, bool, bool]:
    """
    Get user inputs for transcription job (preserving v25.py behavior).
    
    Returns:
        Tuple of (video_url, test_mode, breath_detection)
    """
    # Test mode input
    test_input = input(Colors.BOLD + "🧪 Teszt mód? (csak első 60 másodperc) [i/n]: " + Colors.ENDC).lower().strip()
    test_mode = test_input == 'i'
    
    # Breath detection input
    breath_input = input(Colors.BOLD + "💨 Levegővétel jelölés? [i/n]: " + Colors.ENDC).lower().strip()
    breath_detection = breath_input != 'n'  # Default: yes
    
    # YouTube URL input with validation
    while True:
        video_url = input(Colors.BOLD + "📺 YouTube videó URL: " + Colors.ENDC).strip()
        if is_valid_youtube_url(video_url):
            break
        print(Colors.FAIL + "❌ Érvénytelen YouTube URL! Próbáld újra." + Colors.ENDC)
    
    return video_url, test_mode, breath_detection


def get_bucket_name_interactive(default_bucket: str) -> str:
    """
    Get GCS bucket name interactively with validation.
    
    Args:
        default_bucket: Default bucket name to use
    
    Returns:
        Valid bucket name
    """
    bucket = default_bucket.strip()
    
    if bucket == "YOUR_BUCKET_NAME" or not is_valid_bucket_name(bucket):
        print(Colors.WARNING + "⚠ Nincs érvényes GCS bucket név beállítva." + Colors.ENDC)
        
        while True:
            user_input = input("Add meg a Google Cloud Storage bucket nevét: ").strip()
            if is_valid_bucket_name(user_input):
                return user_input
            print(Colors.FAIL + "✗ Hibás bucket név. Csak kisbetű, szám, kötőjel engedélyezett." + Colors.ENDC)
    
    return bucket


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from YouTube URL.
    
    Args:
        url: YouTube URL
    
    Returns:
        Video ID if found, None otherwise
    """
    # YouTube URL patterns for video ID extraction
    patterns = [
        r'youtube\.com/watch\?v=([^&]+)',
        r'youtu\.be/([^?]+)',
        r'youtube\.com/embed/([^?]+)',
        r'youtube\.com/v/([^?]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None