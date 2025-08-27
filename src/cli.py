"""Interactive CLI module preserving original v25.py user experience."""

import sys
from typing import Tuple

from .core.transcriber import TranscriptionService
from .core.translator import ContextAwareTranslator
from .core.synthesizer import ElevenLabsSynthesizer
from .core.video_muxer import VideoMuxer
from .core.dubbing_service import DubbingService
from .core.postprocessor import VertexPostProcessor
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
        self.postprocessor = VertexPostProcessor()
    
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
                            
                            # Read existing transcript and apply Vertex AI post-processing only
                            try:
                                with open(result["transcript_file"], 'r', encoding='utf-8') as f:
                                    transcript_text = f.read()
                                
                                # Apply Vertex AI post-processing to existing transcript
                                formatted_text = self.postprocessor.process(
                                    transcript_text=transcript_text,
                                    video_title=result.get("title", ""),
                                    vertex_ai_model=selected_model
                                )
                                
                                if formatted_text:
                                    # Write formatted text back to the transcript file
                                    with open(result["transcript_file"], 'w', encoding='utf-8') as f:
                                        f.write(formatted_text)
                                    
                                    # Update word count and status
                                    result["word_count"] = len(formatted_text.split())
                                    result["vertex_ai_used"] = True
                                    result["vertex_ai_model"] = selected_model
                                    print(Colors.GREEN + "✓ Vertex AI formázás alkalmazva!" + Colors.ENDC)
                                else:
                                    print(Colors.WARNING + "⚠ Vertex AI formázás sikertelen, eredeti szöveg megmarad" + Colors.ENDC)
                                    
                            except Exception as vertex_error:
                                print(Colors.WARNING + f"⚠ Vertex AI feldolgozási hiba: {vertex_error}" + Colors.ENDC)
                                print(Colors.CYAN + "Eredeti átirat megmarad." + Colors.ENDC)
                
                # Ask about dubbing
                dubbing_preferences = get_dubbing_preferences()
                
                if dubbing_preferences:
                    dubbing_result = self._process_dubbing_workflow(
                        video_url=video_url,
                        test_mode=test_mode,
                        transcript_result=result,
                        preferences=dubbing_preferences
                    )
                    
                    # Enhanced dubbing result handling
                    if dubbing_result and dubbing_result.get('dubbing_status') == 'completed':
                        # Merge successful dubbing results into main result
                        result.update(dubbing_result)
                        print(Colors.GREEN + "✅ Szinkronizálás sikeres!" + Colors.ENDC)
                        self._show_final_results(result, breath_detection)
                    elif dubbing_result and dubbing_result.get('dubbing_status') == 'cancelled':
                        print(Colors.CYAN + "⚠ Szinkronizálás felhasználó által megszakítva" + Colors.ENDC)
                        self._show_final_results(result, breath_detection)  # Show transcription results
                    elif dubbing_result and dubbing_result.get('dubbing_status') == 'failed':
                        print(Colors.FAIL + "❌ Szinkronizálás sikertelen!" + Colors.ENDC)
                        if dubbing_result.get('dubbing_error'):
                            print(Colors.FAIL + f"   Hiba: {dubbing_result['dubbing_error']}" + Colors.ENDC)
                        print(Colors.CYAN + "\n📝 Átirat feldolgozás eredménye:" + Colors.ENDC)
                        self._show_final_results(result, breath_detection)  # Show only transcription results
                    else:
                        print(Colors.WARNING + "⚠ Szinkronizálás ismeretlen állapotban fejeződött be" + Colors.ENDC)
                        self._show_final_results(result, breath_detection)  # Show transcription results as fallback
                else:
                    # No dubbing requested, show transcription results
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
        Process the complete dubbing workflow with enhanced debug information and error handling.
        
        Args:
            video_url: YouTube video URL
            test_mode: Test mode flag
            transcript_result: Result from transcription
            preferences: User dubbing preferences
            
        Returns:
            Dictionary with dubbing results
        """
        print(Colors.BOLD + "\n" + "="*60 + Colors.ENDC)
        print(Colors.BOLD + Colors.BLUE + "        🎬 DUBBING WORKFLOW INDÍTÁSA" + Colors.ENDC)
        print(Colors.BOLD + "="*60 + Colors.ENDC)
        
        try:
            # Debug: Show current preferences
            print(Colors.CYAN + "🔍 Debug - Dubbing beállítások:" + Colors.ENDC)
            for key, value in preferences.items():
                print(Colors.CYAN + f"   {key}: {value}" + Colors.ENDC)
            
            # Step 1: Get transcript text for cost estimation
            print(Colors.CYAN + "\n📍 1. lépés: Átirat fájl ellenőrzése..." + Colors.ENDC)
            transcript_file = transcript_result.get("transcript_file")
            if not transcript_file:
                print(Colors.FAIL + "✗ Nem található átirat fájl a szinkronizáláshoz" + Colors.ENDC)
                return {'dubbing_status': 'failed', 'dubbing_error': 'Átirat fájl nem található'}
            
            print(Colors.GREEN + f"✓ Átirat fájl: {transcript_file}" + Colors.ENDC)
            
            # Read transcript for cost estimation
            try:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript_text = f.read()
                
                print(Colors.GREEN + f"✓ Átirat betöltve: {len(transcript_text)} karakter" + Colors.ENDC)
            except Exception as read_error:
                print(Colors.FAIL + f"✗ Átirat fájl olvasási hiba: {read_error}" + Colors.ENDC)
                return {'dubbing_status': 'failed', 'dubbing_error': f'Átirat olvasási hiba: {read_error}'}
            
            # Step 2: Show cost estimate and get confirmation
            print(Colors.CYAN + "\n📍 2. lépés: Költségbecslés és jóváhagyás..." + Colors.ENDC)
            try:
                cost_approved = show_dubbing_cost_estimate(self.dubbing_service, len(transcript_text), preferences)
                if not cost_approved:
                    print(Colors.WARNING + "⚠ Költségbecslés nem jóváhagyva" + Colors.ENDC)
                    return {'dubbing_status': 'cancelled', 'dubbing_error': 'Felhasználó által visszavonva'}
                
                print(Colors.GREEN + "✓ Költségbecslés jóváhagyva" + Colors.ENDC)
            except Exception as cost_error:
                print(Colors.WARNING + f"⚠ Költségbecslés hiba: {cost_error}. Folytatás..." + Colors.ENDC)
            
            # Step 3: Get voice selection if synthesis enabled
            print(Colors.CYAN + "\n📍 3. lépés: Hang kiválasztás..." + Colors.ENDC)
            voice_id = None
            synthesizer = None
            if preferences.get('enable_synthesis'):
                print(Colors.CYAN + "🎤 Hangszintézis engedélyezve - hang kiválasztása..." + Colors.ENDC)
                
                # Get the appropriate synthesizer based on provider selection
                tts_provider = preferences.get('tts_provider', TTSProviderEnum.AUTO)
                print(Colors.CYAN + f"🔧 TTS Provider: {tts_provider}" + Colors.ENDC)
                
                try:
                    # Convert to TTSProvider enum if needed
                    if hasattr(tts_provider, 'value'):
                        provider_enum = TTSProvider(tts_provider.value)
                    else:
                        provider_enum = TTSProvider.AUTO
                    
                    synthesizer = TTSFactory.create_synthesizer(provider_enum)
                    print(Colors.GREEN + f"✓ TTS synthesizer inicializálva: {synthesizer.provider_name.value}" + Colors.ENDC)
                    
                    voice_id = get_voice_selection(synthesizer, tts_provider)
                    
                    if voice_id:
                        print(Colors.GREEN + f"✓ Hang kiválasztva: {voice_id}" + Colors.ENDC)
                    else:
                        print(Colors.WARNING + "⚠ Hang kiválasztása sikertelen, alapértelmezett hang használva" + Colors.ENDC)
                        
                except Exception as tts_error:
                    print(Colors.WARNING + f"⚠ TTS provider inicializálás sikertelen: {tts_error}" + Colors.ENDC)
                    print(Colors.CYAN + "🔄 Visszaváltás az alapértelmezett ElevenLabs szolgáltatóra..." + Colors.ENDC)
                    
                    # Fallback to ElevenLabs
                    try:
                        synthesizer = self.synthesizer
                        tts_provider = TTSProviderEnum.ELEVENLABS
                        voice_id = get_voice_selection(synthesizer, tts_provider)
                        print(Colors.GREEN + "✓ ElevenLabs fallback sikeres" + Colors.ENDC)
                    except Exception as fallback_error:
                        print(Colors.WARNING + f"⚠ ElevenLabs fallback is sikertelen: {fallback_error}" + Colors.ENDC)
                        voice_id = None
            else:
                print(Colors.CYAN + "🔇 Hangszintézis kihagyva" + Colors.ENDC)
            
            # Step 4: Create dubbing request
            print(Colors.CYAN + "\n📍 4. lépés: Dubbing kérés létrehozása..." + Colors.ENDC)
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
                
                print(Colors.GREEN + "✓ Dubbing kérés sikeresen létrehozva" + Colors.ENDC)
                print(Colors.CYAN + f"   URL: {video_url}" + Colors.ENDC)
                print(Colors.CYAN + f"   Target: {preferences.get('target_language', 'en-US')}" + Colors.ENDC)
                print(Colors.CYAN + f"   Synthesis: {'Igen' if preferences.get('enable_synthesis') else 'Nem'}" + Colors.ENDC)
                print(Colors.CYAN + f"   Video mux: {'Igen' if preferences.get('enable_video_muxing') else 'Nem'}" + Colors.ENDC)
                
            except Exception as req_error:
                print(Colors.FAIL + f"✗ Szinkronizálási kérés létrehozása sikertelen: {req_error}" + Colors.ENDC)
                return {'dubbing_status': 'failed', 'dubbing_error': f'Kérés létrehozási hiba: {req_error}'}
            
            # Step 5: Define enhanced progress callback for dubbing stages
            print(Colors.CYAN + "\n📍 5. lépés: Dubbing feldolgozás..." + Colors.ENDC)
            current_stage = {'name': 'unknown', 'progress': 0}
            
            def dubbing_progress(status: str, progress: int):
                stage_names = {
                    'queued': '⏳ Várakozás',
                    'starting': '🚀 Indítás',
                    'translating': '🌍 Fordítás',
                    'synthesizing': '🎤 Hangszintézis',
                    'muxing': '🎞️  Videó összekeverés',
                    'finalizing': '🔄 Finalizálás',
                    'completed': '✅ Befejezve',
                    'failed': '❌ Sikertelen'
                }
                
                stage_name = stage_names.get(status, f"🔧 {status}")
                current_stage['name'] = status
                current_stage['progress'] = progress
                
                if progress >= 0:
                    print(Colors.BOLD + f"   {stage_name}: {progress}%" + Colors.ENDC)
                else:
                    print(Colors.CYAN + f"   {stage_name}" + Colors.ENDC)
            
            print(Colors.BOLD + f"🎬 Dubbing folyamat indítása..." + Colors.ENDC)
            
            # Process dubbing with error tracking
            dubbing_result = None
            try:
                dubbing_result = self.dubbing_service.process_dubbing_job(
                    request=dubbing_request,
                    progress_callback=dubbing_progress
                )
                
                if dubbing_result:
                    print(Colors.GREEN + f"\n✅ Dubbing szolgáltatás válasz érkezett: {dubbing_result.status}" + Colors.ENDC)
                else:
                    print(Colors.FAIL + "\n✗ Dubbing szolgáltatás None eredményt adott" + Colors.ENDC)
                    return {'dubbing_status': 'failed', 'dubbing_error': 'Dubbing szolgáltatás nem adott eredményt'}
                    
            except Exception as processing_error:
                print(Colors.FAIL + f"\n✗ Dubbing feldolgozási hiba: {processing_error}" + Colors.ENDC)
                return {'dubbing_status': 'failed', 'dubbing_error': f'Feldolgozási hiba: {processing_error}'}
            
            # Step 6: Process and validate results
            print(Colors.CYAN + "\n📍 6. lépés: Eredmények feldolgozása..." + Colors.ENDC)
            
            # Convert result to dict for merging
            result_dict = {
                'dubbing_status': dubbing_result.status if dubbing_result else 'unknown',
                'translation_file': getattr(dubbing_result, 'translation_file', None),
                'audio_file': getattr(dubbing_result, 'audio_file', None),
                'video_file': getattr(dubbing_result, 'video_file', None),
                'dubbing_cost': getattr(dubbing_result, 'cost_breakdown', None)
            }
            
            # Show detailed results
            if dubbing_result and dubbing_result.status == 'completed':
                print(Colors.GREEN + "✅ Dubbing workflow sikeresen befejezve!" + Colors.ENDC)
                
                if result_dict.get('translation_file'):
                    print(Colors.GREEN + f"   📝 Fordítás: {result_dict['translation_file']}" + Colors.ENDC)
                if result_dict.get('audio_file'):
                    print(Colors.GREEN + f"   🎤 Hang: {result_dict['audio_file']}" + Colors.ENDC)
                if result_dict.get('video_file'):
                    print(Colors.GREEN + f"   🎞️  Videó: {result_dict['video_file']}" + Colors.ENDC)
                    
                cost_info = result_dict.get('dubbing_cost')
                if cost_info and isinstance(cost_info, dict):
                    total_cost = cost_info.get('total_cost_usd', 0)
                    if total_cost > 0:
                        print(Colors.YELLOW + f"   💰 Tényleges költség: ${total_cost:.4f}" + Colors.ENDC)
                        
            elif dubbing_result and dubbing_result.error:
                result_dict['dubbing_error'] = dubbing_result.error
                print(Colors.FAIL + f"✗ Szinkronizálási hiba: {dubbing_result.error}" + Colors.ENDC)
            else:
                error_msg = "Ismeretlen dubbing hiba"
                result_dict['dubbing_error'] = error_msg
                print(Colors.FAIL + f"✗ {error_msg}" + Colors.ENDC)
            
            print(Colors.BOLD + "="*60 + Colors.ENDC)
            return result_dict
            
        except Exception as e:
            print(Colors.FAIL + f"\n✗ Kritikus dubbing workflow hiba: {e}" + Colors.ENDC)
            print(Colors.BOLD + "="*60 + Colors.ENDC)
            return {'dubbing_status': 'failed', 'dubbing_error': f'Kritikus hiba: {e}'}
    
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