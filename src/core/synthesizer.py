"""ElevenLabs TTS integration for audio synthesis with timestamp support."""

import os
import re
import datetime
from typing import Optional, Dict, List, Tuple
from pathlib import Path

from ..config import settings
from ..utils.colors import Colors


class VoiceNotFoundError(Exception):
    """Raised when a requested voice ID is not found."""
    pass


class SynthesisError(Exception):
    """Raised when audio synthesis fails."""
    pass


class ElevenLabsSynthesizer:
    """ElevenLabs TTS synthesizer with timestamp-based audio generation."""
    
    def __init__(self):
        self.api_key = settings.elevenlabs_api_key
        self.base_url = settings.elevenlabs_base_url
        self.default_voice = settings.elevenlabs_default_voice
        self.model = settings.elevenlabs_model
        
        if not self.api_key:
            print(Colors.WARNING + "⚠ ElevenLabs API key not configured!" + Colors.ENDC)
            print(Colors.WARNING + "   Set ELEVENLABS_API_KEY environment variable" + Colors.ENDC)
    
    def synthesize_script(self, 
                         script_text: str, 
                         voice_id: str,
                         output_path: str,
                         model: Optional[str] = None,
                         optimize_streaming: bool = False,
                         audio_quality: str = "high") -> Dict:
        """
        Synthesize timed script to audio file using ElevenLabs API.
        
        Args:
            script_text: Translated script with timestamps
            voice_id: ElevenLabs voice ID
            output_path: Path to save generated audio file
            model: TTS model to use (defaults to config)
            optimize_streaming: Optimize for streaming latency
            audio_quality: Audio quality (low, medium, high)
            
        Returns:
            Dictionary with synthesis result and metadata
        """
        print(Colors.BLUE + f"\n🎵 ElevenLabs audio synthesis indítása..." + Colors.ENDC)
        start_time = datetime.datetime.now()
        
        if not self.api_key:
            raise SynthesisError("ElevenLabs API key not configured")
        
        try:
            # Convert script to ElevenLabs format
            segments = self._script_to_elevenlabs_format(script_text)
            if not segments:
                raise SynthesisError("No valid segments found in script")
            
            print(Colors.CYAN + f"   ├─ {len(segments)} audio segment készítése" + Colors.ENDC)
            print(Colors.CYAN + f"   ├─ Voice: {voice_id}" + Colors.ENDC)
            
            # Determine synthesis method based on content length
            total_chars = sum(len(segment['text']) for segment in segments)
            
            if len(segments) > 50 or total_chars > 10000:
                # Use chunked synthesis for long content
                result = self._synthesize_chunked(segments, voice_id, output_path, model, audio_quality)
            else:
                # Use single API call for short content
                result = self._synthesize_single_call(segments, voice_id, output_path, model, audio_quality)
            
            processing_time = (datetime.datetime.now() - start_time).total_seconds()
            
            # Add metadata
            result.update({
                'processing_time_seconds': processing_time,
                'segments_processed': len(segments),
                'total_characters': total_chars,
                'voice_id': voice_id,
                'model': model or self.model,
                'audio_quality': audio_quality
            })
            
            print(Colors.GREEN + f"   ✓ Audio synthesis kész: {result.get('duration_seconds', 0):.1f}s audio" + Colors.ENDC)
            
            return result
            
        except Exception as e:
            print(Colors.FAIL + f"✗ ElevenLabs synthesis hiba: {e}" + Colors.ENDC)
            raise SynthesisError(f"Audio synthesis failed: {e}")
    
    def _synthesize_single_call(self, segments: List[Dict], voice_id: str, 
                              output_path: str, model: Optional[str], 
                              audio_quality: str) -> Dict:
        """Synthesize audio using single API call for shorter content."""
        try:
            import httpx
            
            # Combine all text segments
            full_text = ' '.join(segment['text'] for segment in segments if segment['text'].strip())
            
            print(Colors.CYAN + f"   ├─ Single API call synthesis ({len(full_text)} karakter)" + Colors.ENDC)
            
            # Configure output format based on quality
            output_format = self._get_output_format(audio_quality)
            
            # Make API request
            with httpx.Client(timeout=300.0) as client:
                response = client.post(
                    f"{self.base_url}/text-to-speech/{voice_id}",
                    headers={
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": full_text,
                        "model_id": model or self.model,
                        "output_format": output_format,
                        "voice_settings": self._get_voice_settings(audio_quality)
                    }
                )
                
                if response.status_code == 200:
                    # Save audio file
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    
                    # Get file info
                    file_size = os.path.getsize(output_path)
                    duration = self._estimate_audio_duration(len(full_text))
                    
                    return {
                        'audio_file_path': output_path,
                        'duration_seconds': duration,
                        'file_size_bytes': file_size,
                        'format': output_format,
                        'sample_rate': self._get_sample_rate(output_format),
                        'estimated_cost': self._estimate_synthesis_cost(len(full_text)),
                        'method': 'single_call'
                    }
                else:
                    error_msg = f"ElevenLabs API error {response.status_code}: {response.text}"
                    raise SynthesisError(error_msg)
                    
        except ImportError:
            raise SynthesisError("httpx library not installed. Run: pip install httpx")
    
    def _synthesize_chunked(self, segments: List[Dict], voice_id: str, 
                          output_path: str, model: Optional[str], 
                          audio_quality: str) -> Dict:
        """Synthesize audio using chunked approach for longer content."""
        print(Colors.YELLOW + f"   📑 Chunked audio synthesis ({len(segments)} segments)" + Colors.ENDC)
        
        try:
            import httpx
            from pydub import AudioSegment
            
            # Group segments into chunks (max ~500 chars per chunk)
            chunks = self._group_segments_into_chunks(segments, max_chars=500)
            print(Colors.CYAN + f"   ├─ {len(chunks)} audio chunk készítése" + Colors.ENDC)
            
            output_format = self._get_output_format(audio_quality)
            temp_files = []
            total_cost = 0.0
            
            with httpx.Client(timeout=300.0) as client:
                for i, (chunk_segments, start_time, end_time) in enumerate(chunks):
                    chunk_text = ' '.join(seg['text'] for seg in chunk_segments if seg['text'].strip())
                    if not chunk_text.strip():
                        continue
                    
                    print(Colors.CYAN + f"   ├─ Chunk {i+1}/{len(chunks)} synthesis ({len(chunk_text)} kar.)" + Colors.ENDC)
                    
                    # Create temporary file for chunk
                    temp_file = f"{output_path}.chunk_{i}.mp3"
                    temp_files.append(temp_file)
                    
                    # Synthesize chunk
                    response = client.post(
                        f"{self.base_url}/text-to-speech/{voice_id}",
                        headers={
                            "xi-api-key": self.api_key,
                            "Content-Type": "application/json"
                        },
                        json={
                            "text": chunk_text,
                            "model_id": model or self.model,
                            "output_format": "mp3_44100_128",  # Standard for chunking
                            "voice_settings": self._get_voice_settings(audio_quality)
                        }
                    )
                    
                    if response.status_code != 200:
                        raise SynthesisError(f"Chunk {i+1} synthesis failed: {response.text}")
                    
                    with open(temp_file, "wb") as f:
                        f.write(response.content)
                    
                    total_cost += self._estimate_synthesis_cost(len(chunk_text))
                    print(Colors.GREEN + f"   ✓ Chunk {i+1} kész" + Colors.ENDC)
            
            # Merge audio chunks
            print(Colors.CYAN + "   ├─ Audio chunk-ok egyesítése..." + Colors.ENDC)
            merged_audio = self._merge_audio_chunks(temp_files, chunks)
            
            # Save final file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            merged_audio.export(output_path, format=self._get_pydub_format(output_format))
            
            # Cleanup temp files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            # Get final file info
            file_size = os.path.getsize(output_path)
            duration = len(merged_audio) / 1000.0  # Convert ms to seconds
            
            print(Colors.GREEN + f"   ✓ Chunked synthesis kész: {len(chunks)} chunk összevonva" + Colors.ENDC)
            
            return {
                'audio_file_path': output_path,
                'duration_seconds': duration,
                'file_size_bytes': file_size,
                'format': output_format,
                'sample_rate': merged_audio.frame_rate,
                'estimated_cost': total_cost,
                'method': 'chunked',
                'chunks_processed': len(chunks)
            }
            
        except ImportError as e:
            missing_lib = "httpx" if "httpx" not in str(e) else "pydub"
            raise SynthesisError(f"Required library not installed: {missing_lib}. Run: pip install {missing_lib}")
    
    def _script_to_elevenlabs_format(self, script: str) -> List[Dict]:
        """Convert timestamped script to ElevenLabs segment format."""
        segments = []
        lines = script.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Match timestamp pattern [HH:MM:SS] or [H:MM:SS] or [M:SS]
            timestamp_match = re.match(r'\\[(\\d{1,2}):(\\d{2}):(\\d{2})\\]\\s*(.*)', line)
            
            if timestamp_match:
                hours, minutes, seconds, text = timestamp_match.groups()
                start_time = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
                
                # Filter out pause markers and empty text
                if text and not text.startswith('[') and text.strip():
                    # Clean text for TTS
                    clean_text = self._clean_text_for_tts(text.strip())
                    if clean_text:
                        segments.append({
                            "text": clean_text,
                            "start_time": start_time,
                            "original_line": line
                        })
        
        # Calculate end times
        for i in range(len(segments) - 1):
            segments[i]["end_time"] = segments[i + 1]["start_time"] - 0.1
        
        # Set end time for last segment
        if segments:
            last_segment = segments[-1]
            # Estimate duration based on text length (roughly 150 words per minute)
            estimated_duration = len(last_segment["text"].split()) / 2.5  # ~150 wpm = 2.5 words/second
            last_segment["end_time"] = last_segment["start_time"] + max(estimated_duration, 1.0)
        
        return segments
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for better TTS synthesis."""
        # Remove or replace problematic characters
        text = re.sub(r'[\\[\\]{}]', '', text)  # Remove brackets and braces
        text = re.sub(r'\\s+', ' ', text)  # Normalize whitespace
        text = text.strip()
        
        # Don't synthesize very short or meaningless text
        if len(text) < 3:
            return ""
        
        return text
    
    def _group_segments_into_chunks(self, segments: List[Dict], max_chars: int = 500) -> List[Tuple[List[Dict], float, float]]:
        """Group segments into chunks for efficient synthesis."""
        chunks = []
        current_chunk = []
        current_chars = 0
        chunk_start_time = None
        
        for segment in segments:
            segment_chars = len(segment['text'])
            
            # Start new chunk if needed
            if chunk_start_time is None:
                chunk_start_time = segment['start_time']
            
            # Add to current chunk if within limits
            if current_chars + segment_chars <= max_chars and len(current_chunk) < 20:
                current_chunk.append(segment)
                current_chars += segment_chars
            else:
                # Finish current chunk
                if current_chunk:
                    chunk_end_time = current_chunk[-1].get('end_time', current_chunk[-1]['start_time'] + 1)
                    chunks.append((current_chunk, chunk_start_time, chunk_end_time))
                
                # Start new chunk
                current_chunk = [segment]
                current_chars = segment_chars
                chunk_start_time = segment['start_time']
        
        # Add final chunk
        if current_chunk:
            chunk_end_time = current_chunk[-1].get('end_time', current_chunk[-1]['start_time'] + 1)
            chunks.append((current_chunk, chunk_start_time, chunk_end_time))
        
        return chunks
    
    def _merge_audio_chunks(self, temp_files: List[str], chunks: List[Tuple]) -> 'AudioSegment':
        """Merge audio chunks with proper timing."""
        try:
            from pydub import AudioSegment
            
            # Load all audio chunks
            audio_chunks = []
            for temp_file, (chunk_segments, start_time, end_time) in zip(temp_files, chunks):
                if os.path.exists(temp_file):
                    chunk_audio = AudioSegment.from_mp3(temp_file)
                    audio_chunks.append((chunk_audio, start_time, end_time))
            
            if not audio_chunks:
                raise SynthesisError("No audio chunks to merge")
            
            # Calculate total duration
            total_duration_ms = int(max(end_time for _, _, end_time in audio_chunks) * 1000)
            
            # Create silent base track
            merged = AudioSegment.silent(duration=total_duration_ms)
            
            # Overlay each chunk at its proper time
            for chunk_audio, start_time, _ in audio_chunks:
                start_ms = int(start_time * 1000)
                merged = merged.overlay(chunk_audio, position=start_ms)
            
            return merged
            
        except ImportError:
            raise SynthesisError("pydub library required for audio merging")
    
    def _get_output_format(self, quality: str) -> str:
        """Get ElevenLabs output format based on quality setting."""
        quality_formats = {
            "low": "mp3_22050_32",
            "medium": "mp3_44100_64", 
            "high": "mp3_44100_128"
        }
        return quality_formats.get(quality, "mp3_44100_128")
    
    def _get_pydub_format(self, elevenlabs_format: str) -> str:
        """Convert ElevenLabs format to pydub format."""
        if "mp3" in elevenlabs_format:
            return "mp3"
        elif "wav" in elevenlabs_format:
            return "wav"
        else:
            return "mp3"  # Default
    
    def _get_sample_rate(self, output_format: str) -> int:
        """Extract sample rate from output format."""
        if "22050" in output_format:
            return 22050
        elif "44100" in output_format:
            return 44100
        else:
            return 44100  # Default
    
    def _get_voice_settings(self, quality: str) -> Dict:
        """Get voice settings based on quality."""
        if quality == "high":
            return {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        elif quality == "medium":
            return {
                "stability": 0.6,
                "similarity_boost": 0.7,
                "style": 0.0,
                "use_speaker_boost": False
            }
        else:  # low quality - faster processing
            return {
                "stability": 0.7,
                "similarity_boost": 0.6,
                "style": 0.0,
                "use_speaker_boost": False
            }
    
    def _estimate_audio_duration(self, text_length: int) -> float:
        """Estimate audio duration based on text length."""
        # Rough estimate: 150 words per minute, avg 5 chars per word
        chars_per_second = (150 * 5) / 60  # ~12.5 chars per second
        return text_length / chars_per_second
    
    def _estimate_synthesis_cost(self, character_count: int) -> float:
        """Estimate synthesis cost based on character count."""
        # ElevenLabs pricing: roughly $0.30 per 1K characters
        return (character_count / 1000) * 0.30
    
    def get_available_voices(self) -> List[Dict]:
        """Get list of available voices from ElevenLabs."""
        if not self.api_key:
            return []
        
        try:
            import httpx
            
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.base_url}/voices",
                    headers={"xi-api-key": self.api_key}
                )
                
                if response.status_code == 200:
                    voices_data = response.json()
                    
                    # Process and format voice data
                    voices = []
                    for voice in voices_data.get('voices', []):
                        voices.append({
                            'voice_id': voice.get('voice_id'),
                            'name': voice.get('name'),
                            'category': voice.get('category', 'Unknown'),
                            'description': voice.get('description', ''),
                            'gender': self._detect_gender(voice.get('name', '')),
                            'language_codes': voice.get('fine_tuning', {}).get('language', ['en']),
                            'preview_url': voice.get('preview_url'),
                            'is_premium': voice.get('category') == 'premium'
                        })
                    
                    return voices
                else:
                    print(Colors.WARNING + f"Failed to fetch voices: {response.status_code}" + Colors.ENDC)
                    return []
                    
        except Exception as e:
            print(Colors.WARNING + f"Error fetching voices: {e}" + Colors.ENDC)
            return []
    
    def _detect_gender(self, name: str) -> Optional[str]:
        """Simple gender detection based on voice name patterns."""
        name_lower = name.lower()
        
        # Common male indicators
        male_indicators = ['male', 'man', 'boy', 'gentleman', 'sir', 'mr']
        # Common female indicators  
        female_indicators = ['female', 'woman', 'girl', 'lady', 'madam', 'mrs', 'ms']
        
        for indicator in male_indicators:
            if indicator in name_lower:
                return 'male'
        
        for indicator in female_indicators:
            if indicator in name_lower:
                return 'female'
        
        return None
    
    def validate_voice_id(self, voice_id: str) -> bool:
        """Validate that a voice ID exists and is accessible."""
        if not self.api_key or not voice_id:
            return False
        
        voices = self.get_available_voices()
        return any(voice['voice_id'] == voice_id for voice in voices)


class ElevenLabsSynthesizerAdapter:
    """Adapter to make ElevenLabsSynthesizer compatible with AbstractTTSSynthesizer interface."""
    
    def __init__(self):
        from .tts_interface import AbstractTTSSynthesizer, TTSProvider, VoiceProfile, SynthesisResult
        self.synthesizer = ElevenLabsSynthesizer()
        
    @property
    def provider_name(self):
        from .tts_interface import TTSProvider
        return TTSProvider.ELEVENLABS
    
    @property  
    def is_available(self) -> bool:
        """Check if ElevenLabs is properly configured and available."""
        return bool(self.synthesizer.api_key)
    
    def synthesize_script(self, script_text: str, voice_id: str, output_path: str, 
                         audio_quality: str = "high", **kwargs):
        """Synthesize script using ElevenLabs with interface compatibility."""
        from .tts_interface import SynthesisResult, TTSProvider
        
        # Call original ElevenLabs synthesizer
        result = self.synthesizer.synthesize_script(
            script_text=script_text,
            voice_id=voice_id,
            output_path=output_path,
            audio_quality=audio_quality,
            **kwargs
        )
        
        # Convert to standardized SynthesisResult
        return SynthesisResult(
            audio_file_path=result.get('audio_file_path', output_path),
            duration_seconds=result.get('duration_seconds', 0.0),
            file_size_bytes=result.get('file_size_bytes', 0),
            format=result.get('format', 'mp3'),
            sample_rate=result.get('sample_rate', 44100),
            estimated_cost=result.get('estimated_cost', 0.0),
            processing_time_seconds=result.get('processing_time_seconds', 0.0),
            provider=TTSProvider.ELEVENLABS,
            voice_id=voice_id,
            model_used=result.get('model', 'eleven_multilingual_v2'),
            method=result.get('method', 'unknown'),
            segments_processed=result.get('segments_processed'),
            total_characters=result.get('total_characters')
        )
    
    def get_available_voices(self, language=None, gender=None, **filters):
        """Get available voices in standardized format."""
        from .tts_interface import VoiceProfile, TTSProvider
        
        voices = self.synthesizer.get_available_voices()
        voice_profiles = []
        
        for voice in voices:
            # Convert ElevenLabs format to VoiceProfile
            profile = VoiceProfile(
                voice_id=voice.get('voice_id'),
                name=voice.get('name'),
                language=voice.get('language_codes', ['en'])[0] if voice.get('language_codes') else 'en',
                gender=voice.get('gender'),
                provider=TTSProvider.ELEVENLABS,
                description=voice.get('description', ''),
                category=voice.get('category', 'premium'),
                is_premium=voice.get('is_premium', True),
                preview_url=voice.get('preview_url'),
                labels=voice.get('labels', {})
            )
            
            # Apply filters
            if language and profile.language != language:
                continue
            if gender and profile.gender != gender:
                continue
                
            voice_profiles.append(profile)
        
        return voice_profiles
    
    def validate_voice_id(self, voice_id: str) -> bool:
        """Validate voice ID."""
        return self.synthesizer.validate_voice_id(voice_id)
    
    def estimate_cost(self, character_count: int, audio_quality: str = "high") -> float:
        """Estimate cost using ElevenLabs pricing."""
        return self.synthesizer._estimate_synthesis_cost(character_count)