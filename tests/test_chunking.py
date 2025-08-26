"""Tests for chunking functionality."""

import unittest
from src.utils.chunking import TranscriptChunker
from src.config import settings


class TestTranscriptChunker(unittest.TestCase):
    """Test cases for TranscriptChunker."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.chunker = TranscriptChunker()
        
        # Short text that doesn't need chunking
        self.short_text = "Ez egy rövid szöveg, amely nem igényel chunking-ot."
        
        # Long text that needs chunking
        self.long_text = "Ez egy nagyon hosszú szöveg. " * 1000  # About 30k characters
        
        # Medium text at the boundary
        boundary_length = settings.max_transcript_length
        self.boundary_text = "x" * boundary_length
    
    def test_needs_chunking_short_text(self):
        """Test that short text doesn't need chunking."""
        self.assertFalse(self.chunker.needs_chunking(self.short_text))
    
    def test_needs_chunking_long_text(self):
        """Test that long text needs chunking."""
        self.assertTrue(self.chunker.needs_chunking(self.long_text))
    
    def test_needs_chunking_boundary_text(self):
        """Test boundary case at exact limit."""
        # At the limit - should not need chunking
        self.assertFalse(self.chunker.needs_chunking(self.boundary_text))
        
        # Just over the limit - should need chunking
        over_boundary = self.boundary_text + "x"
        self.assertTrue(self.chunker.needs_chunking(over_boundary))
    
    def test_chunk_text_short(self):
        """Test chunking of short text returns single chunk."""
        chunks = self.chunker.chunk_text(self.short_text)
        
        self.assertEqual(len(chunks), 1)
        chunk_text, start_pos, end_pos = chunks[0]
        self.assertEqual(chunk_text, self.short_text)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(self.short_text))
    
    def test_chunk_text_long(self):
        """Test chunking of long text creates multiple chunks."""
        chunks = self.chunker.chunk_text(self.long_text)
        
        # Should create multiple chunks
        self.assertGreater(len(chunks), 1)
        
        # Check that chunks are reasonable size
        for chunk_text, start_pos, end_pos in chunks:
            self.assertLessEqual(len(chunk_text), settings.chunk_size + 100)  # Allow some margin
            self.assertGreaterEqual(len(chunk_text.strip()), 10)  # Should have meaningful content
            self.assertGreaterEqual(end_pos, start_pos)
    
    def test_chunk_overlap(self):
        """Test that chunks have proper overlap."""
        chunks = self.chunker.chunk_text(self.long_text)
        
        if len(chunks) > 1:
            # Check overlap between consecutive chunks
            for i in range(len(chunks) - 1):
                _, start1, end1 = chunks[i]
                _, start2, end2 = chunks[i + 1]
                
                # Next chunk should start before current chunk ends (overlap)
                overlap_size = end1 - start2
                if overlap_size > 0:  # Allow for edge cases
                    self.assertLessEqual(overlap_size, settings.chunk_overlap + 100)
    
    def test_estimate_processing_cost(self):
        """Test cost estimation functionality."""
        # Test short text
        short_estimate = self.chunker.estimate_processing_cost(self.short_text)
        
        self.assertEqual(short_estimate['total_chunks'], 1)
        self.assertEqual(short_estimate['original_length'], len(self.short_text))
        self.assertGreater(short_estimate['estimated_cost_usd'], 0)
        self.assertGreater(short_estimate['estimated_time_seconds'], 0)
        
        # Test long text
        long_estimate = self.chunker.estimate_processing_cost(self.long_text)
        
        self.assertGreater(long_estimate['total_chunks'], 1)
        self.assertEqual(long_estimate['original_length'], len(self.long_text))
        
        # Long text should cost more than short text
        self.assertGreater(long_estimate['estimated_cost_usd'], short_estimate['estimated_cost_usd'])
        self.assertGreater(long_estimate['estimated_time_seconds'], short_estimate['estimated_time_seconds'])
    
    def test_merge_chunked_results(self):
        """Test merging of chunked results."""
        # Create test chunks
        chunks_info = [
            ("First chunk content", 0, 100),
            ("Second chunk content", 90, 200),
            ("Third chunk content", 180, 300)
        ]
        
        # Create mock processed results
        results = [
            "Processed first chunk",
            "Processed second chunk", 
            "Processed third chunk"
        ]
        
        merged = self.chunker.merge_chunked_results(results, chunks_info)
        
        # Should contain all processed content
        self.assertIn("Processed first chunk", merged)
        self.assertIn("Processed second chunk", merged)
        self.assertIn("Processed third chunk", merged)
        
        # Should have chunk separators
        self.assertIn("Chunk", merged)
    
    def test_get_chunk_summary(self):
        """Test chunk summary generation."""
        # Short text summary
        short_summary = self.chunker.get_chunk_summary(self.short_text)
        self.assertIn("Egyblokkos", short_summary)
        
        # Long text summary
        long_summary = self.chunker.get_chunk_summary(self.long_text)
        self.assertIn("Chunked", long_summary)
        self.assertIn("chunk", long_summary)
        self.assertIn("mp", long_summary)  # Should show time estimate
        self.assertIn("$", long_summary)   # Should show cost estimate


if __name__ == '__main__':
    unittest.main()