# Voice Profile Selection Guide

## 🎤 Complete Guide to TTS Voice Selection

This guide helps you choose the perfect voice for your multilingual dubbing projects using the YouTube Transcription Service with both **Google Cloud TTS** and **ElevenLabs** providers.

## 🏆 Provider Comparison Quick Reference

| Feature | Google Cloud TTS | ElevenLabs | 
|---------|------------------|------------|
| **Cost** | $0.016/1K chars | $0.30/1K chars |
| **Savings** | **94% cheaper** | - |
| **Voices** | 1,616 voices | 20+ premium voices |
| **Languages** | 40+ languages | 29 languages |
| **Quality** | Neural2/Studio | Premium neural |
| **Recommended For** | Production, cost-sensitive | Premium content |

---

## 🌟 Quick Start

### Get Available Voices

#### All Providers
```bash
# List available TTS providers
curl -X GET http://localhost:8000/v1/tts-providers

# Get Google TTS voices (1,616 voices)
curl -X GET http://localhost:8000/v1/tts-providers/google_tts/voices

# Get ElevenLabs voices (20+ premium voices)
curl -X GET http://localhost:8000/v1/tts-providers/elevenlabs/voices

# Filter Google TTS voices by language
curl -X GET "http://localhost:8000/v1/tts-providers/google_tts/voices?language=hu-HU"
```

#### Legacy Endpoint (ElevenLabs only)
```bash
# List all available voices (ElevenLabs)
curl -X GET http://localhost:8000/v1/voices

# Filter by gender
curl -X GET "http://localhost:8000/v1/voices?gender=female"

# Filter by language and use case
curl -X GET "http://localhost:8000/v1/voices?language=en&use_case=narration"
```

### Use in Dubbing Job

#### With Google Cloud TTS (Recommended - 94% Cost Savings)
```bash
curl -X POST http://localhost:8000/v1/dub \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=example",
    "target_language": "en-US",
    "tts_provider": "google_tts",
    "voice_id": "en-US-Neural2-F",
    "translation_context": "educational"
  }'
```

#### With ElevenLabs (Premium Quality)
```bash
curl -X POST http://localhost:8000/v1/dub \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=example",
    "target_language": "en-US",
    "tts_provider": "elevenlabs",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "translation_context": "educational"
  }'
```

#### Auto Provider Selection (Smart Cost Optimization)
```bash
curl -X POST http://localhost:8000/v1/dub \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=example",
    "target_language": "en-US",
    "tts_provider": "auto",
    "translation_context": "educational"
  }'
```

---

## 🎭 Popular Voice Profiles

## 🌟 Google Cloud TTS Voices (Recommended)

### 🇭🇺 Hungarian Voices (hu-HU)

#### **hu-HU-Neural2-A** (Premium Female) ⭐ **Most Popular**
- **Gender**: Female
- **Type**: Neural2 (Premium quality)
- **Tone**: Clear, natural, professional
- **Cost**: $0.016/1K chars
- **Best For**: Educational content, news, professional presentations
- **Sample**: *"Üdvözöljük a mai magyar nyelvű oktatóprogramban..."*

```json
{
  "tts_provider": "google_tts",
  "voice_id": "hu-HU-Neural2-A",
  "translation_context": "educational"
}
```

#### **hu-HU-Neural2-B** (Premium Male)
- **Gender**: Male  
- **Type**: Neural2 (Premium quality)
- **Tone**: Authoritative, clear, trustworthy
- **Cost**: $0.016/1K chars
- **Best For**: Documentaries, business content, authoritative narration
- **Sample**: *"A kutatási eredmények egyértelműen bizonyítják..."*

#### **hu-HU-Wavenet-A** (Enhanced Female)
- **Gender**: Female
- **Type**: WaveNet (Enhanced quality)
- **Tone**: Warm, conversational, friendly
- **Best For**: Casual content, conversations, storytelling

#### **hu-HU-Wavenet-B** (Enhanced Male)
- **Gender**: Male
- **Type**: WaveNet (Enhanced quality)
- **Tone**: Reliable, clear, approachable
- **Best For**: Tutorials, explanations, general content

### 🇺🇸 English (US) Voices - Top Recommendations

#### **en-US-Neural2-F** (Premium Female) ⭐ **Rachel Equivalent**
- **Gender**: Female
- **Type**: Neural2 (Premium quality)
- **Tone**: Professional, clear, educational
- **Cost**: $0.016/1K chars
- **Best For**: Educational content, professional presentations
- **ElevenLabs Equivalent**: Rachel (`21m00Tcm4TlvDq8ikWAM`)

#### **en-US-Neural2-D** (Premium Male) ⭐ **Adam Equivalent**
- **Gender**: Male
- **Type**: Neural2 (Premium quality)  
- **Tone**: Conversational, warm, engaging
- **Best For**: Casual content, narratives, friendly presentations
- **ElevenLabs Equivalent**: Adam (`pNInz6obpgDQGcFmaJgB`)

#### **en-US-Neural2-A** (Premium Male) ⭐ **Sam Equivalent**
- **Gender**: Male
- **Type**: Neural2 (Premium quality)
- **Tone**: Authoritative, confident, professional
- **Best For**: News, documentaries, serious content
- **ElevenLabs Equivalent**: Sam (`yoZ06aMxZJJ28mfd3POQ`)

#### **en-US-Neural2-G** (Premium Female) ⭐ **Bella Equivalent**
- **Gender**: Female
- **Type**: Neural2 (Premium quality)
- **Tone**: Friendly, approachable, versatile
- **Best For**: Lifestyle content, personal stories, reviews
- **ElevenLabs Equivalent**: Bella (`EXAVITQu4vr4xnSDxMaL`)

#### **en-US-Neural2-J** (Premium Male) ⭐ **Antoni Equivalent**
- **Gender**: Male
- **Type**: Neural2 (Premium quality)
- **Tone**: Energetic, versatile, adaptable
- **Best For**: Entertainment, vlogs, dynamic content
- **ElevenLabs Equivalent**: Antoni (`ErXwobaYiN019PkySvjV`)

### 🇬🇧 English (UK) Voices

#### **en-GB-Neural2-A** (Premium Female)
- **Gender**: Female
- **Type**: Neural2 (Premium quality)
- **Accent**: British English
- **Tone**: Sophisticated, clear, cultured
- **Best For**: British content, formal presentations

#### **en-GB-Neural2-B** (Premium Male)
- **Gender**: Male
- **Type**: Neural2 (Premium quality)
- **Accent**: British English  
- **Tone**: Authoritative, refined, professional
- **Best For**: Documentaries, news, educational content

### 🌍 Other Popular Languages

#### German (de-DE) - 18 voices available
- **de-DE-Neural2-F** (Female) - Clear, professional
- **de-DE-Neural2-D** (Male) - Authoritative, reliable

#### French (fr-FR) - 22 voices available  
- **fr-FR-Neural2-A** (Female) - Elegant, clear
- **fr-FR-Neural2-B** (Male) - Professional, warm

#### Spanish (es-ES) - 16 voices available
- **es-ES-Neural2-F** (Female) - Natural, engaging
- **es-ES-Neural2-B** (Male) - Authoritative, clear

### Google TTS Voice Quality Tiers

| Quality Tier | Cost/1K chars | Description | Use Case |
|--------------|---------------|-------------|----------|
| **Standard** | $0.004 | Basic quality | Testing, drafts |
| **WaveNet** | $0.016 | Enhanced quality | Good production |
| **Neural2** | $0.016 | Premium quality ⭐ | **Recommended** |
| **Studio** | $0.016 | Highest quality | Premium content |

---

## 🎯 ElevenLabs Premium Voices

### 🎓 Educational Content

#### **Rachel** (Recommended for Educational)
- **Voice ID**: `21m00Tcm4TlvDq8ikWAM`
- **Gender**: Female
- **Accent**: American
- **Tone**: Calm, clear, professional
- **Best For**: Tutorial videos, educational content, documentaries
- **Age**: Young adult
- **Sample**: *"Welcome to today's lesson on advanced mathematics..."*

```json
{
  "voice_id": "21m00Tcm4TlvDq8ikWAM",
  "translation_context": "educational",
  "target_audience": "students"
}
```

#### **Adam** (Deep, Authoritative)
- **Voice ID**: `pNInz6obpgDQGcFmaJgB`
- **Gender**: Male
- **Accent**: American
- **Tone**: Deep, authoritative, confident
- **Best For**: Documentaries, scientific content, serious topics
- **Age**: Middle aged
- **Sample**: *"Today we'll explore the fundamental principles of quantum physics..."*

### 📺 Casual Content

#### **Sam** (Conversational)
- **Voice ID**: `yoZ06aMxZJJ28mfd3POQ`
- **Gender**: Male
- **Accent**: American
- **Tone**: Friendly, conversational, energetic
- **Best For**: Vlogs, casual conversations, entertainment
- **Age**: Young adult
- **Sample**: *"Hey everyone! Welcome back to my channel..."*

#### **Nicole** (Warm, Engaging)
- **Voice ID**: `piTKgcLEGmPE4e6mEKli`
- **Gender**: Female
- **Accent**: American
- **Tone**: Warm, engaging, approachable
- **Best For**: Lifestyle content, personal stories, reviews
- **Age**: Young adult
- **Sample**: *"So I tried this amazing new recipe yesterday..."*

### 🏢 Professional Content

#### **Josh** (Corporate Professional)
- **Voice ID**: `TxGEqnHWrfWFTfGW9XjX`
- **Gender**: Male
- **Accent**: American
- **Tone**: Professional, confident, corporate
- **Best For**: Business presentations, corporate training, news
- **Age**: Middle aged
- **Sample**: *"Our quarterly results demonstrate significant growth..."*

#### **Bella** (Professional Female)
- **Voice ID**: `EXAVITQu4vr4xnSDxMaL`
- **Gender**: Female
- **Accent**: American
- **Tone**: Professional, articulate, trustworthy
- **Best For**: News reporting, corporate content, formal presentations
- **Age**: Adult
- **Sample**: *"In today's market analysis, we observe several key trends..."*

---

## 🌍 Multi-Language Voices

### English Voices

#### **Dorothy** (British English)
- **Voice ID**: `ThT5KcBeYPX3keUQqHPh`
- **Accent**: British
- **Tone**: Sophisticated, clear, cultured
- **Best For**: British content, historical documentaries, literature

#### **Antoni** (Versatile Male)
- **Voice ID**: `ErXwobaYiN019PkySvjV`
- **Accent**: American
- **Tone**: Versatile, natural, adaptable
- **Best For**: General purpose, adaptable to various contexts

### European Voices

#### **Matilda** (European Accent)
- **Voice ID**: `XrExE9yKIg1WjnnlVkGX`
- **Accent**: European
- **Tone**: Clear, professional, international
- **Best For**: International content, European topics

---

## 🎯 Content Type Recommendations

### 📚 Educational & Tutorial
**Recommended Voices:**
- Rachel (`21m00Tcm4TlvDq8ikWAM`) - Clear, patient
- Adam (`pNInz6obpgDQGcFmaJgB`) - Authoritative
- Dorothy (`ThT5KcBeYPX3keUQqHPh`) - Sophisticated

**Translation Context:** `educational`
**Target Audience:** `students` or `learners`
**Tone:** `clear` or `patient`

### 🎬 Entertainment & Vlogs
**Recommended Voices:**
- Sam (`yoZ06aMxZJJ28mfd3POQ`) - Energetic
- Nicole (`piTKgcLEGmPE4e6mEKli`) - Warm
- Antoni (`ErXwobaYiN019PkySvjV`) - Versatile

**Translation Context:** `casual`
**Target Audience:** `general public`
**Tone:** `conversational` or `friendly`

### 📰 News & Documentary
**Recommended Voices:**
- Adam (`pNInz6obpgDQGcFmaJgB`) - Authoritative
- Bella (`EXAVITQu4vr4xnSDxMaL`) - Professional
- Josh (`TxGEqnHWrfWFTfGW9XjX`) - Corporate

**Translation Context:** `news`
**Target Audience:** `informed viewers`
**Tone:** `neutral` or `professional`

### 🏢 Business & Corporate
**Recommended Voices:**
- Josh (`TxGEqnHWrfWFTfGW9XjX`) - Corporate
- Bella (`EXAVITQu4vr4xnSDxMaL`) - Professional
- Rachel (`21m00Tcm4TlvDq8ikWAM`) - Clear

**Translation Context:** `marketing` or `educational`
**Target Audience:** `professionals`
**Tone:** `professional` or `confident`

### ⚖️ Legal Content
**Recommended Voices:**
- Adam (`pNInz6obpgDQGcFmaJgB`) - Authoritative
- Dorothy (`ThT5KcBeYPX3keUQqHPh`) - Formal
- Bella (`EXAVITQu4vr4xnSDxMaL`) - Trustworthy

**Translation Context:** `legal`
**Target Audience:** `legal professionals`
**Tone:** `formal` or `authoritative`

### 🙏 Spiritual & Motivational
**Recommended Voices:**
- Rachel (`21m00Tcm4TlvDq8ikWAM`) - Calm
- Nicole (`piTKgcLEGmPE4e6mEKli`) - Warm
- Antoni (`ErXwobaYiN019PkySvjV`) - Natural

**Translation Context:** `spiritual`
**Target Audience:** `believers` or `seekers`
**Tone:** `compassionate` or `uplifting`

---

## 🎨 Voice Selection Strategies

### 1. **Match Original Tone**
Choose a voice that matches the energy and tone of the original Hungarian speaker:
- **High energy content** → Sam, Antoni
- **Calm, measured content** → Rachel, Dorothy
- **Professional content** → Josh, Bella

### 2. **Consider Target Audience**
- **Young audience** → Sam, Nicole, Antoni
- **Professional audience** → Josh, Bella, Rachel
- **Academic audience** → Rachel, Adam, Dorothy
- **General public** → Rachel, Antoni, Nicole

### 3. **Content Length Matters**
- **Short videos (<5 min)** → Any voice works well
- **Medium videos (5-15 min)** → Choose engaging voices (Sam, Nicole, Antoni)
- **Long videos (15+ min)** → Choose clear, non-fatiguing voices (Rachel, Adam)

### 4. **Accent Preferences**
- **American audience** → American accent voices (Rachel, Adam, Sam)
- **British audience** → Dorothy (British accent)
- **International audience** → Matilda, Rachel (clear, neutral)

---

## 🛠️ Implementation Examples

### CLI Usage

```bash
# Interactive CLI with voice selection
docker compose run --rm transcribe python -m src.main --mode cli --interactive
```

The CLI will present a Hungarian-language voice selection menu:
```
🎤 Hang kiválasztása (ElevenLabs):
   1. Rachel (nő, amerikai) - Oktatás, dokumentumok
   2. Adam (férfi, amerikai) - Tekintélyteljes, tudományos
   3. Sam (férfi, amerikai) - Barátságos, szórakoztató
   4. Nicole (nő, amerikai) - Meleg, személyes
   5. Josh (férfi, amerikai) - Üzleti, professzionális

Választás [1-5, Enter = 1]: 1
✓ Kiválasztva: Rachel (nő, amerikai, oktatás)
```

### API Usage

```python
import httpx

def select_voice_for_content(content_type: str, target_audience: str):
    """Smart voice selection based on content analysis."""
    
    # Get available voices
    client = httpx.Client()
    voices_response = client.get("http://localhost:8000/v1/voices")
    voices = voices_response.json()["voices"]
    
    # Selection logic
    if content_type == "educational":
        return next(v for v in voices if v["name"] == "Rachel")
    elif content_type == "business":
        return next(v for v in voices if v["name"] == "Josh")
    elif content_type == "entertainment":
        return next(v for v in voices if v["name"] == "Sam")
    else:
        return next(v for v in voices if v["name"] == "Antoni")  # Versatile

# Usage
voice = select_voice_for_content("educational", "students")
job_response = httpx.post("http://localhost:8000/v1/dub", json={
    "url": "https://youtube.com/watch?v=example",
    "target_language": "en-US",
    "voice_id": voice["voice_id"],
    "translation_context": "educational"
})
```

### Batch Processing with Voice Matching

```python
def process_channel_with_consistent_voice(channel_urls: list, content_type: str):
    """Process multiple videos from a channel with consistent voice."""
    
    # Select appropriate voice once
    voice_mapping = {
        "educational": "21m00Tcm4TlvDq8ikWAM",  # Rachel
        "business": "TxGEqnHWrfWFTfGW9XjX",     # Josh
        "entertainment": "yoZ06aMxZJJ28mfd3POQ", # Sam
        "news": "pNInz6obpgDQGcFmaJgB"          # Adam
    }
    
    voice_id = voice_mapping.get(content_type, "21m00Tcm4TlvDq8ikWAM")
    
    jobs = []
    for url in channel_urls:
        job = httpx.post("http://localhost:8000/v1/dub", json={
            "url": url,
            "target_language": "en-US",
            "voice_id": voice_id,
            "translation_context": content_type,
            "enable_video_muxing": True
        })
        jobs.append(job.json()["job_id"])
    
    return jobs
```

---

## 🎧 Voice Quality Settings

### Audio Quality Levels

#### **High Quality** (Recommended for Production)
- **Setting**: `"audio_quality": "high"`
- **Characteristics**: Best possible audio fidelity
- **Cost**: Highest ElevenLabs cost (~$0.30/1K chars)
- **Processing Time**: Slower
- **Use For**: Final production, important content

#### **Medium Quality** (Balanced)
- **Setting**: `"audio_quality": "medium"`
- **Characteristics**: Good quality with reasonable cost
- **Cost**: Standard ElevenLabs rate
- **Processing Time**: Moderate
- **Use For**: Most content, previews

#### **Low Quality** (Testing)
- **Setting**: `"audio_quality": "low"`
- **Characteristics**: Faster processing, lower fidelity
- **Cost**: Lowest cost
- **Processing Time**: Fastest
- **Use For**: Testing, drafts, quick previews

### ElevenLabs Models

#### **Multilingual V2** (Recommended)
- **Model**: `eleven_multilingual_v2`
- **Languages**: 29 languages supported
- **Quality**: High quality, natural pronunciation
- **Speed**: Good balance of quality and speed

#### **Multilingual V1** (Fallback)
- **Model**: `eleven_multilingual_v1`
- **Languages**: Fewer languages
- **Quality**: Good quality
- **Speed**: Faster processing

---

## 📊 Cost Optimization

### Voice Selection Cost Factors

1. **Character Count**: Longer content = higher cost
2. **Quality Setting**: High quality costs more
3. **Model Choice**: Multilingual V2 is premium
4. **Processing Time**: Complex voices take longer

### Cost-Effective Strategies

#### **Preview Mode**
Test voices with short previews before full processing:
```python
# Preview first 30 seconds
preview_request = {
    "url": "https://youtube.com/watch?v=example",
    "test_mode": True,  # Only first 60 seconds
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "audio_quality": "medium"
}
```

#### **Voice Reuse**
Use consistent voices across channel content:
- Establishes brand identity
- Reduces decision complexity
- Enables bulk processing discounts

#### **Quality Tiers**
- **Draft/Review**: Low quality for internal review
- **Client Preview**: Medium quality for client approval  
- **Final Delivery**: High quality for final production

---

## 🔧 Advanced Configuration

### Custom Voice Parameters

```python
synthesis_request = {
    "script_text": "[00:00:01] Hello world",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "model": "eleven_multilingual_v2",
    "audio_quality": "high",
    "optimize_streaming_latency": False,
    "output_format": "mp3_44100_128",
    # Advanced ElevenLabs settings
    "stability": 0.75,        # Voice consistency (0.0-1.0)
    "similarity_boost": 0.85, # Voice similarity (0.0-1.0) 
    "style": 0.25,            # Style strength (0.0-1.0)
    "use_speaker_boost": True # Enhanced clarity
}
```

### Voice Cloning (Future)
Planning support for:
- Custom voice profiles
- Speaker adaptation
- Multi-speaker content
- Voice characteristic fine-tuning

---

## 🚨 Troubleshooting

### Common Voice Issues

#### **Voice Sounds Robotic**
- **Solution**: Increase stability setting (0.75-0.9)
- **Alternative**: Try different voice (Rachel → Antoni)
- **Check**: Audio quality setting (use "high")

#### **Wrong Pronunciation**
- **Solution**: Use phonetic spelling in translation
- **Alternative**: Different voice with better language support
- **Check**: Target language setting matches voice capabilities

#### **Audio Too Fast/Slow**
- **Solution**: ElevenLabs automatically matches original timing
- **Check**: Transcript timestamps are accurate
- **Alternative**: Manual speed adjustment in post-processing

#### **Voice Doesn't Match Content**
- **Solution**: Review content type recommendations above
- **Test**: Use preview mode with 2-3 different voices
- **Consider**: Target audience preferences

### Error Codes

#### **VOICE_NOT_FOUND**
```json
{
  "error": "Voice ID 'invalid123' not found",
  "available_voices": ["21m00Tcm4TlvDq8ikWAM", "pNInz6obpgDQGcFmaJgB"]
}
```

#### **SYNTHESIS_FAILED**
- Check ElevenLabs API key validity
- Verify account quota/credits
- Ensure text length is within limits

#### **AUDIO_QUALITY_ERROR**
- Use valid quality settings: "low", "medium", "high"
- Check account tier supports requested quality

---

## 🎯 Best Practices

### 1. **Voice Testing Workflow**
1. **Preview Mode**: Test 2-3 voices with first 60 seconds
2. **Content Review**: Match voice to content type and audience  
3. **Quality Check**: Verify audio quality meets requirements
4. **Consistency**: Use same voice across related content

### 2. **Production Workflow**
1. **Content Analysis**: Identify content type, audience, tone
2. **Voice Selection**: Use this guide's recommendations
3. **Preview Generation**: Create short preview for approval
4. **Full Processing**: Process with approved voice and settings
5. **Quality Assurance**: Review final output before delivery

### 3. **Channel Branding**
- **Consistent Voice**: Use same voice for all channel content
- **Voice Documentation**: Document chosen voice for future videos
- **Brand Guidelines**: Include voice selection in brand guidelines
- **Backup Voices**: Identify 2-3 alternative voices if primary unavailable

---

## 📈 Voice Analytics & Optimization

### Performance Metrics

Track these metrics to optimize voice selection:
- **Processing Time**: How long synthesis takes
- **Audio Quality Score**: Technical quality assessment
- **User Engagement**: If audience responds positively
- **Error Rate**: How often synthesis fails
- **Cost Per Character**: Economic efficiency

### A/B Testing

Test different voices for similar content:
```python
test_voices = [
    "21m00Tcm4TlvDq8ikWAM",  # Rachel
    "pNInz6obpgDQGcFmaJgB",  # Adam  
    "yoZ06aMxZJJ28mfd3POQ"   # Sam
]

for voice_id in test_voices:
    job = create_dubbing_job(
        url="https://youtube.com/watch?v=test",
        voice_id=voice_id,
        test_mode=True  # First 60 seconds only
    )
    # Compare results, audience feedback, processing time
```

---

## 📝 Quick Reference

### Most Popular Voices by Category

| Category | Voice | ID | Gender | Accent |
|----------|-------|----|---------| -------|
| **Educational** | Rachel | `21m00Tcm4TlvDq8ikWAM` | Female | American |
| **Professional** | Josh | `TxGEqnHWrfWFTfGW9XjX` | Male | American |
| **Casual** | Sam | `yoZ06aMxZJJ28mfd3POQ` | Male | American |
| **Authoritative** | Adam | `pNInz6obpgDQGcFmaJgB` | Male | American |
| **Warm/Personal** | Nicole | `piTKgcLEGmPE4e6mEKli` | Female | American |
| **British** | Dorothy | `ThT5KcBeYPX3keUQqHPh` | Female | British |
| **Versatile** | Antoni | `ErXwobaYiN019PkySvjV` | Male | American |

### API Quick Commands

```bash
# List voices
curl -X GET http://localhost:8000/v1/voices

# Create dubbing job with specific voice
curl -X POST http://localhost:8000/v1/dub \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=ID", "voice_id": "21m00Tcm4TlvDq8ikWAM"}'

# Get job status
curl -X GET http://localhost:8000/v1/dubbing/{job_id}
```

**Perfect voice selection leads to professional dubbing results! 🎭**

---

For more information, see:
- [Complete API Reference](./API_REFERENCE.md)
- [Dubbing Guide](./DUBBING_GUIDE.md)
- [Quick Start Guide](./QUICK_START.md)