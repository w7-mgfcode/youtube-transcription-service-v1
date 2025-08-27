Development Plan: Multilingual Audio Dubbing Feature
A) Objective
To extend the existing YouTube transcription service with a complete, multilingual audio dubbing solution. This solution will support context-aware translation and leverage ElevenLabs' voice synthesis to replace the original audio track in a video.

B) Key Requirements
Functional (Must)
Translate existing Hungarian transcripts into a target language using a context-aware Vertex AI prompt.

Integrate with the ElevenLabs TTS API for timestamp-based voice synthesis.

Mux the video, replacing the original audio with the newly synthesized audio track.

Allow users to choose a translation context (e.g., legal, spiritual, marketing).

Preserve timing throughout the entire process.

Functional (Should)
Support additional TTS providers like Azure and Google WaveNet.

Allow users to select different voice characters and styles.

Include a preview mode that generates only the audio without video muxing.

Non-Functional
Translation Accuracy: Achieve over 95% accuracy while preserving timing.

Audio Quality: Maintain or exceed the quality of the original YouTube source.

Processing Time: p95 should be less than three times the original video's length.

Video Length: Support videos up to 30 minutes in length due to API limitations.

C) Minimal Architecture
graph TD
    Input[YouTube URL] --> TS[TranscriptionService]
    TS --> MA[Hungarian Transcript]
    MA --> TR{Translation Requested?}
    TR -->|Yes| TM[TranslationModule]
    TM --> TAI[Translation AI<br/>Vertex+Context]
    TAI --> TA[Target Language Transcript]
    TA --> SY{TTS Requested?}
    SY -->|Yes| SM[SynthesisModule]
    SM --> EL[ElevenLabs API]
    EL --> SF[Synthesized Audio File]
    SF --> VM[VideoMuxer]
    VM --> FF[FFmpeg Audio Replace]
    FF --> FV[Final Dubbed Video]
    TR -->|No| MA
    SY -->|No| TA

D) Processing Flow
Original Pipeline: The process begins with the existing, unchanged Hungarian transcription pipeline.

Translation Decision: If a translation is requested, the user selects the context and target language.

Context-Aware Translation: A Vertex AI prompt is generated based on the selected style and target audience.

Synthesis Decision: If TTS is requested, the user selects a voice profile.

Timestamp Processing: The target language script is converted into the ElevenLabs JSON format.

Audio Synthesis: An API call is made to ElevenLabs with the timestamp data.

Video Muxing: FFmpeg is used to replace the original audio track and generate the final output.

Cleanup: All temporary files are deleted.

ASSUMPTION: The ElevenLabs API supports timing for Hungarian-to-target-language audio.
ASSUMPTION: The maximum video length is 30 minutes due to API and processing limits.

E) Modified Module Structure
src/core/
├── translator.py        # NEW - Context-aware translation
├── synthesizer.py       # NEW - TTS integration (ElevenLabs)
├── video_muxer.py       # NEW - FFmpeg video/audio mixing
└── dubbing_service.py   # NEW - Full dubbing orchestrator

src/models.py            # EXPAND - Translation and TTS models
src/config.py            # EXPAND - ElevenLabs and translation config

F) Data Model (Pydantic) Expansions
from enum import Enum
from pydantic import BaseModel
from typing import Optional

class TranslationContext(str, Enum):
    LEGAL = "legal"
    SPIRITUAL = "spiritual"
    MARKETING = "marketing"
    SCIENTIFIC = "scientific"
    CASUAL = "casual"

class TranscribeRequest(BaseModel):  # Extend existing model
    # ... existing fields ...
    enable_translation: bool = False
    target_language: str = "en-US"
    translation_context: TranslationContext = TranslationContext.CASUAL
    target_audience: str = "general public"
    desired_tone: str = "neutral"
    translation_goal: str = "accuracy"

    enable_synthesis: bool = False
    voice_id: Optional[str] = None  # ElevenLabs voice ID
    synthesis_model: str = "eleven_multilingual_v2"

class DubbingJob(BaseModel):
    base_job_id: str  # Original transcription job
    translation_file: Optional[str] = None
    audio_file: Optional[str] = None
    final_video: Optional[str] = None
    synthesis_status: str = "pending"

G) Key Component Code
core/translator.py
import re
from typing import Optional
from enum import Enum

class TranslationContext(str, Enum):
    LEGAL = "legal"
    SPIRITUAL = "spiritual"
    MARKETING = "marketing"
    SCIENTIFIC = "scientific"
    CASUAL = "casual"

class ContextAwareTranslator:
    def __init__(self):
        # self.vertex_client = self._init_vertex()
        pass

    def translate_script(self, script_text: str, context: TranslationContext,
                         target_lang: str, audience: str, tone: str) -> Optional[str]:
        """Context-aware translation while preserving timestamps."""
        prompt = self._build_context_prompt(script_text, context, target_lang, audience, tone)

        # Multi-region/model fallback like in postprocessor
        # for region, model in self._get_model_combinations():
        #     try:
        #         # vertexai.init(project=settings.vertex_project_id, location=region)
        #         # model_instance = GenerativeModel(model)
        #         # response = model_instance.generate_content(prompt)
        #         # return self._validate_translation_output(response.text, script_text)
        #         pass  # Placeholder for actual implementation
        #     except Exception:
        #         continue
        return None

    def _build_context_prompt(self, script: str, context: TranslationContext,
                              target_lang: str, audience: str, tone: str) -> str:
        context_instructions = {
            TranslationContext.SPIRITUAL: "Preserve the spiritual, uplifting, and compassionate tone...",
            TranslationContext.LEGAL: "Keep the formal legal register, ensure precise terminology...",
            TranslationContext.MARKETING: "Adapt it for marketing purposes: make it persuasive...",
        }
        return f"""Translate the following Hungarian timed script into {target_lang}.
CRITICAL: You are translating a TIMED SCRIPT for audio synthesis. The timing is SACRED.

TRANSLATION CONTEXT:
- Type of content: {context.value}
- Target audience: {audience}
- Desired tone: {tone}
- Special instruction: {context_instructions.get(context, "Maintain natural tone")}

TIMING PRESERVATION RULES:
1. PRESERVE ALL TIMESTAMPS [HH:MM:SS] exactly as they are.
2. Translated text must fit the same time slots.
3. If translation is longer, split lines but keep the same timestamps.
4. If translation is shorter, you may merge adjacent lines.
5. Keep pause markers: [levegővétel] → [breath], [szünet] → [pause]

INPUT HUNGARIAN SCRIPT:
{script[:6000]}  # Chunking support

TRANSLATED {target_lang.upper()} SCRIPT:"""

core/synthesizer.py
import httpx
import re
from typing import List, Dict

class ElevenLabsSynthesizer:
    def __init__(self):
        # self.api_key = settings.elevenlabs_api_key
        self.client = httpx.Client(timeout=300.0)

    def synthesize_script(self, script_text: str, voice_id: str,
                          output_path: str) -> bool:
        """Text -> audio file with ElevenLabs timestamp API."""
        timestamps_data = self._script_to_elevenlabs_format(script_text)
        try:
            # response = self.client.post(
            #     "https://api.elevenlabs.io/v1/text-to-speech-with-timestamps",
            #     headers={"xi-api-key": self.api_key},
            #     json={
            #         "voice_id": voice_id,
            #         "model_id": "eleven_multilingual_v2",
            #         "text_segments": timestamps_data,
            #         "output_format": "mp3_44100_128"
            #     }
            # )
            # if response.status_code == 200:
            #     with open(output_path, "wb") as f:
            #         f.write(response.content)
            #     return True
            pass  # Placeholder
        except Exception as e:
            print(f"ElevenLabs synthesis error: {e}")
        return False

    def _script_to_elevenlabs_format(self, script: str) -> List[Dict]:
        """Hungarian timed script -> ElevenLabs JSON format."""
        segments = []
        lines = script.split('\n')
        for line in lines:
            timestamp_match = re.match(r'\[(\d+):(\d+):(\d+)\]\s*(.*)', line)
            if timestamp_match:
                hours, minutes, seconds, text = timestamp_match.groups()
                start_time = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
                if text and not text.startswith('['):
                    segments.append({
                        "text": text.strip(),
                        "start_time": start_time
                    })
        for i, segment in enumerate(segments[:-1]):
            segment["end_time"] = segments[i+1]["start_time"] - 0.1
        if segments:
            segments[-1]["end_time"] = segments[-1]["start_time"] + len(segments[-1]["text"]) * 0.1
        return segments

core/video_muxer.py
import os
import subprocess

class VideoMuxer:
    def replace_audio_in_video(self, original_video_url: str,
                               new_audio_path: str, output_path: str) -> bool:
        """Replace original video audio with new synthesized audio."""
        temp_video = self._download_video_only(original_video_url)
        if not temp_video:
            return False
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', temp_video,
                '-i', new_audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        finally:
            if os.path.exists(temp_video):
                os.remove(temp_video)
        return False

    def _download_video_only(self, url: str) -> str:
        # Placeholder for video download logic
        return "path/to/video.mp4"

H) API Expansion
New Endpoints
POST /v1/translate: Translates an existing Hungarian transcript.

POST /v1/dub: Creates a full dubbing job (transcription → translation → TTS → video).

GET /v1/voices: Lists available voices from ElevenLabs.

I) Configuration Examples
.env Expansion
# Translation settings
ENABLE_TRANSLATION=true
DEFAULT_TARGET_LANGUAGE=en-US
DEFAULT_TRANSLATION_CONTEXT=casual

# ElevenLabs settings
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_DEFAULT_VOICE=pNInz6obpgDQGcFmaJgB
ELEVENLABS_MODEL=eleven_multilingual_v2

# Video processing
MAX_VIDEO_LENGTH_MINUTES=30
TEMP_VIDEO_DIR=/app/temp/videos

J) Security Considerations
Risk

Control

ElevenLabs API Key Leakage

Use environment variables and secrets management.

Large Video File Storage

Implement automatic cleanup and disk limit monitoring.

Copyrighted Video Downloads

Use the original video URL and include a fair use disclaimer.

TTS Quota Exceeded

Implement rate limiting and cost monitoring.

K) Next Steps
Now (Sprint 1)
Implement the translator.py module with the context prompt.

Integrate the ElevenLabs API in synthesizer.py.

Create a basic test pipeline for Hungarian to English translation.

Expand the CLI mode to include translation options.

Next (Sprint 2)
Implement video muxing in video_muxer.py.

Develop the full dubbing orchestrator in dubbing_service.py.

Expand the API with the new endpoints.

Create a UI for selecting voice profiles.

Later (Sprint 3+)
Integrate additional TTS providers (Azure, Google).

Add fine-tuning for voice characters.

Implement a preview mode for audio-only output.

Add batch dubbing for multiple languages.

L) Open Questions & Assumptions
OPEN: Does the ElevenLabs timestamp API accurately support timing conversion from Hungarian to English?

OPEN: How does video muxing perform with large (>100MB) files?

ASSUMPTION: FFmpeg can swap audio without quality loss.

ASSUMPTION: Vertex AI translation can maintain timing with over 95% accuracy.

ASSUMPTION: A maximum video length of 30 minutes is acceptable.

M) Performance Optimization
Parallel Processing: Download the video and translate the transcript simultaneously.

Streaming TTS: Use chunk-based synthesis for long texts.

Video Preprocessing: Download only the audio track when possible.

Cache Voices: Cache frequently used voice profiles locally.

Progress Tracking: Provide realistic ETA estimates for each step.