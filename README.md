# YouTube Transcription Service v1.0

Modern, modular YouTube transcription service with Hungarian language support, built from refactoring the monolithic v25.py script into a containerized microservice architecture.

## Features

- **Dual Interface**: Both CLI (preserving original v25.py experience) and REST API
- **Hungarian Language Focus**: Optimized for Hungarian speech recognition
- **Adaptive Processing**: Automatic sync (<10MB) vs async (GCS) decision
- **Advanced Pause Detection**: Intelligent breath/pause marking with multiple thresholds
- **Progress Tracking**: Real-time progress with animated bars and ETA
- **Vertex AI Integration**: Optional script-style formatting with selectable Gemini models
- **Docker Ready**: Full containerization with docker-compose
- **Production Ready**: Health checks, logging, error handling

## Architecture

```
src/
├── config.py              # Configuration management
├── main.py                 # Entry point (CLI/API mode)
├── api.py                  # FastAPI REST endpoints  
├── cli.py                  # Interactive CLI (v25.py experience)
├── core/
│   ├── transcriber.py      # Main orchestrator
│   ├── downloader.py       # YouTube download (yt-dlp)
│   ├── converter.py        # Audio conversion (FFmpeg)
│   ├── speech_client.py    # Google Speech API
│   ├── segmenter.py        # Pause detection & formatting
│   └── postprocessor.py    # Vertex AI post-processing
└── utils/
    ├── progress.py         # Progress tracking
    ├── colors.py          # Console colors
    └── validators.py      # Input validation
```

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Google Cloud service account with permissions:
  - Cloud Speech-to-Text API
  - Cloud Storage API  
  - Vertex AI API (optional)

### 2. Setup

```bash
# Clone and setup
git clone <repo> youtube-transcribe-service
cd youtube-transcribe-service/v1

# Place your Google Cloud service account key
mkdir credentials
cp ~/path/to/your-service-account.json credentials/service-account.json

# Configure environment
cp .env.example .env
# Edit .env with your settings (GCS bucket name, etc.)
```

### 3. Run with Docker

```bash
# Build and start API server
docker compose up -d

# Check health
curl http://localhost:8000/health

# Submit transcription job
curl -X POST http://localhost:8000/v1/transcribe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=...", "test_mode": true}'

# With Vertex AI model selection
curl -X POST http://localhost:8000/v1/transcribe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=...", "use_vertex_ai": true, "vertex_ai_model": "gemini-2.5-flash"}'
```

### 4. CLI Mode (Original v25.py Experience)

```bash
# Interactive CLI (preserves original Hungarian interface)
docker compose run --rm transcribe python -m src.main --mode cli --interactive

# Direct CLI
docker compose run --rm transcribe python -m src.main --mode cli "https://youtube.com/watch?v=..."
```

## API Endpoints

### Core Endpoints

- `POST /v1/transcribe` - Create transcription job
- `GET /v1/jobs/{job_id}` - Get job status
- `GET /v1/jobs/{job_id}/download` - Download transcript
- `GET /v1/jobs` - List jobs
- `DELETE /v1/jobs/{job_id}` - Delete job

### Monitoring

- `GET /health` - Health check
- `GET /admin/stats` - Service statistics
- `GET /docs` - API documentation (Swagger)

## Configuration

### Environment Variables

```bash
# Mode
MODE=api                    # api or cli

# Google Cloud
GCS_BUCKET_NAME=your-bucket
VERTEX_PROJECT_ID=your-project-id
VERTEX_AI_MODEL=gemini-2.0-flash  # or auto-detect

# Processing
SYNC_SIZE_LIMIT_MB=10      # Sync/async threshold
LANGUAGE_CODE=hu-HU        # Speech recognition language

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### Docker Compose

```yaml
# docker-compose.override.yml for development
version: '3.8'
services:
  transcribe:
    environment:
      - MODE=cli
      - LOG_LEVEL=DEBUG
    volumes:
      - ./src:/app/src  # Live reload
```

## Usage Examples

### API Usage

```python
import httpx

# Submit job
response = httpx.post("http://localhost:8000/v1/transcribe", json={
    "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "test_mode": true,
    "breath_detection": true,
    "use_vertex_ai": true,
    "vertex_ai_model": "gemini-2.5-flash"  # or "auto-detect"
})
job_id = response.json()["job_id"]

# Check status
status = httpx.get(f"http://localhost:8000/v1/jobs/{job_id}")
print(status.json())

# Download when complete
if status.json()["status"] == "completed":
    transcript = httpx.get(f"http://localhost:8000/v1/jobs/{job_id}/download")
    with open("transcript.txt", "w") as f:
        f.write(transcript.text)
```

### CLI Usage

```bash
# Interactive mode (like original v25.py)
python -m src.main --mode cli --interactive

# Direct mode
python -m src.main --mode cli "https://youtube.com/watch?v=..." --test --vertex-ai

# API server
python -m src.main --mode api --port 8080
```

## Processing Pipeline

1. **Download**: yt-dlp extracts best audio format
2. **Convert**: FFmpeg converts to FLAC 16kHz mono
3. **Decide**: Automatic sync (<10MB) vs async (GCS) processing
4. **Transcribe**: Google Speech-to-Text with Hungarian language model
5. **Segment**: Intelligent pause detection with breath marking
6. **Format**: Rich transcript with timestamps and statistics
7. **Post-process**: Optional Vertex AI script formatting
8. **Save**: UTF-8 text file with comprehensive metadata

## Vertex AI Model Selection

The service supports multiple Gemini models for post-processing:

### Available Models

- **gemini-2.0-flash** - Fast and efficient (recommended)
- **gemini-2.5-flash** - Latest fast model
- **gemini-2.5-pro** - Latest detailed model  
- **gemini-1.5-pro** - Detailed analysis
- **gemini-1.5-flash** - Classic fast model
- **auto-detect** - Automatic selection with fallback

### CLI Interface

The CLI provides an interactive model selection prompt:

```
🔧 Vertex AI modell választása:
   1. gemini-2.0-flash - Gyors és hatékony (ajánlott)
   2. gemini-2.5-flash - Legújabb gyors modell
   3. auto-detect - Automatikus kiválasztás

Választás [1-3, Enter = 1]:
```

### API Parameter

```json
{
  "url": "https://youtube.com/watch?v=...",
  "use_vertex_ai": true,
  "vertex_ai_model": "gemini-2.5-flash"
}
```

### Logging & Output

- Selected model appears in logs: `├─ Kiválasztott modell: gemini-2.5-flash`
- Model shown in transcript header: `🤖 Utófeldolgozás: Vertex AI (gemini-2.5-flash)`
- Auto-detect shows which model was selected automatically

## Pause Detection

The service detects and categorizes speech pauses:

- **Short Breath** (•): 0.6-1.5s pause
- **Long Breath** (••): 1.5-3.0s pause  
- **Paragraph Break**: 3.0s+ pause
- **Sentence End**: Punctuation + 1.0s+ pause

## Testing

```bash
# Run tests
docker compose run --rm transcribe python -m pytest tests/

# Run specific test
docker compose run --rm transcribe python -m pytest tests/test_validators.py -v

# Test with coverage
docker compose run --rm transcribe python -m pytest --cov=src tests/
```

## Monitoring & Logging

```bash
# View logs
docker compose logs -f transcribe

# Container stats
docker stats transcribe

# Inside container debugging
docker compose exec transcribe bash
```

## Production Deployment

### Resource Requirements

- **Memory**: 2GB minimum, 4GB recommended
- **CPU**: 2 cores minimum
- **Storage**: 10GB for temporary files
- **Network**: Stable connection for Google APIs

### Security Considerations

- Store service account keys securely
- Use environment variables for sensitive config
- Implement rate limiting for production
- Monitor API quotas and usage
- Regular security updates

## Migration from v25.py

The refactored service preserves 100% functional compatibility:

- **CLI Mode**: Identical Hungarian interface and behavior
- **All Features**: Pause detection, progress bars, statistics
- **Same Output**: Transcript format and file naming
- **Performance**: No regression, improved modularity

### Key Improvements

- **Modular Architecture**: Easy to maintain and extend
- **Docker Ready**: Simple deployment and scaling
- **API Access**: Programmatic integration capability
- **Better Testing**: Comprehensive test suite
- **Configuration Management**: Environment-based settings

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| FFmpeg not found | Ensure Docker image includes ffmpeg |
| GCS permission denied | Verify service account roles |
| Speech API quota exceeded | Check quotas, implement backoff |
| Memory issues | Increase Docker memory limits |
| Port conflicts | Change API_PORT in .env |

### Debug Mode

```bash
# Enable debug logging
docker compose run -e LOG_LEVEL=DEBUG transcribe python -m src.main

# Test individual components
docker compose run transcribe python -c "from src.core.downloader import YouTubeDownloader; print('OK')"
```

## Contributing

1. Follow the existing modular architecture
2. Maintain Hungarian language support
3. Preserve CLI compatibility with v25.py
4. Add tests for new functionality
5. Update documentation

## License

Same as original v25.py project - no license specified.