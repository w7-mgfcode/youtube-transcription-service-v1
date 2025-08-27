"""Google Cloud Text-to-Speech synthesizer implementation."""

import os
import re
import datetime
import asyncio
from typing import Optional, Dict, List, Tuple, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from .tts_interface import (
    AbstractTTSSynthesizer, TTSProvider, VoiceProfile, SynthesisResult,
    VoiceNotFoundError, SynthesisError, ProviderNotAvailableError
)
from ..config import settings
from ..utils.colors import Colors


class GoogleTTSSynthesizer(AbstractTTSSynthesizer):
    """Google Cloud Text-to-Speech synthesizer with advanced SSML support."""
    
    def __init__(self):
        self._client = None
        self._voices_cache = None
        self._voices_cache_time = None
        self._cache_duration = 3600  # 1 hour cache
        
        # Configuration from settings
        self.region = settings.google_tts_region
        self.default_voice = settings.google_tts_default_voice
        self.audio_profile = settings.google_tts_audio_profile
        self.timeout_seconds = settings.google_tts_timeout_seconds
        self.max_retries = settings.google_tts_max_retries
        
        print(Colors.CYAN + f"🔧 Google TTS Synthesizer initialized (region: {self.region})" + Colors.ENDC)
    
    @property
    def provider_name(self) -> TTSProvider:
        """Return the provider identifier."""
        return TTSProvider.GOOGLE_TTS
    
    @property
    def is_available(self) -> bool:
        """Check if Google TTS is properly configured and available."""
        try:
            client = self._get_client()
            if client is None:
                return False
            
            # Test with a simple voice list call
            voices = client.list_voices()
            return len(voices.voices) > 0
            
        except Exception as e:
            print(Colors.WARNING + f"⚠ Google TTS not available: {e}" + Colors.ENDC)
            return False
    
    def _get_client(self):
        """Get or create Google TTS client with proper authentication."""
        if self._client is not None:
            return self._client
        
        try:
            from google.cloud import texttospeech
            
            # Initialize client - will use service account or ADC
            self._client = texttospeech.TextToSpeechClient()
            return self._client
            
        except ImportError:
            raise ProviderNotAvailableError(
                "Google Cloud TTS library not installed. Run: pip install google-cloud-texttospeech"
            )
        except Exception as e:
            raise ProviderNotAvailableError(f"Failed to initialize Google TTS client: {e}")
    
    def synthesize_script(self, 
                         script_text: str, 
                         voice_id: str,
                         output_path: str,
                         audio_quality: str = "high",
                         **kwargs) -> SynthesisResult:
        """
        Synthesize timed script to audio file using Google TTS.
        
        Args:
            script_text: Translated script with timestamps
            voice_id: Google TTS voice name (e.g., 'en-US-Neural2-F')
            output_path: Path to save generated audio file
            audio_quality: Audio quality setting (low, medium, high)
            **kwargs: Additional parameters (model, audio_profile, etc.)
        """
        print(Colors.BLUE + f"\n🎵 Google Cloud TTS synthesis kezdése..." + Colors.ENDC)
        start_time = datetime.datetime.now()
        
        client = self._get_client()
        if not client:
            raise SynthesisError("Google TTS client not available")
        
        try:
            # Validate voice
            if not self.validate_voice_id(voice_id):
                raise VoiceNotFoundError(f"Voice '{voice_id}' not found in Google TTS")
            
            # Convert script to SSML with timestamp preservation
            ssml_content = self._script_to_ssml(script_text)
            
            print(Colors.CYAN + f"   ├─ Voice: {voice_id}" + Colors.ENDC)
            print(Colors.CYAN + f"   ├─ Audio quality: {audio_quality}" + Colors.ENDC)
            print(Colors.CYAN + f"   ├─ SSML content: {len(ssml_content)} characters" + Colors.ENDC)
            
            # Determine synthesis method based on content length
            total_chars = len(ssml_content)
            
            if total_chars > settings.tts_chunk_size_chars:
                # Use chunked synthesis for long content
                result = self._synthesize_chunked(ssml_content, voice_id, output_path, audio_quality, **kwargs)
            else:
                # Use single API call for short content
                result = self._synthesize_single_call(ssml_content, voice_id, output_path, audio_quality, **kwargs)
            
            processing_time = (datetime.datetime.now() - start_time).total_seconds()
            
            # Add provider-specific metadata
            result.provider = TTSProvider.GOOGLE_TTS
            result.voice_id = voice_id
            result.processing_time_seconds = processing_time
            result.total_characters = total_chars
            
            print(Colors.GREEN + f"   ✓ Google TTS synthesis kész: {result.duration_seconds:.1f}s audio" + Colors.ENDC)
            return result
            
        except Exception as e:
            print(Colors.FAIL + f"✗ Google TTS synthesis hiba: {e}" + Colors.ENDC)
            raise SynthesisError(f"Google TTS synthesis failed: {e}")
    
    def _synthesize_single_call(self, 
                               ssml_content: str, 
                               voice_id: str,
                               output_path: str, 
                               audio_quality: str,
                               **kwargs) -> SynthesisResult:
        """Synthesize audio using single Google TTS API call."""
        try:
            from google.cloud import texttospeech
            
            print(Colors.CYAN + f"   ├─ Single API call synthesis ({len(ssml_content)} karakterből)" + Colors.ENDC)
            
            client = self._get_client()
            
            # Parse voice_id to get language and name
            language_code = self._extract_language_from_voice_id(voice_id)
            
            # Set the input text with SSML
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml_content)
            
            # Build the voice request
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_id
            )
            
            # Select the audio configuration
            audio_config = texttospeech.AudioConfig(
                audio_encoding=self._get_audio_encoding(audio_quality),
                effects_profile_id=[self.audio_profile] if self.audio_profile else None,
                sample_rate_hertz=self._get_sample_rate(audio_quality)
            )
            
            # Perform the text-to-speech request
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
                timeout=self.timeout_seconds
            )
            
            # Save the audio file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as out:
                out.write(response.audio_content)
            
            # Get file info
            file_size = os.path.getsize(output_path)
            duration = self._estimate_audio_duration(len(ssml_content))
            cost = self.estimate_cost(len(ssml_content), audio_quality)
            
            return SynthesisResult(
                audio_file_path=output_path,
                duration_seconds=duration,
                file_size_bytes=file_size,
                format=self._get_file_format(audio_quality),
                sample_rate=self._get_sample_rate(audio_quality),
                estimated_cost=cost,
                processing_time_seconds=0,  # Will be set by caller
                provider=TTSProvider.GOOGLE_TTS,
                voice_id=voice_id,
                method="single_call"
            )
            
        except Exception as e:
            raise SynthesisError(f"Google TTS single call synthesis failed: {e}")
    
    def _synthesize_chunked(self, 
                           ssml_content: str, 
                           voice_id: str,
                           output_path: str, 
                           audio_quality: str,
                           **kwargs) -> SynthesisResult:
        """Synthesize audio using chunked approach for longer content."""
        print(Colors.YELLOW + f"   📑 Chunked Google TTS synthesis ({len(ssml_content)} karakter)" + Colors.ENDC)
        
        try:
            from google.cloud import texttospeech
            from pydub import AudioSegment
            
            # Split SSML content into chunks
            chunks = self._split_ssml_into_chunks(ssml_content, settings.tts_chunk_size_chars)
            print(Colors.CYAN + f"   ├─ {len(chunks)} chunk készítése" + Colors.ENDC)
            
            client = self._get_client()
            language_code = self._extract_language_from_voice_id(voice_id)
            
            # Voice and audio configuration
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_id
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=self._get_audio_encoding(audio_quality),
                effects_profile_id=[self.audio_profile] if self.audio_profile else None,
                sample_rate_hertz=self._get_sample_rate(audio_quality)
            )
            
            # Process chunks in parallel if enabled
            if settings.tts_parallel_synthesis and len(chunks) > 1:
                audio_segments = self._process_chunks_parallel(chunks, voice, audio_config, client)
            else:
                audio_segments = self._process_chunks_sequential(chunks, voice, audio_config, client)
            
            # Merge audio segments
            print(Colors.CYAN + "   ├─ Audio chunk-ok egyesítése..." + Colors.ENDC)
            merged_audio = self._merge_audio_segments(audio_segments)
            
            # Save final file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            merged_audio.export(output_path, format=self._get_pydub_format(audio_quality))
            
            # Calculate metadata
            file_size = os.path.getsize(output_path)
            duration = len(merged_audio) / 1000.0  # Convert ms to seconds
            cost = self.estimate_cost(len(ssml_content), audio_quality)
            
            print(Colors.GREEN + f"   ✓ Chunked synthesis kész: {len(chunks)} chunk összevonva" + Colors.ENDC)
            
            return SynthesisResult(
                audio_file_path=output_path,
                duration_seconds=duration,
                file_size_bytes=file_size,
                format=self._get_file_format(audio_quality),
                sample_rate=merged_audio.frame_rate,
                estimated_cost=cost,
                processing_time_seconds=0,  # Will be set by caller
                provider=TTSProvider.GOOGLE_TTS,
                voice_id=voice_id,
                method="chunked",
                segments_processed=len(chunks)
            )
            
        except ImportError:
            raise SynthesisError("pydub library required for chunked synthesis. Run: pip install pydub")
        except Exception as e:
            raise SynthesisError(f"Google TTS chunked synthesis failed: {e}")
    
    def _script_to_ssml(self, script: str) -> str:
        """Convert timestamped script to SSML with timing preservation."""
        ssml_parts = ['<speak>']
        
        lines = script.split('\n')
        last_time = 0.0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Match timestamp pattern [HH:MM:SS] or [H:MM:SS] or [M:SS]
            timestamp_match = re.match(r'\\[(\\d{1,2}):(\\d{2}):(\\d{2})\\]\\s*(.*)', line)
            
            if timestamp_match:
                hours, minutes, seconds, text = timestamp_match.groups()
                current_time = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
                
                if text and not text.startswith('[') and text.strip():
                    # Add pause from last timestamp
                    if current_time > last_time:
                        pause_duration = current_time - last_time
                        if pause_duration > 0.5:  # Only add significant pauses
                            ssml_parts.append(f'<break time="{pause_duration}s"/>')
                    
                    # Clean text and add with proper prosody
                    clean_text = self._clean_text_for_ssml(text.strip())
                    if clean_text:
                        ssml_parts.append(f'<prosody rate="medium">{clean_text}</prosody>')
                    
                    last_time = current_time
        
        ssml_parts.append('</speak>')
        return ''.join(ssml_parts)
    
    def _clean_text_for_ssml(self, text: str) -> str:
        """Clean text for SSML synthesis."""
        # Remove problematic characters
        text = re.sub(r'[\\[\\]{}]', '', text)  # Remove brackets and braces
        text = re.sub(r'\\s+', ' ', text)  # Normalize whitespace
        
        # Handle common abbreviations and numbers
        text = re.sub(r'\\b(\\d+)\\b', r'<say-as interpret-as="number">\\1</say-as>', text)
        text = re.sub(r'\\$([\\d,]+(?:\\.\\d{2})?)', r'<say-as interpret-as="currency" language="en-US">\\1</say-as>', text)
        
        return text.strip()
    
    def _split_ssml_into_chunks(self, ssml_content: str, max_chars: int) -> List[str]:
        """Split SSML content into processable chunks."""
        # Simple splitting - can be enhanced with proper SSML parsing
        chunks = []
        current_chunk = '<speak>'
        
        # Extract content between <speak> tags
        speak_match = re.search(r'<speak>(.*?)</speak>', ssml_content, re.DOTALL)
        if speak_match:
            content = speak_match.group(1)
        else:
            content = ssml_content
        
        # Split by sentence boundaries while preserving SSML tags
        sentences = re.split(r'(</prosody>)', content)
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > max_chars and len(current_chunk) > 20:
                # Close current chunk and start new one
                chunks.append(current_chunk + '</speak>')
                current_chunk = '<speak>'
            
            current_chunk += sentence
        
        # Add final chunk
        if len(current_chunk) > 20:
            chunks.append(current_chunk + '</speak>')
        
        return chunks
    
    def _process_chunks_parallel(self, chunks: List[str], voice, audio_config, client) -> List['AudioSegment']:
        """Process chunks in parallel using ThreadPoolExecutor."""
        from pydub import AudioSegment
        
        audio_segments = [None] * len(chunks)
        
        with ThreadPoolExecutor(max_workers=min(4, len(chunks))) as executor:
            # Submit all chunks for processing
            future_to_index = {}
            for i, chunk in enumerate(chunks):
                future = executor.submit(self._synthesize_chunk, chunk, voice, audio_config, client)
                future_to_index[future] = i
            
            # Collect results
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    import io
                    audio_data = future.result()
                    audio_segments[index] = AudioSegment.from_wav(io.BytesIO(audio_data))
                    print(Colors.GREEN + f"   ✓ Chunk {index + 1}/{len(chunks)} kész" + Colors.ENDC)
                except Exception as e:
                    print(Colors.FAIL + f"   ✗ Chunk {index + 1} hiba: {e}" + Colors.ENDC)
                    raise SynthesisError(f"Chunk {index + 1} synthesis failed: {e}")
        
        return audio_segments
    
    def _process_chunks_sequential(self, chunks: List[str], voice, audio_config, client) -> List['AudioSegment']:
        """Process chunks sequentially."""
        from pydub import AudioSegment
        import io
        
        audio_segments = []
        
        for i, chunk in enumerate(chunks):
            print(Colors.CYAN + f"   ├─ Chunk {i + 1}/{len(chunks)} synthesis..." + Colors.ENDC)
            
            try:
                audio_data = self._synthesize_chunk(chunk, voice, audio_config, client)
                audio_segment = AudioSegment.from_wav(io.BytesIO(audio_data))
                audio_segments.append(audio_segment)
                print(Colors.GREEN + f"   ✓ Chunk {i + 1} kész" + Colors.ENDC)
            except Exception as e:
                print(Colors.FAIL + f"   ✗ Chunk {i + 1} hiba: {e}" + Colors.ENDC)
                raise SynthesisError(f"Chunk {i + 1} synthesis failed: {e}")
        
        return audio_segments
    
    def _synthesize_chunk(self, ssml_chunk: str, voice, audio_config, client) -> bytes:
        """Synthesize a single chunk and return audio data."""
        from google.cloud import texttospeech
        
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_chunk)
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
            timeout=self.timeout_seconds
        )
        
        return response.audio_content
    
    def _merge_audio_segments(self, segments: List['AudioSegment']) -> 'AudioSegment':
        """Merge audio segments into single audio track."""
        from pydub import AudioSegment
        
        if not segments:
            raise SynthesisError("No audio segments to merge")
        
        merged = segments[0]
        for segment in segments[1:]:
            merged = merged + segment
        
        return merged
    
    def get_available_voices(self, 
                           language: Optional[str] = None,
                           gender: Optional[str] = None,
                           **filters) -> List[VoiceProfile]:
        """Get list of available Google TTS voices with optional filtering."""
        # Check cache first
        current_time = datetime.datetime.now().timestamp()
        if (self._voices_cache is not None and 
            self._voices_cache_time is not None and 
            current_time - self._voices_cache_time < self._cache_duration):
            voices = self._voices_cache
        else:
            # Fetch voices from API
            voices = self._fetch_voices_from_api()
            self._voices_cache = voices
            self._voices_cache_time = current_time
        
        # Apply filters
        filtered_voices = voices
        
        if language:
            filtered_voices = [v for v in filtered_voices if v.language == language]
        
        if gender:
            filtered_voices = [v for v in filtered_voices if v.gender == gender.lower()]
        
        # Additional filters
        for key, value in filters.items():
            if key == 'voice_type' and value:
                filtered_voices = [v for v in filtered_voices 
                                 if value.lower() in (v.category or '').lower()]
        
        return filtered_voices
    
    def _fetch_voices_from_api(self) -> List[VoiceProfile]:
        """Fetch available voices from Google TTS API."""
        try:
            client = self._get_client()
            
            # List available voices
            voices_response = client.list_voices()
            
            voice_profiles = []
            for voice in voices_response.voices:
                # Process each language code the voice supports
                for language_code in voice.language_codes:
                    # Determine voice category
                    category = self._determine_voice_category(voice.name)
                    
                    profile = VoiceProfile(
                        voice_id=voice.name,
                        name=voice.name.split('-')[-1] if '-' in voice.name else voice.name,
                        language=language_code,
                        gender=voice.ssml_gender.name.lower() if voice.ssml_gender else None,
                        provider=TTSProvider.GOOGLE_TTS,
                        description=self._get_voice_description(voice.name, category),
                        category=category,
                        is_premium=category in ['neural2', 'studio'],
                        labels={
                            'natural_sample_rate': voice.natural_sample_rate_hertz,
                            'voice_type': category,
                            'language_codes': list(voice.language_codes)
                        }
                    )
                    voice_profiles.append(profile)
            
            print(Colors.GREEN + f"✓ Loaded {len(voice_profiles)} Google TTS voices" + Colors.ENDC)
            return voice_profiles
            
        except Exception as e:
            print(Colors.WARNING + f"Failed to fetch Google TTS voices: {e}" + Colors.ENDC)
            return []
    
    def _determine_voice_category(self, voice_name: str) -> str:
        """Determine voice category from voice name."""
        name_lower = voice_name.lower()
        
        if 'studio' in name_lower:
            return 'studio'
        elif 'neural2' in name_lower:
            return 'neural2'  
        elif 'wavenet' in name_lower:
            return 'wavenet'
        elif 'neural' in name_lower:
            return 'neural'
        else:
            return 'standard'
    
    def _get_voice_description(self, voice_name: str, category: str) -> str:
        """Generate voice description based on name and category."""
        descriptions = {
            'studio': 'Premium quality for long-form content',
            'neural2': 'High-quality neural voice with natural sound',
            'wavenet': 'DeepMind WaveNet technology voice',
            'neural': 'Neural network-based voice',
            'standard': 'Standard concatenative voice'
        }
        return descriptions.get(category, 'Google Cloud TTS voice')
    
    def validate_voice_id(self, voice_id: str) -> bool:
        """Validate that a voice ID exists and is accessible."""
        if not voice_id:
            return False
        
        voices = self.get_available_voices()
        return any(voice.voice_id == voice_id for voice in voices)
    
    def estimate_cost(self, character_count: int, audio_quality: str = "high") -> float:
        """Estimate synthesis cost for given character count."""
        # Google TTS pricing (as of 2024)
        # Standard voices: $4.00 per 1M characters
        # WaveNet voices: $16.00 per 1M characters  
        # Neural2 voices: $16.00 per 1M characters
        # Studio voices: $160.00 per 1M characters
        
        # Assume Neural2 as default for cost estimation
        base_rate_per_million = 16.0
        
        # Quality multipliers (though Google TTS doesn't have quality tiers like ElevenLabs)
        quality_multiplier = 1.0  # Same cost regardless of quality setting
        
        cost = (character_count / 1_000_000) * base_rate_per_million * quality_multiplier
        return max(cost, 0.0001)  # Minimum cost
    
    # Helper methods for audio configuration
    
    def _extract_language_from_voice_id(self, voice_id: str) -> str:
        """Extract language code from Google TTS voice ID."""
        # Google TTS voice IDs format: 'en-US-Neural2-F'
        parts = voice_id.split('-')
        if len(parts) >= 2:
            return f"{parts[0]}-{parts[1]}"
        return "en-US"  # Default fallback
    
    def _get_audio_encoding(self, quality: str):
        """Get Google TTS audio encoding based on quality."""
        from google.cloud import texttospeech
        
        quality_encodings = {
            "low": texttospeech.AudioEncoding.MP3,
            "medium": texttospeech.AudioEncoding.OGG_OPUS,
            "high": texttospeech.AudioEncoding.LINEAR16  # Highest quality
        }
        return quality_encodings.get(quality, texttospeech.AudioEncoding.MP3)
    
    def _get_sample_rate(self, quality: str) -> int:
        """Get sample rate based on quality setting."""
        quality_rates = {
            "low": 22050,
            "medium": 24000,
            "high": 48000
        }
        return quality_rates.get(quality, 24000)
    
    def _get_file_format(self, quality: str) -> str:
        """Get file format string based on quality."""
        quality_formats = {
            "low": "mp3",
            "medium": "ogg",
            "high": "wav"
        }
        return quality_formats.get(quality, "mp3")
    
    def _get_pydub_format(self, quality: str) -> str:
        """Get pydub export format based on quality."""
        return self._get_file_format(quality)
    
    def _estimate_audio_duration(self, text_length: int) -> float:
        """Estimate audio duration based on text length."""
        # Rough estimate: 150 words per minute, avg 5 chars per word
        chars_per_second = (150 * 5) / 60  # ~12.5 chars per second
        return text_length / chars_per_second