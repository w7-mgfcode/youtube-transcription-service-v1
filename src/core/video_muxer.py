"""Video muxing module for replacing audio tracks using FFmpeg."""

import os
import subprocess
import datetime
import tempfile
from typing import Optional, Dict, Tuple
from pathlib import Path

from ..config import settings
from ..utils.colors import Colors


class VideoMuxingError(Exception):
    """Raised when video muxing operations fail."""
    pass


class VideoMuxer:
    """FFmpeg-based video muxer for replacing audio tracks in videos."""
    
    def __init__(self):
        self.temp_video_dir = settings.temp_video_dir
        self.video_format = settings.video_output_format
        self.preserve_quality = True
        
        # Ensure temp directory exists
        os.makedirs(self.temp_video_dir, exist_ok=True)
    
    def replace_audio_in_video(self, 
                             video_url: str,
                             audio_file_path: str, 
                             output_path: str,
                             preserve_video_quality: bool = True,
                             target_format: str = "mp4") -> Dict:
        """
        Replace audio track in video with new synthesized audio.
        
        Args:
            video_url: YouTube video URL or local video path
            audio_file_path: Path to new audio file
            output_path: Path for final dubbed video
            preserve_video_quality: Whether to preserve original video quality
            target_format: Output video format
            
        Returns:
            Dictionary with muxing result and metadata
        """
        print(Colors.BLUE + f"\n🎬 Video muxing indítása..." + Colors.ENDC)
        start_time = datetime.datetime.now()
        
        try:
            # Download video (video-only to save bandwidth)
            temp_video_path = self._download_video_only(video_url)
            if not temp_video_path or not os.path.exists(temp_video_path):
                raise VideoMuxingError("Failed to download video")
            
            print(Colors.CYAN + f"   ├─ Video letöltve: {os.path.basename(temp_video_path)}" + Colors.ENDC)
            
            # Verify audio file exists
            if not os.path.exists(audio_file_path):
                raise VideoMuxingError(f"Audio file not found: {audio_file_path}")
            
            # Get video info
            video_info = self._get_video_info(temp_video_path)
            audio_info = self._get_audio_info(audio_file_path)
            
            print(Colors.CYAN + f"   ├─ Video: {video_info['duration']:.1f}s, {video_info['resolution']}" + Colors.ENDC)
            print(Colors.CYAN + f"   ├─ Audio: {audio_info['duration']:.1f}s, {audio_info['sample_rate']}Hz" + Colors.ENDC)
            
            # Check duration compatibility
            self._validate_duration_compatibility(video_info, audio_info)
            
            # Perform muxing
            final_result = self._mux_video_audio(
                temp_video_path, audio_file_path, output_path,
                preserve_video_quality, target_format
            )
            
            processing_time = (datetime.datetime.now() - start_time).total_seconds()
            
            # Add metadata
            final_result.update({
                'processing_time_seconds': processing_time,
                'original_video_duration': video_info['duration'],
                'audio_duration': audio_info['duration'],
                'video_source': video_url
            })
            
            print(Colors.GREEN + f"   ✓ Video muxing kész: {final_result.get('file_size_bytes', 0) // 1024 // 1024}MB" + Colors.ENDC)
            
            return final_result
            
        except Exception as e:
            print(Colors.FAIL + f"✗ Video muxing hiba: {e}" + Colors.ENDC)
            raise VideoMuxingError(f"Video muxing failed: {e}")
        finally:
            # Cleanup temp video file
            if 'temp_video_path' in locals() and os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                    print(Colors.CYAN + "   └─ Temp video fájl törölve" + Colors.ENDC)
                except:
                    pass
    
    def _download_video_only(self, video_url: str) -> str:
        """Download video stream only (no audio) to save bandwidth."""
        if os.path.isfile(video_url):
            # Local file path provided
            return video_url
        
        print(Colors.CYAN + "   ├─ Video letöltése (csak video track)..." + Colors.ENDC)
        
        # Generate temp file name
        temp_filename = f"video_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.%(ext)s"
        temp_path = os.path.join(self.temp_video_dir, temp_filename)
        
        try:
            # Use yt-dlp to download video-only stream
            cmd = [
                'yt-dlp',
                '--format', 'bv[ext=mp4]/best[ext=mp4]/bv/best',  # Video only, prefer mp4
                '--output', temp_path,
                '--no-warnings',
                '--no-playlist',
                video_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                print(Colors.WARNING + f"   ⚠ yt-dlp error: {result.stderr}" + Colors.ENDC)
                raise VideoMuxingError(f"Video download failed: {result.stderr}")
            
            # Find the downloaded file (yt-dlp changes extension)
            temp_dir = Path(self.temp_video_dir)
            pattern = temp_filename.replace('.%(ext)s', '.*')
            
            for file_path in temp_dir.glob(pattern):
                if file_path.is_file():
                    return str(file_path)
            
            raise VideoMuxingError("Downloaded video file not found")
            
        except subprocess.TimeoutExpired:
            raise VideoMuxingError("Video download timeout (10 minutes)")
        except Exception as e:
            raise VideoMuxingError(f"Video download error: {e}")
    
    def _get_video_info(self, video_path: str) -> Dict:
        """Get video file information using ffprobe."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise VideoMuxingError(f"ffprobe failed: {result.stderr}")
            
            import json
            probe_data = json.loads(result.stdout)
            
            # Find video stream
            video_stream = None
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                raise VideoMuxingError("No video stream found")
            
            duration = float(probe_data.get('format', {}).get('duration', 0))
            width = video_stream.get('width', 0)
            height = video_stream.get('height', 0)
            
            return {
                'duration': duration,
                'resolution': f"{width}x{height}",
                'width': width,
                'height': height,
                'codec': video_stream.get('codec_name', 'unknown'),
                'bitrate': int(probe_data.get('format', {}).get('bit_rate', 0)),
                'fps': self._parse_framerate(video_stream.get('r_frame_rate', '0/0'))
            }
            
        except json.JSONDecodeError:
            raise VideoMuxingError("Failed to parse ffprobe output")
        except Exception as e:
            raise VideoMuxingError(f"Video info extraction failed: {e}")
    
    def _get_audio_info(self, audio_path: str) -> Dict:
        """Get audio file information using ffprobe."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise VideoMuxingError(f"Audio ffprobe failed: {result.stderr}")
            
            import json
            probe_data = json.loads(result.stdout)
            
            # Find audio stream
            audio_stream = None
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                raise VideoMuxingError("No audio stream found")
            
            duration = float(probe_data.get('format', {}).get('duration', 0))
            
            return {
                'duration': duration,
                'codec': audio_stream.get('codec_name', 'unknown'),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'bitrate': int(audio_stream.get('bit_rate', 0)) if audio_stream.get('bit_rate') else 0
            }
            
        except Exception as e:
            raise VideoMuxingError(f"Audio info extraction failed: {e}")
    
    def _validate_duration_compatibility(self, video_info: Dict, audio_info: Dict):
        """Validate that video and audio durations are compatible."""
        video_duration = video_info['duration']
        audio_duration = audio_info['duration']
        
        # Allow some tolerance (up to 10% difference)
        duration_diff = abs(video_duration - audio_duration)
        tolerance = video_duration * 0.1
        
        if duration_diff > tolerance:
            print(Colors.WARNING + f"   ⚠ Duration mismatch: video={video_duration:.1f}s, audio={audio_duration:.1f}s" + Colors.ENDC)
            
            # If audio is much shorter, that's problematic
            if audio_duration < video_duration * 0.8:
                print(Colors.WARNING + "   ⚠ Audio significantly shorter than video" + Colors.ENDC)
            
            # If audio is much longer, we'll trim it
            if audio_duration > video_duration * 1.2:
                print(Colors.WARNING + "   ⚠ Audio will be trimmed to match video" + Colors.ENDC)
    
    def _mux_video_audio(self, video_path: str, audio_path: str, output_path: str,
                        preserve_quality: bool, target_format: str) -> Dict:
        """Perform the actual video/audio muxing using FFmpeg."""
        print(Colors.CYAN + "   ├─ FFmpeg muxing futtatása..." + Colors.ENDC)
        
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Build FFmpeg command
            cmd = self._build_ffmpeg_command(
                video_path, audio_path, output_path, 
                preserve_quality, target_format
            )
            
            print(Colors.CYAN + f"   ├─ FFmpeg cmd: {' '.join(cmd[:8])}..." + Colors.ENDC)
            
            # Run FFmpeg
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=1800  # 30 minutes max
            )
            
            if result.returncode != 0:
                print(Colors.FAIL + f"   ✗ FFmpeg error: {result.stderr}" + Colors.ENDC)
                raise VideoMuxingError(f"FFmpeg failed: {result.stderr}")
            
            # Verify output file was created
            if not os.path.exists(output_path):
                raise VideoMuxingError("Output file was not created")
            
            # Get output file info
            output_info = self._get_video_info(output_path)
            file_size = os.path.getsize(output_path)
            
            return {
                'video_file_path': output_path,
                'final_video_duration': output_info['duration'],
                'file_size_bytes': file_size,
                'format': target_format,
                'resolution': output_info['resolution'],
                'video_codec': output_info['codec'],
                'success': True
            }
            
        except subprocess.TimeoutExpired:
            raise VideoMuxingError("FFmpeg timeout (30 minutes)")
        except Exception as e:
            raise VideoMuxingError(f"Muxing operation failed: {e}")
    
    def _build_ffmpeg_command(self, video_path: str, audio_path: str, output_path: str,
                            preserve_quality: bool, target_format: str) -> list:
        """Build FFmpeg command for video/audio muxing."""
        
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file
            '-i', video_path,  # Video input
            '-i', audio_path,  # Audio input
        ]
        
        if preserve_quality:
            # Copy video stream without re-encoding
            cmd.extend(['-c:v', 'copy'])
        else:
            # Re-encode video (smaller file, quality loss)
            cmd.extend(['-c:v', 'libx264', '-crf', '23'])
        
        # Audio encoding settings
        cmd.extend([
            '-c:a', 'aac',  # Use AAC audio codec
            '-b:a', '128k',  # Audio bitrate
            '-ac', '2',  # Stereo
            '-ar', '44100'  # Sample rate
        ])
        
        # Map streams
        cmd.extend([
            '-map', '0:v:0',  # Video from first input
            '-map', '1:a:0',  # Audio from second input
        ])
        
        # Sync options
        cmd.extend([
            '-shortest',  # Stop at shortest stream
            '-avoid_negative_ts', 'make_zero',  # Handle timing issues
        ])
        
        # Format-specific options
        if target_format == 'mp4':
            cmd.extend(['-movflags', '+faststart'])  # Optimize for streaming
        
        cmd.append(output_path)
        
        return cmd
    
    def _parse_framerate(self, framerate_str: str) -> float:
        """Parse FFmpeg framerate string (e.g., '30000/1001')."""
        try:
            if '/' in framerate_str:
                num, den = framerate_str.split('/')
                return float(num) / float(den)
            else:
                return float(framerate_str)
        except:
            return 0.0
    
    def create_preview_video(self, video_url: str, audio_file_path: str, 
                           output_path: str, duration_seconds: int = 30) -> Dict:
        """Create a short preview of the dubbed video."""
        print(Colors.BLUE + f"\n🎬 Preview video készítése ({duration_seconds}s)..." + Colors.ENDC)
        
        try:
            # Download short segment of video
            temp_video = self._download_video_segment(video_url, 0, duration_seconds)
            
            # Trim audio to same duration
            temp_audio = self._trim_audio(audio_file_path, 0, duration_seconds)
            
            # Mux preview
            result = self._mux_video_audio(temp_video, temp_audio, output_path, True, "mp4")
            
            # Cleanup temp files
            for temp_file in [temp_video, temp_audio]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            result['is_preview'] = True
            result['preview_duration'] = duration_seconds
            
            print(Colors.GREEN + "   ✓ Preview video kész" + Colors.ENDC)
            return result
            
        except Exception as e:
            raise VideoMuxingError(f"Preview creation failed: {e}")
    
    def _download_video_segment(self, video_url: str, start_sec: int, duration_sec: int) -> str:
        """Download a specific segment of video."""
        temp_filename = f"preview_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        temp_path = os.path.join(self.temp_video_dir, temp_filename)
        
        try:
            cmd = [
                'yt-dlp',
                '--format', 'bv[ext=mp4]/best[ext=mp4]',
                '--external-downloader', 'ffmpeg',
                '--external-downloader-args', f'-ss {start_sec} -t {duration_sec}',
                '--output', temp_path,
                '--no-warnings',
                video_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise VideoMuxingError(f"Video segment download failed: {result.stderr}")
            
            return temp_path
            
        except Exception as e:
            raise VideoMuxingError(f"Video segment download error: {e}")
    
    def _trim_audio(self, audio_path: str, start_sec: int, duration_sec: int) -> str:
        """Trim audio file to specified duration."""
        temp_filename = f"audio_trim_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        temp_path = os.path.join(self.temp_video_dir, temp_filename)
        
        try:
            cmd = [
                'ffmpeg',
                '-y',
                '-i', audio_path,
                '-ss', str(start_sec),
                '-t', str(duration_sec),
                '-c:a', 'copy',
                temp_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise VideoMuxingError(f"Audio trimming failed: {result.stderr}")
            
            return temp_path
            
        except Exception as e:
            raise VideoMuxingError(f"Audio trimming error: {e}")
    
    def get_supported_formats(self) -> list:
        """Get list of supported output video formats."""
        return [
            {"format": "mp4", "description": "MP4 (recommended)", "codec": "H.264"},
            {"format": "webm", "description": "WebM", "codec": "VP9"},
            {"format": "avi", "description": "AVI", "codec": "H.264"},
            {"format": "mkv", "description": "Matroska", "codec": "H.264"}
        ]
    
    def validate_video_url(self, video_url: str) -> bool:
        """Validate that a video URL is accessible."""
        if os.path.isfile(video_url):
            return os.path.exists(video_url)
        
        try:
            # Test with yt-dlp
            cmd = ['yt-dlp', '--no-download', '--quiet', video_url]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            return result.returncode == 0
        except:
            return False