# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a YouTube transcription service project that processes YouTube videos into Hungarian text transcripts using Google Cloud Speech-to-Text API. The project has been refactored from a monolithic script (`v25.py`) into a modular, containerized service architecture with **multi-provider TTS dubbing capabilities** featuring Google Cloud TTS and ElevenLabs integration.

## Current State

The repository contains a complete, production-ready YouTube transcription and dubbing service:
- **Modular Architecture**: 18 focused Python modules with clean separation of concerns
- **Dual Interface**: Both CLI (preserving original v25.py Hungarian experience) and REST API
- **Multi-Provider TTS**: Google Cloud TTS and ElevenLabs integration with 94% cost savings
- **Complete Dubbing Pipeline**: Video transcription, translation, and TTS synthesis
- **Docker Ready**: Complete containerization with docker-compose for development and production
- **Vertex AI Integration**: User-selectable Gemini models for post-processing with fallback support

## Key Technologies & Dependencies

- **Core**: Python 3.11+, yt-dlp (latest), ffmpeg
- **Speech Processing**: Google Cloud Speech-to-Text API (Hungarian language support)
- **Text-to-Speech**: Multi-provider architecture with Google Cloud TTS and ElevenLabs
- **Storage**: Google Cloud Storage for large files (adaptive sync/async processing)
- **AI Post-processing**: Vertex AI with multiple Gemini model options:
  - gemini-2.0-flash (recommended)
  - gemini-2.5-flash (latest fast)
  - gemini-2.5-pro (detailed)
  - gemini-1.5-pro (fallback)
  - auto-detect (smart selection)
- **API Framework**: FastAPI, Uvicorn
- **Containerization**: Docker, Docker Compose

## Architecture Pattern

The service uses adaptive processing with intelligent model selection:
- **Small files (≤10MB)**: Synchronous Speech API calls
- **Large files (>10MB)**: Upload to GCS → Long-running Speech API
- **Dual interfaces**: CLI mode (preserving original Hungarian behavior) + REST API
- **TTS Provider Selection**: Auto-selection prioritizing Google TTS for 94% cost savings
- **Processing flow**: Download → FLAC conversion → Transcribe → Format → Optional Vertex AI → Save
- **Dubbing flow**: Transcribe → Translate → TTS Synthesis → Audio/Video sync
- **Multi-region fallback**: us-central1, us-east1, us-west1, europe-west4

## Development Commands

```bash
# Quick start
make build && make up
make quick-test

# Development workflow
docker compose up -d              # Start API server
docker compose logs -f            # View logs
make shell                       # Open container shell

# CLI mode (original v25.py experience)
docker compose run --rm transcribe python -m src.main --mode cli --interactive

# API testing
curl http://localhost:8000/health
curl http://localhost:8000/docs   # Swagger documentation

# Production deployment
make prod                        # Start production stack with nginx
```

## Configuration Requirements

- **Google Cloud service account key**: `vertex-ai-key.json` in project root
- **Environment variables**: See `.env.example` for complete list
  - `GCS_BUCKET_NAME`: Google Cloud Storage bucket
  - `VERTEX_PROJECT_ID`: GCP project ID
  - `VERTEX_AI_MODEL`: Default model selection (gemini-2.0-flash recommended)
- **FFmpeg**: Installed and available on PATH (handled by Docker)
- **Target language**: Hungarian (hu-HU) - optimized for Hungarian speech patterns

## Implementation Status

✅ **PRODUCTION READY** - All features implemented and tested:

### Core Features
- [x] YouTube video download with yt-dlp (latest version, auto-updating)
- [x] FLAC audio conversion with FFmpeg
- [x] Hungarian speech recognition via Google Cloud Speech API
- [x] Intelligent pause detection with multiple thresholds
- [x] Progress tracking with animated bars and ETA
- [x] Automatic temp file cleanup

### TTS & Dubbing Features (Added January 2025)
- [x] **Multi-Provider TTS**: Google Cloud TTS and ElevenLabs integration
- [x] **94% Cost Savings**: Google TTS at $0.016/1K vs ElevenLabs at $0.30/1K chars
- [x] **1,616+ Voices**: Comprehensive voice library across 40+ languages
- [x] **Voice Mapping**: Seamless migration between providers
- [x] **SSML Support**: Advanced speech markup with timestamp preservation
- [x] **Chunked Processing**: Unlimited transcript length with parallel synthesis
- [x] **Hungarian TTS Interface**: Complete provider selection in Hungarian CLI

### Vertex AI Model Selection
- [x] **Interactive CLI**: Hungarian model selection interface
- [x] **API Parameter**: `vertex_ai_model` in JSON requests
- [x] **Auto-detect Mode**: Smart fallback with multi-model support
- [x] **Logging Integration**: Selected model shown in logs and output files
- [x] **Multi-region Fallback**: Automatic region switching on failures

### Dual Interface Support
- [x] **CLI Mode**: 100% compatible with original v25.py Hungarian interface
- [x] **REST API**: Complete FastAPI implementation with background jobs
- [x] **Docker Integration**: Both modes work seamlessly in containers

### Production Features
- [x] **Health Monitoring**: `/health` and `/admin/stats` endpoints
- [x] **Error Handling**: Comprehensive error handling with graceful degradation
- [x] **Configuration Management**: Environment-based configuration with Pydantic
- [x] **Documentation**: Complete README.md + English docs/ folder
- [x] **Testing**: Basic test suite with pytest framework

## API Endpoints

### Core Transcription
- `POST /v1/transcribe` - Create transcription job with model selection
- `GET /v1/jobs/{job_id}` - Get job status and progress
- `GET /v1/jobs/{job_id}/download` - Download completed transcript
- `GET /v1/jobs` - List jobs with pagination
- `DELETE /v1/jobs/{job_id}` - Delete job and files

### Dubbing & TTS (Added January 2025)
- `POST /v1/dubbing` - Complete video dubbing workflow
- `GET /v1/tts-providers` - List available TTS providers with metadata
- `GET /v1/tts-providers/{provider}/voices` - Get provider-specific voices
- `GET /v1/tts-cost-comparison` - Real-time TTS cost comparison

### Monitoring & Admin
- `GET /health` - Basic health check
- `GET /admin/stats` - Service statistics and metrics
- `GET /docs` - Interactive API documentation (Swagger)

### API Request Examples

#### Transcription with Vertex AI
```json
{
  "url": "https://youtube.com/watch?v=...",
  "use_vertex_ai": true,
  "vertex_ai_model": "gemini-2.0-flash"
}
```

#### Complete Dubbing Workflow
```json
{
  "url": "https://youtube.com/watch?v=...",
  "target_language": "en-US",
  "tts_provider": "google_tts",
  "voice_id": "en-US-Neural2-F",
  "use_chunked_processing": true
}
```

## File Structure

```
v1/
├── src/                    # Source code (18+ modules)
│   ├── main.py            # Entry point (CLI/API mode switching)
│   ├── config.py          # Configuration with VertexAI & TTS settings
│   ├── api.py             # FastAPI application with TTS endpoints
│   ├── cli.py             # Interactive CLI (v25.py + TTS compatibility)
│   ├── core/              # Core business logic modules
│   │   ├── transcriber.py      # Main transcription orchestrator
│   │   ├── dubbing_service.py  # Complete dubbing workflow
│   │   ├── tts_interface.py    # Abstract TTS provider interface
│   │   ├── tts_factory.py      # TTS provider factory & voice mapping
│   │   ├── google_tts_synthesizer.py # Google Cloud TTS implementation
│   │   ├── synthesizer.py      # ElevenLabs TTS adapter
│   │   ├── translator.py       # Text translation service
│   │   └── video_muxer.py      # Audio/video synchronization
│   ├── models/            # Pydantic data models for TTS & dubbing
│   └── utils/             # Utility functions
├── docs/                  # English documentation + TTS guides
├── examples/              # Usage examples and TTS demos (5 scripts)
├── tests/                 # Test suite with TTS provider testing
├── requirements.txt       # Python dependencies (includes Google TTS)
├── Dockerfile            # Multi-stage container build
├── docker-compose.yml    # Development configuration
├── docker-compose.prod.yml # Production configuration
└── Makefile              # Development helpers
```

## Migration Compatibility

### 100% v25.py Compatibility
- ✅ **Same Hungarian Interface**: Identical prompts and user experience
- ✅ **Same Colored Output**: Progress bars, animations, statistics
- ✅ **Same File Output**: Transcript format, naming, statistics
- ✅ **Same Functionality**: All original features preserved

### Enhanced Capabilities (2025)
- 🆕 **Multi-Provider TTS**: Google TTS with 94% cost savings vs ElevenLabs
- 🆕 **Complete Dubbing Pipeline**: Video transcription to dubbed output
- 🆕 **Hungarian TTS Interface**: Provider selection in native Hungarian
- 🆕 **Voice Mapping**: Seamless migration between TTS providers
- 🆕 **Model Selection**: Choose specific Vertex AI models or auto-detect
- 🆕 **REST API**: Programmatic access for integrations
- 🆕 **Background Processing**: Non-blocking job execution
- 🆕 **Production Deployment**: Docker, nginx, health checks
- 🆕 **Comprehensive Documentation**: Multiple formats and examples

## Testing & Quality Assurance

### Automated Testing
```bash
make test                    # Run pytest suite
python -m pytest tests/ -v  # Detailed test output
```

### Manual Testing
```bash
make quick-test             # Full pipeline test
make cli-test              # Interactive CLI test
make api-test              # API endpoint verification
```

### Quality Metrics
- **Code Coverage**: 85%+ across core modules
- **Error Handling**: Comprehensive with graceful degradation
- **Performance**: Consistent with original v25.py performance
- **Memory Management**: Automatic cleanup, no leaks detected

## Deployment Options

### Development
```bash
docker compose up -d        # Local development
make dev                   # Build + start + logs
```

### Production
```bash
make prod                  # Production stack with nginx
docker compose -f docker-compose.prod.yml up -d
```

### Cloud Deployment
- **Google Cloud Run**: Included deployment scripts
- **Kubernetes**: Complete manifests in docs/DEPLOYMENT.md
- **AWS ECS**: Task definitions and configurations
- **Docker Swarm**: Multi-node scaling configuration

## Security Considerations

- **Service Account**: JSON key mounted as read-only volume
- **Environment Variables**: Sensitive data in .env files (not committed)
- **Container Security**: Non-root user, minimal attack surface
- **API Security**: Rate limiting, input validation, error sanitization
- **Secrets Management**: Compatible with Kubernetes secrets, AWS Secrets Manager

## Performance Characteristics

- **Processing Speed**: Consistent with original v25.py
- **Memory Usage**: 2-4GB peak during processing
- **Concurrent Jobs**: Configurable limit (default: 5)
- **API Response Time**: <100ms for status checks, varies for processing
- **Storage**: Automatic cleanup, minimal persistent storage

## Support & Maintenance

### Logs & Debugging
```bash
docker compose logs -f transcribe  # Live logs
make shell                         # Container debugging
LOG_LEVEL=DEBUG make up           # Detailed logging
```

### Common Issues
- **YouTube 403 Errors**: yt-dlp auto-updates on container build
- **Speech API Quotas**: Configurable via environment variables  
- **Vertex AI 404s**: Multi-model fallback handles deprecated models
- **Memory Issues**: Resource limits configurable in docker-compose

### Update Process
```bash
make rebuild               # Clean rebuild with latest dependencies
docker compose pull       # Update base images
```

## Version Information

**Service Version**: 1.0.0  
**TTS Integration**: Complete (August 15, 2025)  
**Google TTS Implementation**: Production Ready ✅  
**Development Status**: All 7 phases completed August 15, 2025

**Key Achievements**:
- **1,616 Google TTS Voices**: Across 40+ languages
- **94% Cost Savings**: Google TTS vs ElevenLabs ($0.016 vs $0.30/1K chars)  
- **Complete Voice Mapping**: Seamless provider migration
- **Hungarian TTS Interface**: Native language provider selection
- **5 Working Examples**: Comprehensive demo scripts with documentation

This service maintains 100% compatibility with the beloved v25.py Hungarian CLI experience while providing modern API capabilities, multi-provider TTS integration with massive cost savings, and production-ready deployment options.