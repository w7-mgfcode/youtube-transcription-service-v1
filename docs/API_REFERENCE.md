# API Reference Guide

## 🌐 Complete REST API for YouTube Transcription & Dubbing Service

This document provides a comprehensive reference for all API endpoints. For interactive documentation, visit: http://localhost:8000/docs

---

## 🚀 Base URL and Authentication

**Base URL:** `http://localhost:8000` (development)  
**Authentication:** Currently none (add API keys in production)  
**Content-Type:** `application/json` for all POST requests

---

## 📋 Core Endpoints

### 1. Health and Status

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "dubbing_enabled": true,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

#### Service Statistics
```http
GET /admin/stats
```

---

## 🎬 Dubbing Pipeline Endpoints

### 2. Complete Dubbing Pipeline

#### Full Dubbing Job
```http
POST /v1/dub
```

**Request Body (Google TTS - Recommended 94% Savings):**
```json
{
  "url": "https://youtube.com/watch?v=example",
  "test_mode": false,
  "enable_translation": true,
  "target_language": "en-US",
  "translation_context": "educational",
  "target_audience": "students",
  "desired_tone": "clear", 
  "translation_quality": "high",
  "enable_synthesis": true,
  "tts_provider": "google_tts",
  "voice_id": "en-US-Neural2-F",
  "enable_video_muxing": true,
  "video_format": "mp4",
  "max_cost_usd": 10.0
}
```

**Request Body (ElevenLabs - Premium Quality):**
```json
{
  "url": "https://youtube.com/watch?v=example",
  "test_mode": false,
  "enable_translation": true,
  "target_language": "en-US",
  "translation_context": "educational",
  "target_audience": "students",
  "desired_tone": "clear",
  "translation_quality": "high",
  "enable_synthesis": true,
  "tts_provider": "elevenlabs",
  "voice_id": "21m00Tcm4TlvDq8ikWAM",
  "audio_quality": "high",
  "enable_video_muxing": true,
  "video_format": "mp4",
  "max_cost_usd": 10.0
}
```

**Request Body (Auto Provider - Smart Selection):**
```json
{
  "url": "https://youtube.com/watch?v=example",
  "test_mode": false,
  "enable_translation": true,
  "target_language": "en-US",
  "translation_context": "educational",
  "enable_synthesis": true,
  "tts_provider": "auto",
  "enable_video_muxing": true,
  "video_format": "mp4",
  "max_cost_usd": 10.0
}
```

**Parameters:**
- `tts_provider` (optional): "google_tts", "elevenlabs", or "auto". Default: "auto"
- `voice_id` (required for specific providers): Voice identifier
- `audio_quality` (optional, ElevenLabs only): "low", "medium", "high". Default: "medium"

**Response:**
```json
{
  "job_id": "dub-abc123",
  "status": "processing",
  "progress": 15,
  "current_stage": "translation",
  "estimated_cost": {
    "translation_cost": 0.002,
    "synthesis_cost": 2.45,
    "total_cost": 2.452
  },
  "created_at": "2025-01-15T10:30:00Z"
}
```

### 3. Translation Services

#### Translate Hungarian Transcript
```http
POST /v1/translate
```

**Request Body:**
```json
{
  "transcript_text": "[00:00:01] Magyar szöveg példa\n[00:00:05] Második sor",
  "target_language": "en-US",
  "translation_context": "educational",
  "target_audience": "students",
  "desired_tone": "academic",
  "translation_quality": "high",
  "preserve_timing": true
}
```

**Response:**
```json
{
  "job_id": "trans-def456",
  "success": true,
  "translated_text": "[00:00:01] Hungarian text example\n[00:00:05] Second line",
  "original_length": 47,
  "translated_length": 52,
  "processing_time": 3.2,
  "cost_usd": 0.0003,
  "context": "educational",
  "model_used": "gemini-2.0-flash"
}
```

### 4. Voice Synthesis Services

#### Synthesize Audio from Text
```http
POST /v1/synthesize
```

**Request Body:**
```json
{
  "script_text": "[00:00:01] English text to synthesize\n[00:00:05] Second line",
  "voice_id": "21m00Tcm4TlvDq8ikWAM",
  "model": "eleven_multilingual_v2",
  "audio_quality": "high",
  "optimize_streaming_latency": false,
  "output_format": "mp3_44100_128"
}
```

**Response:**
```json
{
  "job_id": "synth-ghi789",
  "success": true,
  "audio_file": "/app/data/audio_ghi789.mp3",
  "duration_seconds": 12.5,
  "character_count": 52,
  "cost_usd": 0.156,
  "voice_id": "21m00Tcm4TlvDq8ikWAM",
  "processing_time": 8.3
}
```

### 5. TTS Provider Management

#### Get Available TTS Providers
```http
GET /v1/tts-providers
```

**Response:**
```json
{
  "providers": [
    {
      "provider_id": "google_tts",
      "name": "Google Cloud Text-to-Speech",
      "status": "available",
      "cost_per_1k_chars": 0.016,
      "voice_count": 1616,
      "languages_supported": 40,
      "quality_tiers": ["standard", "wavenet", "neural2", "studio"],
      "recommended": true,
      "savings_vs_elevenlabs": "94%"
    },
    {
      "provider_id": "elevenlabs",
      "name": "ElevenLabs",
      "status": "available",
      "cost_per_1k_chars": 0.30,
      "voice_count": 25,
      "languages_supported": 29,
      "quality_tiers": ["low", "medium", "high"],
      "recommended": false,
      "premium_quality": true
    },
    {
      "provider_id": "auto",
      "name": "Auto Selection (Cost Optimized)",
      "status": "available",
      "description": "Automatically selects the most cost-effective provider",
      "cost_savings": "90%+",
      "recommended": true
    }
  ]
}
```

#### Get Provider-Specific Voices
```http
GET /v1/tts-providers/{provider}/voices
```

**Path Parameters:**
- `provider`: "google_tts" or "elevenlabs"

**Query Parameters:**
- `language` (optional): Language code (e.g., "hu-HU", "en-US")
- `gender` (optional): "male" or "female" (ElevenLabs only)
- `voice_type` (optional): "neural2", "wavenet", "studio" (Google TTS)

**Example - Google TTS Hungarian voices:**
```http
GET /v1/tts-providers/google_tts/voices?language=hu-HU
```

**Response:**
```json
{
  "provider": "google_tts",
  "language": "hu-HU", 
  "voices": [
    {
      "voice_id": "hu-HU-Neural2-A",
      "name": "Hungarian Neural2 Female A",
      "gender": "female",
      "language": "hu-HU",
      "voice_type": "neural2",
      "cost_per_1k_chars": 0.016,
      "recommended": true,
      "description": "Clear, natural, professional Hungarian female voice"
    },
    {
      "voice_id": "hu-HU-Neural2-B", 
      "name": "Hungarian Neural2 Male B",
      "gender": "male",
      "language": "hu-HU",
      "voice_type": "neural2",
      "cost_per_1k_chars": 0.016,
      "description": "Authoritative, clear Hungarian male voice"
    },
    {
      "voice_id": "hu-HU-Wavenet-A",
      "name": "Hungarian WaveNet Female A",
      "gender": "female", 
      "language": "hu-HU",
      "voice_type": "wavenet",
      "cost_per_1k_chars": 0.016,
      "description": "Warm, conversational Hungarian female voice"
    }
  ],
  "total_count": 8
}
```

**Example - ElevenLabs voices:**
```http
GET /v1/tts-providers/elevenlabs/voices?gender=female
```

**Response:**
```json
{
  "provider": "elevenlabs",
  "voices": [
    {
      "voice_id": "21m00Tcm4TlvDq8ikWAM",
      "name": "Rachel",
      "gender": "female",
      "accent": "american",
      "description": "calm, clear, professional", 
      "use_case": "educational",
      "cost_per_1k_chars": 0.30,
      "preview_url": "https://api.elevenlabs.io/v1/voices/.../preview.mp3",
      "google_tts_equivalent": "en-US-Neural2-F"
    },
    {
      "voice_id": "EXAVITQu4vr4xnSDxMaL",
      "name": "Bella",
      "gender": "female",
      "accent": "american",
      "description": "friendly, approachable, versatile",
      "use_case": "lifestyle",
      "cost_per_1k_chars": 0.30,
      "preview_url": "https://api.elevenlabs.io/v1/voices/.../preview.mp3", 
      "google_tts_equivalent": "en-US-Neural2-G"
    }
  ],
  "total_count": 12
}
```

#### Compare TTS Costs
```http
GET /v1/tts-cost-comparison
```

**Query Parameters:**
- `text` (required): Sample text to estimate costs for
- `providers` (optional): Comma-separated list ("google_tts,elevenlabs")
- `target_language` (optional): Language code, default "en-US"

**Example:**
```http
GET /v1/tts-cost-comparison?text=Hello world, this is a test&providers=google_tts,elevenlabs&target_language=en-US
```

**Response:**
```json
{
  "text": "Hello world, this is a test", 
  "character_count": 26,
  "target_language": "en-US",
  "comparison": [
    {
      "provider": "google_tts",
      "voice_recommendation": "en-US-Neural2-F",
      "cost": 0.0004,
      "quality": "neural2",
      "processing_time_estimate": "2s"
    },
    {
      "provider": "elevenlabs",
      "voice_recommendation": "21m00Tcm4TlvDq8ikWAM",
      "cost": 0.0078,
      "quality": "high",
      "processing_time_estimate": "3s"
    }
  ],
  "savings": {
    "cheapest_provider": "google_tts",
    "savings_amount": 0.0074,
    "savings_percentage": 94.9
  },
  "recommendation": "google_tts"
}
```

### 6. Legacy Voice Management (ElevenLabs Only)

#### Get Available Voices (Legacy Endpoint)
```http
GET /v1/voices
```
*Note: This endpoint returns ElevenLabs voices only for backward compatibility. Use `/v1/tts-providers/{provider}/voices` for multi-provider support.*

**Query Parameters:**
- `gender` (optional): "male" or "female"
- `language` (optional): "en", "de", "fr", etc.
- `use_case` (optional): "narration", "conversation", etc.

**Response:**
```json
{
  "voices": [
    {
      "voice_id": "21m00Tcm4TlvDq8ikWAM",
      "name": "Rachel",
      "labels": {
        "accent": "american",
        "description": "calm",
        "age": "young",
        "gender": "female",
        "use_case": "narration"
      },
      "preview_url": "https://api.elevenlabs.io/v1/voices/.../preview.mp3"
    },
    {
      "voice_id": "pNInz6obpgDQGcFmaJgB",
      "name": "Adam",
      "labels": {
        "accent": "american", 
        "description": "deep",
        "age": "middle aged",
        "gender": "male",
        "use_case": "narration"
      },
      "preview_url": "https://api.elevenlabs.io/v1/voices/.../preview.mp3"
    }
  ],
  "total_count": 12
}
```

---

## 📊 Job Management Endpoints

### 6. Job Status and Results

#### Get Dubbing Job Status
```http
GET /v1/dubbing/{job_id}
```

**Response (In Progress):**
```json
{
  "job_id": "dub-abc123",
  "status": "translating",
  "progress": 45,
  "current_stage": "translation",
  "stages_completed": ["transcription"],
  "estimated_time_remaining": 120,
  "created_at": "2025-01-15T10:30:00Z",
  "started_at": "2025-01-15T10:30:15Z"
}
```

**Response (Completed):**
```json
{
  "job_id": "dub-abc123", 
  "status": "completed",
  "progress": 100,
  "transcript_file": "/app/data/transcript_abc123.txt",
  "translation_file": "/app/data/translation_abc123_en.txt",
  "audio_file": "/app/data/audio_abc123_en.mp3",
  "video_file": "/app/data/dubbed_abc123_en.mp4",
  "cost_breakdown": {
    "translation_cost": 0.002,
    "synthesis_cost": 2.45,
    "total_cost": 2.452
  },
  "processing_time_seconds": 145,
  "completed_at": "2025-01-15T10:32:30Z"
}
```

#### Download Job Results
```http
GET /v1/dubbing/{job_id}/download?file_type={type}
```

**Query Parameters:**
- `file_type`: "transcript", "translation", "audio", "video"

**Response:** File download (binary data)

---

## 💰 Cost Estimation Endpoints

### 7. Cost Calculation

#### Estimate Dubbing Costs
```http
GET /v1/cost-estimate
```

**Query Parameters:**
- `transcript_length` (required): Character count
- `target_language` (required): Target language code
- `enable_synthesis` (optional): Boolean, default false
- `enable_video_muxing` (optional): Boolean, default false  
- `tts_provider` (optional): "google_tts", "elevenlabs", "auto". Default: "auto"
- `audio_quality` (optional): "low", "medium", "high" (ElevenLabs only)

**Example (Google TTS - 94% Savings):**
```http
GET /v1/cost-estimate?transcript_length=2000&target_language=en-US&enable_synthesis=true&tts_provider=google_tts
```

**Example (ElevenLabs):**
```http
GET /v1/cost-estimate?transcript_length=2000&target_language=en-US&enable_synthesis=true&tts_provider=elevenlabs&audio_quality=high
```

**Example (Auto Provider):**
```http
GET /v1/cost-estimate?transcript_length=2000&target_language=en-US&enable_synthesis=true&tts_provider=auto
```

**Response:**
```json
{
  "character_count": 2000,
  "translation_cost": 0.0004,
  "synthesis_cost": 0.60,
  "video_muxing_cost": 0,
  "total_cost": 0.6004,
  "estimated_time_seconds": 90,
  "breakdown": {
    "translation": {
      "rate_per_million_chars": 20.0,
      "characters": 2000,
      "cost": 0.0004
    },
    "synthesis": {
      "rate_per_thousand_chars": 0.30,
      "characters": 2000, 
      "quality_multiplier": 1.0,
      "cost": 0.60
    }
  }
}
```

---

## 📝 Legacy Transcription Endpoints

### 8. Enhanced Transcription Service

#### Submit Transcription Job (with optional dubbing)
```http
POST /v1/transcribe
```

**Request Body (Basic):**
```json
{
  "url": "https://youtube.com/watch?v=example",
  "test_mode": true,
  "breath_detection": true,
  "use_vertex_ai": true,
  "vertex_ai_model": "gemini-2.0-flash"
}
```

**Request Body (With Dubbing):**
```json
{
  "url": "https://youtube.com/watch?v=example",
  "test_mode": false,
  "breath_detection": true,
  "use_vertex_ai": true,
  "vertex_ai_model": "gemini-2.0-flash",
  "enable_translation": true,
  "target_language": "en-US", 
  "translation_context": "casual",
  "enable_synthesis": true,
  "voice_id": "21m00Tcm4TlvDq8ikWAM",
  "enable_video_muxing": false
}
```

#### Get Job Status
```http
GET /v1/jobs/{job_id}
```

#### List All Jobs
```http
GET /v1/jobs
```

**Query Parameters:**
- `limit` (optional): Max results, default 50
- `offset` (optional): Pagination offset, default 0
- `status` (optional): Filter by status

#### Download Transcript
```http
GET /v1/jobs/{job_id}/download
```

#### Delete Job
```http
DELETE /v1/jobs/{job_id}
```

---

## 🔧 API Models and Enums

### Translation Contexts
- `legal`: Legal content with precise terminology
- `spiritual`: Religious/motivational content  
- `marketing`: Promotional/advertising content
- `scientific`: Technical/research content
- `educational`: Teaching/tutorial content
- `news`: Journalistic/factual content
- `casual`: Conversational/informal content

### Audio Quality Options
- `low`: Fastest processing, lower quality
- `medium`: Balanced speed and quality
- `high`: Best quality, slower processing

### Video Formats
- `mp4`: MP4 format (recommended)
- `webm`: WebM format
- `avi`: AVI format

### Job Statuses
- `pending`: Job queued for processing
- `transcribing`: Transcription in progress
- `translating`: Translation in progress  
- `synthesizing`: Audio synthesis in progress
- `muxing`: Video processing in progress
- `completed`: Job finished successfully
- `failed`: Job failed with errors
- `cancelled`: Job cancelled by user

---

## ⚡ Usage Examples

### Python SDK Example

```python
import httpx
import time
from typing import Optional

class DubbingClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=300)
    
    def create_dubbing_job(self, 
                          url: str,
                          target_language: str = "en-US",
                          voice_id: str = "21m00Tcm4TlvDq8ikWAM",
                          context: str = "casual") -> str:
        """Create a new dubbing job and return job ID."""
        
        request = {
            "url": url,
            "enable_translation": True,
            "target_language": target_language,
            "translation_context": context,
            "enable_synthesis": True,
            "voice_id": voice_id,
            "enable_video_muxing": True,
            "video_format": "mp4"
        }
        
        response = self.client.post(f"{self.base_url}/v1/dub", json=request)
        response.raise_for_status()
        
        return response.json()["job_id"]
    
    def wait_for_completion(self, job_id: str, timeout: int = 1800) -> dict:
        """Wait for job completion and return final result."""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = self.client.get(f"{self.base_url}/v1/dubbing/{job_id}")
            response.raise_for_status()
            
            data = response.json()
            
            if data["status"] == "completed":
                return data
            elif data["status"] == "failed":
                raise Exception(f"Job failed: {data.get('error')}")
            
            print(f"Progress: {data['progress']}% - {data['status']}")
            time.sleep(10)
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")
    
    def download_file(self, job_id: str, file_type: str, output_path: str):
        """Download a result file from completed job."""
        
        url = f"{self.base_url}/v1/dubbing/{job_id}/download"
        params = {"file_type": file_type}
        
        with self.client.stream("GET", url, params=params) as response:
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

# Usage
client = DubbingClient()

# Create dubbing job
job_id = client.create_dubbing_job(
    url="https://youtube.com/watch?v=example",
    target_language="en-US",
    voice_id="21m00Tcm4TlvDq8ikWAM",
    context="educational"
)

print(f"Created job: {job_id}")

# Wait for completion
result = client.wait_for_completion(job_id)
print(f"Job completed! Total cost: ${result['cost_breakdown']['total_cost']:.2f}")

# Download results
client.download_file(job_id, "video", f"dubbed_{job_id}.mp4")
client.download_file(job_id, "audio", f"audio_{job_id}.mp3")

print("Files downloaded successfully!")
```

### cURL Batch Processing

```bash
#!/bin/bash

# Array of video URLs
urls=(
  "https://youtube.com/watch?v=video1"
  "https://youtube.com/watch?v=video2" 
  "https://youtube.com/watch?v=video3"
)

# Submit all jobs
job_ids=()
for url in "${urls[@]}"; do
  response=$(curl -s -X POST http://localhost:8000/v1/dub \
    -H "Content-Type: application/json" \
    -d "{
      \"url\": \"$url\",
      \"enable_translation\": true,
      \"target_language\": \"en-US\",
      \"translation_context\": \"casual\",
      \"enable_synthesis\": true,
      \"voice_id\": \"21m00Tcm4TlvDq8ikWAM\",
      \"enable_video_muxing\": true
    }")
  
  job_id=$(echo $response | jq -r '.job_id')
  job_ids+=("$job_id")
  echo "Submitted job: $job_id for $url"
done

# Wait for all jobs to complete
echo "Waiting for jobs to complete..."
for job_id in "${job_ids[@]}"; do
  while true; do
    status=$(curl -s http://localhost:8000/v1/dubbing/$job_id | jq -r '.status')
    
    if [ "$status" = "completed" ]; then
      echo "✓ Job $job_id completed"
      
      # Download result
      curl -s "http://localhost:8000/v1/dubbing/$job_id/download?file_type=video" \
        -o "dubbed_${job_id}.mp4"
      
      break
    elif [ "$status" = "failed" ]; then
      echo "✗ Job $job_id failed"
      break
    else
      echo "Job $job_id status: $status"
      sleep 30
    fi
  done
done

echo "All jobs processed!"
```

---

## 🚨 Error Handling

### HTTP Status Codes

- **200 OK**: Request successful
- **202 Accepted**: Job accepted for processing
- **400 Bad Request**: Invalid request data
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation error
- **429 Too Many Requests**: Rate limit exceeded  
- **500 Internal Server Error**: Server error

### Error Response Format

```json
{
  "detail": "Error description",
  "error_code": "DUBBING_FAILED",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Common Error Codes

- `INVALID_YOUTUBE_URL`: Invalid or inaccessible YouTube URL
- `TRANSLATION_FAILED`: Translation service error
- `SYNTHESIS_FAILED`: Voice synthesis error
- `VIDEO_MUXING_FAILED`: Video processing error
- `COST_LIMIT_EXCEEDED`: Job cost exceeds maximum limit
- `VOICE_NOT_FOUND`: Invalid voice ID specified
- `QUOTA_EXCEEDED`: API quota exceeded

---

## 📈 Rate Limits and Quotas

### Current Limits (Development)
- **Concurrent Jobs**: 5 per service instance
- **Request Rate**: No limit (add rate limiting in production)
- **File Size**: 1GB per video
- **Video Length**: 30 minutes maximum
- **Cost Per Job**: $50 maximum (configurable)

### Production Recommendations
- Implement API key authentication
- Add rate limiting (e.g., 100 requests/hour per key)
- Set up monitoring and alerting
- Configure auto-scaling for high load

---

## 🔗 Related Documentation

- [Complete Dubbing Guide](./DUBBING_GUIDE.md): Detailed usage guide
- [Quick Start Guide](./QUICK_START.md): Getting started
- [Interactive API Docs](http://localhost:8000/docs): Swagger UI
- [Voice Profile Guide](./VOICE_GUIDE.md): Voice selection help

---

**API Documentation Complete! 🚀**

For the most up-to-date API schema, always refer to the interactive documentation at http://localhost:8000/docs