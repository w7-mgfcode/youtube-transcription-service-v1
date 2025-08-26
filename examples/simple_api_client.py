#!/usr/bin/env python3
"""
Simple API client example for YouTube Transcription Service.

Usage:
    python examples/simple_api_client.py "https://youtube.com/watch?v=dQw4w9WgXcQ"
"""

import sys
import time
import httpx
from typing import Optional


def transcribe_video(url: str, 
                    test_mode: bool = True,
                    use_vertex_ai: bool = True,
                    vertex_ai_model: str = "gemini-2.0-flash",
                    api_base: str = "http://localhost:8000") -> Optional[str]:
    """
    Transcribe a YouTube video using the API.
    
    Args:
        url: YouTube video URL
        test_mode: Process only first 60 seconds
        use_vertex_ai: Enable Vertex AI post-processing
        vertex_ai_model: Which Vertex AI model to use
        api_base: API base URL
        
    Returns:
        Transcript text or None on failure
    """
    print(f"🎥 Transcribing: {url}")
    
    # Submit transcription job
    try:
        response = httpx.post(f"{api_base}/v1/transcribe", json={
            "url": url,
            "test_mode": test_mode,
            "breath_detection": True,
            "use_vertex_ai": use_vertex_ai,
            "vertex_ai_model": vertex_ai_model
        })
        response.raise_for_status()
        
        job_data = response.json()
        job_id = job_data["job_id"]
        print(f"📋 Job submitted: {job_id}")
        
    except Exception as e:
        print(f"❌ Failed to submit job: {e}")
        return None
    
    # Poll for completion
    print("⏳ Waiting for completion...")
    while True:
        try:
            response = httpx.get(f"{api_base}/v1/jobs/{job_id}")
            response.raise_for_status()
            
            job_status = response.json()
            status = job_status["status"]
            progress = job_status["progress"]
            
            print(f"📊 Status: {status} ({progress}%)")
            
            if status == "completed":
                print("✅ Transcription completed!")
                
                # Download transcript
                response = httpx.get(f"{api_base}/v1/jobs/{job_id}/download")
                response.raise_for_status()
                
                transcript = response.text
                print(f"📄 Transcript length: {len(transcript)} characters")
                
                return transcript
                
            elif status == "failed":
                error = job_status.get("error", "Unknown error")
                print(f"❌ Transcription failed: {error}")
                return None
            
            time.sleep(5)
            
        except Exception as e:
            print(f"❌ Error checking job status: {e}")
            return None


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python simple_api_client.py <youtube_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Check if API is available
    try:
        response = httpx.get("http://localhost:8000/health")
        response.raise_for_status()
        print("✅ API is available")
    except Exception as e:
        print(f"❌ API not available: {e}")
        print("💡 Start the API with: docker compose up -d")
        sys.exit(1)
    
    # Transcribe the video
    transcript = transcribe_video(url)
    
    if transcript:
        # Save to file
        filename = f"transcript_{int(time.time())}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(transcript)
        
        print(f"💾 Saved to: {filename}")
        
        # Show preview
        print("\n--- PREVIEW ---")
        print(transcript[:500] + "..." if len(transcript) > 500 else transcript)
    else:
        print("❌ Transcription failed")
        sys.exit(1)


if __name__ == "__main__":
    main()