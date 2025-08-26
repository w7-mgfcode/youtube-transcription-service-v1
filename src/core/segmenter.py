"""Pause detection and transcript segmentation module."""

import datetime
from typing import List, Dict, Any, Optional
from google.cloud import speech

from ..config import settings
from ..utils.colors import Colors


class PauseSegmenter:
    """Pause detection and transcript segmentation."""
    
    def __init__(self):
        self.pause_min = settings.pause_min
        self.pause_short = settings.pause_short
        self.pause_long = settings.pause_long
        self.pause_paragraph = settings.pause_paragraph
    
    def detect_pauses_and_segment(self, words: List[Any]) -> List[Dict[str, Any]]:
        """
        Detect pauses and segment transcript based on timing.
        
        Args:
            words: List of word info objects from Speech API
            
        Returns:
            List of segments with pause information
        """
        segments = []
        current_segment = []
        current_text = ""
        segment_start = None
        
        for i, word_info in enumerate(words):
            word = word_info.word
            start_time = word_info.start_time.total_seconds() if hasattr(word_info, 'start_time') else 0
            end_time = word_info.end_time.total_seconds() if hasattr(word_info, 'end_time') else start_time + 0.3
            
            if segment_start is None:
                segment_start = start_time
            
            current_text += word + " "
            
            # Check pause after current word
            if i < len(words) - 1:
                next_start = words[i+1].start_time.total_seconds() if hasattr(words[i+1], 'start_time') else end_time
                pause_duration = next_start - end_time
                
                # Categorize pause
                if pause_duration > self.pause_min:  # Minimum pause threshold
                    pause_type = self._categorize_pause(pause_duration, word)
                    
                    if pause_type:
                        segments.append({
                            'text': current_text.strip(),
                            'start_time': segment_start,
                            'end_time': end_time,
                            'pause_after': pause_duration,
                            'pause_type': pause_type
                        })
                        current_text = ""
                        segment_start = None
        
        # Add final segment
        if current_text.strip():
            segments.append({
                'text': current_text.strip(),
                'start_time': segment_start,
                'end_time': end_time,
                'pause_after': 0,
                'pause_type': None
            })
        
        return segments
    
    def _categorize_pause(self, pause_duration: float, word: str) -> Optional[str]:
        """
        Categorize pause based on duration and context.
        
        Args:
            pause_duration: Length of pause in seconds
            word: The word before the pause
            
        Returns:
            Pause type string or None
        """
        # Check for sentence ending
        if word.rstrip() and word.rstrip()[-1] in '.!?':
            if pause_duration >= 1.0:
                return 'sentence_end'
        
        # Categorize by duration
        if pause_duration >= self.pause_paragraph:
            return 'paragraph'
        elif pause_duration >= self.pause_long:
            return 'long_breath'
        elif pause_duration >= self.pause_short:
            return 'short_breath'
        
        return None


class TranscriptFormatter:
    """Format transcripts with pause detection and statistics."""
    
    def __init__(self):
        self.segmenter = PauseSegmenter()
        self.breath_symbols = {
            'short_breath': ' • ',      # Short breath
            'long_breath': ' •• ',       # Long pause
            'paragraph': '\n\n',         # Paragraph break
            'sentence_end': '\n',        # Sentence end
            None: ' '                    # No special marking
        }
    
    def format_transcript(self, response: speech.RecognizeResponse, 
                         video_title: str = "", breath_marking: bool = True) -> str:
        """
        Format transcript with intelligent segmentation and breath marking.
        
        Args:
            response: Speech API response
            video_title: Video title
            breath_marking: Enable breath/pause marking
            
        Returns:
            Formatted transcript string
        """
        if not response or not response.results:
            return ""
        
        print(Colors.BLUE + "\n📝 Átirat formázása levegővétel detektálással..." + Colors.ENDC)
        
        # Collect all words and statistics
        all_words = []
        total_words = 0
        total_confidence = 0
        
        for result in response.results:
            if not result.alternatives:
                continue
            
            alternative = result.alternatives[0]
            
            if not hasattr(alternative, 'words') or not alternative.words:
                # No word-level timing, just add transcript
                return self._format_simple_transcript(response, video_title)
            
            for word_info in alternative.words:
                all_words.append(word_info)
                total_words += 1
                if hasattr(word_info, 'confidence'):
                    total_confidence += word_info.confidence
        
        if not all_words:
            return self._format_simple_transcript(response, video_title)
        
        # Segment with pause detection
        segments = self.segmenter.detect_pauses_and_segment(all_words)
        
        # Format transcript
        formatted_text = self._build_formatted_transcript(
            segments, video_title, breath_marking, total_words, total_confidence
        )
        
        return formatted_text
    
    def _format_simple_transcript(self, response: speech.RecognizeResponse, video_title: str) -> str:
        """Format simple transcript without word-level timing."""
        transcript_parts = []
        for result in response.results:
            if result.alternatives:
                transcript_parts.append(result.alternatives[0].transcript)
        
        result_text = f"📹 Videó: {video_title}\n"
        result_text += f"📅 Feldolgozva: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        result_text += "=" * 70 + "\n\n"
        result_text += "\n".join(transcript_parts)
        
        return result_text
    
    def _build_formatted_transcript(self, segments: List[Dict], video_title: str, 
                                  breath_marking: bool, total_words: int, 
                                  total_confidence: float) -> str:
        """Build formatted transcript with segments and statistics."""
        full_transcript = []
        current_paragraph = []
        last_timestamp = None
        
        # Statistics
        pause_stats = {'short_breath': 0, 'long_breath': 0, 'paragraph': 0}
        total_pauses = 0
        
        for segment in segments:
            # Format timestamp
            timestamp = str(datetime.timedelta(seconds=int(segment['start_time'])))
            
            # Add timestamp if needed
            if (last_timestamp is None or 
                segment['pause_type'] == 'paragraph' or
                self._should_add_timestamp(segment['start_time'], last_timestamp)):
                line_start = f"[{timestamp}] "
                last_timestamp = timestamp
            else:
                line_start = ""
            
            # Build text with pause marking
            text = line_start + segment['text']
            
            if breath_marking and segment['pause_type']:
                # Update statistics
                if segment['pause_type'] in pause_stats:
                    pause_stats[segment['pause_type']] += 1
                total_pauses += 1
                
                # Add pause marker
                pause_marker = self.breath_symbols.get(segment['pause_type'], '')
                
                # Handle paragraph breaks
                if segment['pause_type'] == 'paragraph':
                    if current_paragraph:
                        full_transcript.append(' '.join(current_paragraph))
                    full_transcript.append('')  # Empty line
                    current_paragraph = [text]
                else:
                    # Inline pause marking
                    if pause_marker.strip():
                        text += pause_marker
                    current_paragraph.append(text)
            else:
                current_paragraph.append(text)
        
        # Add final paragraph
        if current_paragraph:
            full_transcript.append(' '.join(current_paragraph))
        
        # Build final transcript with header and statistics
        return self._build_final_transcript(
            full_transcript, video_title, total_words, total_confidence,
            pause_stats, total_pauses, segments, breath_marking
        )
    
    def _should_add_timestamp(self, current_time: float, last_timestamp: str) -> bool:
        """Determine if a new timestamp should be added."""
        if not last_timestamp:
            return True
        
        # Parse last timestamp to get seconds
        try:
            time_parts = last_timestamp.split(':')
            last_seconds = int(time_parts[-1]) if time_parts else 0
            return current_time - last_seconds > 30  # Every 30 seconds
        except:
            return True
    
    def _build_final_transcript(self, transcript_lines: List[str], video_title: str,
                              total_words: int, total_confidence: float,
                              pause_stats: Dict, total_pauses: int, 
                              segments: List[Dict], breath_marking: bool) -> str:
        """Build final transcript with header and statistics."""
        result_text = f"📹 Videó: {video_title}\n"
        result_text += f"📅 Feldolgozva: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        result_text += "=" * 70 + "\n\n"
        result_text += "\n".join(transcript_lines)
        
        # Add statistics
        if total_words > 0:
            avg_confidence = (total_confidence / total_words) * 100
            result_text += f"\n\n{'='*70}\n"
            result_text += f"📊 Beszéd statisztika:\n"
            result_text += f"   • Összes szó: {total_words}\n"
            result_text += f"   • Átlagos pontosság: {avg_confidence:.1f}%\n"
            
            if breath_marking and total_pauses > 0:
                result_text += f"\n💨 Levegővétel statisztika:\n"
                result_text += f"   • Rövid szünetek (•): {pause_stats['short_breath']}\n"
                result_text += f"   • Hosszú szünetek (••): {pause_stats['long_breath']}\n"
                result_text += f"   • Bekezdések: {pause_stats['paragraph']}\n"
                result_text += f"   • Összes detektált szünet: {total_pauses}\n"
                
                # Speech dynamics
                if segments:
                    total_speaking_time = sum(s['end_time'] - s['start_time'] for s in segments)
                    total_pause_time = sum(s['pause_after'] for s in segments)
                    
                    if total_speaking_time > 0:
                        words_per_minute = (total_words / total_speaking_time) * 60
                        pause_percentage = (total_pause_time / (total_speaking_time + total_pause_time)) * 100
                        
                        result_text += f"\n📈 Beszéddinamika:\n"
                        result_text += f"   • Beszédtempó: {words_per_minute:.0f} szó/perc\n"
                        result_text += f"   • Szünetek aránya: {pause_percentage:.1f}%\n"
        
        return result_text