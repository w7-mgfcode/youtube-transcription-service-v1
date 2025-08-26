"""Audio conversion module using FFmpeg."""

import os
import re
import time
import subprocess
import shutil
from typing import Optional

from ..config import settings
from ..utils.progress import update_progress
from ..utils.colors import Colors


class AudioConverter:
    """Audio converter using FFmpeg."""
    
    def __init__(self):
        self.sample_rate = settings.ffmpeg_sample_rate
        self.channels = settings.ffmpeg_channels
    
    def to_flac(self, input_file: str) -> str:
        """
        Convert audio file to FLAC format.
        
        Args:
            input_file: Path to input audio file
            
        Returns:
            Path to FLAC file (original file if conversion fails)
        """
        if not shutil.which('ffmpeg'):
            print(Colors.WARNING + "⚠ ffmpeg nem található, konverzió kihagyva" + Colors.ENDC)
            return input_file
        
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_converted.flac"
        
        print(Colors.BLUE + "\n🔄 Audio konvertálás FLAC formátumba..." + Colors.ENDC)
        print(Colors.CYAN + "   ├─ Forrás: " + input_file + Colors.ENDC)
        print(Colors.CYAN + f"   ├─ Cél formátum: FLAC {self.sample_rate}Hz {self.channels} csatorna" + Colors.ENDC)
        print(Colors.CYAN + "   └─ FFmpeg indítása..." + Colors.ENDC)
        
        try:
            start_time = time.time()
            
            # Get file duration for progress tracking
            duration = self._get_audio_duration(input_file)
            if duration > 0:
                duration_str = f"{int(duration//60)}:{int(duration%60):02d}"
                print(f"   ├─ Időtartam: {duration_str}")
            
            # Convert with progress tracking
            success = self._convert_with_progress(input_file, output_file, duration)
            
            if success and os.path.exists(output_file):
                conversion_time = time.time() - start_time
                self._display_conversion_results(input_file, output_file, conversion_time)
                return output_file
            else:
                print(Colors.WARNING + f"⚠ FLAC konverzió sikertelen" + Colors.ENDC)
                return input_file
                
        except Exception as e:
            print(Colors.WARNING + f"⚠ FLAC konverzió sikertelen: {e}" + Colors.ENDC)
            return input_file
    
    def _get_audio_duration(self, file_path: str) -> float:
        """Get audio file duration using ffprobe."""
        try:
            probe_cmd = [
                'ffprobe', '-v', 'error', '-show_entries', 
                'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
                file_path
            ]
            
            duration_output = subprocess.check_output(probe_cmd, stderr=subprocess.DEVNULL)
            return float(duration_output.decode().strip())
        except:
            return 0
    
    def _convert_with_progress(self, input_file: str, output_file: str, duration: float) -> bool:
        """Convert file with progress monitoring."""
        cmd = [
            'ffmpeg', '-y', '-i', input_file,
            '-ac', str(self.channels),  # Audio channels
            '-ar', str(self.sample_rate),  # Sample rate
            '-vn',  # No video
            '-stats',  # Statistics
            output_file
        ]
        
        try:
            # Start FFmpeg process
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Monitor progress
            print()
            while True:
                line = process.stderr.readline()
                if not line:
                    break
                
                # Parse FFmpeg progress
                if 'time=' in line:
                    try:
                        current_time = self._parse_ffmpeg_time(line)
                        if current_time and duration > 0:
                            progress = (current_time / duration) * 100
                            speed = self._parse_ffmpeg_speed(line)
                            
                            eta = (duration - current_time) / speed if speed > 0 else 0
                            eta_str = f"{int(eta//60)}:{int(eta%60):02d}"
                            
                            extra_info = f"Sebesség: {speed:.1f}x │ Hátra: {eta_str}"
                            update_progress(
                                progress, 100,
                                prefix="🔄 Konvertálás",
                                extra_info=extra_info
                            )
                    except:
                        pass
            
            process.wait()
            print()
            return process.returncode == 0
            
        except Exception as e:
            print(Colors.FAIL + f"✗ FFmpeg hiba: {e}" + Colors.ENDC)
            return False
    
    def _parse_ffmpeg_time(self, line: str) -> Optional[float]:
        """Parse current time from FFmpeg output."""
        time_match = re.search(r'time=(\d+):(\d+):(\d+\.?\d*)', line)
        if time_match:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            seconds = float(time_match.group(3))
            return hours * 3600 + minutes * 60 + seconds
        return None
    
    def _parse_ffmpeg_speed(self, line: str) -> float:
        """Parse processing speed from FFmpeg output."""
        speed_match = re.search(r'speed=\s*(\d+\.?\d*)x', line)
        if speed_match:
            return float(speed_match.group(1))
        return 1.0
    
    def _display_conversion_results(self, input_file: str, output_file: str, conversion_time: float):
        """Display conversion results and statistics."""
        original_size = os.path.getsize(input_file) / (1024*1024)
        new_size = os.path.getsize(output_file) / (1024*1024)
        
        print(Colors.GREEN + f"   ✓ Konverzió kész ({conversion_time:.1f}s)" + Colors.ENDC)
        print(f"   ├─ Új fájl: {output_file}")
        print(f"   ├─ Méret: {original_size:.2f} MB → {new_size:.2f} MB")
        
        if original_size > 0:
            size_change = ((new_size - original_size) / original_size * 100)
            if size_change < 0:
                print(f"   └─ Tömörítés: {abs(size_change):.1f}% megtakarítás")
            else:
                print(f"   └─ Méret növekedés: {size_change:.1f}%")
    
    def cleanup_temp_file(self, file_path: str) -> bool:
        """
        Clean up temporary file.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if successfully deleted, False otherwise
        """
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except Exception as e:
                print(Colors.WARNING + f"⚠ Nem sikerült törölni: {file_path} - {e}" + Colors.ENDC)
                return False
        return False