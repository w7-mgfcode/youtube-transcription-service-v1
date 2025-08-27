#!/usr/bin/env python3
"""
🖥️ CLI Workflow Demo - Interactive Dubbing with Provider Selection

This script simulates the enhanced Hungarian CLI interface with 
multi-provider TTS support, demonstrating the complete dubbing
workflow from video input to final output.

Usage:
    python examples/cli_workflow_demo.py --interactive
"""

import argparse
import asyncio
import time
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import random

@dataclass
class VideoInfo:
    url: str
    title: str
    duration: str
    transcript_chars: int
    language: str

@dataclass
class TTSProvider:
    id: str
    name: str
    cost_per_1k_chars: float
    voice_count: int
    languages: int
    recommended: bool

@dataclass
class VoiceOption:
    id: str
    name: str
    gender: str
    description: str
    provider: str
    cost_per_1k_chars: float

class HungarianCLIDemo:
    """Simulate the Hungarian CLI interface with TTS provider selection"""
    
    def __init__(self):
        self.providers = self._initialize_providers()
        self.voices = self._initialize_voices()
        self.selected_provider = None
        self.selected_voice = None
        
    def _initialize_providers(self) -> Dict[str, TTSProvider]:
        """Initialize TTS providers"""
        return {
            "elevenlabs": TTSProvider(
                id="elevenlabs",
                name="ElevenLabs - Prémium neurális hangok (drága)",
                cost_per_1k_chars=0.30,
                voice_count=25,
                languages=29,
                recommended=False
            ),
            "google_tts": TTSProvider(
                id="google_tts", 
                name="Google Cloud TTS - Kiváló minőség (90% olcsóbb)",
                cost_per_1k_chars=0.016,
                voice_count=1616,
                languages=40,
                recommended=True
            ),
            "auto": TTSProvider(
                id="auto",
                name="Automatikus kiválasztás költség alapján",
                cost_per_1k_chars=0.016,  # Will use Google TTS
                voice_count=1641,  # Combined
                languages=40,
                recommended=True
            )
        }
    
    def _initialize_voices(self) -> Dict[str, List[VoiceOption]]:
        """Initialize voice options by provider"""
        return {
            "google_tts": [
                VoiceOption("hu-HU-Neural2-A", "Magyar Neural2 Női A", "női", 
                           "Tiszta, természetes, professzionális", "google_tts", 0.016),
                VoiceOption("hu-HU-Neural2-B", "Magyar Neural2 Férfi B", "férfi",
                           "Tekintélyteljes, világos, megbízható", "google_tts", 0.016),
                VoiceOption("hu-HU-Wavenet-A", "Magyar WaveNet Női A", "női",
                           "Meleg, beszélgetős, barátságos", "google_tts", 0.016),
                VoiceOption("en-US-Neural2-F", "Angol Neural2 Női F", "női",
                           "Professzionális, világos, oktatási", "google_tts", 0.016),
                VoiceOption("en-US-Neural2-D", "Angol Neural2 Férfi D", "férfi", 
                           "Beszélgetős, meleg, vonzó", "google_tts", 0.016)
            ],
            "elevenlabs": [
                VoiceOption("21m00Tcm4TlvDq8ikWAM", "Rachel", "női",
                           "Nyugodt, világos, professzionális", "elevenlabs", 0.30),
                VoiceOption("pNInz6obpgDQGcFmaJgB", "Adam", "férfi",
                           "Mély, tekintélyteljes, magabiztos", "elevenlabs", 0.30),
                VoiceOption("yoZ06aMxZJJ28mfd3POQ", "Sam", "férfi",
                           "Barátságos, beszélgetős, energikus", "elevenlabs", 0.30),
                VoiceOption("EXAVITQu4vr4xnSDxMaL", "Bella", "női",
                           "Barátságos, megközelíthető, sokoldalú", "elevenlabs", 0.30)
            ]
        }
    
    def print_header(self):
        """Print CLI header"""
        print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                   🎤 YouTube Videó Dubbing Szolgáltatás                      ║
║                        Enhanced Multi-Provider TTS                           ║
╚═══════════════════════════════════════════════════════════════════════════════╝

🇭🇺 Magyar nyelvű interaktív felület
🌍 Többnyelvű szinkronizálás támogatás  
💰 Költségoptimalizált TTS szolgáltatók
🎭 1600+ hang közül választhat
        """)
    
    def get_video_info(self, url: str) -> VideoInfo:
        """Simulate getting video information"""
        # Simulate video analysis
        sample_videos = [
            VideoInfo(url, "Magyar Történelem Dokumentumfilm", "25:30", 18750, "hu-HU"),
            VideoInfo(url, "Technológiai Startup Bemutató", "12:15", 9000, "hu-HU"),
            VideoInfo(url, "Főzési Útmutató", "18:45", 13500, "hu-HU"),
            VideoInfo(url, "Tudományos Magyarázat", "8:30", 6250, "hu-HU"),
            VideoInfo(url, "Termék Értékelés", "15:20", 11250, "hu-HU")
        ]
        
        # Return random sample video
        video = random.choice(sample_videos)
        video.url = url  # Use the provided URL
        return video
    
    def display_video_info(self, video: VideoInfo):
        """Display video information"""
        print(f"\n📹 VIDEÓ INFORMÁCIÓK")
        print(f"{'='*50}")
        print(f"URL: {video.url}")
        print(f"Cím: {video.title}")
        print(f"Időtartam: {video.duration}")
        print(f"Becsült karakterszám: {video.transcript_chars:,}")
        print(f"Eredeti nyelv: {video.language}")
    
    def select_tts_provider(self) -> str:
        """Interactive TTS provider selection"""
        print(f"\n🎤 TTS SZOLGÁLTATÓ KIVÁLASZTÁSA")
        print(f"{'='*50}")
        
        # Display provider options
        providers_list = list(self.providers.values())
        for i, provider in enumerate(providers_list, 1):
            star = "⭐" if provider.recommended else "  "
            print(f"{star} {i}. {provider.name}")
            print(f"      Költség: ${provider.cost_per_1k_chars:.3f}/1000 karakter")
            print(f"      Hangok: {provider.voice_count}")
            print(f"      Nyelvek: {provider.languages}")
            print()
        
        # Cost comparison
        print(f"💰 KÖLTSÉG ÖSSZEHASONLÍTÁS (1000 karakter alapján)")
        print(f"{'-'*60}")
        print(f"{'Szolgáltató':<25} {'Költség':<12} {'Éves megtakarítás':<20}")
        print(f"{'-'*60}")
        
        elevenlabs_cost = self.providers["elevenlabs"].cost_per_1k_chars
        for provider in providers_list:
            cost = provider.cost_per_1k_chars
            if provider.id != "elevenlabs":
                annual_savings = (elevenlabs_cost - cost) * 365  # Daily 1K chars
                savings_text = f"${annual_savings:.0f} (94%)"
            else:
                savings_text = "-"
            
            print(f"{provider.name.split(' - ')[0]:<25} "
                  f"${cost:.3f}{'':<7} "
                  f"{savings_text}")
        
        print(f"\n💡 AJÁNLÁS: A Google Cloud TTS 94%-kal olcsóbb!")
        
        # Interactive selection
        while True:
            try:
                choice = input(f"\nVálasztás [1-3, alapértelmezett: 3]: ").strip()
                if not choice:
                    choice = "3"  # Default to auto
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(providers_list):
                    selected_provider = providers_list[choice_idx]
                    self.selected_provider = selected_provider.id
                    print(f"✅ Kiválasztva: {selected_provider.name}")
                    return selected_provider.id
                else:
                    print("❌ Érvénytelen választás. Kérem válasszon 1-3 között.")
            except ValueError:
                print("❌ Kérem számot adjon meg.")
            except KeyboardInterrupt:
                print("\n👋 Kilépés...")
                exit(0)
    
    def select_voice(self, provider_id: str, target_language: str) -> str:
        """Interactive voice selection"""
        print(f"\n🎭 HANG KIVÁLASZTÁSA - {self.providers[provider_id].name.split(' - ')[0]}")
        print(f"{'='*60}")
        
        if provider_id == "auto":
            # Auto mode - show recommended voice
            print("🤖 Automatikus hang kiválasztás...")
            time.sleep(1)
            
            if target_language == "hu-HU":
                recommended_voice = "hu-HU-Neural2-A"
                voice_name = "Magyar Neural2 Női A"
                provider_used = "Google TTS"
            else:
                recommended_voice = "en-US-Neural2-F" 
                voice_name = "Angol Neural2 Női F"
                provider_used = "Google TTS"
            
            print(f"✅ Automatikusan kiválasztva:")
            print(f"   Hang: {voice_name}")
            print(f"   Szolgáltató: {provider_used}")
            print(f"   Indoklás: Költség-optimalizált, kiváló minőség")
            
            self.selected_voice = recommended_voice
            return recommended_voice
        
        # Manual voice selection
        available_voices = self.voices.get(provider_id, [])
        
        # Filter by target language if needed
        if target_language.startswith("hu"):
            available_voices = [v for v in available_voices if v.id.startswith("hu")]
        elif target_language.startswith("en"):
            available_voices = [v for v in available_voices if v.id.startswith("en")]
        
        if not available_voices:
            print("❌ Nincsenek elérhető hangok ehhez a nyelvhez.")
            return ""
        
        print(f"Elérhető hangok ({len(available_voices)} db):")
        for i, voice in enumerate(available_voices, 1):
            print(f"{i}. {voice.name} ({voice.gender})")
            print(f"   ID: {voice.id}")
            print(f"   Leírás: {voice.description}")
            print(f"   Költség: ${voice.cost_per_1k_chars:.3f}/1000 karakter")
            print()
        
        # Interactive selection
        while True:
            try:
                choice = input(f"Választás [1-{len(available_voices)}, Enter = 1]: ").strip()
                if not choice:
                    choice = "1"  # Default to first
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(available_voices):
                    selected_voice = available_voices[choice_idx]
                    print(f"✅ Kiválasztva: {selected_voice.name}")
                    self.selected_voice = selected_voice.id
                    return selected_voice.id
                else:
                    print(f"❌ Érvénytelen választás. Kérem válasszon 1-{len(available_voices)} között.")
            except ValueError:
                print("❌ Kérem számot adjon meg.")
            except KeyboardInterrupt:
                print("\n👋 Kilépés...")
                exit(0)
    
    def select_target_language(self) -> str:
        """Interactive target language selection"""
        print(f"\n🌍 CÉLNYELV KIVÁLASZTÁSA")
        print(f"{'='*40}")
        
        languages = [
            ("en-US", "Angol (Amerikai)", "🇺🇸"),
            ("en-GB", "Angol (Brit)", "🇬🇧"), 
            ("de-DE", "Német", "🇩🇪"),
            ("fr-FR", "Francia", "🇫🇷"),
            ("es-ES", "Spanyol", "🇪🇸"),
            ("it-IT", "Olasz", "🇮🇹")
        ]
        
        for i, (code, name, flag) in enumerate(languages, 1):
            print(f"{i}. {flag} {name} ({code})")
        
        while True:
            try:
                choice = input(f"\nVálasztás [1-{len(languages)}, Enter = 1]: ").strip()
                if not choice:
                    choice = "1"  # Default to English
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(languages):
                    selected_lang = languages[choice_idx]
                    print(f"✅ Kiválasztva: {selected_lang[2]} {selected_lang[1]}")
                    return selected_lang[0]
                else:
                    print(f"❌ Érvénytelen választás. Kérem válasszon 1-{len(languages)} között.")
            except ValueError:
                print("❌ Kérem számot adjon meg.")
            except KeyboardInterrupt:
                print("\n👋 Kilépés...")
                exit(0)
    
    def calculate_costs(self, video: VideoInfo, provider_id: str, target_language: str) -> Dict[str, float]:
        """Calculate processing costs"""
        provider = self.providers[provider_id]
        
        # Translation cost (fixed for all providers)
        translation_cost = video.transcript_chars * (20.0 / 1_000_000)
        
        # TTS cost based on provider
        if provider_id == "auto":
            # Auto mode uses Google TTS
            tts_cost = video.transcript_chars * (0.016 / 1000)
        else:
            tts_cost = video.transcript_chars * (provider.cost_per_1k_chars / 1000)
        
        # Video muxing cost (minimal)
        video_cost = 0.01
        
        total_cost = translation_cost + tts_cost + video_cost
        
        return {
            "translation": translation_cost,
            "tts": tts_cost,
            "video": video_cost,
            "total": total_cost
        }
    
    def display_cost_estimate(self, video: VideoInfo, provider_id: str, target_language: str):
        """Display cost estimation"""
        costs = self.calculate_costs(video, provider_id, target_language)
        
        print(f"\n💰 KÖLTSÉGBECSLÉS")
        print(f"{'='*40}")
        print(f"Fordítás ({video.transcript_chars:,} kar.): ${costs['translation']:.4f}")
        print(f"Hangszintézis ({self.providers[provider_id].name.split(' - ')[0]}): ${costs['tts']:.4f}")
        print(f"Videó feldolgozás: ${costs['video']:.4f}")
        print(f"{'-'*40}")
        print(f"ÖSSZESEN: ${costs['total']:.4f}")
        
        # Show savings comparison
        if provider_id != "elevenlabs":
            elevenlabs_costs = self.calculate_costs(video, "elevenlabs", target_language)
            savings = elevenlabs_costs['total'] - costs['total']
            savings_pct = (savings / elevenlabs_costs['total']) * 100
            print(f"\n💡 MEGTAKARÍTÁS az ElevenLabshoz képest:")
            print(f"Összeg: ${savings:.4f}")
            print(f"Százalék: {savings_pct:.1f}%")
        
        print(f"\n⏱️ Becsült feldolgozási idő: {video.duration} videó → ~{int(video.transcript_chars/1000*0.5)} perc")
    
    async def simulate_processing(self, video: VideoInfo, provider_id: str, voice_id: str, target_language: str):
        """Simulate the dubbing process"""
        print(f"\n🚀 FELDOLGOZÁS INDÍTÁSA")
        print(f"{'='*50}")
        
        # Processing stages
        stages = [
            ("🎬 Videó letöltése és elemzése", 3),
            ("📝 Magyar transcript készítése", 5),
            ("🌍 Fordítás készítése", 4),
            ("🎤 Hangszintézis", 8),
            ("🎥 Videó és hang egyesítése", 3),
            ("💾 Fájlok mentése", 1)
        ]
        
        print(f"Feldolgozási beállítások:")
        print(f"  📹 Videó: {video.title}")
        print(f"  🎤 Szolgáltató: {self.providers[provider_id].name.split(' - ')[0]}")
        print(f"  🗣️  Hang: {voice_id}")
        print(f"  🌍 Célnyelv: {target_language}")
        print()
        
        total_progress = 0
        total_stages = sum(stage[1] for stage in stages)
        
        for stage_name, stage_duration in stages:
            print(f"⏳ {stage_name}...")
            
            # Simulate processing with progress bar
            for i in range(stage_duration):
                await asyncio.sleep(0.5)
                total_progress += 1
                progress_pct = (total_progress / total_stages) * 100
                
                # Simple progress bar
                filled = int(progress_pct / 5)
                bar = "█" * filled + "░" * (20 - filled)
                print(f"\r   [{bar}] {progress_pct:.1f}%", end="", flush=True)
            
            print(f" ✅")
        
        print(f"\n🎉 FELDOLGOZÁS BEFEJEZVE!")
    
    def display_results(self, video: VideoInfo, provider_id: str, target_language: str):
        """Display final results"""
        costs = self.calculate_costs(video, provider_id, target_language)
        
        print(f"\n📊 EREDMÉNYEK")
        print(f"{'='*50}")
        print(f"✅ Dubbing sikeresen elkészült!")
        print(f"   Eredeti: {video.title} ({video.language})")
        print(f"   Szinkron: {video.title} ({target_language})")
        print(f"   Szolgáltató: {self.providers[provider_id].name.split(' - ')[0]}")
        print(f"   Hang: {self.selected_voice}")
        print(f"   Végső költség: ${costs['total']:.4f}")
        
        print(f"\n📁 LETÖLTHETŐ FÁJLOK:")
        print(f"   🎵 Szinkronhang: audio_{video.url.split('=')[-1]}_{target_language}.mp3")
        print(f"   🎬 Szinkronvideó: dubbed_{video.url.split('=')[-1]}_{target_language}.mp4")
        print(f"   📝 Szövegek: transcript_{video.url.split('=')[-1]}_{target_language}.txt")
        
        print(f"\n🎯 MINŐSÉGI MUTATÓK:")
        print(f"   🎤 Hangminőség: Neural2 (Prémium)")
        print(f"   ⚡ Feldolgozási sebesség: Gyors") 
        print(f"   💰 Költséghatékonyság: Kiváló")
        
        if provider_id in ["google_tts", "auto"]:
            print(f"   🏆 90%+ megtakarítás az ElevenLabshoz képest!")

async def main():
    """Main interactive demo"""
    parser = argparse.ArgumentParser(description="CLI Workflow Demo")
    parser.add_argument("--interactive", action="store_true", help="Run interactive demo")
    parser.add_argument("--url", default="https://youtube.com/watch?v=dQw4w9WgXcQ", 
                       help="YouTube URL for demo")
    parser.add_argument("--auto", action="store_true", help="Run with automatic selections")
    
    args = parser.parse_args()
    
    demo = HungarianCLIDemo()
    
    # Print header
    demo.print_header()
    
    if not args.interactive and not args.auto:
        print("Használat: python cli_workflow_demo.py --interactive")
        print("   vagy: python cli_workflow_demo.py --auto")
        return
    
    try:
        # Step 1: Get video information
        print("🔍 Videó információk betöltése...")
        time.sleep(1)
        video = demo.get_video_info(args.url)
        demo.display_video_info(video)
        
        if args.auto:
            # Automatic selections for quick demo
            provider_id = "auto"
            target_language = "en-US"
            voice_id = "en-US-Neural2-F"
            print(f"\n🤖 Automatikus mód aktiválva")
            print(f"✅ Szolgáltató: Automatikus (Google TTS)")
            print(f"✅ Célnyelv: Angol (Amerikai)")
            print(f"✅ Hang: Automatikusan kiválasztva")
        else:
            # Interactive selections
            if input("\nFolytatja a feldolgozást? [I/n]: ").lower() not in ['n', 'nem']:
                # Step 2: Select TTS provider
                provider_id = demo.select_tts_provider()
                
                # Step 3: Select target language  
                target_language = demo.select_target_language()
                
                # Step 4: Select voice
                voice_id = demo.select_voice(provider_id, target_language)
            else:
                print("👋 Viszlát!")
                return
        
        # Step 5: Show cost estimate
        demo.display_cost_estimate(video, provider_id, target_language)
        
        # Step 6: Confirm processing
        if args.auto or input("\nElindítja a feldolgozást? [I/n]: ").lower() not in ['n', 'nem']:
            # Step 7: Process video
            await demo.simulate_processing(video, provider_id, voice_id, target_language)
            
            # Step 8: Show results
            demo.display_results(video, provider_id, target_language)
            
            print(f"\n🎊 Köszönjük, hogy használta a YouTube Dubbing szolgáltatást!")
            print(f"💡 Tipp: Használja a Google TTS-t további 90% megtakarításért!")
        else:
            print("⏸️  Feldolgozás megszakítva.")
    
    except KeyboardInterrupt:
        print(f"\n\n👋 Kilépés... Viszlát!")
    except Exception as e:
        print(f"\n❌ Hiba történt: {e}")

if __name__ == "__main__":
    print("""
🖥️  CLI Workflow Demo - Interactive Dubbing
==========================================

Ez a demo szimulálja a magyar nyelvű CLI felületet a fejlett
TTS szolgáltató kiválasztással és költségoptimalizálással.

Funkciók:
- 🇭🇺 Magyar nyelvű interaktív felület  
- 🎤 TTS szolgáltató kiválasztás
- 💰 Költség összehasonlítás
- 🎭 Hang kiválasztás
- 🎬 Teljes dubbing workflow szimuláció

    """)
    
    asyncio.run(main())