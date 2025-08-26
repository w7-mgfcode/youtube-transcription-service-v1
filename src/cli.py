"""Interactive CLI module preserving original v25.py user experience."""

import sys
from typing import Tuple

from .core.transcriber import TranscriptionService
from .utils.colors import Colors, print_header
from .utils.validators import get_user_inputs
from .config import VertexAIModels


class InteractiveCLI:
    """Interactive CLI interface preserving v25.py behavior."""
    
    def __init__(self):
        self.transcriber = TranscriptionService()
    
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
        print(Colors.GREEN + f"   📁 Eredmény: {result['transcript_file']}" + Colors.ENDC)
        print(Colors.GREEN + f"   📺 Cím: {result['title']}" + Colors.ENDC)
        print(Colors.GREEN + f"   ⏱️  Időtartam: {result['duration']}s" + Colors.ENDC)
        print(Colors.GREEN + f"   📊 Szószám: {result['word_count']}" + Colors.ENDC)
        
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
                    print(Colors.CYAN + f"   💨 Detektált szünetek: {total_pauses} db" + Colors.ENDC)
                    if short_pauses > 0:
                        print(Colors.CYAN + f"      ├─ Rövid (•): {short_pauses}" + Colors.ENDC)
                    if long_pauses > 0:
                        print(Colors.CYAN + f"      ├─ Hosszú (••): {long_pauses}" + Colors.ENDC)
                    if script_pauses > 0:
                        print(Colors.CYAN + f"      └─ Script jelölések: {script_pauses}" + Colors.ENDC)
                        
            except Exception:
                pass
        
        # Show additional stats
        if result.get("vertex_ai_used"):
            print(Colors.BLUE + "   🤖 Vertex AI utófeldolgozás alkalmazva" + Colors.ENDC)
        
        if result.get("test_mode"):
            print(Colors.WARNING + "   ⚡ Teszt mód használva (60s)" + Colors.ENDC)
    
    def _show_completion_message(self):
        """Show completion message exactly like v25.py."""
        print(Colors.CYAN + "\n" + "="*70 + Colors.ENDC)
        print(Colors.BOLD + "   Köszönjük, hogy használtad a YouTube Transcribe-ot! 👋" + Colors.ENDC)
        print(Colors.CYAN + "="*70 + Colors.ENDC)


def run_interactive_cli():
    """Standalone function to run interactive CLI."""
    cli = InteractiveCLI()
    cli.run()