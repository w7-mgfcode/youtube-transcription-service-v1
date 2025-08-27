"""FastAPI application for YouTube transcription service."""

import os
import uuid
import asyncio
from typing import Optional, Dict, Any
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

from .config import settings, VertexAIModels
from .core.transcriber import TranscriptionService
from .utils.colors import Colors
from .utils.chunking import TranscriptChunker
from .models.dubbing import (
    TranslationRequest, SynthesisRequest, DubbingRequest,
    DubbingJobResponse, VoiceListResponse, CostEstimate,
    TranslationContextEnum, AudioQuality
)
from .core.translator import ContextAwareTranslator
from .core.synthesizer import ElevenLabsSynthesizer
from .core.video_muxer import VideoMuxer
from .core.dubbing_service import DubbingService
from .core.tts_factory import TTSFactory
from .core.tts_interface import TTSProvider


# Pydantic models for API
class TranscribeRequest(BaseModel):
    """Request model for transcription (legacy - use DubbingRequest for full features)."""
    url: HttpUrl
    test_mode: bool = False
    breath_detection: bool = True
    use_vertex_ai: bool = False
    vertex_ai_model: Optional[str] = VertexAIModels.AUTO_DETECT
    
    # Optional dubbing parameters for backward compatibility
    enable_translation: bool = False
    target_language: str = "en-US"
    translation_context: TranslationContextEnum = TranslationContextEnum.CASUAL
    enable_synthesis: bool = False
    voice_id: Optional[str] = None
    enable_video_muxing: bool = False
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
                "test_mode": True,
                "breath_detection": True,
                "use_vertex_ai": True,
                "vertex_ai_model": "gemini-2.0-flash",
                "enable_translation": False,
                "enable_synthesis": False,
                "enable_video_muxing": False
            }
        }


class JobResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: str
    progress: int = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class JobListResponse(BaseModel):
    """Response model for job listing."""
    jobs: list
    total_count: int


class ChunkingEstimateRequest(BaseModel):
    """Request model for chunking estimate."""
    transcript_text: str
    
    class Config:
        schema_extra = {
            "example": {
                "transcript_text": "Long transcript text here..."
            }
        }


class ChunkingEstimateResponse(BaseModel):
    """Response model for chunking estimate."""
    needs_chunking: bool
    total_chunks: int
    total_characters: int
    original_length: int
    estimated_cost_usd: float
    estimated_time_seconds: float
    chunks_info: list


class TTSProviderInfo(BaseModel):
    """Information about a TTS provider."""
    provider_id: str
    name: str
    available: bool
    cost_per_1k_chars: float
    voice_count: int
    error: Optional[str] = None


class TTSProvidersResponse(BaseModel):
    """Response model for TTS providers list."""
    providers: list[TTSProviderInfo]
    auto_selected: str


class TTSVoiceInfo(BaseModel):
    """Information about a TTS voice."""
    voice_id: str
    name: str
    language: str
    gender: str
    is_premium: bool = False


class TTSVoicesResponse(BaseModel):
    """Response model for TTS provider voices."""
    provider: str
    voices: list[TTSVoiceInfo]
    total_count: int


class TTSCostComparison(BaseModel):
    """Cost comparison between TTS providers."""
    character_count: int
    elevenlabs_cost: float
    google_tts_cost: float
    savings_percent: float
    recommended_provider: str


# FastAPI app setup
app = FastAPI(
    title="YouTube Transcription & Dubbing Service",
    description="""
    Complete YouTube video transcription and multilingual dubbing service.
    
    **Features:**
    - Hungarian language transcription using Google Cloud Speech-to-Text
    - Context-aware translation to 20+ languages using Vertex AI
    - High-quality voice synthesis using ElevenLabs TTS
    - Complete video dubbing with audio replacement
    - Support for various content contexts (legal, spiritual, marketing, scientific, etc.)
    - Chunking support for unlimited transcript lengths
    - Cost estimation and progress tracking
    
    **Pipeline:** Transcribe → Translate → Synthesize → Video Mux
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
transcriber = TranscriptionService()
chunker = TranscriptChunker()
translator = ContextAwareTranslator()
synthesizer = ElevenLabsSynthesizer()
video_muxer = VideoMuxer()
dubbing_service = DubbingService()

# In-memory job store (replace with Redis/database in production)
jobs: Dict[str, Dict[str, Any]] = {}


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "YouTube Transcription Service",
        "version": "1.0.0",
        "status": "healthy",
        "mode": settings.mode,
        "language": settings.language_code
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "mode": settings.mode,
        "language": settings.language_code,
        "data_dir": settings.data_dir,
        "temp_dir": settings.temp_dir
    }


@app.post("/v1/transcribe", response_model=JobResponse)
async def create_transcription(request: TranscribeRequest, background_tasks: BackgroundTasks):
    """
    Create new transcription job.
    
    Args:
        request: Transcription request parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        Job response with job ID and initial status
    """
    job_id = str(uuid.uuid4())
    
    # Initialize job in store
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "result": None,
        "error": None,
        "request": request.dict(),
        "created_at": None
    }
    
    # Process in background
    background_tasks.add_task(
        process_transcription_job,
        job_id,
        str(request.url),
        request.test_mode,
        request.breath_detection,
        request.use_vertex_ai,
        request.vertex_ai_model,
        request  # Pass full request for dubbing parameters
    )
    
    return JobResponse(job_id=job_id, status="queued")


@app.post("/v1/chunking-estimate", response_model=ChunkingEstimateResponse)
async def get_chunking_estimate(request: ChunkingEstimateRequest):
    """
    Get chunking estimate for a given transcript text.
    
    Args:
        request: Text to estimate chunking for
        
    Returns:
        Chunking estimate with cost and time predictions
    """
    try:
        needs_chunking = chunker.needs_chunking(request.transcript_text)
        
        if needs_chunking:
            estimate = chunker.estimate_processing_cost(request.transcript_text)
            return ChunkingEstimateResponse(**estimate, needs_chunking=True)
        else:
            # Single pass processing
            return ChunkingEstimateResponse(
                needs_chunking=False,
                total_chunks=1,
                total_characters=len(request.transcript_text),
                original_length=len(request.transcript_text),
                estimated_cost_usd=len(request.transcript_text) / 1000 * 0.0001,
                estimated_time_seconds=len(request.transcript_text) / 1000 * 0.5,
                chunks_info=[(1, len(request.transcript_text), 0, len(request.transcript_text))]
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error estimating chunking: {str(e)}")


@app.post("/v1/translate")
async def translate_transcript(request: TranslationRequest):
    """
    Translate existing Hungarian transcript to target language.
    
    Args:
        request: Translation parameters including transcript text, target language, and context
        
    Returns:
        Translation result with timing preservation
    """
    try:
        # Validate input
        if not request.transcript_text.strip():
            raise HTTPException(status_code=400, detail="Transcript text is required")
        
        # Perform translation
        result = translator.translate_script(
            script_text=request.transcript_text,
            target_language=request.target_language,
            context=request.translation_context.value,
            audience=request.audience,
            tone=request.tone,
            quality=request.quality,
            preserve_timing=request.preserve_timing
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Translation failed")
        
        return {
            "status": "completed",
            "translated_text": result["translated_text"],
            "original_language": "hu-HU",
            "target_language": request.target_language,
            "translation_context": request.translation_context.value,
            "timing_preserved": result.get("timing_preserved", True),
            "character_count": len(result["translated_text"]),
            "cost_estimate": result.get("cost_usd", 0.0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")


@app.post("/v1/synthesize")
async def synthesize_audio(request: SynthesisRequest):
    """
    Convert translated text to speech using ElevenLabs.
    
    Args:
        request: Synthesis parameters including text, voice ID, and quality settings
        
    Returns:
        Audio synthesis result with file path
    """
    try:
        # Validate input
        if not request.script_text.strip():
            raise HTTPException(status_code=400, detail="Script text is required")
        
        if not request.voice_id:
            raise HTTPException(status_code=400, detail="Voice ID is required")
        
        # Generate output path
        output_filename = f"synthesis_{uuid.uuid4().hex[:8]}.mp3"
        output_path = os.path.join(settings.temp_dir, output_filename)
        
        # Perform synthesis
        result = synthesizer.synthesize_script(
            script_text=request.script_text,
            voice_id=request.voice_id,
            output_path=output_path,
            model=request.model,
            optimize_streaming=request.optimize_streaming,
            audio_quality=request.audio_quality.value
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Audio synthesis failed")
        
        return {
            "status": "completed",
            "audio_file": output_path,
            "voice_id": request.voice_id,
            "duration_seconds": result.get("duration_seconds", 0),
            "audio_quality": request.audio_quality.value,
            "file_size_bytes": result.get("file_size_bytes", 0),
            "cost_estimate": result.get("cost_usd", 0.0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis error: {str(e)}")


@app.post("/v1/dub", response_model=DubbingJobResponse)
async def create_dubbing_job(request: DubbingRequest, background_tasks: BackgroundTasks):
    """
    Create full dubbing job (transcribe → translate → synthesize → mux).
    
    Args:
        request: Complete dubbing parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        Dubbing job response with job ID and status
    """
    job_id = str(uuid.uuid4())
    
    # Initialize dubbing job in store
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "result": None,
        "error": None,
        "request": request.dict(),
        "created_at": None,
        "job_type": "dubbing"
    }
    
    # Process in background
    background_tasks.add_task(
        process_dubbing_background,
        job_id,
        request
    )
    
    return DubbingJobResponse(
        job_id=job_id,
        status="queued",
        progress=0,
        estimated_duration_minutes=10,  # Default estimate
        cost_estimate=0.0
    )


@app.get("/v1/voices", response_model=VoiceListResponse)
async def list_voices():
    """
    List available ElevenLabs voices.
    
    Returns:
        Available voice profiles with characteristics
    """
    try:
        voices = synthesizer.list_available_voices()
        
        return VoiceListResponse(
            voices=voices.get("voices", []),
            total_count=len(voices.get("voices", [])),
            default_voice_id=settings.elevenlabs_default_voice or voices.get("voices", [{}])[0].get("voice_id")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch voices: {str(e)}")


@app.get("/v1/tts-providers", response_model=TTSProvidersResponse)
async def list_tts_providers():
    """
    List available TTS providers with metadata and availability.
    
    Returns:
        Available TTS providers with cost information and voice counts
    """
    try:
        provider_info = TTSFactory.get_provider_info()
        available_providers = TTSFactory.get_available_providers()
        
        providers = []
        for provider_id, info in provider_info.items():
            providers.append(TTSProviderInfo(
                provider_id=provider_id,
                name=info["name"],
                available=info["available"],
                cost_per_1k_chars=info["cost_per_1k_chars"],
                voice_count=info["voice_count"],
                error=info.get("error")
            ))
        
        # Determine auto-selected provider
        auto_selected = "none"
        if available_providers:
            auto_synthesizer = TTSFactory.create_synthesizer(TTSProvider.AUTO)
            auto_selected = auto_synthesizer.provider_name.value
        
        return TTSProvidersResponse(
            providers=providers,
            auto_selected=auto_selected
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch TTS providers: {str(e)}")


@app.get("/v1/tts-providers/{provider}/voices", response_model=TTSVoicesResponse)
async def list_provider_voices(provider: str):
    """
    List available voices for a specific TTS provider.
    
    Args:
        provider: TTS provider ID (elevenlabs, google_tts)
        
    Returns:
        Available voices for the specified provider
    """
    try:
        # Validate provider
        try:
            tts_provider = TTSProvider(provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
        
        # Check if provider is available
        available_providers = TTSFactory.get_available_providers()
        if tts_provider not in available_providers:
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' is not available")
        
        # Get synthesizer and voices
        synthesizer = TTSFactory.create_synthesizer(tts_provider)
        voices = synthesizer.get_available_voices()
        
        voice_list = []
        for voice in voices:
            voice_list.append(TTSVoiceInfo(
                voice_id=voice.voice_id,
                name=voice.name,
                language=voice.language,
                gender=voice.gender,
                is_premium=voice.is_premium
            ))
        
        return TTSVoicesResponse(
            provider=provider,
            voices=voice_list,
            total_count=len(voice_list)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch voices for {provider}: {str(e)}")


@app.get("/v1/tts-cost-comparison")
async def get_tts_cost_comparison(characters: int = 1000):
    """
    Compare TTS costs between providers for given character count.
    
    Args:
        characters: Number of characters to estimate cost for
        
    Returns:
        Cost comparison between available providers
    """
    try:
        if characters <= 0 or characters > 1000000:
            raise HTTPException(status_code=400, detail="Character count must be between 1 and 1,000,000")
        
        available_providers = TTSFactory.get_available_providers()
        costs = {}
        
        for provider in available_providers:
            try:
                synthesizer = TTSFactory.create_synthesizer(provider)
                cost = synthesizer.estimate_cost(characters, "high")
                costs[provider.value] = cost
            except Exception:
                costs[provider.value] = 0.0
        
        elevenlabs_cost = costs.get("elevenlabs", 0.0)
        google_cost = costs.get("google_tts", 0.0)
        
        if elevenlabs_cost > 0 and google_cost > 0:
            savings = ((elevenlabs_cost - google_cost) / elevenlabs_cost) * 100
            recommended = "google_tts" if google_cost < elevenlabs_cost else "elevenlabs"
        else:
            savings = 0.0
            recommended = "auto"
        
        return TTSCostComparison(
            character_count=characters,
            elevenlabs_cost=elevenlabs_cost,
            google_tts_cost=google_cost,
            savings_percent=max(0, savings),
            recommended_provider=recommended
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate cost comparison: {str(e)}")


@app.get("/v1/dubbing/{job_id}")
async def get_dubbing_job_status(job_id: str):
    """
    Get dubbing job status and download links.
    
    Args:
        job_id: Dubbing job identifier
        
    Returns:
        Detailed dubbing job status with file downloads
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Dubbing job not found")
    
    job = jobs[job_id]
    
    # Check if this is a dubbing job
    if job.get("job_type") != "dubbing":
        raise HTTPException(status_code=400, detail="This is not a dubbing job")
    
    response_data = {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "error": job.get("error")
    }
    
    # Add result files if completed
    if job["status"] == "completed" and job.get("result"):
        result = job["result"]
        response_data.update({
            "transcript_file": result.get("transcript_file"),
            "translation_file": result.get("translation_file"),
            "audio_file": result.get("audio_file"),
            "video_file": result.get("video_file"),
            "cost_breakdown": result.get("cost_breakdown"),
            "processing_time_seconds": result.get("processing_time_seconds")
        })
    
    return response_data


@app.get("/v1/cost-estimate")
async def estimate_dubbing_cost(
    transcript_length: int,
    target_language: str = "en-US",
    enable_synthesis: bool = True,
    enable_video_muxing: bool = True,
    audio_quality: AudioQuality = AudioQuality.HIGH
):
    """
    Estimate costs for dubbing pipeline.
    
    Args:
        transcript_length: Character count of transcript
        target_language: Target language code
        enable_synthesis: Include TTS costs
        enable_video_muxing: Include video processing costs
        audio_quality: Audio quality level
        
    Returns:
        Detailed cost breakdown
    """
    try:
        estimate = dubbing_service.estimate_dubbing_cost(
            transcript_length=transcript_length,
            target_language=target_language,
            enable_synthesis=enable_synthesis,
            enable_video_muxing=enable_video_muxing,
            audio_quality=audio_quality.value
        )
        
        return estimate
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost estimation error: {str(e)}")


@app.get("/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """
    Get transcription job status.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Current job status and results
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return JobResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        result=job.get("result"),
        error=job.get("error")
    )


@app.get("/v1/jobs/{job_id}/download")
async def download_transcript(job_id: str):
    """
    Download transcript file for completed job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        File download response
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed" or not job.get("result"):
        raise HTTPException(status_code=400, detail="Transcript not ready")
    
    result = job["result"]
    file_path = result.get("transcript_file")
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Transcript file not found")
    
    filename = f"transcript_{job_id[:8]}.txt"
    return FileResponse(
        file_path,
        filename=filename,
        media_type='text/plain; charset=utf-8'
    )


@app.get("/v1/jobs", response_model=JobListResponse)
async def list_jobs(limit: int = 10, offset: int = 0):
    """
    List transcription jobs.
    
    Args:
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip
        
    Returns:
        List of jobs with pagination
    """
    # Get jobs from memory store (recent) and completed files
    job_list = []
    
    # Add in-memory jobs
    for job_id, job_data in jobs.items():
        job_list.append({
            "job_id": job_id,
            "status": job_data["status"],
            "created_at": job_data.get("created_at"),
            "url": job_data.get("request", {}).get("url"),
            "test_mode": job_data.get("request", {}).get("test_mode", False)
        })
    
    # Add completed jobs from filesystem
    completed_jobs = transcriber.list_completed_jobs()
    for job_file in completed_jobs:
        if len(job_list) >= limit + offset:
            break
            
        job_list.append({
            "job_id": job_file["filename"].replace("transcript_", "").replace(".txt", ""),
            "status": "completed",
            "filename": job_file["filename"],
            "size_kb": job_file["size_kb"],
            "modified": job_file["modified"]
        })
    
    # Apply pagination
    paginated_jobs = job_list[offset:offset + limit]
    
    return JobListResponse(
        jobs=paginated_jobs,
        total_count=len(job_list)
    )


@app.delete("/v1/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete transcription job and associated files.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Deletion confirmation
    """
    deleted_items = []
    
    # Remove from memory store
    if job_id in jobs:
        jobs.pop(job_id)
        deleted_items.append("job_record")
    
    # Remove transcript file if exists
    transcript_file = os.path.join(settings.data_dir, f"transcript_{job_id}.txt")
    if os.path.exists(transcript_file):
        try:
            os.remove(transcript_file)
            deleted_items.append("transcript_file")
        except Exception as e:
            print(f"Error deleting transcript file: {e}")
    
    if not deleted_items:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "message": f"Job {job_id} deleted successfully",
        "deleted_items": deleted_items
    }


async def process_transcription_job(job_id: str, url: str, test_mode: bool, 
                                  breath_detection: bool, use_vertex_ai: bool, vertex_ai_model: str = VertexAIModels.AUTO_DETECT,
                                  full_request: Optional[TranscribeRequest] = None):
    """
    Background task to process transcription job with optional dubbing.
    
    Args:
        job_id: Job identifier
        url: YouTube video URL
        test_mode: Test mode flag
        breath_detection: Breath detection flag
        use_vertex_ai: Vertex AI post-processing flag
        vertex_ai_model: Vertex AI model to use
        full_request: Full request object for dubbing parameters
    """
    def update_progress(status: str, progress: int):
        """Update job progress in store."""
        if job_id in jobs:
            jobs[job_id]["status"] = status
            jobs[job_id]["progress"] = progress
            
            # Print progress for API mode logging
            if progress >= 0:
                print(f"[API] Job {job_id[:8]}: {status} ({progress}%)")
    
    try:
        # Update job as started
        jobs[job_id]["created_at"] = None  # Could add timestamp here
        
        # Process transcription
        result = transcriber.process(
            url=url,
            test_mode=test_mode,
            breath_detection=breath_detection,
            use_vertex_ai=use_vertex_ai,
            vertex_ai_model=vertex_ai_model,
            progress_callback=update_progress
        )
        
        # Check if dubbing is enabled
        if (full_request and 
            (full_request.enable_translation or full_request.enable_synthesis or full_request.enable_video_muxing) and 
            result.get("status") == "completed"):
            
            # Convert TranscribeRequest to DubbingRequest for processing
            try:
                from pydantic import HttpUrl
                dubbing_request = DubbingRequest(
                    url=HttpUrl(url),
                    test_mode=test_mode,
                    enable_translation=full_request.enable_translation,
                    target_language=full_request.target_language,
                    translation_context=full_request.translation_context,
                    enable_synthesis=full_request.enable_synthesis,
                    voice_id=full_request.voice_id,
                    enable_video_muxing=full_request.enable_video_muxing,
                    # Use transcript from transcription result
                    existing_transcript=result.get("transcript_text", "")
                )
                
                # Process dubbing pipeline
                update_progress("dubbing_in_progress", 50)
                dubbing_result = dubbing_service.process_dubbing_job(
                    request=dubbing_request,
                    progress_callback=update_progress
                )
                
                # Merge results
                result.update({
                    "dubbing_status": dubbing_result.status,
                    "translation_file": dubbing_result.translation_file,
                    "audio_file": dubbing_result.audio_file,
                    "video_file": dubbing_result.video_file,
                    "cost_breakdown": dubbing_result.cost_breakdown
                })
                
                if dubbing_result.status == "failed":
                    result["dubbing_error"] = dubbing_result.error
                    
            except Exception as dubbing_error:
                print(f"[API] Dubbing failed for job {job_id[:8]}: {dubbing_error}")
                result["dubbing_error"] = str(dubbing_error)
                result["dubbing_status"] = "failed"
        
        # Update job with result
        jobs[job_id]["result"] = result
        jobs[job_id]["status"] = result["status"]
        jobs[job_id]["progress"] = 100 if result["status"] == "completed" else 0
        
        if result["status"] == "failed":
            jobs[job_id]["error"] = result.get("error", "Unknown error")
        
        print(f"[API] Job {job_id[:8]} completed: {result['status']}")
        
    except Exception as e:
        error_msg = str(e)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = error_msg
        jobs[job_id]["progress"] = 0
        
        print(f"[API] Job {job_id[:8]} failed: {error_msg}")


async def process_dubbing_background(job_id: str, request: DubbingRequest):
    """
    Background task to process complete dubbing job.
    
    Args:
        job_id: Job identifier
        request: Complete dubbing request parameters
    """
    def update_progress(status: str, progress: int):
        """Update dubbing job progress in store."""
        if job_id in jobs:
            jobs[job_id]["status"] = status
            jobs[job_id]["progress"] = progress
            print(f"[API] Dubbing {job_id[:8]}: {status} ({progress}%)")
    
    try:
        # Update job as started
        jobs[job_id]["created_at"] = None  # Could add timestamp
        
        # Process full dubbing pipeline
        result = dubbing_service.process_dubbing_job(
            request=request,
            progress_callback=update_progress
        )
        
        # Update job with result
        jobs[job_id]["result"] = result.dict()
        jobs[job_id]["status"] = result.status
        jobs[job_id]["progress"] = 100 if result.status == "completed" else 0
        
        if result.status == "failed":
            jobs[job_id]["error"] = result.error or "Unknown dubbing error"
        
        print(f"[API] Dubbing {job_id[:8]} completed: {result.status}")
        
    except Exception as e:
        error_msg = str(e)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = error_msg
        jobs[job_id]["progress"] = 0
        
        print(f"[API] Dubbing {job_id[:8]} failed: {error_msg}")


# Optional: Add admin endpoints for monitoring
@app.get("/admin/stats")
async def get_service_stats():
    """Get service statistics (admin endpoint)."""
    try:
        completed_jobs = transcriber.list_completed_jobs()
        
        active_jobs = sum(1 for job in jobs.values() 
                         if job["status"] in ["queued", "downloading", "converting", "transcribing"])
        
        completed_count = len(completed_jobs)
        failed_jobs = sum(1 for job in jobs.values() if job["status"] == "failed")
        
        return {
            "active_jobs": active_jobs,
            "completed_jobs": completed_count,
            "failed_jobs": failed_jobs,
            "total_memory_jobs": len(jobs),
            "data_dir": settings.data_dir,
            "recent_jobs": list(jobs.keys())[-5:] if jobs else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        access_log=True
    )