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
        
        # Enhanced voice mapping cache for bidirectional lookups
        self._friendly_to_technical = {}  # "Despina" -> "en-US-Studio-O"
        self._technical_to_friendly = {}  # "en-US-Studio-O" -> "Despina"
        self._voice_metadata_cache = {}   # voice_id -> complete metadata
        
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
            
            # Detect voice type to determine input format
            voice_type = self._detect_voice_type(voice_id)
            
            # Chirp voices don't support SSML - use plain text
            if voice_type and 'Chirp' in voice_type:
                # Convert to plain text for Chirp voices
                ssml_content = self._script_to_text(script_text)
                print(Colors.CYAN + f"   ├─ Using plain text input (Chirp voice)" + Colors.ENDC)
            else:
                # Convert script to SSML with timestamp preservation for other voices
                ssml_content = self._script_to_ssml(script_text)
                print(Colors.CYAN + f"   ├─ Using SSML input" + Colors.ENDC)
            
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
            
            # 🔍 COMPREHENSIVE DEBUG INFO
            print(Colors.BOLD + Colors.BLUE + "🔍 GOOGLE TTS DEBUG INFO:" + Colors.ENDC)
            print(Colors.CYAN + f"   ├─ Input Voice ID: '{voice_id}'" + Colors.ENDC)
            print(Colors.CYAN + f"   ├─ Voice ID Type: {type(voice_id)}" + Colors.ENDC)
            print(Colors.CYAN + f"   ├─ SSML Length: {len(ssml_content)} characters" + Colors.ENDC)
            
            # Resolve voice ID using enhanced mapping system
            try:
                resolved_voice_id = self.resolve_voice_id(voice_id)
                if resolved_voice_id:
                    print(Colors.GREEN + f"   ├─ ✓ Voice Resolved Successfully:" + Colors.ENDC)
                    print(Colors.CYAN + f"   │  ├─ Input: '{voice_id}'" + Colors.ENDC)
                    print(Colors.CYAN + f"   │  └─ Resolved to: '{resolved_voice_id}'" + Colors.ENDC)
                    
                    # Get voice metadata from cache
                    voice_metadata = self._voice_metadata_cache.get(resolved_voice_id, {})
                    if voice_metadata:
                        print(Colors.CYAN + f"   │  ├─ Category: {voice_metadata.get('category', 'unknown')}" + Colors.ENDC)
                        print(Colors.CYAN + f"   │  └─ Friendly Name: {voice_metadata.get('friendly_name', 'N/A')}" + Colors.ENDC)
                    
                    final_voice_id = resolved_voice_id
                else:
                    print(Colors.WARNING + f"   ├─ ⚠ Voice '{voice_id}' could not be resolved!" + Colors.ENDC)
                    print(Colors.WARNING + f"   │  └─ Using original voice_id (might cause API errors)" + Colors.ENDC)
                    final_voice_id = voice_id
                    
            except Exception as cache_error:
                print(Colors.WARNING + f"   ├─ ⚠ Cache lookup failed: {cache_error}" + Colors.ENDC)
                final_voice_id = voice_id
                actual_voice = None
            
            client = self._get_client()
            
            # Parse voice_id to get language and name
            language_code = self._extract_language_from_voice_id(final_voice_id)
            print(Colors.CYAN + f"   ├─ Extracted Language Code: {language_code}" + Colors.ENDC)
            
            # Get voice type from cached metadata or detect it
            voice_metadata = self._voice_metadata_cache.get(final_voice_id, {})
            voice_type = voice_metadata.get('category') or self._detect_voice_type(final_voice_id)
            model_name = self._get_voice_model(voice_type)
            
            print(Colors.CYAN + f"   ├─ Voice Type: {voice_type} (from cache: {bool(voice_metadata.get('category'))})" + Colors.ENDC)
            print(Colors.CYAN + f"   ├─ Required Model: {model_name if model_name else 'None (standard voice)'}" + Colors.ENDC)
            
            # Set the input based on voice type
            if voice_type and 'Chirp' in voice_type:
                # Use text input for Chirp voices
                synthesis_input = texttospeech.SynthesisInput(text=ssml_content)
            else:
                # Use SSML input for other voices
                synthesis_input = texttospeech.SynthesisInput(ssml=ssml_content)
            
            # Build the voice request
            voice_params = {
                'language_code': language_code,
                'name': final_voice_id  # Use the resolved voice ID
            }
            
            # Add model parameter if required (for Studio/Journey voices)
            if model_name:
                print(Colors.GREEN + f"   ├─ ✓ Adding Voice Model: {model_name}" + Colors.ENDC)
                # For voices requiring model specification
                voice_params['custom_voice'] = {
                    'model': model_name
                }
            else:
                print(Colors.CYAN + f"   ├─ No special model required (standard voice)" + Colors.ENDC)
            
            # 🔍 DEBUG: Show final API request parameters
            print(Colors.BOLD + Colors.BLUE + "🔍 FINAL API REQUEST PARAMETERS:" + Colors.ENDC)
            print(Colors.CYAN + f"   ├─ voice.language_code: {voice_params['language_code']}" + Colors.ENDC)
            print(Colors.CYAN + f"   ├─ voice.name: {voice_params['name']}" + Colors.ENDC)
            if 'custom_voice' in voice_params:
                print(Colors.CYAN + f"   ├─ voice.custom_voice.model: {voice_params['custom_voice']['model']}" + Colors.ENDC)
            else:
                print(Colors.CYAN + f"   ├─ voice.custom_voice: None" + Colors.ENDC)
            
            voice = texttospeech.VoiceSelectionParams(**voice_params)
            
            # Select the audio configuration
            audio_config = texttospeech.AudioConfig(
                audio_encoding=self._get_audio_encoding(audio_quality),
                effects_profile_id=[self.audio_profile] if self.audio_profile else None,
                sample_rate_hertz=self._get_sample_rate(audio_quality)
            )
            
            # 🔍 DEBUG: Show audio config
            print(Colors.CYAN + f"   ├─ audio_config.encoding: {audio_config.audio_encoding}" + Colors.ENDC)
            print(Colors.CYAN + f"   ├─ audio_config.sample_rate: {audio_config.sample_rate_hertz}" + Colors.ENDC)
            print(Colors.CYAN + f"   └─ Calling Google TTS API..." + Colors.ENDC)
            
            # 🔍 PRE-SYNTHESIS VALIDATION
            validation_result = self._validate_synthesis_request(
                voice_id=final_voice_id,
                voice_type=voice_type,
                model_name=model_name,
                synthesis_input=synthesis_input,
                language_code=language_code
            )
            
            if not validation_result['valid']:
                print(Colors.FAIL + f"   ✗ PRE-SYNTHESIS VALIDATION FAILED!" + Colors.ENDC)
                print(Colors.FAIL + f"   └─ Validation Error: {validation_result['error']}" + Colors.ENDC)
                
                # Enhanced error with suggestions
                error_msg = f"Pre-synthesis validation failed: {validation_result['error']}"
                if validation_result.get('suggestion'):
                    error_msg += f". Suggestion: {validation_result['suggestion']}"
                
                raise SynthesisError(error_msg)
            else:
                print(Colors.GREEN + f"   ✓ Pre-synthesis validation passed" + Colors.ENDC)
            
            # Perform the text-to-speech request
            try:
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config,
                    timeout=self.timeout_seconds
                )
                print(Colors.GREEN + f"   ✓ Google TTS API call successful!" + Colors.ENDC)
                
            except Exception as api_error:
                print(Colors.FAIL + f"   ✗ Google TTS API call FAILED!" + Colors.ENDC)
                print(Colors.FAIL + f"   └─ API Error: {api_error}" + Colors.ENDC)
                
                # Enhanced error context
                error_details = {
                    'voice_id_input': voice_id,
                    'final_voice_id': final_voice_id,
                    'voice_type': voice_type,
                    'model_name': model_name,
                    'language_code': language_code,
                    'api_error': str(api_error)
                }
                
                print(Colors.FAIL + "🔍 ERROR CONTEXT:" + Colors.ENDC)
                for key, value in error_details.items():
                    print(Colors.FAIL + f"   {key}: {value}" + Colors.ENDC)
                
                raise api_error
            
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
            
            # Detect voice type and get model if needed
            voice_type = self._detect_voice_type(voice_id)
            model_name = self._get_voice_model(voice_type)
            
            # Voice and audio configuration
            voice_params = {
                'language_code': language_code,
                'name': voice_id
            }
            
            # Add model parameter if required (for Studio/Journey voices)
            if model_name:
                # For voices requiring model specification
                voice_params['custom_voice'] = {
                    'model': model_name
                }
            
            voice = texttospeech.VoiceSelectionParams(**voice_params)
            
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
    
    def _script_to_text(self, script: str) -> str:
        """Convert timestamped script to plain text for Chirp voices."""
        text_parts = []
        
        lines = script.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Match timestamp pattern and extract text
            timestamp_match = re.match(r'\[(\d{1,2}):(\d{2}):(\d{2})\]\s*(.*)', line)
            
            if timestamp_match:
                hours, minutes, seconds, text = timestamp_match.groups()
                
                if text and not text.startswith('[') and text.strip():
                    # Clean text for plain text usage
                    clean_text = text.strip()
                    # Remove any remaining SSML-like markup
                    clean_text = re.sub(r'<[^>]+>', '', clean_text)
                    
                    if clean_text:
                        text_parts.append(clean_text)
            else:
                # Line without timestamp, include if it's valid text
                if not line.startswith('[') and line.strip():
                    clean_text = re.sub(r'<[^>]+>', '', line.strip())
                    if clean_text:
                        text_parts.append(clean_text)
        
        return ' '.join(text_parts)
    
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
        """Fetch available voices from Google TTS API with enhanced caching."""
        try:
            client = self._get_client()
            
            # List available voices
            voices_response = client.list_voices()
            
            voice_profiles = []
            
            # Clear and rebuild mapping caches
            self._friendly_to_technical.clear()
            self._technical_to_friendly.clear()
            self._voice_metadata_cache.clear()
            
            for voice in voices_response.voices:
                # Process each language code the voice supports
                for language_code in voice.language_codes:
                    # Determine voice category using official API data
                    category = self._determine_voice_category(voice.name)
                    friendly_name = self._get_friendly_voice_name(voice.name, category)
                    
                    # Store complete metadata for this voice
                    self._voice_metadata_cache[voice.name] = {
                        'category': category,
                        'friendly_name': friendly_name,
                        'language_codes': list(voice.language_codes),
                        'ssml_gender': voice.ssml_gender.name.lower() if voice.ssml_gender else None,
                        'natural_sample_rate': voice.natural_sample_rate_hertz
                    }
                    
                    # Build bidirectional mapping
                    self._technical_to_friendly[voice.name] = friendly_name
                    
                    # Priority mapping: prefer studio voices over standard ones for friendly names
                    if friendly_name not in self._friendly_to_technical:
                        self._friendly_to_technical[friendly_name] = voice.name
                    else:
                        # If friendly name already exists, prefer studio/premium voices
                        existing_voice_id = self._friendly_to_technical[friendly_name]
                        existing_category = self._voice_metadata_cache.get(existing_voice_id, {}).get('category', 'unknown')
                        
                        # Priority order: studio > journey > chirp3hd > chirphd > other premium > standard
                        priority_order = ['studio', 'journey', 'chirp3hd', 'chirphd', 'neural2', 'chirp3', 'chirp', 'wavenet', 'neural', 'standard']
                        
                        current_priority = priority_order.index(category) if category in priority_order else len(priority_order)
                        existing_priority = priority_order.index(existing_category) if existing_category in priority_order else len(priority_order)
                        
                        if current_priority < existing_priority:
                            self._friendly_to_technical[friendly_name] = voice.name
                    
                    profile = VoiceProfile(
                        voice_id=voice.name,
                        name=friendly_name,
                        language=language_code,
                        gender=voice.ssml_gender.name.lower() if voice.ssml_gender else None,
                        provider=TTSProvider.GOOGLE_TTS,
                        description=self._get_voice_description(voice.name, category),
                        category=category,
                        is_premium=category in ['neural2', 'studio', 'journey', 'chirp3hd', 'chirphd', 'chirp3', 'chirp'],
                        labels={
                            'natural_sample_rate': voice.natural_sample_rate_hertz,
                            'voice_type': category,
                            'language_codes': list(voice.language_codes),
                            'technical_id': voice.name,
                            'friendly_name': friendly_name
                        }
                    )
                    voice_profiles.append(profile)
            
            print(Colors.GREEN + f"✓ Loaded {len(voice_profiles)} Google TTS voices with enhanced mapping" + Colors.ENDC)
            print(Colors.CYAN + f"✓ Built {len(self._friendly_to_technical)} friendly name mappings" + Colors.ENDC)
            return voice_profiles
            
        except Exception as e:
            print(Colors.WARNING + f"Failed to fetch Google TTS voices: {e}" + Colors.ENDC)
            return []
    
    def _determine_voice_category(self, voice_name: str) -> str:
        """Determine voice category from voice name."""
        name_lower = voice_name.lower()
        
        # Special cases for voices that don't follow naming conventions
        # These voices require model parameters despite their simple names
        special_cases = {
            'despina': 'studio',  # Plain "Despina" is actually a Studio voice
            'erato': 'studio',    # Plain "Erato" is actually a Studio voice  
            'ceres': 'studio',    # Plain "Ceres" is actually a Studio voice
            'luna': 'studio',     # Plain "Luna" is actually a Studio voice
            'stella': 'studio',   # Plain "Stella" is actually a Studio voice
            'aoede': 'studio',    # Plain "Aoede" is actually a Studio voice
        }
        
        # Check special cases first
        if voice_name.lower() in special_cases:
            return special_cases[voice_name.lower()]
        
        # Check for Chirp voices first (most specific)
        if ('chirp3hd' in name_lower or 'chirp-3-hd' in name_lower or 
            'chirp3-hd' in name_lower):
            return 'chirp3hd'
        elif 'chirphd' in name_lower or 'chirp-hd' in name_lower:
            return 'chirphd'
        elif 'chirp3' in name_lower:
            return 'chirp3'
        elif 'chirp' in name_lower:
            return 'chirp'
        elif 'studio' in name_lower:
            return 'studio'
        elif 'journey' in name_lower:
            return 'journey'
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
            'chirp3hd': 'Chirp 3: HD - Ultra-realistic voice with emotional depth',
            'chirphd': 'Chirp HD - High-definition natural voice',
            'chirp3': 'Chirp 3 - Advanced conversational voice',
            'chirp': 'Chirp - Natural conversational voice',
            'studio': 'Studio - Premium quality for long-form content',
            'journey': 'Journey - Experimental advanced voice',
            'neural2': 'Neural2 - High-quality neural voice with natural sound',
            'wavenet': 'WaveNet - DeepMind WaveNet technology voice',
            'neural': 'Neural - Neural network-based voice',
            'standard': 'Standard - Basic concatenative voice'
        }
        return descriptions.get(category, 'Google Cloud TTS voice')
    
    def _get_friendly_voice_name(self, voice_name: str, category: str) -> str:
        """Get friendly name for Google TTS voices, including custom Studio voice names."""
        
        # Studio voice friendly names mapping (these are the actual names used by Google)
        studio_voice_names = {
            'en-US-Studio-O': 'Despina',
            'en-US-Studio-Q': 'Erato', 
            'en-US-Studio-M': 'Ceres',
            'en-GB-Studio-A': 'Aoede',
            'en-GB-Studio-B': 'Luna',
            'en-GB-Studio-C': 'Stella',
            # Add more as needed based on actual Google TTS voices
        }
        
        # If it's a studio voice with a known friendly name, use that
        if category == 'studio' and voice_name in studio_voice_names:
            return studio_voice_names[voice_name]
        
        # For other voices, use the last part of the voice name (original logic)
        if '-' in voice_name:
            return voice_name.split('-')[-1]
        else:
            return voice_name
    
    def resolve_voice_id(self, voice_identifier: str) -> Optional[str]:
        """
        Resolve voice identifier to technical voice ID.
        
        Args:
            voice_identifier: Either friendly name ("Despina") or technical ID ("en-US-Studio-O")
            
        Returns:
            Technical voice ID if found, None otherwise
        """
        if not voice_identifier:
            return None
        
        # Ensure voice cache is populated
        self.get_available_voices()
        
        # Check if it's already a technical ID
        if voice_identifier in self._voice_metadata_cache:
            return voice_identifier
            
        # Check if it's a friendly name that maps to a technical ID
        if voice_identifier in self._friendly_to_technical:
            return self._friendly_to_technical[voice_identifier]
            
        # Check in voice profiles as fallback
        voices = self.get_available_voices()
        for voice in voices:
            if voice.voice_id == voice_identifier or voice.name == voice_identifier:
                return voice.voice_id
                
        return None
    
    def validate_voice_id(self, voice_id: str) -> bool:
        """Validate that a voice ID exists and is accessible (supports both formats)."""
        return self.resolve_voice_id(voice_id) is not None
    
    def _validate_synthesis_request(self, voice_id: str, voice_type: Optional[str], 
                                  model_name: Optional[str], synthesis_input, 
                                  language_code: str) -> Dict[str, Any]:
        """
        Comprehensive pre-synthesis validation to catch common errors before API call.
        
        Returns:
            Dictionary with 'valid' boolean and 'error'/'suggestion' if invalid
        """
        try:
            # Check 1: Voice ID format validation
            if not voice_id or len(voice_id.strip()) == 0:
                return {
                    'valid': False,
                    'error': 'Voice ID is empty or None',
                    'suggestion': 'Ensure voice selection returns a valid voice ID'
                }
            
            # Check 2: Language code validation
            if not language_code or len(language_code) < 2:
                return {
                    'valid': False,
                    'error': f'Invalid language code: {language_code}',
                    'suggestion': 'Language code should be in format like "en-US" or "hu-HU"'
                }
            
            # Check 3: Studio/Journey voice model requirement validation
            if voice_type in ['Studio', 'Journey'] and not model_name:
                return {
                    'valid': False,
                    'error': f'{voice_type} voice "{voice_id}" requires model parameter but none provided',
                    'suggestion': f'For {voice_type} voices, model parameter must be "{voice_type.lower()}"'
                }
            
            # Check 4: SSML content validation for non-Chirp voices
            if hasattr(synthesis_input, 'ssml') and synthesis_input.ssml:
                if voice_type and 'Chirp' in voice_type:
                    return {
                        'valid': False,
                        'error': f'Chirp voice "{voice_id}" does not support SSML input',
                        'suggestion': 'Use plain text input for Chirp voices'
                    }
                
                # Basic SSML validation
                ssml_content = synthesis_input.ssml
                if not ssml_content.strip().startswith('<speak>'):
                    return {
                        'valid': False,
                        'error': 'SSML content does not start with <speak> tag',
                        'suggestion': 'SSML content must be wrapped in <speak></speak> tags'
                    }
            
            # Check 5: Voice resolution and existence validation
            resolved_voice_id = self.resolve_voice_id(voice_id)
            if not resolved_voice_id:
                return {
                    'valid': False,
                    'error': f'Voice "{voice_id}" not found in available Google TTS voices',
                    'suggestion': 'Use a valid voice ID or friendly name. Check available voices with get_available_voices()'
                }
            
            # Check 6: Known problematic voice patterns
            if 'studio' in voice_id.lower() and voice_type and voice_type.lower() != 'studio':
                return {
                    'valid': False,
                    'error': f'Voice ID "{voice_id}" appears to be Studio voice but type detected as "{voice_type}"',
                    'suggestion': 'Check voice type detection logic or use different voice selection'
                }
            
            # Check 7: Use resolved voice ID for final validation
            # (Voice existence already validated in Check 5)
            
            # All validations passed
            return {'valid': True}
            
        except Exception as validation_error:
            return {
                'valid': False,
                'error': f'Validation process failed: {validation_error}',
                'suggestion': 'Check validation logic or skip validation'
            }
    
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
    
    def _detect_voice_type(self, voice_id: str) -> Optional[str]:
        """
        Detect voice type from voice ID.
        
        Returns:
            Voice type (Standard, WaveNet, Neural2, Studio, Journey, Chirp3HD, Polyglot, News) or None
        """
        voice_id_upper = voice_id.upper()
        
        # Check for specific voice types in the voice ID
        # Order matters - check most specific first
        if ('CHIRP3HD' in voice_id_upper or 'CHIRP-3-HD' in voice_id_upper or 
            'CHIRP3-HD' in voice_id_upper):
            return 'Chirp3HD'
        elif 'CHIRPHD' in voice_id_upper or 'CHIRP-HD' in voice_id_upper:
            return 'ChirpHD'
        elif 'CHIRP3' in voice_id_upper:
            return 'Chirp3'
        elif 'CHIRP' in voice_id_upper:
            return 'Chirp'
        elif 'STUDIO' in voice_id_upper:
            return 'Studio'
        elif 'JOURNEY' in voice_id_upper:
            return 'Journey'
        elif 'NEURAL2' in voice_id_upper:
            return 'Neural2'
        elif 'WAVENET' in voice_id_upper:
            return 'WaveNet'
        elif 'POLYGLOT' in voice_id_upper:
            return 'Polyglot'
        elif 'NEWS' in voice_id_upper:
            return 'News'
        elif 'STANDARD' in voice_id_upper:
            return 'Standard'
        
        # Default to None if no specific type detected
        return None
    
    def _get_voice_model(self, voice_type: Optional[str]) -> Optional[str]:
        """
        Get the model parameter for specific voice types.
        
        Based on testing, most Google TTS voices work with standard VoiceSelectionParams.
        The custom_voice.model parameter is rarely needed and often causes issues.
        
        Returns:
            Model name for API or None (None for most voices)
        """
        if not voice_type:
            return None
            
        voice_type_lower = voice_type.lower()
        
        # After testing, Studio voices work better WITHOUT the model parameter
        # The original error was misleading - Studio voices don't need custom_voice.model
        if voice_type_lower == 'studio':
            return None  # Studio voices work without model parameter
        elif voice_type_lower == 'journey':
            return None  # Journey voices also likely work without model parameter
        
        # All other voice types work with standard VoiceSelectionParams
        return None
    
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