# 🎤 Text-to-Speech Providers Guide

## Overview

This service supports multiple TTS providers, offering flexibility in cost, quality, and voice options. You can choose between ElevenLabs for premium neural voices or Google Cloud TTS for cost-effective, high-quality synthesis.

## Quick Comparison

| Feature | ElevenLabs | Google Cloud TTS | Auto Mode |
|---------|------------|------------------|-----------|
| **Cost** | $0.30/1K chars | $0.016/1K chars | Cost-optimized |
| **Savings** | - | **90%+ cheaper** | **90%+ savings** |
| **Voices** | 20+ premium | 1,616 voices | Best available |
| **Languages** | 29 languages | 40+ languages | All supported |
| **Quality** | Premium neural | Neural2/Studio | Balanced |
| **Setup** | API key only | Service account | Auto-configured |

## Provider Details

### 🚀 Google Cloud Text-to-Speech (Recommended)

**Best for**: Cost-conscious projects, production deployments, multi-language content

#### Key Benefits
- **90%+ Cost Savings**: $0.016/1K characters vs $0.30/1K for ElevenLabs
- **Massive Voice Library**: 1,616+ voices across 40+ languages
- **Enterprise Quality**: Neural2 and Studio voice models
- **SSML Support**: Advanced speech markup for timing and prosody
- **Unlimited Scale**: No practical limits on synthesis volume

#### Voice Quality Tiers
- **Standard**: Basic quality, lowest cost ($0.004/1K chars)
- **WaveNet**: Enhanced quality ($0.016/1K chars)
- **Neural2**: Premium quality ($0.016/1K chars) - **Recommended**
- **Studio**: Highest quality ($0.016/1K chars)

#### Configuration Example
```bash
# .env configuration
TTS_DEFAULT_PROVIDER=google_tts
GOOGLE_TTS_REGION=us-central1
GOOGLE_TTS_DEFAULT_VOICE=hu-HU-Neural2-A
GOOGLE_TTS_QUALITY_PREFERENCE=neural2
```

#### Popular Hungarian Voices
| Voice ID | Gender | Type | Description |
|----------|---------|------|-------------|
| `hu-HU-Neural2-A` | Female | Neural2 | Clear, natural Hungarian |
| `hu-HU-Neural2-B` | Male | Neural2 | Professional, authoritative |
| `hu-HU-Wavenet-A` | Female | WaveNet | Warm, conversational |
| `hu-HU-Wavenet-B` | Male | WaveNet | Clear, reliable |

### 🎯 ElevenLabs

**Best for**: Premium content, character voices, maximum quality

#### Key Benefits
- **Premium Neural Voices**: Industry-leading voice cloning technology
- **Character Voices**: Distinct personalities and styles
- **Low Latency**: Fast synthesis for real-time applications
- **Voice Cloning**: Custom voice creation (Pro plans)

#### Popular Voice Mappings
When switching from ElevenLabs to Google TTS, these voices are automatically mapped:

| ElevenLabs Voice | Google TTS Equivalent | Description |
|------------------|----------------------|-------------|
| Rachel | `en-US-Neural2-F` | Professional female |
| Adam | `en-US-Neural2-D` | Conversational male |
| Sam | `en-US-Neural2-A` | Authoritative male |
| Bella | `en-US-Neural2-G` | Friendly female |
| Antoni | `en-US-Neural2-J` | Energetic male |

### ⚡ Auto Mode (Smart Selection)

**Best for**: Most users, cost optimization, hassle-free setup

Auto mode intelligently selects the best provider based on:
1. **Cost Preference**: Google TTS preferred for cost savings
2. **Voice Availability**: Fallback if specific voice unavailable
3. **Provider Status**: Automatic failover on API issues
4. **Quality Requirements**: Balances cost vs quality needs

## Usage Guide

### API Usage

#### Provider Selection in Requests
```json
{
  "transcript": "Text to synthesize",
  "tts_provider": "google_tts",
  "voice_id": "hu-HU-Neural2-A",
  "target_language": "hu-HU"
}
```

#### Get Available Providers
```bash
curl http://localhost:8000/v1/tts-providers
```

#### Cost Comparison
```bash
curl http://localhost:8000/v1/tts-cost-comparison?text="Sample text"
```

### CLI Usage

The Hungarian CLI includes an interactive provider selection:

```
🎤 TTS szolgáltató kiválasztása:
   1. ElevenLabs - Prémium neurális hangok (drága)
   2. Google Cloud TTS - Kiváló minőség (90% olcsóbb) ⭐
   3. Automatikus kiválasztás költség alapján

Választás [1-3, alapértelmezett: 3]: 
```

### Environment Configuration

Complete configuration example in `.env`:

```bash
# TTS Provider Selection
TTS_DEFAULT_PROVIDER=auto              # elevenlabs | google_tts | auto
TTS_AUTO_SELECTION_COST_FIRST=true     # Prioritize cost-effective providers
TTS_FALLBACK_ENABLED=true              # Enable automatic fallback

# Google Cloud TTS Settings
GOOGLE_TTS_ENABLED=true
GOOGLE_TTS_REGION=us-central1
GOOGLE_TTS_DEFAULT_VOICE=hu-HU-Neural2-A
GOOGLE_TTS_QUALITY_PREFERENCE=neural2
GOOGLE_TTS_AUDIO_PROFILE=telephony-class-application

# ElevenLabs Settings
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_DEFAULT_VOICE=pNInz6obpgDQGcFmaJgB
ELEVENLABS_MODEL=eleven_multilingual_v2
```

## Cost Analysis

### Per-Character Pricing Comparison

| Provider | Standard | Premium | Ultra Premium |
|----------|----------|---------|---------------|
| **Google TTS** | $0.004/1K | $0.016/1K | $0.016/1K |
| **ElevenLabs** | - | $0.30/1K | $0.30/1K |
| **Savings** | - | **94%** | **94%** |

### Real-World Cost Examples

#### 10-Minute Video Transcript (~1,500 words, ~7,500 characters)

| Provider | Cost | Annual (100 videos) | Savings |
|----------|------|-------------------|---------|
| ElevenLabs | $2.25 | $225.00 | - |
| Google TTS | $0.12 | $12.00 | **94%** |

#### Full-Length Movie Dubbing (~25,000 words, ~125,000 characters)

| Provider | Cost | 10 Movies/Year | Savings |
|----------|------|----------------|---------|
| ElevenLabs | $37.50 | $375.00 | - |
| Google TTS | $2.00 | $20.00 | **95%** |

## Voice Selection Guide

### By Language

#### Hungarian (hu-HU) - 8 voices
- **Neural2-A** (Female) - Natural, professional ⭐ **Recommended**
- **Neural2-B** (Male) - Clear, authoritative
- **Wavenet-A** (Female) - Warm, conversational
- **Wavenet-B** (Male) - Reliable, clear

#### English (en-US) - 120+ voices
- **Neural2-F** (Female) - Professional, clear ⭐ **Rachel equivalent**
- **Neural2-D** (Male) - Conversational ⭐ **Adam equivalent**
- **Neural2-A** (Male) - Authoritative ⭐ **Sam equivalent**
- **Studio-O** (Female) - Premium quality

#### Multi-Language Projects
Google TTS supports 40+ languages with regional variants:
- **German**: de-DE (18 voices)
- **French**: fr-FR (22 voices)  
- **Spanish**: es-ES (16 voices)
- **Italian**: it-IT (14 voices)
- **Portuguese**: pt-BR (12 voices)

### Voice Quality Recommendations

#### For Professional Content
1. **Google Neural2** - Best balance of quality and cost
2. **Google Studio** - Maximum quality when budget allows
3. **ElevenLabs** - When premium branding matters

#### For High-Volume Content
1. **Google WaveNet** - Good quality, lower cost
2. **Google Standard** - Basic quality, minimal cost
3. **Auto mode** - Intelligent cost optimization

## Migration Guide

### From ElevenLabs to Google TTS

#### 1. Update Configuration
```bash
# Change provider preference
TTS_DEFAULT_PROVIDER=google_tts

# Add Google TTS settings
GOOGLE_TTS_REGION=us-central1
GOOGLE_TTS_DEFAULT_VOICE=hu-HU-Neural2-A
```

#### 2. Voice Mapping
The system automatically maps ElevenLabs voices to Google TTS equivalents:
- No code changes required
- Same API calls work with new provider
- Quality maintained or improved

#### 3. Cost Optimization
- **Immediate savings**: 90%+ cost reduction
- **Same quality**: Neural2 voices comparable to ElevenLabs
- **Better features**: SSML support, timestamp preservation

### Testing Your Migration

```bash
# Test provider availability
curl http://localhost:8000/v1/tts-providers

# Test voice discovery  
curl http://localhost:8000/v1/tts-providers/google_tts/voices

# Compare costs
curl http://localhost:8000/v1/tts-cost-comparison?text="Test synthesis"
```

## Troubleshooting

### Common Issues

#### Google TTS Not Available
```bash
# Check service account authentication
docker compose logs transcribe | grep "Google TTS"

# Verify environment variables
docker compose exec transcribe env | grep GOOGLE_TTS
```

#### Voice Not Found
```bash
# List available voices for provider
curl http://localhost:8000/v1/tts-providers/google_tts/voices?language=hu-HU
```

#### Cost Estimation Errors
```bash
# Check provider status
curl http://localhost:8000/v1/tts-providers

# Validate text length
echo "Your text here" | wc -c
```

### Performance Optimization

#### For Large Content
- Enable chunked processing: `CHUNKING_ENABLED=true`
- Increase chunk size: `CHUNK_SIZE=5000`
- Use parallel synthesis: `TTS_PARALLEL_SYNTHESIS=true`

#### For High Throughput
- Use Google TTS: Better rate limits than ElevenLabs
- Configure multiple regions: Automatic failover
- Enable caching: `TTS_CACHE_ENABLED=true`

## Best Practices

### Provider Selection Strategy

1. **Start with Auto Mode**: Let the system choose optimally
2. **Use Google TTS for Production**: 90%+ cost savings
3. **Reserve ElevenLabs for Premium**: Special content only
4. **Test Voice Quality**: Compare before large deployments

### Configuration Recommendations

```bash
# Production-optimized settings
TTS_DEFAULT_PROVIDER=auto
TTS_COST_OPTIMIZATION=true
TTS_FALLBACK_ENABLED=true
GOOGLE_TTS_QUALITY_PREFERENCE=neural2
TTS_PARALLEL_SYNTHESIS=true
```

### Monitoring and Logging

```bash
# Enable detailed TTS logging
LOG_LEVEL=INFO
ENABLE_PERFORMANCE_LOGGING=true

# Monitor usage and costs
curl http://localhost:8000/admin/stats
```

## API Reference

### Core Endpoints

#### List Providers
```http
GET /v1/tts-providers
```

#### Provider Voices
```http
GET /v1/tts-providers/{provider}/voices?language=hu-HU
```

#### Cost Comparison
```http
GET /v1/tts-cost-comparison?text=sample&providers=elevenlabs,google_tts
```

#### Dubbing with Provider Selection
```http
POST /v1/dubbing
Content-Type: application/json

{
  "url": "https://youtube.com/watch?v=...",
  "target_language": "en-US",
  "tts_provider": "google_tts",
  "voice_id": "en-US-Neural2-F",
  "use_chunked_processing": true
}
```

## Support

### Getting Help

For TTS provider issues:
1. Check provider status: `/v1/tts-providers`
2. Review configuration: `.env` file
3. Test authentication: Service account setup
4. Check quotas: Google Cloud console

### Feature Requests

The TTS provider system is designed for extensibility. Future providers can be added following the same abstract interface pattern.

---

## Version Information

**Documentation Version**: 1.0.0  
**Last Updated**: January 15, 2025  
**Status**: Production Ready ✅  
**Google TTS Integration**: Completed January 15, 2025  
**Development Status**: All 7 phases completed successfully  
**Voice Library**: 1,616 Google TTS voices + 25 ElevenLabs voices  
**Cost Savings**: 94% with Google TTS ($0.016 vs $0.30/1K characters)  
**Next Review**: As needed for new features or provider updates

**Implementation Timeline**:
- Phase 1-7: January 9-15, 2025 (7 days development)
- Multi-provider architecture: ✅ Complete
- Voice mapping system: ✅ Complete  
- Hungarian CLI interface: ✅ Complete
- API integration: ✅ Complete
- Documentation & examples: ✅ Complete