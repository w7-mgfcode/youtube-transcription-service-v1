# YouTube Transcription & Dubbing Service v1.0

Modern, modular YouTube transcription and dubbing service with Hungarian language support and multi-provider TTS integration, built from refactoring the monolithic v25.py script into a containerized microservice architecture.

## Features

### Transcription
- **Dual Interface**: Both CLI (preserving original v25.py experience) and REST API
- **Hungarian Language Focus**: Optimized for Hungarian speech recognition
- **Adaptive Processing**: Automatic sync (<10MB) vs async (GCS) decision
- **Advanced Pause Detection**: Intelligent breath/pause marking with multiple thresholds
- **Progress Tracking**: Real-time progress with animated bars and ETA
- **Vertex AI Integration**: Optional script-style formatting with selectable Gemini models

### Text-to-Speech & Dubbing
- **Multi-Provider TTS**: Google Cloud TTS and ElevenLabs support with auto-selection
- **94% Cost Savings**: Google TTS at $0.016/1K vs ElevenLabs at $0.30/1K characters
- **1,616+ Voices**: Massive voice library across 40+ languages
- **Voice Mapping**: Seamless ElevenLabs to Google TTS migration
- **SSML Support**: Advanced speech markup with timestamp preservation
- **Chunked Processing**: Unlimited transcript length with parallel synthesis

### Infrastructure
- **Docker Ready**: Full containerization with docker-compose
- **Production Ready**: Health checks, logging, error handling
- **Hungarian CLI**: Complete TTS provider selection interface

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
│   ├── postprocessor.py    # Vertex AI post-processing
│   ├── dubbing_service.py  # Complete dubbing workflow
│   ├── tts_interface.py    # Abstract TTS provider interface
│   ├── tts_factory.py      # TTS provider factory & voice mapping
│   ├── google_tts_synthesizer.py # Google Cloud TTS implementation
│   ├── synthesizer.py      # ElevenLabs TTS adapter
│   ├── translator.py       # Text translation service
│   └── video_muxer.py      # Audio/video synchronization
├── models/                 # Pydantic data models
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

### Transcription Endpoints

- `POST /v1/transcribe` - Create transcription job
- `GET /v1/jobs/{job_id}` - Get job status
- `GET /v1/jobs/{job_id}/download` - Download transcript
- `GET /v1/jobs` - List jobs
- `DELETE /v1/jobs/{job_id}` - Delete job

### Dubbing & TTS Endpoints

- `POST /v1/dubbing` - Create complete dubbing job
- `GET /v1/tts-providers` - List available TTS providers
- `GET /v1/tts-providers/{provider}/voices` - Get provider voices
- `GET /v1/tts-cost-comparison` - Compare TTS provider costs

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

# TTS Providers
TTS_DEFAULT_PROVIDER=auto          # elevenlabs | google_tts | auto
GOOGLE_TTS_ENABLED=true
GOOGLE_TTS_REGION=us-central1
ELEVENLABS_API_KEY=your_api_key    # Optional

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

# Transcription job
response = httpx.post("http://localhost:8000/v1/transcribe", json={
    "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "test_mode": true,
    "breath_detection": true,
    "use_vertex_ai": true,
    "vertex_ai_model": "gemini-2.5-flash"
})
job_id = response.json()["job_id"]

# Complete dubbing workflow
response = httpx.post("http://localhost:8000/v1/dubbing", json={
    "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "target_language": "en-US",
    "tts_provider": "google_tts",  # or "elevenlabs", "auto"
    "voice_id": "en-US-Neural2-F",
    "use_chunked_processing": true
})

# Compare TTS costs
cost_comparison = httpx.get(
    "http://localhost:8000/v1/tts-cost-comparison?text=Sample text"
)
print(cost_comparison.json())  # Shows 94% savings with Google TTS

# List TTS providers
providers = httpx.get("http://localhost:8000/v1/tts-providers")
print(providers.json())  # Google TTS: 1,616 voices, ElevenLabs: 25 voices
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

### Transcription Pipeline

1. **Download**: yt-dlp extracts best audio format
2. **Convert**: FFmpeg converts to FLAC 16kHz mono
3. **Decide**: Automatic sync (<10MB) vs async (GCS) processing
4. **Transcribe**: Google Speech-to-Text with Hungarian language model
5. **Segment**: Intelligent pause detection with breath marking
6. **Format**: Rich transcript with timestamps and statistics
7. **Post-process**: Optional Vertex AI script formatting
8. **Save**: UTF-8 text file with comprehensive metadata

### Dubbing Pipeline

1. **Transcribe**: Extract text using transcription pipeline
2. **Translate**: Optional translation to target language
3. **TTS Provider Selection**: Choose Google TTS (cost-effective) or ElevenLabs (premium)
4. **Voice Mapping**: Automatic voice equivalents between providers
5. **SSML Generation**: Preserve timing and add speech markup
6. **Chunked Synthesis**: Process large content with parallel synthesis
7. **Audio Merging**: Combine chunks with seamless transitions
8. **Sync**: Align generated audio with original video timing

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

## TTS Provider Comparison

| Feature | Google Cloud TTS | ElevenLabs | Auto Mode |
|---------|------------------|------------|-----------|
| **Cost** | $0.016/1K chars | $0.30/1K chars | Cost-optimized |
| **Savings** | **94% cheaper** | - | **94% savings** |
| **Voices** | 1,616 voices | 25+ voices | Best available |
| **Languages** | 40+ languages | 29 languages | All supported |
| **Quality** | Neural2/Studio | Premium neural | Balanced |

### Hungarian CLI Interface

The CLI includes TTS provider selection in Hungarian:

```
🎤 TTS szolgáltató kiválasztása:
   1. ElevenLabs - Prémium neurális hangok (drága)
   2. Google Cloud TTS - Kiváló minőség (90% olcsóbb) ⭐
   3. Automatikus kiválasztás költség alapján

💰 KÖLTSÉG ÖSSZEHASONLÍTÁS (1000 karakter alapján)
------------------------------------------------------------
Szolgáltató              Költség     Éves megtakarítás   
------------------------------------------------------------
ElevenLabs               $0.300      -
Google Cloud TTS         $0.016      $284 (94%)
Automatikus              $0.016      $284 (94%)

💡 AJÁNLÁS: A Google Cloud TTS 94%-kal olcsóbb!
```

## Migration from v25.py

The refactored service preserves 100% functional compatibility:

- **CLI Mode**: Identical Hungarian interface and behavior
- **All Features**: Pause detection, progress bars, statistics
- **Same Output**: Transcript format and file naming
- **Performance**: No regression, improved modularity

### Key Improvements

- **Modular Architecture**: Easy to maintain and extend
- **Multi-Provider TTS**: Google TTS with 94% cost savings
- **Dubbing Capability**: Complete video dubbing workflow
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

## Documentation

- [Complete API Reference](docs/API_REFERENCE.md) - All endpoints and models
- [TTS Providers Guide](docs/TTS_PROVIDERS.md) - Provider comparison and setup
- [Voice Selection Guide](docs/VOICE_GUIDE.md) - Voice profiles and recommendations  
- [Cost Optimization Guide](docs/COST_GUIDE.md) - Strategies for cost-effective dubbing
- [Examples & Demos](examples/README.md) - Working examples and tutorials

## Version Information

**Service Version**: 1.0.0  
**TTS Integration**: Complete (August 15, 2025)  
**Status**: Production Ready ✅  
**Google TTS Voices**: 1,616 voices across 40+ languages  
**Cost Savings**: 94% with Google TTS vs ElevenLabs  

**Development Timeline**:
- Google TTS Integration: Completed August 15, 2025
- All 7 development phases completed
- 5 comprehensive example scripts provided
- Complete documentation and migration guides

## License

Same as original v25.py project - no license specified.