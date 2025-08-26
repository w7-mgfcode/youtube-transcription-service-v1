"""Google Cloud Speech API client module."""

import os
import time
import math
from typing import Optional
from google.cloud import speech
from google.cloud import storage
from google.api_core import exceptions as gcloud_exceptions

from ..config import settings, get_bucket_name, setup_google_credentials
from ..utils.progress import update_progress, SmoothProgressSimulator
from ..utils.colors import Colors


class SpeechClient:
    """Google Cloud Speech API client with adaptive processing."""
    
    def __init__(self):
        """Initialize Speech API client with credentials."""
        setup_google_credentials()
        self.speech_client = speech.SpeechClient()
        self.storage_client = storage.Client()
        self.bucket_name = get_bucket_name()
    
    def transcribe(self, file_path: str, duration_seconds: Optional[int] = None, 
                   video_title: str = "", breath_detection: bool = True) -> Optional[speech.RecognizeResponse]:
        """
        Transcribe audio file using adaptive sync/async processing.
        
        Args:
            file_path: Path to FLAC audio file
            duration_seconds: Duration in seconds (optional)
            video_title: Video title for logging
            breath_detection: Enable breath detection features
            
        Returns:
            Speech API response or None on error
        """
        try:
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024*1024)
            
            print(Colors.BLUE + f"\n🎤 Speech API feldolgozás ({size_mb:.1f} MB)..." + Colors.ENDC)
            
            if breath_detection:
                print(Colors.CYAN + "   💨 Levegővétel detektálás: BEKAPCSOLVA (finomított)" + Colors.ENDC)
                print(Colors.CYAN + "   📊 Szünet küszöbök: 0.25s+" + Colors.ENDC)
            
            # Decide processing method based on file size and duration
            if self._should_use_async(file_size, duration_seconds):
                return self._transcribe_long(file_path, video_title)
            else:
                return self._transcribe_short(file_path, breath_detection)
                
        except Exception as e:
            print(Colors.FAIL + f"✗ Speech API hiba: {e}" + Colors.ENDC)
            return None
    
    def _should_use_async(self, file_size: int, duration_seconds: Optional[int]) -> bool:
        """
        Determine whether to use async processing.
        
        Args:
            file_size: File size in bytes
            duration_seconds: Duration in seconds
            
        Returns:
            True if async processing should be used
        """
        size_mb = file_size / (1024*1024)
        return (size_mb > settings.sync_size_limit_mb or 
                (duration_seconds is not None and duration_seconds > 55))
    
    def _transcribe_short(self, file_path: str, breath_detection: bool = True) -> Optional[speech.RecognizeResponse]:
        """
        Synchronous transcription for small files (≤10MB, ≤60s).
        
        Args:
            file_path: Path to audio file
            breath_detection: Enable breath detection
            
        Returns:
            Speech API response or None on error
        """
        print(Colors.BLUE + "⚡ Gyors feldolgozás (sync recognize)..." + Colors.ENDC)
        
        try:
            with open(file_path, "rb") as audio_file:
                content = audio_file.read()
            
            audio = speech.RecognitionAudio(content=content)
            config = self._get_speech_config()
            
            response = self.speech_client.recognize(config=config, audio=audio)
            
            if response.results:
                print(Colors.GREEN + f"✓ Feldolgozás kész! ({len(response.results)} blokk)" + Colors.ENDC)
                return response
            else:
                print(Colors.WARNING + "⚠ Nincs felismert szöveg" + Colors.ENDC)
                return None
                
        except Exception as e:
            print(Colors.FAIL + f"✗ Felismerési hiba: {e}" + Colors.ENDC)
            return None
    
    def _transcribe_long(self, file_path: str, video_title: str = "") -> Optional[speech.LongRunningRecognizeResponse]:
        """
        Asynchronous transcription for large files via GCS.
        
        Args:
            file_path: Path to audio file
            video_title: Video title for logging
            
        Returns:
            Long-running Speech API response or None on error
        """
        try:
            # Upload to GCS
            gcs_uri = self._upload_to_gcs(file_path)
            if not gcs_uri:
                return None
            
            # Configure and start long-running recognition
            audio = speech.RecognitionAudio(uri=gcs_uri)
            config = self._get_speech_config()
            
            print(Colors.BLUE + "\n🔄 Hosszú feldolgozás indítása..." + Colors.ENDC)
            print(Colors.CYAN + f"   ├─ Videó: {video_title[:50]}{'...' if len(video_title) > 50 else ''}" + Colors.ENDC)
            print(Colors.CYAN + f"   ├─ GCS URI: {gcs_uri}" + Colors.ENDC)
            print(Colors.CYAN + "   └─ API hívás..." + Colors.ENDC)
            
            operation = self.speech_client.long_running_recognize(config=config, audio=audio)
            print(Colors.GREEN + "   ✓ Feldolgozás elindult" + Colors.ENDC)
            print()
            
            # Monitor progress
            response = self._monitor_long_running_operation(operation, file_path)
            
            # Cleanup GCS file
            self._cleanup_gcs_file(gcs_uri)
            
            return response
            
        except Exception as e:
            print(Colors.FAIL + f"\n✗ Long running hiba: {e}" + Colors.ENDC)
            if hasattr(e, 'details'):
                print(Colors.FAIL + f"   Részletek: {e.details}" + Colors.ENDC)
            return None
    
    def _upload_to_gcs(self, file_path: str) -> Optional[str]:
        """Upload audio file to Google Cloud Storage."""
        try:
            print(Colors.BLUE + f"☁️  Feltöltés GCS-be..." + Colors.ENDC)
            
            bucket = self.storage_client.bucket(self.bucket_name)
            blob_name = f"audio/{os.path.basename(file_path)}"
            blob = bucket.blob(blob_name)
            
            blob.upload_from_filename(file_path)
            
            gcs_uri = f"gs://{self.bucket_name}/{blob_name}"
            print(Colors.GREEN + f"✓ Feltöltve: {gcs_uri}" + Colors.ENDC)
            return gcs_uri
            
        except Exception as e:
            print(Colors.FAIL + f"✗ GCS feltöltési hiba: {e}" + Colors.ENDC)
            return None
    
    def _monitor_long_running_operation(self, operation, file_path: str) -> Optional[speech.LongRunningRecognizeResponse]:
        """Monitor long-running operation with progress tracking."""
        start_time = time.time()
        last_percent = -1
        stuck_counter = 0
        
        # Estimate processing time based on file size (approximately 1 minute per MB)
        file_size_mb = os.path.getsize(file_path) / (1024*1024)
        estimated_time = max(60, min(300, file_size_mb * 60))  # Between 1-5 minutes
        
        while not operation.done():
            elapsed = time.time() - start_time
            
            # Try to get real progress
            actual_percent = 0
            has_real_progress = False
            
            try:
                if hasattr(operation, 'metadata') and operation.metadata:
                    metadata = operation.metadata
                    if hasattr(metadata, 'progress_percent'):
                        actual_percent = metadata.progress_percent
                        has_real_progress = True
                        
                        # Track progress changes
                        if actual_percent != last_percent:
                            last_percent = actual_percent
                            stuck_counter = 0
                        else:
                            stuck_counter += 1
            except:
                pass
            
            # Display progress
            if has_real_progress and actual_percent > 0:
                # Real progress available
                total_estimated = elapsed / (actual_percent / 100) if actual_percent > 0 else estimated_time
                eta = max(0, total_estimated - elapsed)
                
                elapsed_str = f"{int(elapsed//60)}:{int(elapsed%60):02d}"
                eta_str = f"{int(eta//60)}:{int(eta%60):02d}" if eta > 0 else "0:00"
                
                status = "Várakozás" if stuck_counter > 10 else "Feldolgozás"
                extra_info = f"Állapot: {status} │ Eltelt: {elapsed_str} │ Hátra: ~{eta_str}"
                
                update_progress(
                    actual_percent, 100,
                    prefix="🎤 Speech API",
                    extra_info=extra_info
                )
            else:
                # Use estimated progress
                if elapsed < estimated_time:
                    # Logarithmic curve for realistic feel
                    progress_ratio = elapsed / estimated_time
                    simulated_percent = min(95, 100 * (1 - math.exp(-3 * progress_ratio)))
                else:
                    # Slow approach to 95% if over estimated time
                    simulated_percent = min(95, 95 - 5 * math.exp(-(elapsed - estimated_time) / 60))
                
                elapsed_str = f"{int(elapsed//60)}:{int(elapsed%60):02d}"
                eta = max(0, estimated_time - elapsed)
                eta_str = f"{int(eta//60)}:{int(eta%60):02d}" if eta > 0 else "?"
                
                extra_info = f"Becsült │ Eltelt: {elapsed_str} │ Hátra: ~{eta_str}"
                
                update_progress(
                    simulated_percent, 100,
                    prefix="🎤 Speech API",
                    extra_info=extra_info
                )
            
            time.sleep(0.5)  # Check every 500ms
        
        # Complete
        total_time = time.time() - start_time
        elapsed_str = f"{int(total_time//60)}:{int(total_time%60):02d}"
        
        update_progress(100, 100, prefix="✓ Kész", extra_info=f"Teljes idő: {elapsed_str}")
        
        try:
            response = operation.result(timeout=10)
            
            if response.results:
                print(Colors.GREEN + f"\n✓ Átirat elkészült!" + Colors.ENDC)
                print(f"   ├─ Feldolgozási idő: {elapsed_str}")
                print(f"   ├─ Eredmény blokkok: {len(response.results)}")
                
                # Word count estimation
                word_count = sum(len(r.alternatives[0].transcript.split()) 
                               for r in response.results if r.alternatives)
                print(f"   └─ Becsült szószám: ~{word_count}")
                
                return response
            else:
                print(Colors.WARNING + "\n⚠ Nincs felismert szöveg" + Colors.ENDC)
                return None
                
        except Exception as e:
            print(Colors.FAIL + f"\n✗ Eredmény lekérési hiba: {e}" + Colors.ENDC)
            return None
    
    def _get_speech_config(self) -> speech.RecognitionConfig:
        """Get Speech API configuration."""
        return speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
            sample_rate_hertz=settings.ffmpeg_sample_rate,
            language_code=settings.language_code,
            enable_automatic_punctuation=settings.enable_punctuation,
            enable_word_time_offsets=settings.enable_word_offsets,
            audio_channel_count=settings.ffmpeg_channels,
        )
    
    def _cleanup_gcs_file(self, gcs_uri: str):
        """Clean up uploaded file from GCS."""
        try:
            # Extract bucket and blob name from URI
            if gcs_uri.startswith("gs://"):
                parts = gcs_uri[5:].split("/", 1)
                if len(parts) == 2:
                    bucket_name, blob_name = parts
                    bucket = self.storage_client.bucket(bucket_name)
                    blob = bucket.blob(blob_name)
                    blob.delete()
                    print(Colors.GREEN + f"   ✓ GCS fájl törölve: {blob_name}" + Colors.ENDC)
        except Exception as e:
            print(Colors.WARNING + f"   ⚠ GCS cleanup hiba: {e}" + Colors.ENDC)