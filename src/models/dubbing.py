"""Pydantic models for dubbing functionality."""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime

from ..config import TranslationContext


class TranslationContextEnum(str, Enum):
    """Enumeration of supported translation contexts."""
    LEGAL = TranslationContext.LEGAL
    SPIRITUAL = TranslationContext.SPIRITUAL
    MARKETING = TranslationContext.MARKETING
    SCIENTIFIC = TranslationContext.SCIENTIFIC
    CASUAL = TranslationContext.CASUAL
    EDUCATIONAL = TranslationContext.EDUCATIONAL
    NEWS = TranslationContext.NEWS


class AudioQuality(str, Enum):
    """Audio quality options for synthesis."""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"


class VideoFormat(str, Enum):
    """Supported video output formats."""
    MP4 = "mp4"
    WEBM = "webm"
    AVI = "avi"


class TTSProviderEnum(str, Enum):
    """Available TTS providers."""
    ELEVENLABS = "elevenlabs"
    GOOGLE_TTS = "google_tts" 
    AUTO = "auto"


class DubbingJobStatus(str, Enum):
    """Status of dubbing jobs."""
    PENDING = "pending"
    TRANSCRIBING = "transcribing"
    TRANSLATING = "translating"
    SYNTHESIZING = "synthesizing"
    MUXING = "muxing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Request Models
class TranslationRequest(BaseModel):
    """Request model for translation operations."""
    transcript_text: str = Field(..., description="Hungarian transcript to translate")
    target_language: str = Field("en-US", description="Target language code (e.g., en-US, de-DE)")
    translation_context: TranslationContextEnum = Field(
        TranslationContextEnum.CASUAL, 
        description="Translation context for appropriate tone/style"
    )
    target_audience: str = Field("general public", description="Target audience for translation")
    desired_tone: str = Field("neutral", description="Desired tone (neutral, formal, casual, etc.)")
    translation_goal: str = Field("accuracy", description="Primary goal (accuracy, fluency, brevity)")
    preserve_timing: bool = Field(True, description="Whether to preserve timestamp accuracy")

    class Config:
        json_schema_extra = {
            "example": {
                "transcript_text": "[0:00:01] Sziasztok, üdvözöllek benneteket!\n[0:00:03] Ma egy izgalmas témáról beszélek...",
                "target_language": "en-US",
                "translation_context": "spiritual",
                "target_audience": "general public",
                "desired_tone": "uplifting",
                "translation_goal": "accuracy"
            }
        }


class SynthesisRequest(BaseModel):
    """Request model for audio synthesis."""
    script_text: str = Field(..., description="Translated script with timestamps")
    voice_id: str = Field(..., description="ElevenLabs voice ID")
    model: str = Field("eleven_multilingual_v2", description="ElevenLabs model to use")
    audio_quality: AudioQuality = Field(AudioQuality.HIGH, description="Output audio quality")
    optimize_streaming_latency: bool = Field(False, description="Optimize for streaming")
    output_format: str = Field("mp3_44100_128", description="Audio output format")

    class Config:
        json_schema_extra = {
            "example": {
                "script_text": "[0:00:01] Hello, welcome everyone!\n[0:00:03] Today I'm talking about an exciting topic...",
                "voice_id": "pNInz6obpgDQGcFmaJgB",
                "model": "eleven_multilingual_v2",
                "audio_quality": "high"
            }
        }


class DubbingRequest(BaseModel):
    """Extended transcription request with dubbing parameters."""
    # Original transcription parameters
    url: HttpUrl = Field(..., description="YouTube video URL")
    test_mode: bool = Field(False, description="Process only first 60 seconds")
    breath_detection: bool = Field(True, description="Enable breath/pause detection")
    use_vertex_ai: bool = Field(False, description="Use Vertex AI for post-processing")
    vertex_ai_model: Optional[str] = Field(None, description="Specific Vertex AI model")
    
    # Translation parameters
    enable_translation: bool = Field(False, description="Enable translation feature")
    target_language: str = Field("en-US", description="Target language for translation")
    translation_context: TranslationContextEnum = Field(
        TranslationContextEnum.CASUAL,
        description="Translation context"
    )
    target_audience: str = Field("general public", description="Target audience")
    desired_tone: str = Field("neutral", description="Desired translation tone")
    
    # Synthesis parameters
    enable_synthesis: bool = Field(False, description="Enable audio synthesis")
    tts_provider: TTSProviderEnum = Field(TTSProviderEnum.AUTO, description="TTS provider to use")
    voice_id: Optional[str] = Field(None, description="Voice ID (provider-specific)")
    synthesis_model: str = Field("eleven_multilingual_v2", description="TTS model")
    audio_quality: AudioQuality = Field(AudioQuality.HIGH, description="Audio quality")
    
    # Video muxing parameters
    enable_video_muxing: bool = Field(False, description="Create final dubbed video")
    video_format: VideoFormat = Field(VideoFormat.MP4, description="Output video format")
    preserve_video_quality: bool = Field(True, description="Preserve original video quality")
    
    # Cost and processing controls
    max_cost_usd: Optional[float] = Field(None, description="Maximum allowed cost")
    preview_mode: bool = Field(False, description="Generate audio-only preview")
    
    # Optional existing transcript (for CLI mode)
    existing_transcript: Optional[str] = Field(None, description="Pre-existing transcript text")

    @validator('enable_video_muxing')  
    def video_muxing_requires_synthesis(cls, v, values):
        """Ensure synthesis is enabled when video muxing is requested."""
        if v and not values.get('enable_synthesis'):
            raise ValueError('enable_synthesis must be True when enable_video_muxing is True')
        return v

    @validator('voice_id', always=True)
    def voice_id_required_for_synthesis(cls, v, values):
        """Ensure voice_id is provided when synthesis is enabled."""
        enable_synthesis = values.get('enable_synthesis')
        if enable_synthesis and not v:
            raise ValueError('voice_id is required when enable_synthesis is True')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
                "test_mode": True,
                "breath_detection": True,
                "use_vertex_ai": True,
                "enable_translation": True,
                "target_language": "en-US",
                "translation_context": "spiritual",
                "enable_synthesis": True,
                "tts_provider": "google_tts",
                "voice_id": "en-US-Neural2-F",
                "enable_video_muxing": True,
                "max_cost_usd": 5.00
            }
        }


# Response Models
class TranslationResult(BaseModel):
    """Result of translation operation."""
    original_text: str = Field(..., description="Original Hungarian text")
    translated_text: str = Field(..., description="Translated text")
    source_language: str = Field("hu-HU", description="Source language")
    target_language: str = Field(..., description="Target language")
    translation_context: str = Field(..., description="Context used for translation")
    word_count: int = Field(..., description="Word count of translated text")
    estimated_cost: float = Field(..., description="Estimated translation cost")
    processing_time_seconds: float = Field(..., description="Time taken to translate")
    confidence_score: Optional[float] = Field(None, description="Translation confidence (0-1)")


class SynthesisResult(BaseModel):
    """Result of audio synthesis operation."""
    audio_file_path: str = Field(..., description="Path to generated audio file")
    duration_seconds: float = Field(..., description="Audio duration in seconds")
    file_size_bytes: int = Field(..., description="Audio file size")
    format: str = Field(..., description="Audio format")
    sample_rate: int = Field(..., description="Audio sample rate")
    voice_id: str = Field(..., description="Voice ID used")
    model: str = Field(..., description="TTS model used")
    estimated_cost: float = Field(..., description="Synthesis cost")
    processing_time_seconds: float = Field(..., description="Synthesis processing time")


class VideoMuxingResult(BaseModel):
    """Result of video muxing operation."""
    video_file_path: str = Field(..., description="Path to final dubbed video")
    original_video_duration: float = Field(..., description="Original video duration")
    final_video_duration: float = Field(..., description="Final video duration")
    file_size_bytes: int = Field(..., description="Final video file size")
    format: str = Field(..., description="Video format")
    resolution: str = Field(..., description="Video resolution (e.g., 1920x1080)")
    processing_time_seconds: float = Field(..., description="Muxing processing time")


class DubbingJob(BaseModel):
    """Complete dubbing job with all stages."""
    job_id: str = Field(..., description="Unique job identifier")
    base_transcription_job_id: Optional[str] = Field(None, description="Base transcription job ID")
    status: DubbingJobStatus = Field(DubbingJobStatus.PENDING, description="Current job status")
    progress_percentage: int = Field(0, description="Overall progress (0-100)")
    
    # Request parameters
    request: DubbingRequest = Field(..., description="Original request parameters")
    
    # Stage results
    transcription_result: Optional[Dict[str, Any]] = Field(None, description="Transcription stage result")
    translation_result: Optional[TranslationResult] = Field(None, description="Translation stage result")
    synthesis_result: Optional[SynthesisResult] = Field(None, description="Synthesis stage result")
    video_muxing_result: Optional[VideoMuxingResult] = Field(None, description="Video muxing result")
    
    # Job metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Job creation time")
    started_at: Optional[datetime] = Field(None, description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    
    # Cost tracking
    estimated_total_cost: float = Field(0.0, description="Estimated total cost")
    actual_total_cost: float = Field(0.0, description="Actual total cost")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(0, description="Number of retry attempts")


class DubbingJobResponse(BaseModel):
    """API response for dubbing job operations."""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Current status")
    progress: int = Field(0, description="Progress percentage")
    message: Optional[str] = Field(None, description="Status message")
    estimated_completion_time: Optional[str] = Field(None, description="ETA for completion")
    result: Optional[DubbingJob] = Field(None, description="Complete job details")
    error: Optional[str] = Field(None, description="Error details if failed")


class VoiceProfile(BaseModel):
    """ElevenLabs voice profile information."""
    voice_id: str = Field(..., description="Unique voice identifier")
    name: str = Field(..., description="Voice name")
    category: str = Field(..., description="Voice category")
    description: Optional[str] = Field(None, description="Voice description")
    gender: Optional[str] = Field(None, description="Voice gender")
    accent: Optional[str] = Field(None, description="Voice accent")
    language_codes: List[str] = Field(default_factory=list, description="Supported language codes")
    preview_url: Optional[str] = Field(None, description="Voice preview audio URL")
    is_premium: bool = Field(False, description="Whether voice requires premium subscription")


class VoiceListResponse(BaseModel):
    """Response model for available voices."""
    voices: List[VoiceProfile] = Field(..., description="Available voice profiles")
    total_count: int = Field(..., description="Total number of voices")
    categories: List[str] = Field(default_factory=list, description="Available voice categories")


class CostEstimate(BaseModel):
    """Cost estimation for dubbing operations."""
    translation_cost: float = Field(0.0, description="Translation cost estimate")
    synthesis_cost: float = Field(0.0, description="TTS synthesis cost estimate")
    processing_cost: float = Field(0.0, description="Additional processing costs")
    total_cost: float = Field(0.0, description="Total estimated cost")
    currency: str = Field("USD", description="Cost currency")
    
    # Breakdown details
    character_count: int = Field(0, description="Characters to be processed")
    audio_duration_estimate: float = Field(0.0, description="Estimated audio duration")
    cost_per_character: float = Field(0.0, description="Cost per character")
    
    # Warnings
    warnings: List[str] = Field(default_factory=list, description="Cost warnings")
    exceeds_limit: bool = Field(False, description="Whether cost exceeds user limit")