"""Main transcription orchestrator service."""

import os
import uuid
import datetime
from typing import Tuple, Optional, Callable, Dict, Any

from ..config import settings, VertexAIModels
from ..utils.progress import ProgressTracker
from ..utils.colors import Colors
from .downloader import YouTubeDownloader
from .converter import AudioConverter
from .speech_client import SpeechClient
from .segmenter import TranscriptFormatter
from .postprocessor import VertexPostProcessor


class TranscriptionService:
    """Main orchestrator for the transcription pipeline."""
    
    def __init__(self):
        """Initialize all service components."""
        self.downloader = YouTubeDownloader()
        self.converter = AudioConverter()
        self.speech_client = SpeechClient()
        self.formatter = TranscriptFormatter()
        self.postprocessor = VertexPostProcessor()
        
        # Ensure data directory exists
        os.makedirs(settings.data_dir, exist_ok=True)
        os.makedirs(settings.temp_dir, exist_ok=True)
    
    def process(self, url: str, test_mode: bool = False, breath_detection: bool = True,
                use_vertex_ai: bool = False, vertex_ai_model: str = VertexAIModels.AUTO_DETECT, 
                progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Main transcription processing pipeline.
        
        Args:
            url: YouTube video URL
            test_mode: If True, process only first 60 seconds
            breath_detection: Enable breath/pause detection
            use_vertex_ai: Enable Vertex AI post-processing
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with job results
        """
        job_id = str(uuid.uuid4())
        tracker = ProgressTracker(job_id, progress_callback)
        
        temp_files = []  # Track temporary files for cleanup
        
        try:
            print(Colors.BOLD + f"\n🎯 Feldolgozási folyamat indítása - Job ID: {job_id[:8]}" + Colors.ENDC)
            
            # Step 1: Download audio
            tracker.update("downloading", 10)
            audio_file, duration, video_title = self.downloader.download(
                url, test_mode, tracker.update_download
            )
            
            if not audio_file:
                raise Exception("Audio letöltés sikertelen")
            
            temp_files.append(audio_file)
            
            # Step 2: Convert to FLAC
            tracker.update("converting", 30)
            flac_file = self.converter.to_flac(audio_file)
            
            if flac_file != audio_file:
                temp_files.append(flac_file)
            
            # Step 3: Transcribe using Speech API
            tracker.update("transcribing", 40)
            response = self.speech_client.transcribe(
                flac_file, duration, video_title, breath_detection
            )
            
            if not response:
                raise Exception("Speech API átirat készítése sikertelen")
            
            # Step 4: Format transcript
            tracker.update("formatting", 80)
            transcript_text = self.formatter.format_transcript(
                response, video_title, breath_detection
            )
            
            if not transcript_text:
                raise Exception("Átirat formázás sikertelen")
            
            # Step 5: Optional Vertex AI post-processing
            if use_vertex_ai:
                tracker.update("postprocessing", 90)
                vertex_result = self.postprocessor.process(transcript_text, video_title, vertex_ai_model)
                if vertex_result:
                    transcript_text = vertex_result
                    print(Colors.GREEN + "✓ Vertex AI formázás alkalmazva!" + Colors.ENDC)
            
            # Step 6: Save transcript
            tracker.update("saving", 95)
            output_file = self._save_transcript(transcript_text, url, video_title)
            
            if not output_file:
                raise Exception("Átirat mentés sikertelen")
            
            # Step 7: Cleanup temporary files
            tracker.update("cleanup", 98)
            self._cleanup_temp_files(temp_files)
            
            # Complete
            tracker.update("completed", 100)
            
            # Prepare result
            result = {
                "job_id": job_id,
                "status": "completed",
                "title": video_title,
                "duration": duration,
                "transcript_file": output_file,
                "word_count": len(transcript_text.split()),
                "url": url,
                "test_mode": test_mode,
                "breath_detection": breath_detection,
                "vertex_ai_used": use_vertex_ai,
                "processed_at": datetime.datetime.now().isoformat()
            }
            
            print(Colors.BOLD + Colors.GREEN + f"\n✅ SIKERES FELDOLGOZÁS!" + Colors.ENDC)
            print(Colors.GREEN + f"   📁 Eredmény: {output_file}" + Colors.ENDC)
            print(Colors.GREEN + f"   📊 Szószám: {result['word_count']}" + Colors.ENDC)
            print(Colors.GREEN + f"   ⏱️  Időtartam: {duration}s" + Colors.ENDC)
            
            return result
            
        except Exception as e:
            # Cleanup on error
            self._cleanup_temp_files(temp_files)
            tracker.update("error", -1)
            
            error_msg = f"Transcription failed: {str(e)}"
            print(Colors.FAIL + f"\n✗ {error_msg}" + Colors.ENDC)
            
            return {
                "job_id": job_id,
                "status": "failed",
                "error": error_msg,
                "url": url,
                "test_mode": test_mode,
                "processed_at": datetime.datetime.now().isoformat()
            }
    
    def _save_transcript(self, text: str, video_url: str, video_title: str = "") -> Optional[str]:
        """
        Save transcript to file.
        
        Args:
            text: Transcript text
            video_url: Original video URL
            video_title: Video title
            
        Returns:
            Path to saved file or None on error
        """
        try:
            # Generate filename from video URL or timestamp
            video_id = self._extract_video_id_from_url(video_url)
            if not video_id:
                video_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            filename = f"transcript_{video_id}.txt"
            output_path = os.path.join(settings.data_dir, filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            file_size = os.path.getsize(output_path) / 1024  # KB
            
            print(Colors.GREEN + f"\n💾 Átirat mentve: {filename} ({file_size:.1f} KB)" + Colors.ENDC)
            print(Colors.CYAN + f"   📄 {len(text.split())} szó" + Colors.ENDC)
            print(Colors.CYAN + f"   📝 {len(text.splitlines())} sor" + Colors.ENDC)
            
            return output_path
            
        except Exception as e:
            print(Colors.FAIL + f"✗ Mentési hiba: {e}" + Colors.ENDC)
            return None
    
    def _extract_video_id_from_url(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        import re
        
        patterns = [
            r'youtube\.com/watch\?v=([^&]+)',
            r'youtu\.be/([^?]+)',
            r'youtube\.com/embed/([^?]+)',
            r'youtube\.com/v/([^?]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _cleanup_temp_files(self, temp_files: list):
        """
        Clean up temporary files.
        
        Args:
            temp_files: List of file paths to clean up
        """
        if not temp_files:
            return
            
        print(Colors.BLUE + "\n🧹 Takarítás..." + Colors.ENDC)
        
        for file_path in temp_files:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(Colors.GREEN + f"   ✓ Törölve: {os.path.basename(file_path)}" + Colors.ENDC)
                except Exception as e:
                    print(Colors.WARNING + f"   ⚠ Nem törölhető: {os.path.basename(file_path)} - {e}" + Colors.ENDC)
    
    def get_job_info(self, job_id: str) -> Dict[str, Any]:
        """
        Get information about a completed job (placeholder for future enhancement).
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job information dictionary
        """
        # This could be enhanced to store job info in a database
        return {
            "job_id": job_id,
            "status": "unknown",
            "message": "Job tracking not implemented in basic version"
        }
    
    def list_completed_jobs(self) -> list:
        """
        List completed transcription jobs by scanning data directory.
        
        Returns:
            List of completed job files
        """
        try:
            transcript_files = []
            if os.path.exists(settings.data_dir):
                for filename in os.listdir(settings.data_dir):
                    if filename.startswith("transcript_") and filename.endswith(".txt"):
                        file_path = os.path.join(settings.data_dir, filename)
                        file_size = os.path.getsize(file_path)
                        mod_time = os.path.getmtime(file_path)
                        
                        transcript_files.append({
                            "filename": filename,
                            "path": file_path,
                            "size_kb": file_size / 1024,
                            "modified": datetime.datetime.fromtimestamp(mod_time).isoformat()
                        })
            
            # Sort by modification time, newest first
            transcript_files.sort(key=lambda x: x["modified"], reverse=True)
            return transcript_files
            
        except Exception as e:
            print(Colors.WARNING + f"⚠ Job listing error: {e}" + Colors.ENDC)
            return []