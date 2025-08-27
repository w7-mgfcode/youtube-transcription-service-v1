#!/usr/bin/env python3
"""Quick test script for TTS provider integration."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.tts_factory import TTSFactory
from src.core.tts_interface import TTSProvider
from src.utils.colors import Colors


def test_provider_availability():
    """Test which TTS providers are available."""
    print(Colors.HEADER + "🔍 Testing TTS Provider Availability" + Colors.ENDC)
    print("=" * 50)
    
    available_providers = TTSFactory.get_available_providers()
    provider_info = TTSFactory.get_provider_info()
    
    for provider_name, info in provider_info.items():
        status = "✅ AVAILABLE" if info["available"] else "❌ NOT AVAILABLE"
        cost = f"${info['cost_per_1k_chars']:.4f}/1K chars" if info["available"] else "N/A"
        voices = f"{info['voice_count']} voices" if info["available"] else "N/A"
        
        print(f"{status} | {info['name']}")
        print(f"         Cost: {cost}")
        print(f"         Voices: {voices}")
        if "error" in info:
            print(f"         Error: {info['error']}")
        print()


def test_voice_discovery():
    """Test voice discovery for available providers."""
    print(Colors.HEADER + "🎤 Testing Voice Discovery" + Colors.ENDC)
    print("=" * 50)
    
    available_providers = TTSFactory.get_available_providers()
    
    for provider in available_providers:
        try:
            synthesizer = TTSFactory.create_synthesizer(provider)
            voices = synthesizer.get_available_voices()
            
            print(f"📋 {provider.value.upper()} Voices:")
            
            # Group voices by language
            by_language = {}
            for voice in voices[:10]:  # Show first 10 voices
                lang = voice.language
                if lang not in by_language:
                    by_language[lang] = []
                by_language[lang].append(voice)
            
            for language, lang_voices in by_language.items():
                print(f"   {language}:")
                for voice in lang_voices[:3]:  # Show 3 voices per language
                    gender_icon = "👨" if voice.gender == "male" else "👩" if voice.gender == "female" else "🎭"
                    premium_mark = "⭐" if voice.is_premium else ""
                    print(f"     {gender_icon} {voice.name} ({voice.voice_id}) {premium_mark}")
            print()
            
        except Exception as e:
            print(f"❌ {provider.value}: {e}")
            print()


def test_voice_mapping():
    """Test voice mapping between providers."""
    print(Colors.HEADER + "🔄 Testing Voice Mapping" + Colors.ENDC)
    print("=" * 50)
    
    # Test popular ElevenLabs voices -> Google TTS mapping
    test_voices = [
        ("21m00Tcm4TlvDq8ikWAM", "Rachel"),
        ("pNInz6obpgDQGcFmaJgB", "Adam"),
        ("yoZ06aMxZJJ28mfd3POQ", "Sam")
    ]
    
    for elevenlabs_id, name in test_voices:
        google_equivalent = TTSFactory.get_voice_mapping(
            TTSProvider.ELEVENLABS, 
            TTSProvider.GOOGLE_TTS, 
            elevenlabs_id
        )
        
        reverse_mapping = TTSFactory.get_voice_mapping(
            TTSProvider.GOOGLE_TTS,
            TTSProvider.ELEVENLABS,
            google_equivalent
        ) if google_equivalent else None
        
        print(f"🔄 {name}")
        print(f"   ElevenLabs: {elevenlabs_id}")
        print(f"   Google TTS: {google_equivalent or 'No mapping'}")
        print(f"   Reverse:    {reverse_mapping or 'No reverse mapping'}")
        print()


def test_cost_comparison():
    """Test cost estimation comparison between providers."""
    print(Colors.HEADER + "💰 Testing Cost Comparison" + Colors.ENDC)
    print("=" * 50)
    
    test_lengths = [1000, 5000, 10000, 50000]  # Character counts
    available_providers = TTSFactory.get_available_providers()
    
    print("Characters | ElevenLabs  | Google TTS  | Savings")
    print("-" * 50)
    
    for char_count in test_lengths:
        costs = {}
        
        for provider in available_providers:
            try:
                synthesizer = TTSFactory.create_synthesizer(provider)
                cost = synthesizer.estimate_cost(char_count, "high")
                costs[provider.value] = cost
            except Exception:
                costs[provider.value] = 0.0
        
        elevenlabs_cost = costs.get("elevenlabs", 0.0)
        google_cost = costs.get("google_tts", 0.0)
        
        if elevenlabs_cost > 0 and google_cost > 0:
            savings = ((elevenlabs_cost - google_cost) / elevenlabs_cost) * 100
            savings_text = f"{savings:.1f}%"
        else:
            savings_text = "N/A"
        
        print(f"{char_count:>10} | ${elevenlabs_cost:>9.4f} | ${google_cost:>9.4f} | {savings_text:>7}")


def test_auto_selection():
    """Test automatic provider selection."""
    print(Colors.HEADER + "🤖 Testing Auto-Selection" + Colors.ENDC)
    print("=" * 50)
    
    try:
        # Test auto-selection
        auto_synthesizer = TTSFactory.create_synthesizer(TTSProvider.AUTO)
        print(f"✅ Auto-selected provider: {auto_synthesizer.provider_name.value}")
        
        # Test explicit provider selection
        available_providers = TTSFactory.get_available_providers()
        for provider in available_providers:
            synthesizer = TTSFactory.create_synthesizer(provider)
            print(f"✅ {provider.value} synthesizer created successfully")
        
    except Exception as e:
        print(f"❌ Auto-selection failed: {e}")


def main():
    """Run all tests."""
    print(Colors.HEADER + "🎤 TTS Provider Integration Test Suite" + Colors.ENDC)
    print(Colors.HEADER + "=" * 60 + Colors.ENDC)
    print()
    
    try:
        test_provider_availability()
        test_voice_discovery()
        test_voice_mapping()
        test_cost_comparison()
        test_auto_selection()
        
        print(Colors.GREEN + "🎉 All tests completed!" + Colors.ENDC)
        
    except KeyboardInterrupt:
        print(Colors.WARNING + "\n⚠ Tests interrupted by user" + Colors.ENDC)
    except Exception as e:
        print(Colors.FAIL + f"\n❌ Test suite error: {e}" + Colors.ENDC)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())