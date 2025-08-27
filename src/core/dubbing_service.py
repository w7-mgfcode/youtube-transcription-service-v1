"""Main dubbing orchestration service coordinating all dubbing pipeline steps."""

import os
import uuid
import datetime
from typing import Optional, Dict, Callable, Any, List
from pathlib import Path

from .transcriber import TranscriptionService
from .translator import ContextAwareTranslator, TranslationQuality
from .synthesizer import ElevenLabsSynthesizer, SynthesisError
from .video_muxer import VideoMuxer, VideoMuxingError
from .tts_factory import TTSFactory
from .tts_interface import TTSProvider, AbstractTTSSynthesizer, SynthesisError as TTSSynthesisError
from ..config import settings, TranslationContext
from ..utils.colors import Colors
from ..models.dubbing import DubbingJob, DubbingJobStatus, DubbingRequest, TTSProviderEnum


class DubbingServiceError(Exception):
    """Base exception for dubbing service errors."""
    pass


class DubbingService:
    """
    Main dubbing orchestration service.
    Coordinates: Transcription → Translation → Synthesis → Video Muxing
    """
    
    def __init__(self):
        self.transcriber = TranscriptionService()
        self.translator = ContextAwareTranslator()
        self.video_muxer = VideoMuxer()
        
        # Progress tracking
        self.current_job: Optional[DubbingJob] = None
        self.progress_callback: Optional[Callable[[str, int], None]] = None
    
    def _get_synthesizer(self, tts_provider: TTSProviderEnum):
        """Get appropriate synthesizer based on provider selection."""
        if tts_provider == TTSProviderEnum.AUTO:
            provider = TTSProvider.AUTO
        elif tts_provider == TTSProviderEnum.ELEVENLABS:
            provider = TTSProvider.ELEVENLABS
        elif tts_provider == TTSProviderEnum.GOOGLE_TTS:
            provider = TTSProvider.GOOGLE_TTS
        else:
            provider = TTSProvider.AUTO
        
        return TTSFactory.create_synthesizer(provider)
    
    def process_dubbing_job(self, 
                          request: DubbingRequest,
                          progress_callback: Optional[Callable[[str, int], None]] = None) -> DubbingJob:
        """
        Process a complete dubbing job from URL to final video.
        
        Args:
            request: Dubbing request with all parameters
            progress_callback: Optional callback for progress updates
            
        Returns:
            Completed DubbingJob with all results
        """
        job_id = str(uuid.uuid4())
        self.progress_callback = progress_callback
        
        # Initialize job
        job = DubbingJob(
            job_id=job_id,
            status=DubbingJobStatus.PENDING,
            progress_percentage=0,
            request=request,
            created_at=datetime.datetime.now()
        )
        
        self.current_job = job
        
        print(Colors.BOLD + f"\n🎬 Dubbing job indítása: {job_id}" + Colors.ENDC)
        self._update_progress("Job initialized", 5)
        
        try:
            job.started_at = datetime.datetime.now()
            job.status = DubbingJobStatus.TRANSCRIBING
            
            # Step 1: Transcription
            if not self._skip_transcription(request):
                transcription_result = self._transcribe_video(request)
                job.transcription_result = transcription_result
                self._update_progress("Transcription completed", 25)
            
            # Step 2: Translation (if enabled)
            if request.enable_translation:
                job.status = DubbingJobStatus.TRANSLATING
                translation_result = self._translate_transcript(request, job.transcription_result)
                job.translation_result = translation_result
                self._update_progress("Translation completed", 50)
            
            # Step 3: Audio Synthesis (if enabled)
            if request.enable_synthesis:
                job.status = DubbingJobStatus.SYNTHESIZING
                synthesis_result = self._synthesize_audio(request, job)
                job.synthesis_result = synthesis_result
                self._update_progress("Audio synthesis completed", 75)
            
            # Step 4: Video Muxing (if enabled)
            if request.enable_video_muxing:
                job.status = DubbingJobStatus.MUXING
                muxing_result = self._mux_video(request, job)
                job.video_muxing_result = muxing_result
                self._update_progress("Video muxing completed", 95)
            
            # Finalize job
            job.status = DubbingJobStatus.COMPLETED
            job.completed_at = datetime.datetime.now()
            job.progress_percentage = 100
            
            # Calculate costs
            self._calculate_final_costs(job)
            
            self._update_progress("Dubbing job completed successfully", 100)
            print(Colors.GREEN + f"✅ Dubbing job kész: {job_id}" + Colors.ENDC)
            
            return job
            
        except Exception as e:
            print(Colors.FAIL + f"✗ Dubbing job hiba: {e}" + Colors.ENDC)
            
            job.status = DubbingJobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.datetime.now()
            
            # Cleanup on failure
            self._cleanup_job_files(job)
            
            raise DubbingServiceError(f"Dubbing job failed: {e}")
    
    def _transcribe_video(self, request: DubbingRequest) -> Dict[str, Any]:
        """Handle transcription step."""
        print(Colors.BLUE + "\n📝 1️⃣ Transcription lépés..." + Colors.ENDC)
        
        try:
            result = self.transcriber.process(
                url=str(request.url),
                test_mode=request.test_mode,
                breath_detection=request.breath_detection,
                use_vertex_ai=request.use_vertex_ai,
                vertex_ai_model=request.vertex_ai_model,
                progress_callback=self._transcription_progress_callback
            )
            
            if result["status"] != "completed":
                raise DubbingServiceError(f"Transcription failed: {result.get('error', 'Unknown error')}")
            
            print(Colors.GREEN + "   ✓ Transcription successful" + Colors.ENDC)
            return result
            
        except Exception as e:
            raise DubbingServiceError(f"Transcription step failed: {e}")
    
    def _translate_transcript(self, request: DubbingRequest, transcription_result: Dict) -> Dict:
        """Handle translation step."""
        print(Colors.BLUE + "\n🔄 2️⃣ Translation lépés..." + Colors.ENDC)
        
        try:
            # Get transcript text
            transcript_file = transcription_result.get("transcript_file")
            if not transcript_file or not os.path.exists(transcript_file):
                raise DubbingServiceError("Transcript file not found for translation")
            
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcript_text = f.read()
            
            # Determine translation quality based on request
            quality = TranslationQuality.HIGH if request.use_vertex_ai else TranslationQuality.BALANCED
            
            # Perform translation
            translation_result = self.translator.translate_script(
                script_text=transcript_text,
                target_language=request.target_language,
                context=request.translation_context.value,
                audience=request.target_audience,
                tone=request.desired_tone,
                quality=quality,
                preserve_timing=True
            )
            
            if not translation_result:
                raise DubbingServiceError("Translation returned no result")
            
            # Save translated script
            translated_file = self._save_translated_script(
                translation_result['translated_text'], 
                request.target_language,
                self.current_job.job_id
            )
            
            translation_result['translated_file'] = translated_file
            
            print(Colors.GREEN + f"   ✓ Translation successful: {translation_result['word_count']} words" + Colors.ENDC)
            return translation_result
            
        except Exception as e:
            raise DubbingServiceError(f"Translation step failed: {e}")
    
    def _synthesize_audio(self, request: DubbingRequest, job: DubbingJob) -> Dict:
        """Handle audio synthesis step."""
        print(Colors.BLUE + "\n🎵 3️⃣ Audio Synthesis lépés..." + Colors.ENDC)
        
        try:
            # Get appropriate synthesizer based on provider selection
            synthesizer = self._get_synthesizer(request.tts_provider)
            print(Colors.CYAN + f"   🎤 Using TTS Provider: {synthesizer.provider_name.value}" + Colors.ENDC)
            
            # Get script text for synthesis
            if job.translation_result:
                script_text = job.translation_result['translated_text']
                language_code = request.target_language
            elif job.transcription_result:
                # Use original transcript if no translation
                with open(job.transcription_result['transcript_file'], 'r', encoding='utf-8') as f:
                    script_text = f.read()
                language_code = 'hu-HU'
            else:
                raise DubbingServiceError("No script available for synthesis")
            
            # Use default voice if not specified, or validate provided voice
            voice_id = request.voice_id
            if not voice_id:
                # Get default voice for the provider
                if hasattr(synthesizer, 'get_default_voice'):
                    voice_id = synthesizer.get_default_voice(language_code)
                else:
                    # Fallback to provider-specific defaults
                    if synthesizer.provider_name == TTSProvider.GOOGLE_TTS:
                        voice_id = "en-US-Neural2-F" if language_code.startswith("en") else "hu-HU-Wavenet-A"
                    else:
                        voice_id = settings.elevenlabs_default_voice
            
            if not voice_id:
                raise DubbingServiceError("Voice ID required for synthesis")
            
            # Generate output path
            audio_filename = f"dubbed_audio_{job.job_id}.mp3"
            audio_output_path = os.path.join(settings.data_dir, audio_filename)
            
            # Perform synthesis using the new interface
            synthesis_result = synthesizer.synthesize_script(
                script_text=script_text,
                voice_id=voice_id,
                output_path=audio_output_path,
                audio_quality=request.audio_quality.value
            )
            
            # Convert to dict format if it's a SynthesisResult object
            if hasattr(synthesis_result, '__dict__'):
                result_dict = {
                    'audio_file_path': synthesis_result.audio_file_path,  # Fixed: was output_path
                    'duration_seconds': synthesis_result.duration_seconds,
                    'character_count': len(script_text) if script_text else 0,  # Calculate from input
                    'estimated_cost': synthesis_result.estimated_cost,  # Fixed: was cost_usd
                    'provider_used': getattr(synthesis_result, 'provider', TTSProvider.GOOGLE_TTS).value if hasattr(synthesis_result, 'provider') else 'google_tts',  # Fixed attribute name
                    'voice_used': synthesis_result.voice_id  # Fixed: was voice_used
                }
            else:
                result_dict = synthesis_result
            
            print(Colors.GREEN + f"   ✓ Audio synthesis successful: {result_dict.get('duration_seconds', 0):.1f}s" + Colors.ENDC)
            print(Colors.GREEN + f"   ✓ Provider: {result_dict.get('provider_used', 'unknown')}, Cost: ${result_dict.get('estimated_cost', 0):.4f}" + Colors.ENDC)
            return result_dict
            
        except (SynthesisError, TTSSynthesisError) as e:
            raise DubbingServiceError(f"Audio synthesis failed: {e}")
        except Exception as e:
            raise DubbingServiceError(f"Synthesis step failed: {e}")
    
    def _mux_video(self, request: DubbingRequest, job: DubbingJob) -> Dict:
        """Handle video muxing step."""
        print(Colors.BLUE + "\n🎬 4️⃣ Video Muxing lépés..." + Colors.ENDC)
        
        try:
            if not job.synthesis_result:
                raise DubbingServiceError("No synthesized audio available for muxing")
            
            audio_file = job.synthesis_result['audio_file_path']
            if not os.path.exists(audio_file):
                raise DubbingServiceError(f"Synthesized audio file not found: {audio_file}")
            
            # Generate output path
            video_filename = f"dubbed_video_{job.job_id}.{request.video_format.value}"
            video_output_path = os.path.join(settings.data_dir, video_filename)
            
            # Perform muxing
            if request.preview_mode:
                # Create short preview
                muxing_result = self.video_muxer.create_preview_video(
                    video_url=str(request.url),
                    audio_file_path=audio_file,
                    output_path=video_output_path,
                    duration_seconds=30
                )
            else:
                # Full video muxing
                muxing_result = self.video_muxer.replace_audio_in_video(
                    video_url=str(request.url),
                    audio_file_path=audio_file,
                    output_path=video_output_path,
                    preserve_video_quality=request.preserve_video_quality,
                    target_format=request.video_format.value
                )
            
            print(Colors.GREEN + f"   ✓ Video muxing successful: {muxing_result.get('file_size_bytes', 0) // 1024 // 1024}MB" + Colors.ENDC)
            return muxing_result
            
        except VideoMuxingError as e:
            raise DubbingServiceError(f"Video muxing failed: {e}")
        except Exception as e:
            raise DubbingServiceError(f"Muxing step failed: {e}")
    
    def _save_translated_script(self, translated_text: str, target_language: str, job_id: str) -> str:
        """Save translated script to file."""
        filename = f"translated_{target_language}_{job_id}.txt"
        file_path = os.path.join(settings.data_dir, filename)
        
        os.makedirs(settings.data_dir, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(translated_text)
        
        return file_path
    
    def _calculate_final_costs(self, job: DubbingJob):
        """Calculate and update final job costs."""
        total_cost = 0.0
        
        # Translation costs
        if job.translation_result:
            total_cost += job.translation_result.get('estimated_cost', 0.0)
        
        # Synthesis costs
        if job.synthesis_result:
            total_cost += job.synthesis_result.get('estimated_cost', 0.0)
        
        # Video processing costs (minimal, mainly storage)
        if job.video_muxing_result:
            file_size_gb = job.video_muxing_result.get('file_size_bytes', 0) / (1024**3)
            storage_cost = file_size_gb * 0.02  # Rough estimate $0.02 per GB
            total_cost += storage_cost
        
        job.actual_total_cost = total_cost
        
        # Warn if over budget
        if job.request.max_cost_usd and total_cost > job.request.max_cost_usd:
            print(Colors.WARNING + f"   ⚠ Cost exceeded limit: ${total_cost:.4f} > ${job.request.max_cost_usd:.4f}" + Colors.ENDC)
    
    def _skip_transcription(self, request: DubbingRequest) -> bool:
        """Check if transcription can be skipped (e.g., if transcript already exists)."""
        # For now, always do transcription
        # Future: could check for existing transcript files
        return False
    
    def _cleanup_job_files(self, job: DubbingJob):
        """Clean up temporary files on job failure."""
        print(Colors.CYAN + "   🧹 Cleaning up temporary files..." + Colors.ENDC)
        
        files_to_cleanup = []
        
        # Add files to cleanup list
        if job.transcription_result:
            files_to_cleanup.append(job.transcription_result.get('transcript_file'))
        
        if job.translation_result:
            files_to_cleanup.append(job.translation_result.get('translated_file'))
        
        if job.synthesis_result:
            files_to_cleanup.append(job.synthesis_result.get('audio_file_path'))
        
        if job.video_muxing_result:
            files_to_cleanup.append(job.video_muxing_result.get('video_file_path'))
        
        # Remove files
        for file_path in files_to_cleanup:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(Colors.CYAN + f"   └─ Removed: {os.path.basename(file_path)}" + Colors.ENDC)
                except:
                    pass
    
    def _update_progress(self, message: str, percentage: int):
        """Update job progress and notify callback."""
        if self.current_job:
            self.current_job.progress_percentage = percentage
        
        print(Colors.CYAN + f"   📊 Progress: {percentage}% - {message}" + Colors.ENDC)
        
        if self.progress_callback:
            try:
                self.progress_callback(message, percentage)
            except:
                pass  # Don't fail job if callback fails
    
    def _transcription_progress_callback(self, status: str, progress: int):
        """Handle progress updates from transcription service."""
        # Map transcription progress to overall progress (0-25%)
        overall_progress = int(progress * 0.25)
        self._update_progress(f"Transcription: {status}", overall_progress)
    
    def estimate_dubbing_cost(self, request: DubbingRequest) -> Dict:
        """Estimate total cost for a dubbing job."""
        print(Colors.BLUE + "\n💰 Dubbing cost estimation..." + Colors.ENDC)
        
        cost_breakdown = {
            'transcription_cost': 0.0,
            'translation_cost': 0.0,
            'synthesis_cost': 0.0,
            'video_processing_cost': 0.0,
            'storage_cost': 0.0,
            'total_cost': 0.0
        }
        
        try:
            # Estimate based on video duration (rough)
            # For accurate estimates, we'd need to transcribe first
            estimated_duration = 300 if request.test_mode else 1800  # 5min vs 30min max
            
            # Transcription cost (minimal for Google Speech API)
            cost_breakdown['transcription_cost'] = estimated_duration / 60 * 0.016  # $0.016 per minute
            
            if request.enable_translation:
                # Estimate transcript length (~150 words per minute)
                estimated_words = estimated_duration / 60 * 150
                estimated_chars = estimated_words * 5  # ~5 chars per word
                cost_breakdown['translation_cost'] = (estimated_chars / 1_000_000) * 20  # $20 per 1M chars
            
            if request.enable_synthesis:
                estimated_chars = estimated_duration / 60 * 150 * 5  # Same as translation
                cost_breakdown['synthesis_cost'] = (estimated_chars / 1000) * 0.30  # $0.30 per 1K chars
            
            if request.enable_video_muxing:
                cost_breakdown['video_processing_cost'] = 0.05  # Minimal processing cost
                cost_breakdown['storage_cost'] = 0.10  # Storage estimate
            
            cost_breakdown['total_cost'] = sum(cost_breakdown.values())
            
            print(Colors.GREEN + f"   ✓ Estimated total cost: ${cost_breakdown['total_cost']:.4f}" + Colors.ENDC)
            
            return cost_breakdown
            
        except Exception as e:
            print(Colors.WARNING + f"   ⚠ Cost estimation failed: {e}" + Colors.ENDC)
            return cost_breakdown
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of a dubbing job by ID."""
        # This would typically query a database
        # For now, only current job is tracked
        if self.current_job and self.current_job.job_id == job_id:
            return {
                'job_id': job_id,
                'status': self.current_job.status.value,
                'progress': self.current_job.progress_percentage,
                'created_at': self.current_job.created_at.isoformat(),
                'started_at': self.current_job.started_at.isoformat() if self.current_job.started_at else None,
                'completed_at': self.current_job.completed_at.isoformat() if self.current_job.completed_at else None,
                'error_message': self.current_job.error_message
            }
        
        return None
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running dubbing job."""
        if self.current_job and self.current_job.job_id == job_id:
            print(Colors.WARNING + f"🛑 Cancelling dubbing job: {job_id}" + Colors.ENDC)
            
            self.current_job.status = DubbingJobStatus.CANCELLED
            self.current_job.completed_at = datetime.datetime.now()
            
            # Cleanup files
            self._cleanup_job_files(self.current_job)
            
            return True
        
        return False
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get supported target languages for dubbing."""
        return self.translator.get_supported_languages()
    
    def get_available_voices(self, provider: TTSProviderEnum = TTSProviderEnum.AUTO) -> List[Dict]:
        """Get available voices for specified provider."""
        synthesizer = self._get_synthesizer(provider)
        
        # Convert voice profiles to dict format for backward compatibility
        voices = synthesizer.get_available_voices()
        voice_list = []
        
        for voice in voices:
            voice_list.append({
                "voice_id": voice.voice_id,
                "name": voice.name,
                "language": voice.language,
                "gender": voice.gender,
                "is_premium": voice.is_premium
            })
        
        return voice_list