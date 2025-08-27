# Quick Start Guide

## 🚀 Get Up and Running in 5 Minutes

This guide shows how to quickly start using the refactored YouTube Transcription Service.

## ⚡ NEW: Complete Multilingual Audio Dubbing

This service now includes **full audio dubbing capabilities** with context-aware translation and professional voice synthesis:

### 🎬 Dubbing Features
- **Context-aware translation**: 7 specialized contexts (legal, spiritual, marketing, scientific, educational, news, casual)
- **Professional voice synthesis**: ElevenLabs TTS with 20+ voice options
- **Video muxing**: Replace audio tracks while preserving video quality
- **Cost transparency**: Real-time cost estimation and budget controls
- **Multi-language support**: 20+ target languages with accurate timing preservation

### 🔧 Chunking for Long Content
- **Unlimited length support**: Automatic chunking for videos of any duration
- **Intelligent splitting**: Uses sentence boundaries for clean breaks  
- **Overlap handling**: 200-character overlap between chunks
- **Progress tracking**: Real-time progress for chunked processing

### Chunking Configuration

Chunking behavior can be configured in `src/config.py`:

```python
# Text chunking settings for long transcripts
chunking_enabled: bool = True
chunk_size: int = 4000        # Characters per chunk  
chunk_overlap: int = 200      # Overlap between chunks
max_chunks: int = 20          # Safety limit
max_transcript_length: int = 5000  # Single-pass limit
```

### Step 1: Setup (2 minutes)

```bash
# Navigate to the refactored version
cd v1

# Set up environment configuration
cp .env.example .env

# Edit .env with your settings (at minimum, set GCS_BUCKET_NAME)
nano .env
```

Your `.env` should look like:
```bash
# Core Configuration
MODE=api
GCS_BUCKET_NAME=your-bucket-name-here
VERTEX_PROJECT_ID=your-project-id
VERTEX_AI_MODEL=gemini-2.0-flash
LANGUAGE_CODE=hu-HU

# Dubbing Configuration (Optional)
ELEVENLABS_API_KEY=your-elevenlabs-key-here
ELEVENLABS_DEFAULT_VOICE=pNInz6obpgDQGcFmaJgB
DEFAULT_TARGET_LANGUAGE=en-US
DEFAULT_TRANSLATION_CONTEXT=casual
```

### Step 2: Google Cloud Credentials

```bash
# Create credentials directory
mkdir -p credentials

# Copy your service account key
cp ~/path/to/your-service-account.json credentials/service-account.json
```

### Step 3: Choose Your Interface

#### Option A: CLI Mode (Original v25.py Experience)

```bash
# Interactive CLI - exact same experience as v25.py
docker compose run --rm transcribe python -m src.main --mode cli --interactive

# Or direct command line usage
docker compose run --rm transcribe python -m src.main --mode cli \
  "https://youtube.com/watch?v=dQw4w9WgXcQ" --test
```

#### Option B: API Mode (New Capability)

```bash
# Start the API server
docker compose up -d

# Check if it's running
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs
```

## 📱 Using the API

### Basic transcription job
```bash
curl -X POST http://localhost:8000/v1/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "test_mode": true,
    "breath_detection": true,
    "use_vertex_ai": true,
    "vertex_ai_model": "gemini-2.0-flash"
  }'
```

### Full dubbing pipeline job
```bash
curl -X POST http://localhost:8000/v1/dub \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "test_mode": true,
    "enable_translation": true,
    "target_language": "en-US",
    "translation_context": "casual",
    "enable_synthesis": true,
    "voice_id": "pNInz6obpgDQGcFmaJgB",
    "audio_quality": "high",
    "enable_video_muxing": true,
    "video_format": "mp4"
  }'
```

### Translation-only job
```bash
curl -X POST http://localhost:8000/v1/translate \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "[00:00:01] Magyar szöveg példa",
    "target_language": "en-US",
    "translation_context": "educational",
    "target_audience": "students"
  }'
```

### Get available voices
```bash
curl -X GET http://localhost:8000/v1/voices
```

### Cost estimation
```bash
curl -X GET "http://localhost:8000/v1/cost-estimate?transcript_length=2000&target_language=en-US&enable_synthesis=true"
```

Response:
```json
{
  "job_id": "abc123...",
  "status": "queued",
  "progress": 0
}
```

### Check job status
```bash
curl http://localhost:8000/v1/jobs/abc123...
```

Response:
```json
{
  "job_id": "abc123...",
  "status": "completed",
  "progress": 100,
  "result": {
    "title": "Video Title",
    "duration": 125,
    "word_count": 234,
    "transcript_file": "/app/data/transcript_abc123.txt"
  }
}
```

### Download the transcript
```bash
curl http://localhost:8000/v1/jobs/abc123.../download -o transcript.txt
```

## 🎨 CLI Mode Walkthrough

When you run interactive CLI mode, you'll see the familiar v25.py interface:

```
🎥 YouTube Videó → Szöveges Átirat (Google Speech API)
======================================================================
  ⚡ Optimalizált verzió: FLAC konverzió, progress bar, teszt mód
======================================================================

🧪 Teszt mód? (csak első 60 másodperc) [i/n]: i
💨 Levegővétel jelölés? [i/n]: i
📺 YouTube videó URL: https://youtube.com/watch?v=dQw4w9WgXcQ

📥 Videó információk lekérése...
   ├─ URL feldolgozása...
   ├─ Kapcsolódás YouTube-hoz...
   └─ Információk lekérve (0.8s)

📺 Videó részletek:
   ├─ Cím: Rick Astley - Never Gonna Give You Up
   ├─ Feltöltő: RickAstleyVEVO
   ├─ Hossz: 3:32
   ├─ Megtekintések: 1,234,567,890
   └─ Video ID: dQw4w9WgXcQ

⚡ TESZT MÓD: Csak az első 60 másodperc lesz letöltve!

🎵 Audio stream letöltése...
📥 Letöltés │████████████████████████████████████████│ 100.0% │ Méret: 2.1/2.1MB │ Sebesség: 850KB/s
   ✓ Letöltés kész (2.5s)

🔄 Audio konvertálás FLAC formátumba...
   ├─ Forrás: audio_dQw4w9WgXcQ.m4a
   ├─ Cél formátum: FLAC 16kHz 1 csatorna
   ├─ Időtartam: 1:00
   └─ FFmpeg indítása...

🔄 Konvertálás │████████████████████████████████████████│ 100.0% │ Sebesség: 2.1x │ Hátra: 0:00
   ✓ Konverzió kész (28.5s)

🎤 Speech API feldolgozás (1.8 MB)...
   💨 Levegővétel detektálás: BEKAPCSOLVA (finomított)
   📊 Szünet küszöbök: 0.25s+

⚡ Gyors feldolgozás (sync recognize)...
✓ Feldolgozás kész! (3 blokk)

📝 Átirat formázása levegővétel detektálással...

--- ELŐNÉZET (első 800 karakter) ---
📹 Videó: Rick Astley - Never Gonna Give You Up
📅 Feldolgozva: 2025-01-15 10:30
======================================================================

[0:00:00] We're no strangers to love • You know the rules and so do I ••
[0:00:07] A full commitment's what I'm thinking of • You wouldn't get this from any other guy ••

[0:00:15] I just wanna tell you how I'm feeling • Gotta make you understand ••

[0:00:22] Never gonna give you up • Never gonna let you down ••
[0:00:29] Never gonna run around and desert you • Never gonna make you cry ••
[0:00:36] Never gonna say goodbye • Never gonna tell a lie and hurt you ••

======================================================================
📊 Beszéd statisztika:
   • Összes szó: 87
   • Átlagos pontosság: 94.2%

💨 Levegővétel statisztika:
   • Rövid szünetek (•): 12
   • Hosszú szünetek (••): 8
   • Bekezdések: 3
   • Összes detektált szünet: 23

📈 Beszéddinamika:
   • Beszédtempó: 87 szó/perc
   • Szünetek aránya: 15.2%

🤖 Szeretnéd Vertex AI-val újraformázni script stílusra? [i/n]: i

🔧 Vertex AI modell választása:
   1. gemini-2.0-flash - Gyors és hatékony (ajánlott)
   2. gemini-2.5-flash - Legújabb gyors modell
   3. auto-detect - Automatikus kiválasztás

Választás [1-3, Enter = 1]: 1
✓ Kiválasztva: gemini-2.0-flash

🤖 Vertex AI utófeldolgozás (gemini-2.0-flash)...
   ├─ Project: 275163613290
   ├─ Kiválasztott modell: gemini-2.0-flash
   ├─ Próbálkozás: gemini-2.0-flash @ us-central1
   ✓ Sikeres kapcsolat: gemini-2.0-flash @ us-central1
   └─ Prompt küldése...
   ⏳ Gemini válaszára várunk...
   ✓ Vertex AI formázás kész (gemini-2.0-flash): 513 szó
✓ Vertex AI formázás alkalmazva!

💾 Átirat mentve: transcript_dQw4w9WgXcQ.txt (2.8 KB)
   📄 98 szó
   📝 28 sor

✅ SIKERES FELDOLGOZÁS!
   📁 Eredmény: transcript_dQw4w9WgXcQ.txt
   💨 Detektált szünetek: 23 db

🧹 Takarítás...
   ✓ Törölve: audio_dQw4w9WgXcQ.m4a
   ✓ Törölve: audio_dQw4w9WgXcQ_converted.flac

======================================================================
   Köszönjük, hogy használtad a YouTube Transcribe-ot! 👋
======================================================================
```

## ⚡ Advanced Usage

### Batch Processing with API
```python
import httpx
import time

def process_multiple_videos(urls):
    # Submit all jobs
    jobs = []
    for url in urls:
        response = httpx.post("http://localhost:8000/v1/transcribe", json={
            "url": url,
            "breath_detection": True,
            "use_vertex_ai": True,
            "vertex_ai_model": "auto-detect"
        })
        jobs.append(response.json()["job_id"])
    
    # Wait for completion
    for job_id in jobs:
        while True:
            status = httpx.get(f"http://localhost:8000/v1/jobs/{job_id}")
            if status.json()["status"] == "completed":
                # Download transcript
                transcript = httpx.get(f"http://localhost:8000/v1/jobs/{job_id}/download")
                with open(f"transcript_{job_id[:8]}.txt", "w") as f:
                    f.write(transcript.text)
                break
            time.sleep(10)

# Usage
urls = [
    "https://youtube.com/watch?v=video1",
    "https://youtube.com/watch?v=video2"
]
process_multiple_videos(urls)
```

### CLI Batch Mode
```bash
# Process multiple videos with CLI
for url in "https://youtube.com/watch?v=..." "https://youtube.com/watch?v=..."; do
    docker compose run --rm transcribe python -m src.main --mode cli "$url" --test
done
```

## 🛠️ Troubleshooting

### Common Issues
1. **Service won't start**: Check that port 8000 is available
2. **Authentication errors**: Verify service account key is in `credentials/`
3. **GCS errors**: Ensure bucket name is valid and accessible
4. **Docker issues**: Run `docker compose build` to rebuild

### Debug Mode
```bash
# Enable detailed logging
docker compose run -e LOG_LEVEL=DEBUG transcribe python -m src.main --mode api

# Test individual components
docker compose run transcribe python -c "from src.utils.validators import is_valid_youtube_url; print(is_valid_youtube_url('https://youtube.com/watch?v=test'))"
```

## 🔧 Configuration Options

### Environment Variables (.env)
```bash
# Required
GCS_BUCKET_NAME=your-bucket-name       # Google Cloud Storage bucket
VERTEX_PROJECT_ID=your-project-id      # For Vertex AI (optional)
VERTEX_AI_MODEL=gemini-2.0-flash       # Vertex AI model selection

# Optional
MODE=api                               # api or cli
API_PORT=8000                         # API server port
SYNC_SIZE_LIMIT_MB=10                 # Sync vs async threshold
LANGUAGE_CODE=hu-HU                   # Speech recognition language
LOG_LEVEL=INFO                        # DEBUG, INFO, WARNING, ERROR
```

### Service Account Permissions
Your Google Cloud service account needs:
- **Cloud Speech-to-Text API**: `roles/speech.client`
- **Cloud Storage**: `roles/storage.objectAdmin` (for your bucket)
- **Vertex AI** (optional): `roles/aiplatform.user`

## 🎯 What's Different from v25.py?

### Identical Experience
- ✅ Same Hungarian interface and prompts
- ✅ Same colored progress bars and animations
- ✅ Same breath detection and transcript formatting
- ✅ Same statistics and file output

### New Capabilities
- 🆕 **Complete dubbing pipeline**: Context-aware translation + voice synthesis + video muxing
- 🆕 **REST API**: 6 new endpoints for full dubbing functionality
- 🆕 **Multi-language support**: 20+ languages with specialized translation contexts
- 🆕 **Professional voice synthesis**: ElevenLabs TTS integration with quality controls
- 🆕 **Cost transparency**: Real-time cost estimation and budget management
- 🆕 **Background job processing**: Async handling for long dubbing tasks
- 🆕 **Docker containerization**: Easy deployment and scaling
- 🆕 **Health monitoring**: Complete service observability
- 🆕 **Comprehensive testing**: 200+ tests with performance benchmarking

Users familiar with v25.py can start using the CLI mode immediately with zero learning curve, while developers can leverage the powerful new dubbing capabilities for creating multilingual content at scale.

**Ready to transcribe! 🎉**