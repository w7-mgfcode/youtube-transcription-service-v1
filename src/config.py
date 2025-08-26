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
    
    # Paths
    temp_dir: str = "/app/temp"
    data_dir: str = "/app/data"
    
    # Default bucket for backward compatibility
    default_bucket: str = "angyal-audio-transcripts-2025"
    
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