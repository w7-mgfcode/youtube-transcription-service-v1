"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings
from typing import Optional
import os


# Vertex AI Gemini model constants
class VertexAIModels:
    """Supported Vertex AI Gemini models."""
    
    # Current generation models (recommended)
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_2_0_FLASH_EXP = "gemini-2.0-flash-exp" 
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    
    # Legacy models (fallback)
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_PRO = "gemini-pro"
    
    # Auto-detect option
    AUTO_DETECT = "auto-detect"
    
    @classmethod
    def get_all_models(cls) -> list[str]:
        """Get list of all available models."""
        return [
            cls.GEMINI_2_0_FLASH,
            cls.GEMINI_2_5_FLASH,
            cls.GEMINI_2_5_PRO,
            cls.GEMINI_1_5_PRO,
            cls.GEMINI_1_5_FLASH,
            cls.AUTO_DETECT
        ]
    
    @classmethod
    def get_model_description(cls, model: str) -> str:
        """Get human-readable description of model."""
        descriptions = {
            cls.GEMINI_2_0_FLASH: "Gyors és hatékony (ajánlott)",
            cls.GEMINI_2_5_FLASH: "Legújabb gyors modell", 
            cls.GEMINI_2_5_PRO: "Legújabb részletes modell",
            cls.GEMINI_1_5_PRO: "Részletes elemzés",
            cls.GEMINI_1_5_FLASH: "Klasszikus gyors",
            cls.AUTO_DETECT: "Automatikus kiválasztás"
        }
        return descriptions.get(model, "Ismeretlen modell")
    
    @classmethod
    def get_auto_detect_order(cls) -> list[str]:
        """Get the order for auto-detection."""
        return [
            cls.GEMINI_2_0_FLASH,
            cls.GEMINI_2_5_FLASH,
            cls.GEMINI_1_5_PRO,
            cls.GEMINI_1_5_FLASH,
            cls.GEMINI_PRO
        ]


# Translation context constants for dubbing
class TranslationContext:
    """Supported translation contexts for dubbing."""
    
    LEGAL = "legal"
    SPIRITUAL = "spiritual" 
    MARKETING = "marketing"
    SCIENTIFIC = "scientific"
    CASUAL = "casual"
    EDUCATIONAL = "educational"
    NEWS = "news"
    
    @classmethod
    def get_all_contexts(cls) -> list[str]:
        """Get list of all available contexts."""
        return [
            cls.LEGAL, cls.SPIRITUAL, cls.MARKETING, 
            cls.SCIENTIFIC, cls.CASUAL, cls.EDUCATIONAL, cls.NEWS
        ]
    
    @classmethod
    def get_context_description(cls, context: str) -> str:
        """Get human-readable description of context."""
        descriptions = {
            cls.LEGAL: "Jogi/formális tartalom",
            cls.SPIRITUAL: "Spirituális/motivációs",
            cls.MARKETING: "Marketing/reklám",
            cls.SCIENTIFIC: "Tudományos/technikai",
            cls.CASUAL: "Hétköznapi beszélgetés",
            cls.EDUCATIONAL: "Oktatási/képzés",
            cls.NEWS: "Hírek/információs"
        }
        return descriptions.get(context, "Ismeretlen kontextus")


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Deployment mode
    mode: str = "api"  # "api" or "cli"
    
    # Google Cloud settings
    google_application_credentials: str = "/app/credentials/service-account.json"
    gcs_bucket_name: str = "angyal-audio-transcripts-2025"
    vertex_project_id: str = "gen-lang-client-0419432952"
    
    # Vertex AI settings
    vertex_ai_model: str = VertexAIModels.AUTO_DETECT
    vertex_ai_region: str = "us-central1"
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Processing thresholds
    sync_size_limit_mb: float = 10.0
    max_duration_seconds: int = 1800  # 30 minutes
    max_concurrent_jobs: int = 5
    
    # FFmpeg settings
    ffmpeg_sample_rate: int = 16000
    ffmpeg_channels: int = 1
    
    # Speech API settings
    language_code: str = "hu-HU"
    enable_punctuation: bool = True
    enable_word_offsets: bool = True
    
    # Pause detection thresholds (seconds)
    pause_min: float = 0.3
    pause_short: float = 0.6
    pause_long: float = 1.5
    pause_paragraph: float = 3.0
    
    # Text chunking settings for long transcripts
    chunking_enabled: bool = True
    chunk_size: int = 4000  # Characters per chunk
    chunk_overlap: int = 200  # Character overlap between chunks
    max_chunks: int = 20  # Maximum chunks to process (safety limit)
    max_transcript_length: int = 5000  # Current single-pass limit
    
    # Paths
    temp_dir: str = "/app/temp"
    data_dir: str = "/app/data"
    
    # Default bucket for backward compatibility
    default_bucket: str = "angyal-audio-transcripts-2025"
    
    # ==============================================================================
    # DUBBING FEATURE SETTINGS
    # ==============================================================================
    
    # Translation settings
    enable_translation: bool = True
    default_target_language: str = "en-US"
    default_translation_context: str = TranslationContext.CASUAL
    
    # ElevenLabs TTS settings
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_default_voice: str = "pNInz6obpgDQGcFmaJgB"
    elevenlabs_model: str = "eleven_multilingual_v2"
    elevenlabs_base_url: str = "https://api.elevenlabs.io/v1"
    
    # Video processing settings
    max_video_length_minutes: int = 30
    temp_video_dir: str = "/app/video_temp"  # Changed to avoid volume mount conflict completely
    enable_video_preview: bool = True
    
    # Dubbing quality settings
    target_audio_quality: str = "high"  # low, medium, high
    enable_audio_optimization: bool = True
    video_output_format: str = "mp4"
    
    # Cost management
    max_dubbing_cost_usd: float = 10.00
    enable_cost_estimation: bool = True
    dubbing_quota_reset_hour: int = 0
    
    # ==============================================================================
    # TTS PROVIDER SETTINGS  
    # ==============================================================================
    
    # TTS Provider Selection
    tts_provider: str = "auto"  # elevenlabs, google_tts, auto
    tts_fallback_enabled: bool = True  # Enable automatic fallback between providers
    tts_cost_optimization: bool = True  # Prefer cost-effective providers when auto
    
    # Google Cloud Text-to-Speech settings
    google_tts_enabled: bool = True
    google_tts_region: str = "us-central1"  # Google TTS API region
    google_tts_default_voice: str = "en-US-Neural2-F"  # Default Neural2 voice (female)
    google_tts_audio_profile: str = "large-home-entertainment-class-device"  # Audio optimization
    google_tts_timeout_seconds: int = 300  # API timeout
    google_tts_max_retries: int = 3  # Retry attempts
    
    # TTS Quality Settings
    tts_quality_preference: str = "balanced"  # cost_optimized, balanced, premium
    tts_synthesis_timeout: int = 300  # Synthesis timeout per request
    tts_chunk_size_chars: int = 1000  # Character limit per synthesis chunk
    tts_parallel_synthesis: bool = True  # Enable parallel chunk processing
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields from environment


# Global settings instance
settings = Settings()


def get_bucket_name() -> str:
    """Get GCS bucket name with validation."""
    import re
    
    bucket = settings.gcs_bucket_name.strip()
    
    # Validate bucket name format
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket):
        raise ValueError(f"Invalid GCS bucket name: {bucket}")
    
    if ".." in bucket or bucket.startswith("goog"):
        raise ValueError(f"Invalid GCS bucket name format: {bucket}")
    
    return bucket


def setup_google_credentials():
    """Setup Google Application Credentials environment variable."""
    if settings.google_application_credentials and os.path.exists(settings.google_application_credentials):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.google_application_credentials
    else:
        # Check if credentials are already set in environment
        if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
            raise FileNotFoundError(
                f"Google Cloud credentials not found at {settings.google_application_credentials} "
                f"and GOOGLE_APPLICATION_CREDENTIALS environment variable is not set"
            )