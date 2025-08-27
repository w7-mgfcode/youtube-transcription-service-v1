"""Abstract interface for Text-to-Speech providers."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class TTSProvider(str, Enum):
    """Supported TTS providers."""
    ELEVENLABS = "elevenlabs"
    GOOGLE_TTS = "google_tts"
    AUTO = "auto"


class VoiceProfile(BaseModel):
    """Standardized voice profile across all TTS providers."""
    voice_id: str
    name: str
    language: str
    gender: Optional[str] = None
    provider: TTSProvider
    description: Optional[str] = None
    category: Optional[str] = None
    is_premium: bool = False
    preview_url: Optional[str] = None
    
    # Provider-specific metadata
    labels: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "voice_id": "en-US-Neural2-A",
                "name": "Neural2-A",
                "language": "en-US", 
                "gender": "female",
                "provider": "google_tts",
                "description": "Clear, professional female voice",
                "category": "neural2",
                "is_premium": True,
                "labels": {
                    "accent": "american",
                    "age": "young_adult",
                    "use_case": "narration"
                }
            }
        }


class SynthesisResult(BaseModel):
    """Standardized synthesis result across all TTS providers."""
    audio_file_path: str
    duration_seconds: float
    file_size_bytes: int
    format: str
    sample_rate: int
    estimated_cost: float
    processing_time_seconds: float
    
    # Provider-specific metadata
    provider: TTSProvider
    voice_id: str
    model_used: Optional[str] = None
    method: Optional[str] = None  # single_call, chunked, etc.
    segments_processed: Optional[int] = None
    total_characters: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "audio_file_path": "/app/data/audio_job123.mp3",
                "duration_seconds": 12.5,
                "file_size_bytes": 200000,
                "format": "mp3",
                "sample_rate": 44100,
                "estimated_cost": 0.048,
                "processing_time_seconds": 3.2,
                "provider": "google_tts",
                "voice_id": "en-US-Neural2-A",
                "model_used": "Neural2",
                "method": "single_call",
                "total_characters": 120
            }
        }


class AbstractTTSSynthesizer(ABC):
    """Abstract base class for all TTS synthesizers."""
    
    @property
    @abstractmethod
    def provider_name(self) -> TTSProvider:
        """Return the provider identifier."""
        pass
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is properly configured and available."""
        pass
    
    @abstractmethod
    def synthesize_script(self, 
                         script_text: str, 
                         voice_id: str,
                         output_path: str,
                         audio_quality: str = "high",
                         **kwargs) -> SynthesisResult:
        """
        Synthesize timed script to audio file.
        
        Args:
            script_text: Translated script with timestamps
            voice_id: Provider-specific voice identifier
            output_path: Path to save generated audio file
            audio_quality: Audio quality setting (low, medium, high)
            **kwargs: Provider-specific additional parameters
            
        Returns:
            SynthesisResult with metadata about the generated audio
        """
        pass
    
    @abstractmethod
    def get_available_voices(self, 
                           language: Optional[str] = None,
                           gender: Optional[str] = None,
                           **filters) -> List[VoiceProfile]:
        """
        Get list of available voices with optional filtering.
        
        Args:
            language: Filter by language code (e.g., 'en-US')
            gender: Filter by gender ('male', 'female')
            **filters: Provider-specific filters
            
        Returns:
            List of VoiceProfile objects
        """
        pass
    
    @abstractmethod
    def validate_voice_id(self, voice_id: str) -> bool:
        """
        Validate that a voice ID exists and is accessible.
        
        Args:
            voice_id: Voice identifier to validate
            
        Returns:
            True if voice is valid and accessible
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, character_count: int, audio_quality: str = "high") -> float:
        """
        Estimate synthesis cost for given character count.
        
        Args:
            character_count: Number of characters to synthesize
            audio_quality: Audio quality setting
            
        Returns:
            Estimated cost in USD
        """
        pass
    
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes.
        
        Returns:
            List of language codes (e.g., ['en-US', 'de-DE'])
        """
        voices = self.get_available_voices()
        languages = set()
        for voice in voices:
            if voice.language:
                languages.add(voice.language)
        return sorted(list(languages))
    
    def get_voices_by_language(self, language: str) -> List[VoiceProfile]:
        """
        Get voices for a specific language.
        
        Args:
            language: Language code (e.g., 'en-US')
            
        Returns:
            List of VoiceProfile objects for the language
        """
        return self.get_available_voices(language=language)
    
    def find_voice_by_name(self, name: str) -> Optional[VoiceProfile]:
        """
        Find a voice by name.
        
        Args:
            name: Voice name to search for
            
        Returns:
            VoiceProfile if found, None otherwise
        """
        voices = self.get_available_voices()
        for voice in voices:
            if voice.name.lower() == name.lower():
                return voice
        return None
    
    def get_recommended_voice(self, 
                            language: str = "en-US",
                            gender: Optional[str] = None,
                            use_case: str = "general") -> Optional[VoiceProfile]:
        """
        Get a recommended voice for given criteria.
        
        Args:
            language: Target language
            gender: Preferred gender
            use_case: Use case (general, narration, conversation, etc.)
            
        Returns:
            Recommended VoiceProfile or None if not found
        """
        voices = self.get_available_voices(language=language, gender=gender)
        
        if not voices:
            return None
        
        # Prioritize premium voices
        premium_voices = [v for v in voices if v.is_premium]
        if premium_voices:
            return premium_voices[0]
        
        # Return first available voice
        return voices[0]


class TTSSynthesizerError(Exception):
    """Base exception for TTS synthesizer errors."""
    pass


class VoiceNotFoundError(TTSSynthesizerError):
    """Raised when a requested voice ID is not found."""
    pass


class SynthesisError(TTSSynthesizerError):
    """Raised when audio synthesis fails."""
    pass


class ProviderNotAvailableError(TTSSynthesizerError):
    """Raised when TTS provider is not properly configured or available."""
    pass