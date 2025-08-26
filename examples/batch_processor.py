#!/usr/bin/env python3
"""
Batch processing example for multiple YouTube videos.

Usage:
    python examples/batch_processor.py urls.txt
"""

import sys
import time
import csv
import httpx
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed


class BatchTranscriber:
    """Batch transcription processor."""
    
    def __init__(self, api_base: str = "http://localhost:8000"):
        self.api_base = api_base
        self.client = httpx.Client(timeout=30.0)
    
    def submit_job(self, url: str, vertex_ai_model: str = "auto-detect") -> Dict[str, Any]:
        """Submit a transcription job."""
        try:
            response = self.client.post(f"{self.api_base}/v1/transcribe", json={
                "url": url,
                "test_mode": False,
                "breath_detection": True,
                "use_vertex_ai": True,
                "vertex_ai_model": vertex_ai_model
            })
            response.raise_for_status()
            
            job_data = response.json()
            return {
                "url": url,
                "job_id": job_data["job_id"],
                "status": "submitted",
                "model": vertex_ai_model
            }
        except Exception as e:
            return {
                "url": url,
                "job_id": None,
                "status": "failed",
                "error": str(e)
            }
    
    def check_job_status(self, job_id: str) -> Dict[str, Any]:
        """Check job status."""
        try:
            response = self.client.get(f"{self.api_base}/v1/jobs/{job_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def download_transcript(self, job_id: str, filename: str) -> bool:
        """Download completed transcript."""
        try:
            response = self.client.get(f"{self.api_base}/v1/jobs/{job_id}/download")
            response.raise_for_status()
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.text)
            return True
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False
    
    def process_batch(self, urls: List[str], max_workers: int = 3) -> List[Dict[str, Any]]:
        """Process multiple URLs in batch."""
        print(f"🚀 Starting batch processing of {len(urls)} URLs...")
        
        # Submit all jobs
        jobs = []
        print("\n📋 Submitting jobs...")
        for i, url in enumerate(urls, 1):
            print(f"  {i}/{len(urls)}: Submitting {url}")
            job = self.submit_job(url)
            jobs.append(job)
            
            if job["status"] == "submitted":
                print(f"    ✅ Job ID: {job['job_id']}")
            else:
                print(f"    ❌ Failed: {job.get('error', 'Unknown error')}")
        
        successful_jobs = [j for j in jobs if j["status"] == "submitted"]
        print(f"\n📊 Submitted {len(successful_jobs)}/{len(jobs)} jobs successfully")
        
        if not successful_jobs:
            return jobs
        
        # Monitor completion
        print("\n⏳ Monitoring job completion...")
        completed = []
        
        while successful_jobs:
            for job in successful_jobs[:]:
                status_data = self.check_job_status(job["job_id"])
                job_status = status_data.get("status", "unknown")
                
                if job_status == "completed":
                    # Download transcript
                    video_id = job["url"].split("=")[-1][:11]  # Extract video ID
                    filename = f"transcript_{video_id}_{job['job_id'][:8]}.txt"
                    
                    if self.download_transcript(job["job_id"], filename):
                        job.update({
                            "status": "completed",
                            "filename": filename,
                            "word_count": status_data.get("result", {}).get("word_count", 0)
                        })
                        completed.append(job)
                        successful_jobs.remove(job)
                        
                        print(f"✅ Completed: {job['url']} -> {filename}")
                    else:
                        job["status"] = "download_failed"
                        successful_jobs.remove(job)
                
                elif job_status == "failed":
                    job.update({
                        "status": "failed",
                        "error": status_data.get("error", "Processing failed")
                    })
                    successful_jobs.remove(job)
                    
                    print(f"❌ Failed: {job['url']} - {job['error']}")
            
            if successful_jobs:
                print(f"⏳ Waiting... {len(successful_jobs)} jobs still processing")
                time.sleep(10)
        
        # Combine all results
        all_results = completed + [j for j in jobs if j["status"] != "submitted"]
        
        print(f"\n✅ Batch processing complete!")
        print(f"   📊 Total: {len(jobs)} jobs")
        print(f"   ✅ Successful: {len(completed)}")
        print(f"   ❌ Failed: {len(jobs) - len(completed)}")
        
        return all_results
    
    def close(self):
        """Close HTTP client."""
        self.client.close()


def load_urls_from_file(filename: str) -> List[str]:
    """Load URLs from text file."""
    urls = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if url and not url.startswith('#'):
                urls.append(url)
    return urls


def save_results_to_csv(results: List[Dict[str, Any]], filename: str):
    """Save results to CSV file."""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'url', 'status', 'job_id', 'filename', 'word_count', 'model', 'error'
        ])
        writer.writeheader()
        writer.writerows(results)


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python batch_processor.py <urls_file>")
        print("\nExample urls.txt:")
        print("https://youtube.com/watch?v=dQw4w9WgXcQ")
        print("https://youtube.com/watch?v=L_jWHffIx5E")
        print("# Comments start with #")
        sys.exit(1)
    
    urls_file = sys.argv[1]
    
    if not Path(urls_file).exists():
        print(f"❌ File not found: {urls_file}")
        sys.exit(1)
    
    # Load URLs
    urls = load_urls_from_file(urls_file)
    if not urls:
        print(f"❌ No URLs found in {urls_file}")
        sys.exit(1)
    
    print(f"📁 Loaded {len(urls)} URLs from {urls_file}")
    
    # Check API availability
    try:
        response = httpx.get("http://localhost:8000/health")
        response.raise_for_status()
        print("✅ API is available")
    except Exception as e:
        print(f"❌ API not available: {e}")
        print("💡 Start the API with: docker compose up -d")
        sys.exit(1)
    
    # Process batch
    transcriber = BatchTranscriber()
    try:
        results = transcriber.process_batch(urls)
        
        # Save results
        results_file = f"batch_results_{int(time.time())}.csv"
        save_results_to_csv(results, results_file)
        print(f"💾 Results saved to: {results_file}")
        
    finally:
        transcriber.close()


if __name__ == "__main__":
    main()