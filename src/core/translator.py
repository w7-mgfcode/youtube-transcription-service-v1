"""Context-aware translation module using Vertex AI."""

import re
import datetime
from typing import Optional, Dict, List, Tuple
from enum import Enum

from ..config import settings, VertexAIModels, TranslationContext
from ..utils.colors import Colors
from ..utils.chunking import TranscriptChunker


class TranslationQuality(str, Enum):
    """Translation quality levels."""
    FAST = "fast"        # Quick translation, may sacrifice some accuracy
    BALANCED = "balanced"  # Balance between speed and quality
    HIGH = "high"        # High quality, slower processing


class ContextAwareTranslator:
    """Vertex AI-powered context-aware translator with timing preservation."""
    
    def __init__(self):
        self.project_id = settings.vertex_project_id
        self.chunker = TranscriptChunker()
        
        # Context-specific instruction templates
        self.context_instructions = {
            TranslationContext.SPIRITUAL: {
                "instruction": "Preserve the spiritual, uplifting, and compassionate tone. Maintain motivational language and keep religious/spiritual terminology accurate. Focus on emotional resonance.",
                "terminology": "Use respectful spiritual language, preserve metaphors and inspirational phrases",
                "tone": "Warm, encouraging, and reverent"
            },
            TranslationContext.LEGAL: {
                "instruction": "Keep the formal legal register and ensure precise terminology. Maintain professional tone and accuracy of legal concepts. Avoid ambiguity.",
                "terminology": "Use exact legal terminology, preserve technical precision",
                "tone": "Formal, precise, and authoritative"
            },
            TranslationContext.MARKETING: {
                "instruction": "Adapt for marketing purposes: make it persuasive, engaging, and action-oriented. Preserve selling points and emotional appeals.",
                "terminology": "Use compelling marketing language, maintain call-to-action elements",
                "tone": "Persuasive, engaging, and dynamic"
            },
            TranslationContext.SCIENTIFIC: {
                "instruction": "Maintain scientific accuracy and technical precision. Keep technical terms consistent and preserve logical flow.",
                "terminology": "Use precise scientific vocabulary, maintain technical accuracy",
                "tone": "Objective, precise, and analytical"
            },
            TranslationContext.EDUCATIONAL: {
                "instruction": "Make it clear and educational. Ensure concepts are well-explained and accessible to the learning audience.",
                "terminology": "Use clear educational language, define complex terms",
                "tone": "Clear, instructive, and supportive"
            },
            TranslationContext.NEWS: {
                "instruction": "Maintain journalistic objectivity and factual accuracy. Keep the informational tone and news-style structure.",
                "terminology": "Use professional news language, maintain factual precision",
                "tone": "Objective, informative, and professional"
            },
            TranslationContext.CASUAL: {
                "instruction": "Maintain natural conversational tone. Keep it friendly and accessible while preserving the speaker's personality.",
                "terminology": "Use natural conversational language, maintain personal style",
                "tone": "Natural, friendly, and conversational"
            }
        }
    
    def translate_script(self, 
                        script_text: str, 
                        target_language: str,
                        context: str = TranslationContext.CASUAL,
                        audience: str = "general public",
                        tone: str = "neutral",
                        quality: TranslationQuality = TranslationQuality.BALANCED,
                        preserve_timing: bool = True) -> Optional[Dict]:
        """
        Translate Hungarian timed script with context awareness.
        
        Args:
            script_text: Hungarian transcript with timestamps
            target_language: Target language code (e.g., 'en-US', 'de-DE')
            context: Translation context (spiritual, legal, marketing, etc.)
            audience: Target audience description
            tone: Desired tone for translation
            quality: Translation quality level
            preserve_timing: Whether to preserve timestamp accuracy
            
        Returns:
            Dictionary with translation result and metadata
        """
        print(Colors.BLUE + f"\n🔄 Translation indítása: {context} kontextus → {target_language}" + Colors.ENDC)
        
        try:
            # Check if chunking is needed for long scripts
            if self.chunker.needs_chunking(script_text):
                return self._translate_with_chunking(
                    script_text, target_language, context, audience, tone, quality, preserve_timing
                )
            else:
                return self._translate_single_chunk(
                    script_text, target_language, context, audience, tone, quality, preserve_timing
                )
                
        except Exception as e:
            print(Colors.FAIL + f"✗ Translation hiba: {e}" + Colors.ENDC)
            return None
    
    def _translate_with_chunking(self, script_text: str, target_language: str, 
                               context: str, audience: str, tone: str,
                               quality: TranslationQuality, preserve_timing: bool) -> Optional[Dict]:
        """Handle translation of long scripts using chunking."""
        print(Colors.YELLOW + f"📑 Hosszú script észlelve ({len(script_text)} karakter)" + Colors.ENDC)
        
        chunks = self.chunker.chunk_text(script_text)
        print(Colors.CYAN + f"   ├─ {len(chunks)} chunk létrehozva translation-höz" + Colors.ENDC)
        
        translated_chunks = []
        total_cost = 0.0
        total_time = 0.0
        
        for i, (chunk_text, start_pos, end_pos) in enumerate(chunks):
            print(Colors.CYAN + f"   ├─ Translation chunk {i+1}/{len(chunks)} ({len(chunk_text)} kar.)" + Colors.ENDC)
            
            result = self._translate_single_chunk_internal(
                chunk_text, target_language, context, audience, tone, quality, preserve_timing
            )
            
            if result is None:
                print(Colors.WARNING + f"   ✗ Chunk {i+1} translation sikertelen" + Colors.ENDC)
                return None
                
            translated_chunks.append(result['translated_text'])
            total_cost += result.get('estimated_cost', 0.0)
            total_time += result.get('processing_time', 0.0)
            
            print(Colors.GREEN + f"   ✓ Chunk {i+1} lefordítva" + Colors.ENDC)
        
        # Merge translated chunks
        print(Colors.CYAN + "   ├─ Translation chunk-ok egyesítése..." + Colors.ENDC)
        merged_translation = self._merge_translated_chunks(translated_chunks, chunks)
        
        print(Colors.GREEN + f"   ✓ Chunked translation kész: {len(chunks)} chunk összevonva" + Colors.ENDC)
        
        return {
            'translated_text': merged_translation,
            'original_text': script_text,
            'source_language': 'hu-HU',
            'target_language': target_language,
            'translation_context': context,
            'word_count': len(merged_translation.split()),
            'estimated_cost': total_cost,
            'processing_time': total_time,
            'chunks_processed': len(chunks),
            'method': 'chunked'
        }
    
    def _translate_single_chunk(self, script_text: str, target_language: str,
                              context: str, audience: str, tone: str,
                              quality: TranslationQuality, preserve_timing: bool) -> Optional[Dict]:
        """Handle translation of single chunk scripts."""
        result = self._translate_single_chunk_internal(
            script_text, target_language, context, audience, tone, quality, preserve_timing
        )
        
        if result:
            result['method'] = 'single_pass'
            
        return result
    
    def _translate_single_chunk_internal(self, chunk_text: str, target_language: str,
                                       context: str, audience: str, tone: str,
                                       quality: TranslationQuality, preserve_timing: bool) -> Optional[Dict]:
        """Internal method to translate a single chunk of text."""
        start_time = datetime.datetime.now()
        
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel, GenerationConfig
            
            # Build context-aware prompt
            prompt = self._build_translation_prompt(
                chunk_text, target_language, context, audience, tone, quality, preserve_timing
            )
            
            # Get model combinations to try
            models_to_try = VertexAIModels.get_auto_detect_order()
            regions = ["us-central1", "us-east1", "us-west1", "europe-west4"]
            
            for region in regions:
                for model_name in models_to_try:
                    try:
                        # Initialize Vertex AI
                        vertexai.init(project=self.project_id, location=region)
                        model = GenerativeModel(model_name)
                        
                        # Configure generation parameters based on quality
                        generation_config = self._get_generation_config(quality)
                        
                        # Generate translation
                        response = model.generate_content(prompt, generation_config=generation_config)
                        translated_text = response.text.strip()
                        
                        # Validate translation
                        if self._validate_translation(chunk_text, translated_text, preserve_timing):
                            processing_time = (datetime.datetime.now() - start_time).total_seconds()
                            
                            return {
                                'translated_text': translated_text,
                                'original_text': chunk_text,
                                'source_language': 'hu-HU',
                                'target_language': target_language,
                                'translation_context': context,
                                'word_count': len(translated_text.split()),
                                'estimated_cost': self._estimate_translation_cost(chunk_text),
                                'processing_time': processing_time,
                                'model_used': model_name,
                                'region_used': region
                            }
                        else:
                            print(Colors.WARNING + f"   ⚠ Translation validation failed for {model_name}@{region}" + Colors.ENDC)
                            continue
                            
                    except Exception as e:
                        print(Colors.WARNING + f"   ✗ {model_name}@{region}: {str(e)[:100]}..." + Colors.ENDC)
                        continue
            
            raise Exception("Nem sikerült egyetlen modellel sem lefordítani a szöveget")
            
        except ImportError:
            print(Colors.WARNING + "⚠ Vertex AI könyvtár nincs telepítve!" + Colors.ENDC)
            return None
        except Exception as e:
            print(Colors.FAIL + f"✗ Translation hiba: {e}" + Colors.ENDC)
            return None
    
    def _build_translation_prompt(self, script_text: str, target_language: str,
                                context: str, audience: str, tone: str,
                                quality: TranslationQuality, preserve_timing: bool) -> str:
        """Build context-aware translation prompt."""
        
        context_info = self.context_instructions.get(context, self.context_instructions[TranslationContext.CASUAL])
        
        prompt = f"""Fordítsd le ezt a magyar nyelvű időzített scriptet {target_language} nyelvre.

KRITIKUS: Ez egy IDŐZÍTETT SCRIPT audio szintézishez. Az időzítés SZENT!

FORDÍTÁSI KONTEXTUS:
- Tartalom típusa: {context}
- Célközönség: {audience}
- Kívánt hangvétel: {tone}
- Speciális utasítás: {context_info['instruction']}
- Terminológia: {context_info['terminology']}
- Hangulat: {context_info['tone']}

IDŐZÍTÉS MEGŐRZÉSI SZABÁLYOK:
1. MINDEN időbélyeget [HH:MM:SS] PONTOSAN őrizz meg!
2. A fordított szöveg UGYANAZOKBA az időslotokba kell illeszkedjen.
3. Ha a fordítás hosszabb, oszd fel a sorokat, de TARTSD meg az időbélyegeket.
4. Ha a fordítás rövidebb, összevonhatsz szomszédos sorokat.
5. Szünet jelölők megőrzése: [levegővétel] → [breath], [rövid szünet] → [short pause], [hosszú szünet] → [long pause], [TÉMAVÁLTÁS] → [TOPIC CHANGE]

FORDÍTÁSI MINŐSÉG: {quality.value.upper()}
{'- Gyors fordítás, hatékonyság prioritás' if quality == TranslationQuality.FAST else ''}
{'- Kiegyensúlyozott sebesség és minőség' if quality == TranslationQuality.BALANCED else ''}
{'- Magas minőség, pontosság prioritás' if quality == TranslationQuality.HIGH else ''}

EREDETI MAGYAR SCRIPT:
{script_text}

LEFORDÍTOTT {target_language.upper()} SCRIPT:"""

        return prompt
    
    def _get_generation_config(self, quality: TranslationQuality) -> object:
        """Get generation configuration based on quality setting."""
        try:
            from vertexai.generative_models import GenerationConfig
            
            if quality == TranslationQuality.FAST:
                return GenerationConfig(
                    temperature=0.1,  # Very consistent
                    max_output_tokens=8192,
                    top_p=0.8,
                )
            elif quality == TranslationQuality.HIGH:
                return GenerationConfig(
                    temperature=0.3,  # More creative but controlled
                    max_output_tokens=8192,
                    top_p=0.9,
                )
            else:  # BALANCED
                return GenerationConfig(
                    temperature=0.2,  # Balanced
                    max_output_tokens=8192,
                    top_p=0.85,
                )
        except ImportError:
            # Fallback if vertexai not available
            return None
    
    def _validate_translation(self, original: str, translated: str, preserve_timing: bool) -> bool:
        """Validate translation quality and timing preservation."""
        if not translated or len(translated.strip()) == 0:
            return False
            
        # Check for obvious translation failures
        if translated == original:  # No translation happened
            return False
        
        if preserve_timing:
            # Check that timestamps are preserved
            original_timestamps = re.findall(r'\[\d+:\d+:\d+\]', original)
            translated_timestamps = re.findall(r'\[\d+:\d+:\d+\]', translated)
            
            if len(original_timestamps) != len(translated_timestamps):
                return False
            
            # Check that timestamps match exactly
            if original_timestamps != translated_timestamps:
                return False
        
        # Check for reasonable length (translation shouldn't be too short or too long)
        original_words = len(original.split())
        translated_words = len(translated.split())
        
        if translated_words < original_words * 0.3:  # Too short
            return False
        if translated_words > original_words * 3.0:  # Too long
            return False
            
        return True
    
    def _merge_translated_chunks(self, translated_chunks: List[str], 
                               chunk_info: List[Tuple[str, int, int]]) -> str:
        """Merge translated chunks back into single script."""
        if not translated_chunks:
            return ""
        
        if len(translated_chunks) == 1:
            return translated_chunks[0]
        
        merged_lines = []
        
        for i, translated_chunk in enumerate(translated_chunks):
            lines = [line.strip() for line in translated_chunk.split('\n') if line.strip()]
            
            # Add chunk separator for debugging (except first chunk)
            if i > 0 and lines:
                merged_lines.append(f"[--- Translation Chunk {i+1} continues ---]")
            
            merged_lines.extend(lines)
        
        return '\n'.join(merged_lines)
    
    def _estimate_translation_cost(self, text: str) -> float:
        """Estimate translation cost based on text length."""
        # Rough estimate: $0.20 per 1M characters for Vertex AI translation
        character_count = len(text)
        cost_per_million_chars = 0.20
        
        return (character_count / 1_000_000) * cost_per_million_chars
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported target languages."""
        return [
            {"code": "en-US", "name": "English (US)", "native": "English"},
            {"code": "en-GB", "name": "English (UK)", "native": "English"},
            {"code": "de-DE", "name": "German", "native": "Deutsch"},
            {"code": "fr-FR", "name": "French", "native": "Français"},
            {"code": "es-ES", "name": "Spanish", "native": "Español"},
            {"code": "it-IT", "name": "Italian", "native": "Italiano"},
            {"code": "pt-PT", "name": "Portuguese", "native": "Português"},
            {"code": "ru-RU", "name": "Russian", "native": "Русский"},
            {"code": "zh-CN", "name": "Chinese (Simplified)", "native": "中文"},
            {"code": "ja-JP", "name": "Japanese", "native": "日本語"},
            {"code": "ko-KR", "name": "Korean", "native": "한국어"},
            {"code": "ar-SA", "name": "Arabic", "native": "العربية"},
            {"code": "hi-IN", "name": "Hindi", "native": "हिन्दी"},
            {"code": "th-TH", "name": "Thai", "native": "ไทย"},
            {"code": "tr-TR", "name": "Turkish", "native": "Türkçe"},
            {"code": "pl-PL", "name": "Polish", "native": "Polski"},
            {"code": "nl-NL", "name": "Dutch", "native": "Nederlands"},
            {"code": "sv-SE", "name": "Swedish", "native": "Svenska"},
            {"code": "da-DK", "name": "Danish", "native": "Dansk"},
            {"code": "no-NO", "name": "Norwegian", "native": "Norsk"}
        ]