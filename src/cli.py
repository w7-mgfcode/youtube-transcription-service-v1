"""Interactive CLI module preserving original v25.py user experience."""

import sys
from typing import Tuple

from .core.transcriber import TranscriptionService
from .core.translator import ContextAwareTranslator
from .core.synthesizer import ElevenLabsSynthesizer
from .core.video_muxer import VideoMuxer
from .core.dubbing_service import DubbingService
from .core.tts_factory import TTSFactory
from .core.tts_interface import TTSProvider
from .utils.colors import Colors, print_header
from .utils.validators import (
    get_user_inputs, get_dubbing_preferences, 
    get_voice_selection, show_dubbing_cost_estimate
)
from .utils.chunking import TranscriptChunker
from .config import VertexAIModels
from .models.dubbing import DubbingRequest, TranslationContextEnum, TTSProviderEnum
from pydantic import HttpUrl


class InteractiveCLI:
    """Interactive CLI interface preserving v25.py behavior."""
    
    def __init__(self):
        self.transcriber = TranscriptionService()
        self.chunker = TranscriptChunker()
        self.translator = ContextAwareTranslator()
        self.synthesizer = ElevenLabsSynthesizer()
        self.video_muxer = VideoMuxer()
        self.dubbing_service = DubbingService()
    
    def run(self):
        """Run interactive CLI session."""
        try:
            # Show header (exactly like v25.py)
            print_header()
            
            # Get user inputs (preserves Hungarian interface)
            video_url, test_mode, breath_detection = get_user_inputs()
            
            # Show processing info
            if test_mode:
                print(Colors.WARNING + "\n⚡ TESZT MÓD AKTÍV - Maximum 60 másodperc lesz feldolgozva!" + Colors.ENDC)
            
            if breath_detection:
                print(Colors.CYAN + "💨 Levegővétel detektálás bekapcsolva - szünetek jelölve lesznek (• és ••)" + Colors.ENDC)
            
            # Progress callback for console output
            def print_progress(status: str, progress: int):
                """Progress callback that doesn't interfere with existing progress bars."""
                # The individual modules handle their own progress display
                # This callback is mainly for API mode
                pass
            
            # Process transcription
            print(Colors.BOLD + f"\n🎯 Feldolgozás indítása..." + Colors.ENDC)
            
            result = self.transcriber.process(
                url=video_url,
                test_mode=test_mode,
                breath_detection=breath_detection,
                use_vertex_ai=False,  # Will ask user later
                progress_callback=print_progress
            )
            
            if result["status"] == "completed":
                # Show preview (like v25.py)
                self._show_preview(result["transcript_file"], breath_detection)
                
                # Ask about Vertex AI post-processing
                if breath_detection:
                    use_vertex, selected_model = self._ask_vertex_ai_processing()
                    
                    if use_vertex:
                        # Check if chunking is needed and show estimate
                        continue_processing = self._show_chunking_info(result["transcript_file"])
                        
                        if not continue_processing:
                            print(Colors.CYAN + "Vertex AI feldolgozás kihagyva." + Colors.ENDC)
                        else:
                            print(Colors.BLUE + f"\n🤖 Vertex AI utófeldolgozás ({selected_model})..." + Colors.ENDC)
                            
                            # Re-process with Vertex AI
                            vertex_result = self.transcriber.process(
                                url=video_url,
                                test_mode=test_mode,
                                breath_detection=breath_detection,
                                use_vertex_ai=True,
                                vertex_ai_model=selected_model,
                                progress_callback=print_progress
                            )
                            
                            if vertex_result["status"] == "completed":
                                result = vertex_result
                                print(Colors.GREEN + "✓ Vertex AI formázás alkalmazva!" + Colors.ENDC)
                
                # Ask about dubbing
                dubbing_preferences = get_dubbing_preferences()
                
                if dubbing_preferences:
                    dubbing_result = self._process_dubbing_workflow(
                        video_url=video_url,
                        test_mode=test_mode,
                        transcript_result=result,
                        preferences=dubbing_preferences
                    )
                    
                    if dubbing_result:
                        # Merge dubbing results into main result
                        result.update(dubbing_result)
                        print(Colors.GREEN + "✅ Szinkronizálás sikeres!" + Colors.ENDC)
                    else:
                        print(Colors.WARNING + "⚠ Szinkronizálás részben vagy egészben sikertelen" + Colors.ENDC)
                
                # Show final results
                self._show_final_results(result, breath_detection)
            else:
                print(Colors.FAIL + f"\n✗ Nem sikerült átírni az audiót: {result.get('error', 'Ismeretlen hiba')}" + Colors.ENDC)
                sys.exit(1)
        
        except KeyboardInterrupt:
            print(Colors.WARNING + "\n\n⚠ Megszakítva felhasználó által!" + Colors.ENDC)
            sys.exit(0)
        except Exception as e:
            print(Colors.FAIL + f"\n\n✗ Kritikus hiba: {e}" + Colors.ENDC)
            sys.exit(1)
        finally:
            # Show completion message (exactly like v25.py)
            self._show_completion_message()
    
    def _show_preview(self, transcript_file: str, breath_detection: bool):
        """Show transcript preview like v25.py."""
        try:
            with open(transcript_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(Colors.CYAN + "\n--- ELŐNÉZET (első 800 karakter) ---" + Colors.ENDC)
            preview = content[:800]
            
            # Highlight breath markers if enabled
            if breath_detection and '•' in preview:
                preview = preview.replace('•', Colors.WARNING + '•' + Colors.ENDC)
            
            print(preview + ("..." if len(content) > 800 else ""))
            
        except Exception as e:
            print(Colors.WARNING + f"⚠ Előnézet hiba: {e}" + Colors.ENDC)
    
    def _ask_vertex_ai_processing(self) -> Tuple[bool, str]:
        """Ask user about Vertex AI post-processing and model selection."""
        while True:
            try:
                print(Colors.BOLD + "\n🤖 Szeretnéd Vertex AI-val újraformázni script stílusra? [i/n]: " + Colors.ENDC, end="")
                response = input().lower().strip()
                
                if response == 'i':
                    # User wants Vertex AI, now ask for model
                    selected_model = self._ask_vertex_ai_model()
                    return True, selected_model
                elif response == 'n':
                    return False, ""
                else:
                    print(Colors.WARNING + "Kérlek válaszolj 'i' (igen) vagy 'n' (nem) karakterrel!" + Colors.ENDC)
            except (EOFError, KeyboardInterrupt):
                return False, ""
    
    def _ask_vertex_ai_model(self) -> str:
        """Ask user to select Vertex AI model."""
        models = VertexAIModels.get_all_models()
        
        print(Colors.CYAN + "\n🔧 Vertex AI modell választása:" + Colors.ENDC)
        
        for i, model in enumerate(models, 1):
            description = VertexAIModels.get_model_description(model)
            if model == VertexAIModels.GEMINI_2_0_FLASH:
                print(Colors.GREEN + f"   {i}. {model} - {description}" + Colors.ENDC)
            else:
                print(Colors.CYAN + f"   {i}. {model} - {description}" + Colors.ENDC)
        
        while True:
            try:
                print(Colors.BOLD + f"\nVálasztás [1-{len(models)}, Enter = 1]: " + Colors.ENDC, end="")
                response = input().strip()
                
                if response == "":
                    # Default to first option (recommended)
                    return models[0]
                
                try:
                    choice = int(response)
                    if 1 <= choice <= len(models):
                        selected = models[choice - 1]
                        print(Colors.GREEN + f"✓ Kiválasztva: {selected}" + Colors.ENDC)
                        return selected
                    else:
                        print(Colors.WARNING + f"Kérlek válassz 1 és {len(models)} között!" + Colors.ENDC)
                except ValueError:
                    print(Colors.WARNING + "Kérlek adj meg egy számot!" + Colors.ENDC)
            except (EOFError, KeyboardInterrupt):
                # Default selection on interrupt
                return models[0]
    
    def _show_final_results(self, result: dict, breath_detection: bool):
        """Show final results like v25.py."""
        print(Colors.BOLD + Colors.GREEN + f"\n✅ SIKERES FELDOLGOZÁS!" + Colors.ENDC)
        print(Colors.GREEN + f"   📁 Magyar átirat: {result['transcript_file']}" + Colors.ENDC)
        print(Colors.GREEN + f"   📺 Cím: {result['title']}" + Colors.ENDC)
        print(Colors.GREEN + f"   ⏱️  Időtartam: {result['duration']}s" + Colors.ENDC)
        print(Colors.GREEN + f"   📊 Szószám: {result['word_count']}" + Colors.ENDC)
        
        # Show dubbing results if available
        if result.get('dubbing_status'):
            print(Colors.CYAN + f"\n🎬 SZINKRONIZÁLÁSI EREDMÉNYEK:" + Colors.ENDC)
            
            dubbing_status = result.get('dubbing_status')
            if dubbing_status == 'completed':
                print(Colors.GREEN + f"   ✅ Szinkronizálási státusz: Sikeres" + Colors.ENDC)
            elif dubbing_status == 'failed':
                print(Colors.FAIL + f"   ❌ Szinkronizálási státusz: Sikertelen" + Colors.ENDC)
                if result.get('dubbing_error'):
                    print(Colors.FAIL + f"      └─ Hiba: {result['dubbing_error']}" + Colors.ENDC)
            else:
                print(Colors.WARNING + f"   ⚠ Szinkronizálási státusz: {dubbing_status}" + Colors.ENDC)
            
            # Show generated files
            if result.get('translation_file'):
                print(Colors.GREEN + f"   🌍 Fordított átirat: {result['translation_file']}" + Colors.ENDC)
            
            if result.get('audio_file'):
                print(Colors.GREEN + f"   🎤 Szintetizált hang: {result['audio_file']}" + Colors.ENDC)
            
            if result.get('video_file'):
                print(Colors.GREEN + f"   🎞️  Szinkronizált videó: {result['video_file']}" + Colors.ENDC)
            
            # Show cost breakdown if available
            if result.get('dubbing_cost'):
                cost_info = result['dubbing_cost']
                total_cost = cost_info.get('total_cost_usd', 0.0)
                if total_cost > 0:
                    print(Colors.YELLOW + f"   💰 Szinkronizálási költség: ${total_cost:.4f}" + Colors.ENDC)
        
        # Show breath detection statistics if enabled
        if breath_detection:
            try:
                with open(result['transcript_file'], 'r', encoding='utf-8') as f:
                    transcript_content = f.read()
                    
                # Count different pause markers
                short_pauses = transcript_content.count('•')
                long_pauses = transcript_content.count('••')
                script_pauses = (transcript_content.count('[szünet]') + 
                               transcript_content.count('[levegővétel]') + 
                               transcript_content.count('[hosszú szünet]'))
                
                total_pauses = short_pauses + long_pauses + script_pauses
                
                if total_pauses > 0:
                    print(Colors.CYAN + f"\n💨 DETEKTÁLT SZÜNETEK: {total_pauses} db" + Colors.ENDC)
                    if short_pauses > 0:
                        print(Colors.CYAN + f"   ├─ Rövid (•): {short_pauses}" + Colors.ENDC)
                    if long_pauses > 0:
                        print(Colors.CYAN + f"   ├─ Hosszú (••): {long_pauses}" + Colors.ENDC)
                    if script_pauses > 0:
                        print(Colors.CYAN + f"   └─ Script jelölések: {script_pauses}" + Colors.ENDC)
                        
            except Exception:
                pass
        
        # Show additional stats
        if result.get("vertex_ai_used"):
            print(Colors.BLUE + "\n🤖 Vertex AI utófeldolgozás alkalmazva" + Colors.ENDC)
        
        if result.get("test_mode"):
            print(Colors.WARNING + "\n⚡ Teszt mód használva (60s)" + Colors.ENDC)
    
    def _show_chunking_info(self, transcript_file: str):
        """Show chunking information and cost estimates before processing."""
        try:
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcript_text = f.read()
            
            # Check if chunking is needed
            if self.chunker.needs_chunking(transcript_text):
                cost_info = self.chunker.estimate_processing_cost(transcript_text)
                
                print(Colors.YELLOW + "\n📑 Hosszú átirat észlelve - Chunked feldolgozás lesz alkalmazva" + Colors.ENDC)
                print(Colors.CYAN + f"   ├─ Eredeti hossz: {len(transcript_text)} karakter" + Colors.ENDC)
                print(Colors.CYAN + f"   ├─ Chunks száma: {cost_info['total_chunks']}" + Colors.ENDC)
                print(Colors.CYAN + f"   ├─ Becsült feldolgozási idő: {cost_info['estimated_time_seconds']:.1f} mp" + Colors.ENDC)
                print(Colors.CYAN + f"   └─ Becsült költség: ${cost_info['estimated_cost_usd']:.4f}" + Colors.ENDC)
                
                # Ask for confirmation
                print(Colors.WARNING + "\nFigyelm: A chunked feldolgozás több időt és költséget igényel." + Colors.ENDC)
                response = input(Colors.BOLD + "Folytatod? (i/n) [i]: " + Colors.ENDC).strip().lower()
                
                if response and response.startswith('n'):
                    print(Colors.WARNING + "Vertex AI feldolgozás megszakítva." + Colors.ENDC)
                    return False
                    
                print(Colors.GREEN + "✓ Chunked feldolgozás jóváhagyva" + Colors.ENDC)
            else:
                print(Colors.GREEN + f"\n✓ Standard feldolgozás ({len(transcript_text)} karakter)" + Colors.ENDC)
                
            return True
            
        except Exception as e:
            print(Colors.WARNING + f"⚠ Chunking információ lekérése sikertelen: {e}" + Colors.ENDC)
            return True
    
    def _process_dubbing_workflow(self, video_url: str, test_mode: bool, 
                                transcript_result: dict, preferences: dict) -> dict:
        """
        Process the complete dubbing workflow.
        
        Args:
            video_url: YouTube video URL
            test_mode: Test mode flag
            transcript_result: Result from transcription
            preferences: User dubbing preferences
            
        Returns:
            Dictionary with dubbing results
        """
        try:
            # Get transcript text for cost estimation
            transcript_file = transcript_result.get("transcript_file")
            if not transcript_file:
                print(Colors.FAIL + "✗ Nem található átirat fájl a szinkronizáláshoz" + Colors.ENDC)
                return {}
            
            # Read transcript for cost estimation
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcript_text = f.read()
            
            # Show cost estimate and get confirmation
            if not show_dubbing_cost_estimate(self.dubbing_service, len(transcript_text), preferences):
                return {}
            
            # Get voice selection if synthesis enabled
            voice_id = None
            synthesizer = None
            if preferences.get('enable_synthesis'):
                # Get the appropriate synthesizer based on provider selection
                tts_provider = preferences.get('tts_provider', TTSProviderEnum.AUTO)
                
                try:
                    synthesizer = TTSFactory.create_synthesizer(
                        TTSProvider(tts_provider.value) if hasattr(tts_provider, 'value') else TTSProvider.AUTO
                    )
                    print(Colors.CYAN + f"\n🎤 {synthesizer.provider_name.value} hang kiválasztása..." + Colors.ENDC)
                    
                    voice_id = get_voice_selection(synthesizer, tts_provider)
                    
                    if not voice_id:
                        print(Colors.WARNING + "⚠ Hang kiválasztása sikertelen, alapértelmezett hang használva" + Colors.ENDC)
                        
                except Exception as e:
                    print(Colors.WARNING + f"⚠ TTS provider inicializálás sikertelen: {e}" + Colors.ENDC)
                    print(Colors.CYAN + "Visszaváltás az alapértelmezett ElevenLabs szolgáltatóra..." + Colors.ENDC)
                    
                    # Fallback to ElevenLabs
                    synthesizer = self.synthesizer
                    tts_provider = TTSProviderEnum.ELEVENLABS
                    voice_id = get_voice_selection(synthesizer, tts_provider)
            
            # Create dubbing request
            try:
                context_map = {
                    'casual': TranslationContextEnum.CASUAL,
                    'educational': TranslationContextEnum.EDUCATIONAL,
                    'marketing': TranslationContextEnum.MARKETING,
                    'spiritual': TranslationContextEnum.SPIRITUAL,
                    'legal': TranslationContextEnum.LEGAL,
                    'news': TranslationContextEnum.NEWS,
                    'scientific': TranslationContextEnum.SCIENTIFIC
                }
                
                translation_context = context_map.get(
                    preferences.get('translation_context', 'casual'),
                    TranslationContextEnum.CASUAL
                )
                
                dubbing_request = DubbingRequest(
                    url=HttpUrl(video_url),
                    test_mode=test_mode,
                    enable_translation=True,
                    target_language=preferences.get('target_language', 'en-US'),
                    translation_context=translation_context,
                    enable_synthesis=preferences.get('enable_synthesis', False),
                    tts_provider=preferences.get('tts_provider', TTSProviderEnum.AUTO),
                    voice_id=voice_id,
                    enable_video_muxing=preferences.get('enable_video_muxing', False),
                    existing_transcript=transcript_text
                )
                
            except Exception as e:
                print(Colors.FAIL + f"✗ Szinkronizálási kérés létrehozása sikertelen: {e}" + Colors.ENDC)
                return {}
            
            # Define progress callback for dubbing stages
            def dubbing_progress(status: str, progress: int):
                stage_names = {
                    'translating': '🌍 Fordítás',
                    'synthesizing': '🎤 Hangszintézis',
                    'muxing': '🎞️  Videó összekeverés',
                    'completed': '✅ Befejezve'
                }
                
                stage_name = stage_names.get(status, status)
                if progress >= 0:
                    print(f"   {stage_name}: {progress}%")
            
            print(Colors.BOLD + f"\n🎬 Szinkronizálás indítása..." + Colors.ENDC)
            
            # Process dubbing
            dubbing_result = self.dubbing_service.process_dubbing_job(
                request=dubbing_request,
                progress_callback=dubbing_progress
            )
            
            # Convert result to dict for merging
            result_dict = {
                'dubbing_status': dubbing_result.status,
                'translation_file': dubbing_result.translation_file,
                'audio_file': dubbing_result.audio_file,
                'video_file': dubbing_result.video_file,
                'dubbing_cost': dubbing_result.cost_breakdown
            }
            
            if dubbing_result.error:
                result_dict['dubbing_error'] = dubbing_result.error
                print(Colors.FAIL + f"✗ Szinkronizálási hiba: {dubbing_result.error}" + Colors.ENDC)
            
            return result_dict
            
        except Exception as e:
            print(Colors.FAIL + f"✗ Szinkronizálási folyamat hiba: {e}" + Colors.ENDC)
            return {}
    
    def _show_completion_message(self):
        """Show completion message with enhanced service features."""
        print(Colors.CYAN + "\n" + "="*80 + Colors.ENDC)
        print(Colors.BOLD + "   Köszönjük, hogy használtad a YouTube Transcribe & Dubbing szolgáltatást! 👋" + Colors.ENDC)
        print(Colors.CYAN + "   🎯 Magyar átírás ✓ | 🌍 Multilingual fordítás ✓ | 🎤 Hangszintézis ✓ | 🎞️ Videó szinkronizálás ✓" + Colors.ENDC)
        print(Colors.CYAN + "="*80 + Colors.ENDC)


def run_interactive_cli():
    """Standalone function to run interactive CLI."""
    cli = InteractiveCLI()
    cli.run()