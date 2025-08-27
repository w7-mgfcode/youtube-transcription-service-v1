"""Input validation utilities."""

import re
from typing import Tuple, Optional, Dict, List
from .colors import Colors
from ..config import TranslationContext
from ..core.tts_factory import TTSFactory
from ..core.tts_interface import TTSProvider
from ..models.dubbing import TTSProviderEnum


def is_valid_bucket_name(name: str) -> bool:
    """
    Validate GCS bucket name format.
    
    Args:
        name: Bucket name to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not name or len(name) < 3 or len(name) > 63:
        return False
    
    # Check pattern: lowercase letters, numbers, dashes, dots
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", name):
        return False
    
    # Additional restrictions
    if ".." in name or name.startswith("goog"):
        return False
    
    return True


def is_valid_youtube_url(url: str) -> bool:
    """
    Validate YouTube URL format.
    
    Args:
        url: URL to validate
    
    Returns:
        True if valid YouTube URL, False otherwise
    """
    if not url:
        return False
    
    # Check for common YouTube URL patterns
    youtube_patterns = [
        r'youtube\.com/watch',
        r'youtu\.be/',
        r'youtube\.com/embed/',
        r'youtube\.com/v/',
    ]
    
    return any(re.search(pattern, url) for pattern in youtube_patterns)


def get_user_inputs() -> Tuple[str, bool, bool]:
    """
    Get user inputs for transcription job (preserving v25.py behavior).
    
    Returns:
        Tuple of (video_url, test_mode, breath_detection)
    """
    # Test mode input
    test_input = input(Colors.BOLD + "🧪 Teszt mód? (csak első 60 másodperc) [i/n]: " + Colors.ENDC).lower().strip()
    test_mode = test_input == 'i'
    
    # Breath detection input
    breath_input = input(Colors.BOLD + "💨 Levegővétel jelölés? [i/n]: " + Colors.ENDC).lower().strip()
    breath_detection = breath_input != 'n'  # Default: yes
    
    # YouTube URL input with validation
    while True:
        video_url = input(Colors.BOLD + "📺 YouTube videó URL: " + Colors.ENDC).strip()
        if is_valid_youtube_url(video_url):
            break
        print(Colors.FAIL + "❌ Érvénytelen YouTube URL! Próbáld újra." + Colors.ENDC)
    
    return video_url, test_mode, breath_detection


def get_bucket_name_interactive(default_bucket: str) -> str:
    """
    Get GCS bucket name interactively with validation.
    
    Args:
        default_bucket: Default bucket name to use
    
    Returns:
        Valid bucket name
    """
    bucket = default_bucket.strip()
    
    if bucket == "YOUR_BUCKET_NAME" or not is_valid_bucket_name(bucket):
        print(Colors.WARNING + "⚠ Nincs érvényes GCS bucket név beállítva." + Colors.ENDC)
        
        while True:
            user_input = input("Add meg a Google Cloud Storage bucket nevét: ").strip()
            if is_valid_bucket_name(user_input):
                return user_input
            print(Colors.FAIL + "✗ Hibás bucket név. Csak kisbetű, szám, kötőjel engedélyezett." + Colors.ENDC)
    
    return bucket


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from YouTube URL.
    
    Args:
        url: YouTube URL
    
    Returns:
        Video ID if found, None otherwise
    """
    # YouTube URL patterns for video ID extraction
    patterns = [
        r'youtube\.com/watch\?v=([^&]+)',
        r'youtu\.be/([^?]+)',
        r'youtube\.com/embed/([^?]+)',
        r'youtube\.com/v/([^?]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def get_dubbing_preferences() -> Optional[Dict]:
    """
    Get user preferences for dubbing workflow.
    
    Returns:
        Dictionary with dubbing preferences or None if dubbing not wanted
    """
    print(Colors.BOLD + "\n" + "="*60 + Colors.ENDC)
    print(Colors.BOLD + Colors.CYAN + "        🎬 MULTILINGUAL DUBBING OPCIÓK" + Colors.ENDC)
    print(Colors.BOLD + "="*60 + Colors.ENDC)
    
    # Ask if user wants dubbing
    enable_dubbing = input(Colors.BOLD + "\n🌍 Szeretnéd a videót szinkronizálni más nyelvre? [i/n]: " + Colors.ENDC).lower().strip()
    
    if enable_dubbing != 'i':
        return None
    
    preferences = {}
    
    # Get target language
    target_language = get_target_language()
    preferences['target_language'] = target_language
    
    # Get translation context
    context = get_translation_context()
    preferences['translation_context'] = context
    
    # Ask about voice synthesis
    enable_voice = input(Colors.BOLD + "🎤 Szeretnél hangszintézist is? [i/n]: " + Colors.ENDC).lower().strip()
    preferences['enable_synthesis'] = (enable_voice == 'i')
    
    if preferences['enable_synthesis']:
        # TTS provider selection
        preferences['tts_provider'] = get_tts_provider_selection()
        
        # Voice selection will be handled separately
        preferences['voice_id'] = None
        
        # Ask about video muxing
        enable_video = input(Colors.BOLD + "🎞️  Szeretnéd a végleges szinkronizált videót? [i/n]: " + Colors.ENDC).lower().strip()
        preferences['enable_video_muxing'] = (enable_video == 'i')
    else:
        preferences['enable_video_muxing'] = False
    
    # Ask about preview mode
    preview_only = input(Colors.BOLD + "🔍 Csak előnézet mód? (gyorsabb, csak hang) [i/n]: " + Colors.ENDC).lower().strip()
    preferences['preview_mode'] = (preview_only == 'i')
    
    return preferences


def get_target_language() -> str:
    """
    Get target language selection from user.
    
    Returns:
        Selected language code
    """
    languages = [
        ("en-US", "Angol (amerikai)"),
        ("en-GB", "Angol (brit)"), 
        ("de-DE", "Német"),
        ("es-ES", "Spanyol"),
        ("fr-FR", "Francia"),
        ("it-IT", "Olasz"),
        ("pt-PT", "Portugál"),
        ("ru-RU", "Orosz"),
        ("ja-JP", "Japán"),
        ("ko-KR", "Koreai"),
        ("zh-CN", "Kínai (egyszerűsített)"),
        ("pl-PL", "Lengyel"),
        ("nl-NL", "Holland"),
        ("sv-SE", "Svéd"),
        ("da-DK", "Dán"),
        ("no-NO", "Norvég"),
        ("fi-FI", "Finn"),
        ("cs-CZ", "Cseh"),
        ("sk-SK", "Szlovák"),
        ("ro-RO", "Román")
    ]
    
    print(Colors.CYAN + "\n🌍 Válaszd ki a célnyelvet:" + Colors.ENDC)
    
    # Show languages in two columns
    for i in range(0, len(languages), 2):
        left = f"   {i+1:2}. {languages[i][1]:<20}"
        right = f"{i+2:2}. {languages[i+1][1]}" if i+1 < len(languages) else ""
        print(Colors.CYAN + left + right + Colors.ENDC)
    
    while True:
        try:
            print(Colors.BOLD + f"\nVálasztás [1-{len(languages)}, Enter = 1]: " + Colors.ENDC, end="")
            response = input().strip()
            
            if response == "":
                # Default to English (US)
                selected = languages[0]
                print(Colors.GREEN + f"✓ Kiválasztva: {selected[1]}" + Colors.ENDC)
                return selected[0]
            
            choice = int(response)
            if 1 <= choice <= len(languages):
                selected = languages[choice - 1]
                print(Colors.GREEN + f"✓ Kiválasztva: {selected[1]}" + Colors.ENDC)
                return selected[0]
            else:
                print(Colors.WARNING + f"Kérlek válassz 1 és {len(languages)} között!" + Colors.ENDC)
        except ValueError:
            print(Colors.WARNING + "Kérlek adj meg egy számot!" + Colors.ENDC)
        except (EOFError, KeyboardInterrupt):
            # Default selection on interrupt
            return languages[0][0]


def get_translation_context() -> str:
    """
    Get translation context selection from user.
    
    Returns:
        Selected context string
    """
    contexts = [
        (TranslationContext.CASUAL, "Beszélgetős/informális"),
        (TranslationContext.EDUCATIONAL, "Oktatási/tudományos"),
        (TranslationContext.MARKETING, "Marketing/reklám"),
        (TranslationContext.SPIRITUAL, "Spirituális/motivációs"),
        (TranslationContext.LEGAL, "Jogi/formális"),
        (TranslationContext.NEWS, "Hírek/újságírói"),
        (TranslationContext.SCIENTIFIC, "Tudományos/technikai")
    ]
    
    print(Colors.CYAN + "\n🎯 Válaszd ki a tartalom típusát (fordítási kontextus):" + Colors.ENDC)
    
    for i, (context, description) in enumerate(contexts, 1):
        color = Colors.GREEN if context == TranslationContext.CASUAL else Colors.CYAN
        print(color + f"   {i}. {description}" + Colors.ENDC)
    
    while True:
        try:
            print(Colors.BOLD + f"\nVálasztás [1-{len(contexts)}, Enter = 1]: " + Colors.ENDC, end="")
            response = input().strip()
            
            if response == "":
                # Default to casual
                selected = contexts[0]
                print(Colors.GREEN + f"✓ Kiválasztva: {selected[1]}" + Colors.ENDC)
                return selected[0]
            
            choice = int(response)
            if 1 <= choice <= len(contexts):
                selected = contexts[choice - 1]
                print(Colors.GREEN + f"✓ Kiválasztva: {selected[1]}" + Colors.ENDC)
                return selected[0]
            else:
                print(Colors.WARNING + f"Kérlek válassz 1 és {len(contexts)} között!" + Colors.ENDC)
        except ValueError:
            print(Colors.WARNING + "Kérlek adj meg egy számot!" + Colors.ENDC)
        except (EOFError, KeyboardInterrupt):
            # Default selection on interrupt
            return contexts[0][0]


def get_tts_provider_selection() -> TTSProviderEnum:
    """
    Get TTS provider selection from user with Hungarian interface.
    
    Returns:
        Selected TTS provider enum
    """
    try:
        print(Colors.BOLD + "\n" + "="*60 + Colors.ENDC)
        print(Colors.BOLD + Colors.CYAN + "        🎤 TTS SZOLGÁLTATÓ KIVÁLASZTÁSA" + Colors.ENDC)
        print(Colors.BOLD + "="*60 + Colors.ENDC)
        
        # Get provider information and costs
        provider_info = TTSFactory.get_provider_info()
        available_providers = TTSFactory.get_available_providers()
        
        print(Colors.CYAN + "\n📊 Elérhető TTS szolgáltatók:" + Colors.ENDC)
        print()
        
        providers_menu = []
        
        # Show available providers with status and costs
        for i, (provider_id, info) in enumerate(provider_info.items(), 1):
            status = "✅" if info["available"] else "❌"
            cost = f"${info['cost_per_1k_chars']:.4f}/1K karakter" if info["available"] else "N/A"
            voice_count = f"{info['voice_count']} hang" if info["available"] else "N/A"
            
            if provider_id == "elevenlabs":
                name = "ElevenLabs - Prémium neurális hangok"
                note = "(drága, de kiváló minőség)"
            elif provider_id == "google_tts":
                name = "Google Cloud TTS - Kiváló minőség"
                savings = 90 if info["available"] and provider_info.get("elevenlabs", {}).get("cost_per_1k_chars", 0) > 0 else 0
                note = f"(90%+ olcsóbb)" if savings > 0 else "(költséghatékony)"
            else:
                name = info["name"]
                note = ""
            
            print(f"{status} {i}. {name}")
            print(f"      💰 Költség: {cost}")
            print(f"      🎭 Hangok: {voice_count} {note}")
            
            if not info["available"] and "error" in info:
                print(Colors.WARNING + f"      ⚠ Hiba: {info['error']}" + Colors.ENDC)
            
            print()
            providers_menu.append((provider_id, info["available"]))
        
        # Auto-selection option
        print(f"✨ {len(providers_menu) + 1}. Automatikus kiválasztás költség alapján")
        print("      🤖 A rendszer automatikusan a legköltséghatékonyabb szolgáltatót választja")
        print()
        
        # Show cost comparison if both providers are available
        if len(available_providers) >= 2:
            print(Colors.GREEN + "💡 Költség összehasonlítás (1000 karakterre):" + Colors.ENDC)
            elevenlabs_cost = provider_info.get("elevenlabs", {}).get("cost_per_1k_chars", 0)
            google_cost = provider_info.get("google_tts", {}).get("cost_per_1k_chars", 0)
            
            if elevenlabs_cost > 0 and google_cost > 0:
                savings = ((elevenlabs_cost - google_cost) / elevenlabs_cost) * 100
                print(f"    ElevenLabs: ${elevenlabs_cost:.4f}")
                print(f"    Google TTS: ${google_cost:.4f}")
                print(Colors.GREEN + f"    💰 Megtakarítás: {savings:.1f}%" + Colors.ENDC)
            print()
        
        while True:
            try:
                max_choice = len(providers_menu) + 1
                print(Colors.BOLD + f"Választás [1-{max_choice}, Enter = automatikus]: " + Colors.ENDC, end="")
                response = input().strip()
                
                if response == "":
                    print(Colors.GREEN + "✓ Automatikus kiválasztás (költség alapú optimalizálás)" + Colors.ENDC)
                    return TTSProviderEnum.AUTO
                
                choice = int(response)
                
                if choice == max_choice:
                    print(Colors.GREEN + "✓ Automatikus kiválasztás (költség alapú optimalizálás)" + Colors.ENDC)
                    return TTSProviderEnum.AUTO
                elif 1 <= choice <= len(providers_menu):
                    provider_id, available = providers_menu[choice - 1]
                    
                    if not available:
                        print(Colors.WARNING + f"⚠ A {provider_id} szolgáltató nem elérhető. Válassz másikat!" + Colors.ENDC)
                        continue
                    
                    if provider_id == "elevenlabs":
                        provider_enum = TTSProviderEnum.ELEVENLABS
                        name = "ElevenLabs"
                    elif provider_id == "google_tts":
                        provider_enum = TTSProviderEnum.GOOGLE_TTS  
                        name = "Google Cloud TTS"
                    else:
                        provider_enum = TTSProviderEnum.AUTO
                        name = "Auto"
                    
                    print(Colors.GREEN + f"✓ Kiválasztva: {name}" + Colors.ENDC)
                    return provider_enum
                else:
                    print(Colors.WARNING + f"⚠ Kérlek 1 és {max_choice} közötti számot válassz!" + Colors.ENDC)
                    
            except ValueError:
                print(Colors.WARNING + "⚠ Kérlek érvényes számot adj meg!" + Colors.ENDC)
            except KeyboardInterrupt:
                print(Colors.WARNING + "\n⚠ Megszakítva. Automatikus kiválasztás használva." + Colors.ENDC)
                return TTSProviderEnum.AUTO
                
    except Exception as e:
        print(Colors.WARNING + f"⚠ TTS szolgáltató kiválasztás sikertelen: {e}" + Colors.ENDC)
        print(Colors.CYAN + "Automatikus kiválasztás használva." + Colors.ENDC)
        return TTSProviderEnum.AUTO


def get_voice_selection(synthesizer, tts_provider: TTSProviderEnum = TTSProviderEnum.ELEVENLABS) -> Optional[str]:
    """
    Get voice selection from available TTS provider voices.
    
    Args:
        synthesizer: TTS synthesizer instance (can be any provider)
        tts_provider: Selected TTS provider enum
    
    Returns:
        Selected voice ID or None if selection failed
    """
    try:
        provider_name = "Google TTS" if tts_provider == TTSProviderEnum.GOOGLE_TTS else "ElevenLabs"
        print(Colors.CYAN + f"\n🎤 {provider_name} hangok lekérése..." + Colors.ENDC)
        
        # Use the new interface if available
        if hasattr(synthesizer, 'get_available_voices'):
            # New unified interface (returns VoiceProfile objects)
            voice_profiles = synthesizer.get_available_voices()
            voices = voice_profiles[:10]  # Show top 10 voices
            
            print(Colors.CYAN + f"\n🎭 Válaszd ki a {provider_name} hangot:" + Colors.ENDC)
            
            for i, voice in enumerate(voices, 1):
                name = voice.name
                language = voice.language
                gender = voice.gender
                
                # Add visual indicators based on provider and voice characteristics
                if tts_provider == TTSProviderEnum.GOOGLE_TTS:
                    if 'Neural2' in name:
                        indicator = "🧠"  # Neural voice
                    elif 'WaveNet' in name:
                        indicator = "🌊"  # WaveNet voice
                    elif 'Standard' in name:
                        indicator = "📢"  # Standard voice
                    else:
                        indicator = "🎙️"
                else:
                    # ElevenLabs indicators
                    if voice.is_premium:
                        indicator = "⭐"
                    elif 'professional' in name.lower():
                        indicator = "💼"
                    elif 'conversational' in name.lower():
                        indicator = "💬"
                    else:
                        indicator = "🎙️"
                
                premium_mark = " ⭐" if voice.is_premium else ""
                print(Colors.CYAN + f"   {i:2}. {indicator} {name} ({gender}, {language}){premium_mark}" + Colors.ENDC)
        
        else:
            # Legacy ElevenLabs interface (for backward compatibility)
            voices_response = synthesizer.list_available_voices()
            
            if not voices_response or 'voices' not in voices_response:
                print(Colors.WARNING + "⚠ Nem sikerült lekérni a hangokat. Alapértelmezett hang lesz használva." + Colors.ENDC)
                return None
            
            voices = voices_response['voices'][:10]  # Show top 10 voices
            
            print(Colors.CYAN + "\n🎭 Válaszd ki a hangot:" + Colors.ENDC)
            
            for i, voice in enumerate(voices, 1):
                name = voice.get('name', 'Unknown')
                category = voice.get('category', 'general')
                gender = voice.get('labels', {}).get('gender', 'Unknown')
                
                # Add visual indicators for different categories
                if 'professional' in category.lower():
                    indicator = "💼"
                elif 'conversational' in category.lower():
                    indicator = "💬"
                elif 'narrative' in category.lower():
                    indicator = "📚"
                else:
                    indicator = "🎙️"
                
                print(Colors.CYAN + f"   {i:2}. {indicator} {name} ({gender}, {category})" + Colors.ENDC)
        
        while True:
            try:
                print(Colors.BOLD + f"\nVálasztás [1-{len(voices)}, Enter = 1]: " + Colors.ENDC, end="")
                response = input().strip()
                
                if response == "":
                    # Default to first voice
                    selected = voices[0]
                    if hasattr(selected, 'voice_id'):
                        # New interface (VoiceProfile object)
                        print(Colors.GREEN + f"✓ Kiválasztva: {selected.name}" + Colors.ENDC)
                        return selected.voice_id
                    else:
                        # Legacy interface (dict)
                        print(Colors.GREEN + f"✓ Kiválasztva: {selected.get('name', 'Unknown')}" + Colors.ENDC)
                        return selected.get('voice_id')
                
                choice = int(response)
                if 1 <= choice <= len(voices):
                    selected = voices[choice - 1]
                    if hasattr(selected, 'voice_id'):
                        # New interface (VoiceProfile object)
                        print(Colors.GREEN + f"✓ Kiválasztva: {selected.name}" + Colors.ENDC)
                        return selected.voice_id
                    else:
                        # Legacy interface (dict)
                        print(Colors.GREEN + f"✓ Kiválasztva: {selected.get('name', 'Unknown')}" + Colors.ENDC)
                        return selected.get('voice_id')
                else:
                    print(Colors.WARNING + f"Kérlek válassz 1 és {len(voices)} között!" + Colors.ENDC)
            except ValueError:
                print(Colors.WARNING + "Kérlek adj meg egy számot!" + Colors.ENDC)
            except (EOFError, KeyboardInterrupt):
                # Default selection on interrupt
                if voices:
                    selected = voices[0]
                    if hasattr(selected, 'voice_id'):
                        print(Colors.WARNING + f"\n⚠ Megszakítva. Első hang használva: {selected.name}" + Colors.ENDC)
                        return selected.voice_id
                    else:
                        print(Colors.WARNING + f"\n⚠ Megszakítva. Első hang használva: {selected.get('name', 'Unknown')}" + Colors.ENDC)
                        return selected.get('voice_id')
                return None
                
    except Exception as e:
        print(Colors.WARNING + f"⚠ Hiba a hangok lekérésekor: {e}" + Colors.ENDC)
        return None


def show_dubbing_cost_estimate(dubbing_service, transcript_length: int, preferences: Dict) -> bool:
    """
    Show cost estimation for dubbing and get user confirmation.
    
    Args:
        dubbing_service: DubbingService instance
        transcript_length: Length of transcript in characters
        preferences: Dubbing preferences
    
    Returns:
        True if user wants to proceed, False otherwise
    """
    try:
        print(Colors.CYAN + "\n💰 Költségbecslés számítása..." + Colors.ENDC)
        
        # Create a minimal DubbingRequest for cost estimation
        from ..models.dubbing import DubbingRequest, TTSProviderEnum, TranslationContextEnum
        from pydantic import HttpUrl
        
        dummy_request = DubbingRequest(
            url=HttpUrl("https://youtube.com/watch?v=dummy"),
            enable_translation=True,
            target_language=preferences.get('target_language', 'en-US'),
            enable_synthesis=preferences.get('enable_synthesis', False),
            enable_video_muxing=preferences.get('enable_video_muxing', False),
            tts_provider=preferences.get('tts_provider', TTSProviderEnum.AUTO),
            translation_context=TranslationContextEnum.CASUAL,
            existing_transcript="x" * transcript_length  # Mock transcript for length
        )
        
        estimate = dubbing_service.estimate_dubbing_cost(dummy_request)
        
        print(Colors.YELLOW + "\n" + "="*50 + Colors.ENDC)
        print(Colors.YELLOW + "              💰 KÖLTSÉGBECSLÉS" + Colors.ENDC)
        print(Colors.YELLOW + "="*50 + Colors.ENDC)
        
        print(Colors.CYAN + f"📝 Átirat hossza: {transcript_length:,} karakter" + Colors.ENDC)
        
        # Show breakdown
        breakdown = estimate.get('breakdown', {})
        if breakdown:
            print(Colors.CYAN + "\n💸 Költség lebontás:" + Colors.ENDC)
            
            if 'translation_cost' in breakdown:
                print(Colors.CYAN + f"   ├─ Fordítás: ${breakdown['translation_cost']:.4f}" + Colors.ENDC)
            
            if 'synthesis_cost' in breakdown:
                print(Colors.CYAN + f"   ├─ Hangszintézis: ${breakdown['synthesis_cost']:.4f}" + Colors.ENDC)
            
            if 'processing_cost' in breakdown:
                print(Colors.CYAN + f"   └─ Videó feldolgozás: ${breakdown['processing_cost']:.4f}" + Colors.ENDC)
        
        total_cost = estimate.get('total_cost_usd', 0.0)
        processing_time = estimate.get('estimated_time_minutes', 5)
        
        print(Colors.BOLD + Colors.GREEN + f"\n💵 Teljes költség: ${total_cost:.4f}" + Colors.ENDC)
        print(Colors.CYAN + f"⏱️  Becsült idő: {processing_time:.1f} perc" + Colors.ENDC)
        
        print(Colors.YELLOW + "="*50 + Colors.ENDC)
        
        # Get confirmation
        if total_cost > 0.05:  # Show warning for costs over 5 cents
            print(Colors.WARNING + f"\nFigyelem: A szinkronizálás költsége ${total_cost:.4f} lesz." + Colors.ENDC)
        
        response = input(Colors.BOLD + "Folytatod a szinkronizálást? (i/n) [i]: " + Colors.ENDC).strip().lower()
        
        if response and response.startswith('n'):
            print(Colors.WARNING + "Szinkronizálás megszakítva." + Colors.ENDC)
            return False
            
        print(Colors.GREEN + "✓ Szinkronizálás jóváhagyva" + Colors.ENDC)
        return True
        
    except Exception as e:
        print(Colors.WARNING + f"⚠ Költségbecslés hiba: {e}" + Colors.ENDC)
        print(Colors.WARNING + "Folytatás alapértelmezett becsléssel..." + Colors.ENDC)
        return True