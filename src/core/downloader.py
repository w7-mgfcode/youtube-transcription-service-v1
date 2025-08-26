"""YouTube audio download module."""

import os
import time
import subprocess
import shutil
from typing import Tuple, Optional, Callable
import yt_dlp

from ..config import settings
from ..utils.progress import update_progress
from ..utils.colors import Colors
from ..utils.validators import extract_video_id


class YouTubeDownloader:
    """YouTube audio downloader using yt-dlp."""
    
    def __init__(self):
        self.temp_dir = settings.temp_dir
        
    def download(self, url: str, test_mode: bool = False, 
                 progress_callback: Optional[Callable] = None) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        """
        Download audio from YouTube video.
        
        Args:
            url: YouTube video URL
            test_mode: If True, limit to first 60 seconds
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (audio_file_path, duration_seconds, video_title) or (None, None, None) on error
        """
        try:
            print(Colors.BLUE + "\n📥 Videó információk lekérése..." + Colors.ENDC)
            print(Colors.CYAN + "   ├─ URL feldolgozása..." + Colors.ENDC)
            
            # Extract video information
            start_time = time.time()
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                print(Colors.CYAN + "   ├─ Kapcsolódás YouTube-hoz..." + Colors.ENDC)
                info = ydl.extract_info(url, download=False)
                fetch_time = time.time() - start_time
                
                video_title = info.get('title', 'Ismeretlen')
                video_duration = info.get('duration', 0)
                video_id = info.get('id', 'unknown')
                uploader = info.get('uploader', 'Ismeretlen')
                view_count = info.get('view_count', 0)
            
            print(Colors.GREEN + f"   └─ Információk lekérve ({fetch_time:.1f}s)" + Colors.ENDC)
            print()
            
            # Display video details
            self._display_video_info(video_title, uploader, video_duration, view_count, video_id)
            
            if test_mode:
                print(Colors.WARNING + "\n⚡ TESZT MÓD: Csak az első 60 másodperc lesz letöltve!" + Colors.ENDC)
            
            # Download audio
            audio_file = self._download_audio(url, video_id, test_mode, progress_callback)
            
            if not audio_file:
                return None, None, None
            
            # Trim to 60 seconds if test mode and duration > 60
            if test_mode and video_duration > 60:
                print(Colors.BLUE + "\n✂️ Audio vágása 60 másodpercre..." + Colors.ENDC)
                trimmed_file = self._trim_audio_to_60s(audio_file)
                if trimmed_file and trimmed_file != audio_file:
                    # Clean up original file
                    try:
                        os.remove(audio_file)
                    except:
                        pass
                    audio_file = trimmed_file
            
            final_duration = min(60, video_duration) if test_mode else video_duration
            return audio_file, final_duration, video_title
            
        except Exception as e:
            print(Colors.FAIL + f"✗ Hiba a letöltés során: {e}" + Colors.ENDC)
            return None, None, None
    
    def _display_video_info(self, title: str, uploader: str, duration: int, view_count: int, video_id: str):
        """Display video information in Hungarian."""
        print(Colors.BOLD + "📺 Videó részletek:" + Colors.ENDC)
        print(f"   ├─ Cím: {title[:60]}{'...' if len(title) > 60 else ''}")
        print(f"   ├─ Feltöltő: {uploader}")
        print(f"   ├─ Hossz: {duration//60}:{duration%60:02d}")
        if view_count:
            print(f"   ├─ Megtekintések: {view_count:,}")
        else:
            print("   ├─ Megtekintések: N/A")
        print(f"   └─ Video ID: {video_id}")
    
    def _download_audio(self, url: str, video_id: str, test_mode: bool, 
                       progress_callback: Optional[Callable] = None) -> Optional[str]:
        """Download audio file with progress tracking."""
        output_file = f"audio_{video_id}.%(ext)s"
        download_start = time.time()
        
        def download_hook(d):
            """Progress hook for yt-dlp."""
            if d['status'] == 'downloading':
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                speed = d.get('speed', 0)
                
                if total > 0:
                    # Size information
                    downloaded_mb = downloaded / (1024*1024)
                    total_mb = total / (1024*1024)
                    speed_kb = speed / 1024 if speed else 0
                    
                    extra_info = f"Méret: {downloaded_mb:.1f}/{total_mb:.1f}MB │ Sebesség: {speed_kb:.0f}KB/s"
                    
                    update_progress(
                        downloaded, total,
                        prefix="📥 Letöltés",
                        extra_info=extra_info
                    )
                    
                    # Call external progress callback if provided
                    if progress_callback:
                        progress_callback("downloading", int((downloaded / total) * 100))
                        
            elif d['status'] == 'finished':
                download_time = time.time() - download_start
                print(Colors.GREEN + f"\n   ✓ Letöltés kész ({download_time:.1f}s)" + Colors.ENDC)
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio',
            'outtmpl': output_file,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [download_hook],
        }
        
        if test_mode:
            ydl_opts['postprocessor_args'] = ['-t', '60']
        
        print(Colors.BLUE + "\n🎵 Audio stream letöltése..." + Colors.ENDC)
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            print(Colors.FAIL + f"✗ Letöltési hiba: {e}" + Colors.ENDC)
            return None
        
        # Find downloaded file
        return self._find_downloaded_file(video_id)
    
    def _find_downloaded_file(self, video_id: str) -> Optional[str]:
        """Find the downloaded audio file."""
        print(Colors.CYAN + "\n🔍 Letöltött fájl keresése..." + Colors.ENDC)
        
        for ext in ['m4a', 'webm', 'mp4', 'mp3']:
            filename = f"audio_{video_id}.{ext}"
            if os.path.exists(filename):
                size_mb = os.path.getsize(filename) / (1024*1024)
                print(Colors.GREEN + f"   ✓ Találat: {filename}" + Colors.ENDC)
                print(f"   ├─ Méret: {size_mb:.2f} MB")
                print(f"   └─ Formátum: {ext.upper()}")
                return filename
        
        print(Colors.FAIL + "✗ Nem található a letöltött fájl!" + Colors.ENDC)
        return None
    
    def _trim_audio_to_60s(self, input_file: str) -> Optional[str]:
        """
        Trim audio file to 60 seconds using ffmpeg.
        
        Args:
            input_file: Path to input audio file
            
        Returns:
            Path to trimmed file or original file if trimming fails
        """
        if not shutil.which('ffmpeg'):
            print(Colors.WARNING + "⚠ ffmpeg nem található, vágás kihagyva" + Colors.ENDC)
            return input_file
        
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_60s{ext}"
        
        try:
            cmd = [
                'ffmpeg', '-y', '-i', input_file,
                '-t', '60',  # 60 seconds
                '-c', 'copy',  # Copy codec, no re-encoding
                output_file
            ]
            
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(Colors.GREEN + "✓ Audio levágva 60 másodpercre" + Colors.ENDC)
            return output_file
            
        except subprocess.CalledProcessError:
            print(Colors.WARNING + "⚠ Audio vágás sikertelen, eredeti fájl használva" + Colors.ENDC)
            return input_file
        except Exception as e:
            print(Colors.WARNING + f"⚠ Audio vágás hiba: {e}, eredeti fájl használva" + Colors.ENDC)
            return input_file