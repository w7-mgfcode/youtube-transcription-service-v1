"""Vertex AI post-processing module for transcript formatting."""

import datetime
from typing import Optional

from ..config import settings, VertexAIModels
from ..utils.colors import Colors


class VertexPostProcessor:
    """Vertex AI (Gemini) post-processor for script-style formatting."""
    
    def __init__(self):
        self.project_id = settings.vertex_project_id
    
    def process(self, transcript_text: str, video_title: str = "", vertex_ai_model: str = "") -> Optional[str]:
        """
        Post-process transcript using Vertex AI (Gemini) for script formatting.
        
        Args:
            transcript_text: Original transcript text
            video_title: Video title
            
        Returns:
            Formatted script text or None on error
        """
        print(Colors.BLUE + "\n🤖 Vertex AI utófeldolgozás indítása..." + Colors.ENDC)
        
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel, GenerationConfig
            
            print(Colors.CYAN + f"   ├─ Project: {self.project_id}" + Colors.ENDC)
            
            # Determine which models to try
            if vertex_ai_model and vertex_ai_model != VertexAIModels.AUTO_DETECT:
                # User specified a model, try only that one first
                models_to_try = [vertex_ai_model] + VertexAIModels.get_auto_detect_order()
                print(Colors.CYAN + f"   ├─ Kiválasztott modell: {vertex_ai_model}" + Colors.ENDC)
            else:
                # Auto-detect mode
                models_to_try = VertexAIModels.get_auto_detect_order()
                print(Colors.CYAN + "   ├─ Automatikus modell kiválasztás" + Colors.ENDC)
            
            # Try different regions
            regions = ["us-central1", "us-east1", "us-west1", "europe-west4"]
            
            model = None
            successful_config = None
            
            for region in regions:
                for model_name in models_to_try:
                    try:
                        print(Colors.CYAN + f"   ├─ Próbálkozás: {model_name} @ {region}" + Colors.ENDC)
                        
                        # Initialize Vertex AI with current region
                        vertexai.init(project=self.project_id, location=region)
                        model = GenerativeModel(model_name)
                        
                        successful_config = (model_name, region)
                        print(Colors.GREEN + f"   ✓ Sikeres kapcsolat: {model_name} @ {region}" + Colors.ENDC)
                        break
                        
                    except Exception as e:
                        print(Colors.WARNING + f"   ✗ {model_name} @ {region}: {str(e)[:100]}..." + Colors.ENDC)
                        continue
                
                if successful_config:
                    break
            
            if not successful_config:
                raise Exception("Nem sikerült kapcsolódni egyetlen Gemini modellhez sem")
                
            print(Colors.CYAN + "   └─ Prompt küldése..." + Colors.ENDC)
            
            # Create formatting prompt
            prompt = self._build_formatting_prompt(transcript_text)
            
            # Call Gemini API
            print(Colors.BLUE + "   ⏳ Gemini válaszára várunk..." + Colors.ENDC)
            
            response = model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    temperature=0.3,  # Low temperature for consistent formatting
                    max_output_tokens=8192,
                    top_p=0.8,
                )
            )
            
            formatted_text = response.text
            
            # Build final result with header
            final_text = self._build_final_result(formatted_text, video_title, transcript_text, successful_config[0])
            
            print(Colors.GREEN + f"   ✓ Vertex AI formázás kész ({successful_config[0]}): {len(formatted_text.split())} szó" + Colors.ENDC)
            
            return final_text
            
        except ImportError:
            print(Colors.WARNING + "⚠ Vertex AI könyvtár nincs telepítve!" + Colors.ENDC)
            print(Colors.WARNING + "   Telepítsd: pip install google-cloud-aiplatform" + Colors.ENDC)
            return self._fallback_processing(transcript_text, video_title)
        except Exception as e:
            print(Colors.FAIL + f"✗ Vertex AI hiba: {e}" + Colors.ENDC)
            print(Colors.WARNING + f"   Részletek: {str(e)}" + Colors.ENDC)
            print(Colors.CYAN + "   🔄 Fallback formázás alkalmazása..." + Colors.ENDC)
            return self._fallback_processing(transcript_text, video_title)
    
    def _fallback_processing(self, transcript_text: str, video_title: str = "") -> str:
        """
        Fallback processing when Vertex AI is unavailable.
        Apply basic formatting without AI processing.
        """
        print(Colors.CYAN + "   ├─ Egyszerű formázás alkalmazása" + Colors.ENDC)
        
        # Add header and basic formatting
        lines = transcript_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip():
                # Add proper capitalization and punctuation
                formatted_line = line.strip()
                if formatted_line and not formatted_line[0].isupper():
                    formatted_line = formatted_line[0].upper() + formatted_line[1:]
                if formatted_line and not formatted_line.endswith(('.', '!', '?')):
                    formatted_line += '.'
                formatted_lines.append(formatted_line)
            else:
                formatted_lines.append('')
        
        # Build final result
        formatted_text = '\n'.join(formatted_lines)
        final_text = self._build_final_result(formatted_text, video_title, transcript_text, "Fallback Format")
        
        print(Colors.GREEN + "   ✓ Fallback formázás kész" + Colors.ENDC)
        return final_text
    
    def _build_formatting_prompt(self, transcript_text: str) -> str:
        """Build the formatting prompt for Gemini."""
        # Limit transcript to first 5000 characters due to prompt limits
        limited_transcript = transcript_text[:5000]
        
        prompt = f"""Formázd át ezt a YouTube videó átiratot professzionális SCRIPT/FELIRAT stílusúra!

EREDETI ÁTIRAT (Google Speech API):
{limited_transcript}

FORMÁZÁSI SZABÁLYOK:
1. MINDEN mondatot/tagmondatot külön sorba, időbélyeggel [HH:MM:SS] formátumban
2. Maximum 12-15 szó soronként (átlag beszédtempó: 140 szó/perc)
3. Mondatvégeknél (.!?) MINDIG új sor
4. Minden jelentős szünetet jelölj külön sorban időbélyeggel:
   [0:XX:XX] [rövid szünet] = kb 0.5-1s csend
   [0:XX:XX] [levegővétel] = kb 1-2s szünet
   [0:XX:XX] [hosszú szünet] = kb 2-3s szünet
   [0:XX:XX] [TÉMAVÁLTÁS] = 3s+ szünet vagy új téma
5. Természetes beszédritmus követése
6. Kötőszavaknál (és, de, hogy, mert, hiszen) törj sort ha már 8+ szó van
7. Vesszőknél törj sort ha a mondat már hosszú
8. Becsüld meg reálisan az időbélyegeket (140 szó/perc = kb 2.3 szó/mp)

PÉLDA KIMENETI FORMÁTUM:
[0:00:00] Sziasztok, szeretettel köszöntelek benneteket.
[0:00:03] [levegővétel]
[0:00:04] Hoztam nektek a mai napra is egy üzenetet,
[0:00:07] egy általános kártya olvasást.
[0:00:09] [rövid szünet]
[0:00:10] Kártya kirakás, itt látjátok az asztalomon
[0:00:13] az univerzumnak az üzenetével kezdeném,
[0:00:16] [levegővétel]
[0:00:17] ami azt mondja és azt üzeni nektek,
[0:00:20] hogy jó lenne, hogyha át adnátok magatokat
[0:00:23] egy nálatok hatalmasabb Erőnek.
[0:00:26] [hosszú szünet]
[0:00:28] Az azt jelenti, hogy átadom magam
[0:00:31] egy nálam hatalmasabb Erőnek.

FONTOS: 
- Legalább 100-150 sor legyen a végeredmény
- Minden szünetet jelölj ahol érzed a beszédben
- A mondatok legyenek természetesek, ne törj rossz helyen
- Az időbélyegek legyenek reálisak

FORMÁZOTT SCRIPT:"""
        
        return prompt
    
    def _build_final_result(self, formatted_text: str, video_title: str, 
                          original_transcript: str, model_name: str = "Gemini") -> str:
        """Build final result with header and statistics."""
        final_text = f"📹 Videó: {video_title}\n"
        final_text += f"📅 Feldolgozva: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        final_text += f"🤖 Utófeldolgozás: Vertex AI ({model_name})\n"
        final_text += "=" * 70 + "\n\n"
        final_text += formatted_text
        
        # Add note if transcript was truncated
        if len(original_transcript) > 5000:
            final_text += f"\n\n[FIGYELEM: A teljes átirat {len(original_transcript)} karakter, csak az első 5000 lett formázva]"
        
        # Calculate statistics
        lines = formatted_text.split('\n')
        word_count = len(formatted_text.split())
        pause_count = formatted_text.count('[') - formatted_text.count('[0:')
        
        final_text += f"\n\n{'='*70}\n"
        final_text += f"📊 Script statisztika (AI formázás):\n"
        final_text += f"   • Sorok száma: {len(lines)}\n"
        final_text += f"   • Összes szó: {word_count}\n"
        final_text += f"   • Detektált szünetek: {pause_count}\n"
        final_text += f"   • Átlagos sorhossz: {word_count/len(lines) if lines else 0:.1f} szó\n"
        
        return final_text