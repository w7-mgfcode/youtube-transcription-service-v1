# Usage Examples

## 🆕 Chunking Examples

### Get Chunking Estimate
```python
import httpx

# Get estimate for long transcript
response = httpx.post("http://localhost:8000/v1/chunking-estimate", json={
    "transcript_text": "Your very long transcript text here..." * 1000
})

estimate = response.json()
print(f"Needs chunking: {estimate['needs_chunking']}")
print(f"Chunks: {estimate['total_chunks']}")
print(f"Estimated cost: ${estimate['estimated_cost_usd']:.4f}")
print(f"Estimated time: {estimate['estimated_time_seconds']:.1f}s")
```

### CLI with Long Video
```bash
# CLI automatically detects long transcripts and shows estimates
docker exec -it v1-transcribe python src/main.py

# Example output for long video:
# 📑 Hosszú átirat észlelve - Chunked feldolgozás lesz alkalmazva
#    ├─ Eredeti hossz: 25000 karakter
#    ├─ Chunks száma: 7
#    ├─ Becsült feldolgozási idő: 12.5 mp
#    └─ Becsült költség: $0.0025
# Folytatod? (i/n) [i]:
```

## API Usage Examples

### Python Client
```python
import httpx
import time

# Submit transcription job
response = httpx.post("http://localhost:8000/v1/transcribe", json={
    "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "test_mode": True,  # Process only 60 seconds
    "breath_detection": True,
    "use_vertex_ai": True,
    "vertex_ai_model": "gemini-2.5-flash"  # or "auto-detect"
})

job_id = response.json()["job_id"]
print(f"Job submitted: {job_id}")

# Poll for completion
while True:
    status = httpx.get(f"http://localhost:8000/v1/jobs/{job_id}")
    job_status = status.json()
    
    print(f"Status: {job_status['status']} ({job_status['progress']}%)")
    
    if job_status["status"] == "completed":
        # Download transcript
        transcript = httpx.get(f"http://localhost:8000/v1/jobs/{job_id}/download")
        
        with open("transcript.txt", "w", encoding="utf-8") as f:
            f.write(transcript.text)
        
        print("Transcript saved!")
        break
    elif job_status["status"] == "failed":
        print(f"Error: {job_status['error']}")
        break
    
    time.sleep(5)
```

### JavaScript Client
```javascript
async function transcribeVideo(url) {
    // Submit job
    const response = await fetch('http://localhost:8000/v1/transcribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            url: url,
            test_mode: false,
            breath_detection: true,
            use_vertex_ai: true,
            vertex_ai_model: "gemini-2.0-flash"
        })
    });
    
    const { job_id } = await response.json();
    console.log('Job submitted:', job_id);
    
    // Poll for completion
    while (true) {
        const status = await fetch(`http://localhost:8000/v1/jobs/${job_id}`);
        const jobStatus = await status.json();
        
        console.log(`Status: ${jobStatus.status} (${jobStatus.progress}%)`);
        
        if (jobStatus.status === 'completed') {
            // Download transcript
            const transcript = await fetch(`http://localhost:8000/v1/jobs/${job_id}/download`);
            const text = await transcript.text();
            
            // Save or display transcript
            console.log('Transcript ready!');
            return text;
        } else if (jobStatus.status === 'failed') {
            throw new Error(jobStatus.error);
        }
        
        await new Promise(resolve => setTimeout(resolve, 5000));
    }
}

// Usage
transcribeVideo('https://youtube.com/watch?v=dQw4w9WgXcQ')
    .then(transcript => console.log('Done!'))
    .catch(error => console.error('Error:', error));
```

### curl Commands
```bash
# Submit job
curl -X POST http://localhost:8000/v1/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "test_mode": true,
    "breath_detection": true,
    "use_vertex_ai": true,
    "vertex_ai_model": "auto-detect"
  }'

# Check status (replace JOB_ID)
curl http://localhost:8000/v1/jobs/JOB_ID

# Download transcript
curl http://localhost:8000/v1/jobs/JOB_ID/download -o transcript.txt

# List jobs
curl http://localhost:8000/v1/jobs

# Health check
curl http://localhost:8000/health

# Vertex AI model selection examples
curl -X POST http://localhost:8000/v1/transcribe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=...", "use_vertex_ai": true, "vertex_ai_model": "gemini-2.0-flash"}'

curl -X POST http://localhost:8000/v1/transcribe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=...", "use_vertex_ai": true, "vertex_ai_model": "gemini-2.5-pro"}'

curl -X POST http://localhost:8000/v1/transcribe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=...", "use_vertex_ai": true, "vertex_ai_model": "auto-detect"}'
```

## CLI Usage Examples

### Interactive Mode (Original v25.py Experience)
```bash
# Start interactive session
docker compose run --rm transcribe python -m src.main --mode cli --interactive

# This will show the original Hungarian interface:
# 🧪 Teszt mód? (csak első 60 másodperc) [i/n]: i
# 💨 Levegővétel jelölés? [i/n]: i  
# 📺 YouTube videó URL: https://youtube.com/watch?v=...
```

### Direct CLI Mode
```bash
# Basic transcription
docker compose run --rm transcribe python -m src.main --mode cli \
  "https://youtube.com/watch?v=dQw4w9WgXcQ"

# Test mode (60 seconds only)
docker compose run --rm transcribe python -m src.main --mode cli \
  "https://youtube.com/watch?v=dQw4w9WgXcQ" --test

# With Vertex AI post-processing
docker compose run --rm transcribe python -m src.main --mode cli \
  "https://youtube.com/watch?v=dQw4w9WgXcQ" --vertex-ai

# Disable breath detection
docker compose run --rm transcribe python -m src.main --mode cli \
  "https://youtube.com/watch?v=dQw4w9WgXcQ" --no-breath-detection
```

## Integration Examples

### Web Application Integration
```python
from fastapi import FastAPI, BackgroundTasks
import httpx

app = FastAPI()

@app.post("/transcribe")
async def transcribe_video(url: str, background_tasks: BackgroundTasks):
    # Submit to transcription service
    response = httpx.post("http://transcribe:8000/v1/transcribe", json={
        "url": url,
        "breath_detection": True,
        "use_vertex_ai": True,
        "vertex_ai_model": "gemini-2.0-flash"
    })
    
    job_id = response.json()["job_id"]
    
    # Add background task to check completion
    background_tasks.add_task(check_transcription, job_id)
    
    return {"job_id": job_id, "status": "submitted"}

async def check_transcription(job_id: str):
    # Poll and process when complete
    while True:
        status = httpx.get(f"http://transcribe:8000/v1/jobs/{job_id}")
        if status.json()["status"] == "completed":
            # Process completed transcription
            break
        await asyncio.sleep(10)
```

### Batch Processing Script
```python
import httpx
import csv
import time

def process_youtube_playlist(urls):
    """Process multiple YouTube URLs in batch."""
    jobs = []
    
    # Submit all jobs
    for url in urls:
        response = httpx.post("http://localhost:8000/v1/transcribe", json={
            "url": url,
            "test_mode": False,
            "breath_detection": True,
            "use_vertex_ai": True,
            "vertex_ai_model": "gemini-2.0-flash"
        })
        jobs.append({
            "url": url,
            "job_id": response.json()["job_id"]
        })
        print(f"Submitted: {url}")
    
    # Wait for completion
    completed = []
    while jobs:
        for job in jobs[:]:  # Copy list to modify during iteration
            status = httpx.get(f"http://localhost:8000/v1/jobs/{job['job_id']}")
            job_status = status.json()
            
            if job_status["status"] == "completed":
                # Download transcript
                transcript = httpx.get(f"http://localhost:8000/v1/jobs/{job['job_id']}/download")
                
                filename = f"transcript_{job['job_id'][:8]}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(transcript.text)
                
                completed.append({
                    "url": job["url"],
                    "filename": filename,
                    "word_count": job_status["result"]["word_count"]
                })
                
                jobs.remove(job)
                print(f"Completed: {job['url']}")
                
            elif job_status["status"] == "failed":
                print(f"Failed: {job['url']} - {job_status['error']}")
                jobs.remove(job)
        
        if jobs:
            time.sleep(10)
    
    return completed

# Usage
urls = [
    "https://youtube.com/watch?v=video1",
    "https://youtube.com/watch?v=video2",
    "https://youtube.com/watch?v=video3"
]

results = process_youtube_playlist(urls)
print(f"Processed {len(results)} videos")
```

### Webhook Integration
```python
from flask import Flask, request, jsonify
import httpx

app = Flask(__name__)

@app.route('/transcribe', methods=['POST'])
def start_transcription():
    data = request.json
    
    # Submit to transcription service
    response = httpx.post("http://transcribe:8000/v1/transcribe", json={
        "url": data["url"],
        "breath_detection": data.get("breath_detection", True),
        "vertex_ai_model": data.get("vertex_ai_model", "auto-detect")
    })
    
    return jsonify(response.json())

@app.route('/webhook', methods=['POST'])
def transcription_webhook():
    """Receive completion notifications."""
    data = request.json
    job_id = data["job_id"]
    
    if data["status"] == "completed":
        # Process completed transcription
        # Send notification, save to database, etc.
        print(f"Transcription {job_id} completed!")
    
    return jsonify({"status": "received"})
```

## Production Examples

### Load Balanced Setup
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - transcribe

  transcribe:
    build: .
    deploy:
      replicas: 3
    expose:
      - "8000"
    environment:
      - VERTEX_AI_MODEL=gemini-2.0-flash
```

### Monitoring with Prometheus
```python
from prometheus_client import Counter, Histogram, generate_latest

# Add to api.py
job_counter = Counter('transcribe_jobs_total', 'Total jobs', ['status'])
job_duration = Histogram('transcribe_job_duration_seconds', 'Job duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Vertex AI Model Selection Examples

### Different Use Cases

```python
# For fast processing
response = httpx.post("http://localhost:8000/v1/transcribe", json={
    "url": "https://youtube.com/watch?v=...",
    "use_vertex_ai": True,
    "vertex_ai_model": "gemini-2.0-flash"  # Fastest option
})

# For detailed analysis
response = httpx.post("http://localhost:8000/v1/transcribe", json={
    "url": "https://youtube.com/watch?v=...",
    "use_vertex_ai": True,
    "vertex_ai_model": "gemini-2.5-pro"  # Most detailed
})

# Let the system decide
response = httpx.post("http://localhost:8000/v1/transcribe", json={
    "url": "https://youtube.com/watch?v=...",
    "use_vertex_ai": True,
    "vertex_ai_model": "auto-detect"  # Smart fallback
})
```

These examples demonstrate the full capability and flexibility of the refactored YouTube Transcription Service with Vertex AI model selection!