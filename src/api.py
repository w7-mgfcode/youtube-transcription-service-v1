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


# Pydantic models for API
class TranscribeRequest(BaseModel):
    """Request model for transcription."""
    url: HttpUrl
    test_mode: bool = False
    breath_detection: bool = True
    use_vertex_ai: bool = False
    vertex_ai_model: Optional[str] = VertexAIModels.AUTO_DETECT
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
                "test_mode": True,
                "breath_detection": True,
                "use_vertex_ai": True,
                "vertex_ai_model": "gemini-2.0-flash"
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


# FastAPI app setup
app = FastAPI(
    title="YouTube Transcribe Service",
    description="YouTube video transcription service with Hungarian language support",
    version="1.0.0",
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
        request.vertex_ai_model
    )
    
    return JobResponse(job_id=job_id, status="queued")


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
                                  breath_detection: bool, use_vertex_ai: bool, vertex_ai_model: str = VertexAIModels.AUTO_DETECT):
    """
    Background task to process transcription job.
    
    Args:
        job_id: Job identifier
        url: YouTube video URL
        test_mode: Test mode flag
        breath_detection: Breath detection flag
        use_vertex_ai: Vertex AI post-processing flag
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