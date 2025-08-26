"""Text chunking utilities for handling long transcripts."""

import re
from typing import List, Tuple, Optional
from ..config import settings


class TranscriptChunker:
    """Handles intelligent chunking of long transcripts for processing."""
    
    def __init__(self, chunk_size: int = None, overlap: int = None):
        self.chunk_size = chunk_size or settings.chunk_size
        self.overlap = overlap or settings.chunk_overlap
        
        # Hungarian sentence ending patterns
        self.sentence_endings = re.compile(r'[.!?]+\s+')
        self.paragraph_breaks = re.compile(r'\n\s*\n')
    
    def needs_chunking(self, text: str) -> bool:
        """Check if text needs chunking based on length."""
        return (settings.chunking_enabled and 
                len(text) > settings.max_transcript_length)
    
    def chunk_text(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Split text into overlapping chunks with sentence boundary detection.
        
        Returns:
            List of tuples: (chunk_text, start_pos, end_pos)
        """
        if not self.needs_chunking(text):
            return [(text, 0, len(text))]
        
        chunks = []
        text_length = len(text)
        
        # Calculate maximum chunks to process
        max_chunks = min(settings.max_chunks, 
                        (text_length // (self.chunk_size - self.overlap)) + 1)
        
        start_pos = 0
        chunk_count = 0
        
        while start_pos < text_length and chunk_count < max_chunks:
            # Calculate end position
            end_pos = min(start_pos + self.chunk_size, text_length)
            
            # If this isn't the last possible chunk, find good break point
            if end_pos < text_length:
                # Look for sentence boundary within last 300 characters
                search_start = max(end_pos - 300, start_pos + 100)
                chunk_text = text[search_start:end_pos]
                
                # Find last sentence ending
                matches = list(self.sentence_endings.finditer(chunk_text))
                if matches:
                    last_match = matches[-1]
                    # Adjust end_pos to sentence boundary
                    end_pos = search_start + last_match.end()
                else:
                    # Fallback: look for paragraph break
                    paragraph_matches = list(self.paragraph_breaks.finditer(chunk_text))
                    if paragraph_matches:
                        last_para = paragraph_matches[-1]
                        end_pos = search_start + last_para.start()
            
            # Extract chunk
            chunk_text = text[start_pos:end_pos].strip()
            if chunk_text:
                chunks.append((chunk_text, start_pos, end_pos))
            
            # Move to next chunk with overlap
            start_pos = max(end_pos - self.overlap, start_pos + 1)
            chunk_count += 1
        
        return chunks
    
    def estimate_processing_cost(self, text: str) -> dict:
        """Estimate processing cost and time for chunked text."""
        chunks = self.chunk_text(text)
        
        # Rough estimates based on Vertex AI pricing and processing time
        cost_per_1k_chars = 0.0001  # Very rough estimate in USD
        seconds_per_1k_chars = 0.5  # Processing time estimate
        
        total_chars = sum(len(chunk[0]) for chunk in chunks)
        
        return {
            'total_chunks': len(chunks),
            'total_characters': total_chars,
            'original_length': len(text),
            'estimated_cost_usd': (total_chars / 1000) * cost_per_1k_chars,
            'estimated_time_seconds': (total_chars / 1000) * seconds_per_1k_chars,
            'chunks_info': [(i+1, len(chunk[0]), chunk[1], chunk[2]) 
                           for i, chunk in enumerate(chunks)]
        }
    
    def merge_chunked_results(self, results: List[str], 
                            chunk_info: List[Tuple[str, int, int]]) -> str:
        """Merge processed chunks back into single formatted text."""
        if not results:
            return ""
        
        if len(results) == 1:
            return results[0]
        
        merged_lines = []
        
        # Process each chunk result
        for i, (result, chunk_info_tuple) in enumerate(zip(results, chunk_info)):
            chunk_text, start_pos, end_pos = chunk_info_tuple
            
            if not result.strip():
                continue
            
            # Split into lines and clean
            lines = [line.strip() for line in result.split('\n') if line.strip()]
            
            # Filter out header/footer lines from individual chunks
            cleaned_lines = []
            for line in lines:
                # Skip processing metadata lines
                if (line.startswith('📹') or line.startswith('📅') or 
                    line.startswith('🤖') or line.startswith('=') or
                    line.startswith('📊') or '[FIGYELEM:' in line):
                    continue
                cleaned_lines.append(line)
            
            # Add chunk separator for debugging (except first chunk)
            if i > 0 and cleaned_lines:
                merged_lines.append(f"[--- Chunk {i+1} folytatás ---]")
            
            merged_lines.extend(cleaned_lines)
        
        return '\n'.join(merged_lines)
    
    def get_chunk_summary(self, text: str) -> str:
        """Get a summary of how the text would be chunked."""
        chunks = self.chunk_text(text)
        cost_info = self.estimate_processing_cost(text)
        
        if len(chunks) <= 1:
            return f"Egyblokkos feldolgozás ({len(text)} karakter)"
        
        summary = f"Chunked feldolgozás:\n"
        summary += f"  • {len(chunks)} chunk ({cost_info['total_characters']} összkarakter)\n"
        summary += f"  • Becsült idő: {cost_info['estimated_time_seconds']:.1f} mp\n"
        summary += f"  • Becsült költség: ${cost_info['estimated_cost_usd']:.4f}\n"
        
        return summary