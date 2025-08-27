#!/usr/bin/env python3
"""
🎤 TTS Provider Comparison Demo

This script demonstrates side-by-side synthesis comparison between 
Google Cloud TTS and ElevenLabs providers, showcasing cost savings 
and quality differences.

Usage:
    python examples/provider_comparison.py --text "Sample text" --language en-US
"""

import asyncio
import time
import argparse
from typing import Dict, Any, List
from dataclasses import dataclass
import json

# Simulated API calls for demo purposes
@dataclass
class SynthesisResult:
    provider: str
    voice_id: str
    voice_name: str
    cost: float
    processing_time: float
    quality: str
    file_size_kb: int
    
class TTSProviderComparison:
    """Compare TTS providers side-by-side"""
    
    def __init__(self):
        self.google_tts_voices = {
            "en-US": {
                "en-US-Neural2-F": {"name": "Neural2 Female", "type": "neural2"},
                "en-US-Neural2-D": {"name": "Neural2 Male", "type": "neural2"},
                "en-US-Wavenet-F": {"name": "WaveNet Female", "type": "wavenet"}
            },
            "hu-HU": {
                "hu-HU-Neural2-A": {"name": "Neural2 Female", "type": "neural2"},
                "hu-HU-Neural2-B": {"name": "Neural2 Male", "type": "neural2"},
                "hu-HU-Wavenet-A": {"name": "WaveNet Female", "type": "wavenet"}
            }
        }
        
        self.elevenlabs_voices = {
            "21m00Tcm4TlvDq8ikWAM": {"name": "Rachel", "accent": "American"},
            "pNInz6obpgDQGcFmaJgB": {"name": "Adam", "accent": "American"},
            "EXAVITQu4vr4xnSDxMaL": {"name": "Bella", "accent": "American"}
        }
        
    async def synthesize_google_tts(self, text: str, voice_id: str) -> SynthesisResult:
        """Simulate Google TTS synthesis"""
        # Simulate processing time
        await asyncio.sleep(1.5)
        
        char_count = len(text)
        cost = char_count * (0.016 / 1000)  # Neural2 pricing
        
        voice_info = self.google_tts_voices.get("en-US", {}).get(voice_id, {})
        
        return SynthesisResult(
            provider="google_tts",
            voice_id=voice_id,
            voice_name=voice_info.get("name", "Unknown"),
            cost=cost,
            processing_time=1.5,
            quality="neural2",
            file_size_kb=int(char_count * 0.8)  # Estimated
        )
    
    async def synthesize_elevenlabs(self, text: str, voice_id: str) -> SynthesisResult:
        """Simulate ElevenLabs synthesis"""
        # Simulate processing time
        await asyncio.sleep(2.5)
        
        char_count = len(text)
        cost = char_count * (0.30 / 1000)  # Standard pricing
        
        voice_info = self.elevenlabs_voices.get(voice_id, {})
        
        return SynthesisResult(
            provider="elevenlabs",
            voice_id=voice_id,
            voice_name=voice_info.get("name", "Unknown"),
            cost=cost,
            processing_time=2.5,
            quality="high",
            file_size_kb=int(char_count * 1.2)  # Estimated
        )
    
    async def compare_providers(self, text: str, language: str = "en-US") -> Dict[str, Any]:
        """Run side-by-side comparison"""
        
        print(f"\n🎤 TTS Provider Comparison")
        print(f"{'='*50}")
        print(f"Text: {text}")
        print(f"Language: {language}")
        print(f"Characters: {len(text)}")
        print(f"{'='*50}\n")
        
        # Select appropriate voices
        if language == "en-US":
            google_voice = "en-US-Neural2-F"  # Rachel equivalent
            elevenlabs_voice = "21m00Tcm4TlvDq8ikWAM"  # Rachel
        elif language == "hu-HU":
            google_voice = "hu-HU-Neural2-A"
            elevenlabs_voice = "21m00Tcm4TlvDq8ikWAM"  # Fallback to English
        else:
            google_voice = "en-US-Neural2-F"
            elevenlabs_voice = "21m00Tcm4TlvDq8ikWAM"
        
        # Run synthesis in parallel
        print("🔄 Running synthesis with both providers...")
        start_time = time.time()
        
        google_task = self.synthesize_google_tts(text, google_voice)
        elevenlabs_task = self.synthesize_elevenlabs(text, elevenlabs_voice)
        
        google_result, elevenlabs_result = await asyncio.gather(google_task, elevenlabs_task)
        
        total_time = time.time() - start_time
        
        # Display results
        self._display_comparison(google_result, elevenlabs_result, total_time)
        
        return {
            "google_tts": google_result.__dict__,
            "elevenlabs": elevenlabs_result.__dict__,
            "comparison": self._calculate_comparison_metrics(google_result, elevenlabs_result)
        }
    
    def _display_comparison(self, google: SynthesisResult, elevenlabs: SynthesisResult, total_time: float):
        """Display formatted comparison results"""
        
        print(f"\n📊 SYNTHESIS RESULTS")
        print(f"{'='*80}")
        
        # Header
        print(f"{'Metric':<25} {'Google TTS':<20} {'ElevenLabs':<20} {'Winner':<15}")
        print(f"{'-'*80}")
        
        # Cost comparison
        cost_winner = "Google TTS" if google.cost < elevenlabs.cost else "ElevenLabs"
        cost_savings = ((elevenlabs.cost - google.cost) / elevenlabs.cost * 100) if elevenlabs.cost > 0 else 0
        
        print(f"{'Cost':<25} ${google.cost:.4f:<19} ${elevenlabs.cost:.4f:<19} {cost_winner:<15}")
        print(f"{'Savings':<25} {cost_savings:.1f}% cheaper{'':<8} -{'':19} {'Google TTS':<15}")
        
        # Speed comparison  
        speed_winner = "Google TTS" if google.processing_time < elevenlabs.processing_time else "ElevenLabs"
        print(f"{'Processing Time':<25} {google.processing_time:.1f}s{'':<15} {elevenlabs.processing_time:.1f}s{'':<15} {speed_winner:<15}")
        
        # Quality
        print(f"{'Quality':<25} {google.quality:<20} {elevenlabs.quality:<20} {'Comparable':<15}")
        
        # Voice details
        print(f"{'Voice':<25} {google.voice_name:<20} {elevenlabs.voice_name:<20} {'Personal Pref':<15}")
        
        print(f"{'-'*80}")
        print(f"{'Total Time':<25} {total_time:.1f} seconds (parallel processing)")
        
        # Summary
        print(f"\n💡 SUMMARY")
        print(f"{'='*40}")
        print(f"🏆 Most Cost-Effective: Google TTS (saves {cost_savings:.1f}%)")
        print(f"⚡ Fastest Processing: {speed_winner}")
        print(f"🎯 Best Value: Google TTS (94% cheaper, comparable quality)")
        
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS")
        print(f"{'='*40}")
        print(f"💰 For Cost-Conscious Projects: Google TTS")
        print(f"🎭 For Premium Branding: ElevenLabs")
        print(f"⚖️  For Balanced Approach: Start with Google TTS, upgrade if needed")
    
    def _calculate_comparison_metrics(self, google: SynthesisResult, elevenlabs: SynthesisResult) -> Dict[str, Any]:
        """Calculate detailed comparison metrics"""
        
        cost_savings_pct = ((elevenlabs.cost - google.cost) / elevenlabs.cost * 100) if elevenlabs.cost > 0 else 0
        cost_savings_amount = elevenlabs.cost - google.cost
        
        time_diff = elevenlabs.processing_time - google.processing_time
        time_savings_pct = (time_diff / elevenlabs.processing_time * 100) if elevenlabs.processing_time > 0 else 0
        
        return {
            "cost_savings_percentage": round(cost_savings_pct, 1),
            "cost_savings_amount": round(cost_savings_amount, 4),
            "time_difference_seconds": round(time_diff, 1),
            "time_savings_percentage": round(time_savings_pct, 1),
            "recommended_provider": "google_tts" if cost_savings_pct > 50 else "elevenlabs",
            "quality_difference": "comparable",
            "annual_savings_1000_chars_per_day": round(cost_savings_amount * 365, 2)
        }

async def main():
    """Main demo function"""
    parser = argparse.ArgumentParser(description="Compare TTS providers")
    parser.add_argument("--text", default="Hello! This is a demonstration of text-to-speech synthesis using different providers. We're comparing cost, quality, and processing speed.", help="Text to synthesize")
    parser.add_argument("--language", default="en-US", choices=["en-US", "hu-HU"], help="Target language")
    parser.add_argument("--output", help="Save results to JSON file")
    
    args = parser.parse_args()
    
    comparison = TTSProviderComparison()
    
    # Run comparison
    results = await comparison.compare_providers(args.text, args.language)
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {args.output}")
    
    # Interactive demo
    print(f"\n🎮 INTERACTIVE DEMO")
    print(f"{'='*40}")
    print(f"Try different texts to see how costs scale:")
    
    sample_texts = [
        "Short text",
        "This is a medium length text with approximately fifty characters in it.",
        "This is a much longer text that demonstrates how costs scale with character count. It includes multiple sentences, various punctuation marks, and represents the kind of content you might find in educational videos, podcasts, or documentary narration. The purpose is to show realistic cost differences between providers when processing substantial amounts of text content."
    ]
    
    for i, sample_text in enumerate(sample_texts, 1):
        print(f"\n{i}. Sample Text ({len(sample_text)} chars)")
        google_cost = len(sample_text) * (0.016 / 1000)
        elevenlabs_cost = len(sample_text) * (0.30 / 1000)
        savings = elevenlabs_cost - google_cost
        savings_pct = (savings / elevenlabs_cost * 100) if elevenlabs_cost > 0 else 0
        
        print(f"   Google TTS: ${google_cost:.4f}")
        print(f"   ElevenLabs: ${elevenlabs_cost:.4f}")
        print(f"   You save: ${savings:.4f} ({savings_pct:.1f}%)")

if __name__ == "__main__":
    print("""
🎤 TTS Provider Comparison Demo
================================

This demo compares Google Cloud TTS and ElevenLabs providers across:
- 💰 Cost per character
- ⚡ Processing speed  
- 🎯 Voice quality
- 📊 Overall value proposition

Real-world scenarios show 90%+ cost savings with Google TTS!
    """)
    
    asyncio.run(main())