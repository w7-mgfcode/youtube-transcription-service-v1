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
    Get user preferences for dubbing workflow with enhanced error handling.
    
    Returns:
        Dictionary with dubbing preferences or None if dubbing not wanted
    """
    try:
        print(Colors.BOLD + "\n" + "="*60 + Colors.ENDC)
        print(Colors.BOLD + Colors.CYAN + "        🎬 MULTILINGUAL DUBBING OPCIÓK" + Colors.ENDC)
        print(Colors.BOLD + "="*60 + Colors.ENDC)
        
        # Ask if user wants dubbing with better error handling
        try:
            enable_dubbing = input(Colors.BOLD + "\n🌍 Szeretnéd a videót szinkronizálni más nyelvre? [i/n]: " + Colors.ENDC).lower().strip()
        except (EOFError, KeyboardInterrupt):
            print(Colors.WARNING + "\n⚠ Megszakítva. Szinkronizálás kihagyva." + Colors.ENDC)
            return None
        
        if enable_dubbing != 'i':
            print(Colors.CYAN + "✓ Szinkronizálás kihagyva." + Colors.ENDC)
            return None
        
        print(Colors.GREEN + "✅ Szinkronizálás engedélyezve. Beállítások konfigurálása..." + Colors.ENDC)
        preferences = {}
        
        # Get target language with error handling
        try:
            print(Colors.CYAN + "\n📍 1. lépés: Célnyelv kiválasztása" + Colors.ENDC)
            target_language = get_target_language()
            preferences['target_language'] = target_language
            print(Colors.GREEN + f"✓ Célnyelv beállítva: {target_language}" + Colors.ENDC)
        except Exception as e:
            print(Colors.WARNING + f"⚠ Célnyelv kiválasztás hiba: {e}. Angol (US) használva." + Colors.ENDC)
            preferences['target_language'] = 'en-US'
        
        # Get translation context with error handling
        try:
            print(Colors.CYAN + "\n📍 2. lépés: Fordítási kontextus" + Colors.ENDC)
            context = get_translation_context()
            preferences['translation_context'] = context
            print(Colors.GREEN + f"✓ Kontextus beállítva: {context}" + Colors.ENDC)
        except Exception as e:
            print(Colors.WARNING + f"⚠ Kontextus kiválasztás hiba: {e}. Casual használva." + Colors.ENDC)
            preferences['translation_context'] = 'casual'
        
        # Ask about voice synthesis with error handling
        try:
            print(Colors.CYAN + "\n📍 3. lépés: Hangszintézis opciók" + Colors.ENDC)
            enable_voice = input(Colors.BOLD + "🎤 Szeretnél hangszintézist is? [i/n]: " + Colors.ENDC).lower().strip()
            preferences['enable_synthesis'] = (enable_voice == 'i')
            
            if preferences['enable_synthesis']:
                print(Colors.GREEN + "✅ Hangszintézis engedélyezve" + Colors.ENDC)
                
                # TTS provider selection with error handling
                try:
                    print(Colors.CYAN + "\n📍 4. lépés: TTS szolgáltató kiválasztása" + Colors.ENDC)
                    preferences['tts_provider'] = get_tts_provider_selection()
                    print(Colors.GREEN + f"✓ TTS provider beállítva: {preferences['tts_provider']}" + Colors.ENDC)
                except Exception as e:
                    print(Colors.WARNING + f"⚠ TTS provider hiba: {e}. AUTO használva." + Colors.ENDC)
                    preferences['tts_provider'] = TTSProviderEnum.AUTO
                
                # Voice selection will be handled separately
                preferences['voice_id'] = None
                
                # Ask about video muxing with error handling
                try:
                    enable_video = input(Colors.BOLD + "🎞️  Szeretnéd a végleges szinkronizált videót? [i/n]: " + Colors.ENDC).lower().strip()
                    preferences['enable_video_muxing'] = (enable_video == 'i')
                    
                    if preferences['enable_video_muxing']:
                        print(Colors.GREEN + "✅ Videó szinkronizálás engedélyezve" + Colors.ENDC)
                    else:
                        print(Colors.CYAN + "✓ Csak hang szintézis (videó nélkül)" + Colors.ENDC)
                except (EOFError, KeyboardInterrupt):
                    print(Colors.WARNING + "⚠ Megszakítva. Videó muxing kihagyva." + Colors.ENDC)
                    preferences['enable_video_muxing'] = False
            else:
                print(Colors.CYAN + "✓ Csak fordítás (hang nélkül)" + Colors.ENDC)
                preferences['enable_video_muxing'] = False
                
        except (EOFError, KeyboardInterrupt):
            print(Colors.WARNING + "⚠ Megszakítva. Hangszintézis kihagyva." + Colors.ENDC)
            preferences['enable_synthesis'] = False
            preferences['enable_video_muxing'] = False
        
        # Ask about preview mode with error handling
        try:
            preview_only = input(Colors.BOLD + "🔍 Csak előnézet mód? (gyorsabb, csak hang) [i/n]: " + Colors.ENDC).lower().strip()
            preferences['preview_mode'] = (preview_only == 'i')
            
            if preferences['preview_mode']:
                print(Colors.YELLOW + "⚡ Előnézet mód aktív - gyors feldolgozás" + Colors.ENDC)
            else:
                print(Colors.GREEN + "🎬 Teljes feldolgozás mód" + Colors.ENDC)
                
        except (EOFError, KeyboardInterrupt):
            print(Colors.WARNING + "⚠ Megszakítva. Standard mód használva." + Colors.ENDC)
            preferences['preview_mode'] = False
        
        # Show final configuration summary
        print(Colors.BOLD + "\n" + "="*50 + Colors.ENDC)
        print(Colors.BOLD + Colors.GREEN + "        📋 VÉGSŐ KONFIGURÁCIÓ" + Colors.ENDC)
        print(Colors.BOLD + "="*50 + Colors.ENDC)
        print(Colors.CYAN + f"🌍 Célnyelv: {preferences['target_language']}" + Colors.ENDC)
        print(Colors.CYAN + f"🎯 Kontextus: {preferences['translation_context']}" + Colors.ENDC)
        print(Colors.CYAN + f"🎤 Hangszintézis: {'Igen' if preferences['enable_synthesis'] else 'Nem'}" + Colors.ENDC)
        if preferences['enable_synthesis']:
            print(Colors.CYAN + f"🔧 TTS Provider: {preferences['tts_provider']}" + Colors.ENDC)
        print(Colors.CYAN + f"🎞️  Videó szinkronizálás: {'Igen' if preferences['enable_video_muxing'] else 'Nem'}" + Colors.ENDC)
        print(Colors.CYAN + f"⚡ Előnézet mód: {'Igen' if preferences['preview_mode'] else 'Nem'}" + Colors.ENDC)
        print(Colors.BOLD + "="*50 + Colors.ENDC)
        
        return preferences
        
    except Exception as e:
        print(Colors.FAIL + f"\n✗ Kritikus hiba a dubbing beállítások lekérésekor: {e}" + Colors.ENDC)
        print(Colors.WARNING + "Szinkronizálás kihagyva." + Colors.ENDC)
        return None


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
    Get TTS provider selection from user with Hungarian interface and enhanced error handling.
    
    Returns:
        Selected TTS provider enum
    """
    try:
        print(Colors.BOLD + "\n" + "="*60 + Colors.ENDC)
        print(Colors.BOLD + Colors.CYAN + "        🎤 TTS SZOLGÁLTATÓ KIVÁLASZTÁSA" + Colors.ENDC)
        print(Colors.BOLD + "="*60 + Colors.ENDC)
        
        # Get provider information and costs with error handling
        try:
            provider_info = TTSFactory.get_provider_info()
            available_providers = TTSFactory.get_available_providers()
            
            print(Colors.CYAN + f"\n🔍 {len(available_providers)} elérhető szolgáltató találva..." + Colors.ENDC)
            
            # Check if any providers are available
            if not available_providers:
                print(Colors.WARNING + "⚠ Nincsenek elérhető TTS szolgáltatók!" + Colors.ENDC)
                print(Colors.CYAN + "Automatikus kiválasztás használva (fallback)." + Colors.ENDC)
                return TTSProviderEnum.AUTO
                
        except Exception as e:
            print(Colors.WARNING + f"⚠ TTS szolgáltatók lekérése sikertelen: {e}" + Colors.ENDC)
            print(Colors.CYAN + "Automatikus kiválasztás használva (fallback)." + Colors.ENDC)
            return TTSProviderEnum.AUTO
        
        print(Colors.CYAN + "\n📊 Elérhető TTS szolgáltatók:" + Colors.ENDC)
        print()
        
        providers_menu = []
        available_count = 0
        
        # Show available providers with status and costs
        for i, (provider_id, info) in enumerate(provider_info.items(), 1):
            status = "✅" if info["available"] else "❌"
            cost = f"${info['cost_per_1k_chars']:.4f}/1K karakter" if info["available"] else "N/A"
            voice_count = f"{info['voice_count']} hang" if info["available"] else "N/A"
            
            if info["available"]:
                available_count += 1
            
            if provider_id == "elevenlabs":
                name = "ElevenLabs - Prémium neurális hangok"
                note = "(drága, de kiváló minőség)" if info["available"] else "(nem elérhető)"
            elif provider_id == "google_tts":
                name = "Google Cloud TTS - Kiváló minőség"
                if info["available"] and provider_info.get("elevenlabs", {}).get("available", False):
                    elevenlabs_cost = provider_info.get("elevenlabs", {}).get("cost_per_1k_chars", 0)
                    google_cost = info.get("cost_per_1k_chars", 0)
                    if elevenlabs_cost > 0 and google_cost > 0:
                        savings = ((elevenlabs_cost - google_cost) / elevenlabs_cost) * 100
                        note = f"({savings:.0f}%+ olcsóbb)"
                    else:
                        note = "(költséghatékony)"
                else:
                    note = "(nem elérhető)" if not info["available"] else "(költséghatékony)"
            else:
                name = info.get("name", "Ismeretlen szolgáltató")
                note = ""
            
            color = Colors.GREEN if info["available"] else Colors.FAIL
            print(color + f"{status} {i}. {name}" + Colors.ENDC)
            print(f"      💰 Költség: {cost}")
            print(f"      🎭 Hangok: {voice_count} {note}")
            
            if not info["available"] and "error" in info:
                print(Colors.WARNING + f"      ⚠ Hiba: {info['error']}" + Colors.ENDC)
            
            print()
            providers_menu.append((provider_id, info["available"]))
        
        # Check if we have at least one available provider
        if available_count == 0:
            print(Colors.FAIL + "❌ Egyetlen TTS szolgáltató sem elérhető!" + Colors.ENDC)
            print(Colors.WARNING + "Kérlek ellenőrizd a konfigurációt és a hálózati kapcsolatot." + Colors.ENDC)
            print(Colors.CYAN + "Automatikus kiválasztás használva (alapértelmezett fallback)." + Colors.ENDC)
            return TTSProviderEnum.AUTO
        
        # Auto-selection option
        print(Colors.BOLD + f"✨ {len(providers_menu) + 1}. Automatikus kiválasztás költség alapján" + Colors.ENDC)
        print("      🤖 A rendszer automatikusan a legköltséghatékonyabb szolgáltatót választja")
        print()
        
        # Show cost comparison if both providers are available
        if available_count >= 2:
            print(Colors.GREEN + "💡 Költség összehasonlítás (1000 karakterre):" + Colors.ENDC)
            elevenlabs_cost = provider_info.get("elevenlabs", {}).get("cost_per_1k_chars", 0) if provider_info.get("elevenlabs", {}).get("available", False) else 0
            google_cost = provider_info.get("google_tts", {}).get("cost_per_1k_chars", 0) if provider_info.get("google_tts", {}).get("available", False) else 0
            
            if elevenlabs_cost > 0:
                print(f"    ElevenLabs: ${elevenlabs_cost:.4f}")
            if google_cost > 0:
                print(f"    Google TTS: ${google_cost:.4f}")
                
            if elevenlabs_cost > 0 and google_cost > 0:
                savings = ((elevenlabs_cost - google_cost) / elevenlabs_cost) * 100
                recommended = "Google TTS" if google_cost < elevenlabs_cost else "ElevenLabs"
                print(Colors.GREEN + f"    💰 Legjobb választás: {recommended} ({abs(savings):.1f}% {'megtakarítás' if savings > 0 else 'drágább'})" + Colors.ENDC)
            print()
        
        # User selection loop with improved error handling
        while True:
            try:
                max_choice = len(providers_menu) + 1
                prompt = Colors.BOLD + f"Választás [1-{max_choice}, Enter = automatikus]: " + Colors.ENDC
                
                try:
                    response = input(prompt).strip()
                except (EOFError, KeyboardInterrupt):
                    print(Colors.WARNING + "\n⚠ Megszakítva. Automatikus kiválasztás használva." + Colors.ENDC)
                    return TTSProviderEnum.AUTO
                
                if response == "":
                    print(Colors.GREEN + "✓ Automatikus kiválasztás (költség alapú optimalizálás)" + Colors.ENDC)
                    return TTSProviderEnum.AUTO
                
                try:
                    choice = int(response)
                except ValueError:
                    print(Colors.WARNING + "⚠ Kérlek érvényes számot adj meg!" + Colors.ENDC)
                    continue
                
                if choice == max_choice:
                    print(Colors.GREEN + "✓ Automatikus kiválasztás (költség alapú optimalizálás)" + Colors.ENDC)
                    return TTSProviderEnum.AUTO
                elif 1 <= choice <= len(providers_menu):
                    provider_id, available = providers_menu[choice - 1]
                    
                    if not available:
                        provider_name = provider_info.get(provider_id, {}).get("name", provider_id)
                        print(Colors.WARNING + f"⚠ A {provider_name} szolgáltató nem elérhető. Válassz másikat!" + Colors.ENDC)
                        continue
                    
                    # Map provider ID to enum
                    provider_mapping = {
                        "elevenlabs": (TTSProviderEnum.ELEVENLABS, "ElevenLabs"),
                        "google_tts": (TTSProviderEnum.GOOGLE_TTS, "Google Cloud TTS")
                    }
                    
                    if provider_id in provider_mapping:
                        provider_enum, name = provider_mapping[provider_id]
                        print(Colors.GREEN + f"✓ Kiválasztva: {name}" + Colors.ENDC)
                        
                        # Show additional info about the selected provider
                        cost = provider_info[provider_id].get('cost_per_1k_chars', 0)
                        if cost > 0:
                            print(Colors.CYAN + f"  💰 Költség: ${cost:.4f}/1K karakter" + Colors.ENDC)
                        
                        return provider_enum
                    else:
                        print(Colors.WARNING + f"⚠ Ismeretlen szolgáltató: {provider_id}. Automatikus használva." + Colors.ENDC)
                        return TTSProviderEnum.AUTO
                else:
                    print(Colors.WARNING + f"⚠ Kérlek 1 és {max_choice} közötti számot válassz!" + Colors.ENDC)
                    
            except Exception as inner_e:
                print(Colors.WARNING + f"⚠ Hiba a választás során: {inner_e}. Próbáld újra." + Colors.ENDC)
                continue
                
    except Exception as e:
        print(Colors.FAIL + f"✗ Kritikus hiba a TTS szolgáltató kiválasztáskor: {e}" + Colors.ENDC)
        print(Colors.WARNING + "Automatikus kiválasztás használva (fallback)." + Colors.ENDC)
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
    Show cost estimation for dubbing and get user confirmation with enhanced error handling.
    
    Args:
        dubbing_service: DubbingService instance
        transcript_length: Length of transcript in characters
        preferences: Dubbing preferences
    
    Returns:
        True if user wants to proceed, False otherwise
    """
    try:
        print(Colors.CYAN + "\n💰 Költségbecslés számítása..." + Colors.ENDC)
        
        # Validate inputs first
        if not dubbing_service:
            print(Colors.WARNING + "⚠ DubbingService nem elérhető. Alapértelmezett becslés használva." + Colors.ENDC)
            return _show_fallback_cost_estimate(transcript_length, preferences)
        
        if transcript_length <= 0:
            print(Colors.WARNING + "⚠ Érvénytelen transcript hossz. Alapértelmezett becslés használva." + Colors.ENDC)
            return _show_fallback_cost_estimate(1000, preferences)  # Use 1000 chars as fallback
        
        # Create a minimal DubbingRequest for cost estimation with error handling
        try:
            from ..models.dubbing import DubbingRequest, TTSProviderEnum, TranslationContextEnum
            from pydantic import HttpUrl
            
            # Safely extract preferences with defaults
            enable_synthesis = preferences.get('enable_synthesis', False)
            enable_video_muxing = preferences.get('enable_video_muxing', False)
            voice_id = preferences.get('voice_id', None)
            target_language = preferences.get('target_language', 'en-US')
            tts_provider = preferences.get('tts_provider', TTSProviderEnum.AUTO)
            translation_context = preferences.get('translation_context', 'casual')
            
            # Map string context to enum if needed
            context_map = {
                'casual': TranslationContextEnum.CASUAL,
                'educational': TranslationContextEnum.EDUCATIONAL,
                'marketing': TranslationContextEnum.MARKETING,
                'spiritual': TranslationContextEnum.SPIRITUAL,
                'legal': TranslationContextEnum.LEGAL,
                'news': TranslationContextEnum.NEWS,
                'scientific': TranslationContextEnum.SCIENTIFIC
            }
            
            if isinstance(translation_context, str):
                translation_context = context_map.get(translation_context, TranslationContextEnum.CASUAL)
            
            print(Colors.CYAN + f"📊 Beállítások: {target_language} | {'Hang: ' + str(tts_provider) if enable_synthesis else 'Csak fordítás'} | {'Videó ✓' if enable_video_muxing else 'Csak hang'}" + Colors.ENDC)
            
            # Provide default voice_id if synthesis is enabled but no voice selected yet
            if enable_synthesis and not voice_id:
                # Use provider-specific default voice for cost estimation
                if tts_provider == TTSProviderEnum.GOOGLE_TTS:
                    voice_id = "en-US-Neural2-F" if target_language.startswith('en') else "hu-HU-Wavenet-A"
                elif tts_provider == TTSProviderEnum.ELEVENLABS:
                    voice_id = "pNInz6obpgDQGcFmaJgB"  # Default ElevenLabs voice
                else:
                    voice_id = "auto-selected"  # Placeholder for auto selection
                    
                print(Colors.CYAN + f"🎤 Hang becsléshez: {voice_id}" + Colors.ENDC)
            
            dummy_request = DubbingRequest(
                url=HttpUrl("https://youtube.com/watch?v=dummy"),
                enable_translation=True,
                target_language=target_language,
                enable_synthesis=enable_synthesis,
                enable_video_muxing=enable_video_muxing,
                voice_id=voice_id,
                tts_provider=tts_provider,
                translation_context=translation_context,
                existing_transcript="x" * transcript_length  # Mock transcript for length
            )
            
        except Exception as req_error:
            print(Colors.WARNING + f"⚠ DubbingRequest létrehozás sikertelen: {req_error}" + Colors.ENDC)
            return _show_fallback_cost_estimate(transcript_length, preferences)
        
        # Try to get estimate from dubbing service
        try:
            print(Colors.CYAN + "🧮 Költség számítás..." + Colors.ENDC)
            estimate = dubbing_service.estimate_dubbing_cost(dummy_request)
            
            if not estimate or not isinstance(estimate, dict):
                print(Colors.WARNING + "⚠ Érvénytelen költségbecslés eredmény." + Colors.ENDC)
                return _show_fallback_cost_estimate(transcript_length, preferences)
                
        except Exception as estimate_error:
            print(Colors.WARNING + f"⚠ Költségbecslés szolgáltatás hiba: {estimate_error}" + Colors.ENDC)
            return _show_fallback_cost_estimate(transcript_length, preferences)
        
        # Display results
        print(Colors.YELLOW + "\n" + "="*50 + Colors.ENDC)
        print(Colors.YELLOW + "              💰 KÖLTSÉGBECSLÉS" + Colors.ENDC)
        print(Colors.YELLOW + "="*50 + Colors.ENDC)
        
        print(Colors.CYAN + f"📝 Átirat hossza: {transcript_length:,} karakter" + Colors.ENDC)
        
        # Show breakdown with error handling
        breakdown = estimate.get('breakdown', {})
        if breakdown and isinstance(breakdown, dict):
            print(Colors.CYAN + "\n💸 Költség lebontás:" + Colors.ENDC)
            
            if 'translation_cost' in breakdown:
                trans_cost = breakdown['translation_cost']
                if isinstance(trans_cost, (int, float)) and trans_cost >= 0:
                    print(Colors.CYAN + f"   ├─ Fordítás: ${trans_cost:.4f}" + Colors.ENDC)
            
            if 'synthesis_cost' in breakdown:
                synth_cost = breakdown['synthesis_cost']
                if isinstance(synth_cost, (int, float)) and synth_cost >= 0:
                    print(Colors.CYAN + f"   ├─ Hangszintézis: ${synth_cost:.4f}" + Colors.ENDC)
            
            if 'processing_cost' in breakdown:
                proc_cost = breakdown['processing_cost']
                if isinstance(proc_cost, (int, float)) and proc_cost >= 0:
                    print(Colors.CYAN + f"   └─ Videó feldolgozás: ${proc_cost:.4f}" + Colors.ENDC)
        
        total_cost = estimate.get('total_cost_usd', 0.0)
        processing_time = estimate.get('estimated_time_minutes', 5)
        
        # Validate cost values
        if not isinstance(total_cost, (int, float)) or total_cost < 0:
            total_cost = 0.0
            
        if not isinstance(processing_time, (int, float)) or processing_time <= 0:
            processing_time = 5.0
        
        print(Colors.BOLD + Colors.GREEN + f"\n💵 Teljes költség: ${total_cost:.4f}" + Colors.ENDC)
        print(Colors.CYAN + f"⏱️  Becsült idő: {processing_time:.1f} perc" + Colors.ENDC)
        
        print(Colors.YELLOW + "="*50 + Colors.ENDC)
        
        # Get confirmation with error handling
        try:
            if total_cost > 0.05:  # Show warning for costs over 5 cents
                print(Colors.WARNING + f"\nFigyelem: A szinkronizálás költsége ${total_cost:.4f} lesz." + Colors.ENDC)
            else:
                print(Colors.GREEN + "\n✅ Költséghatékony feldolgozás (< $0.05)" + Colors.ENDC)
            
            try:
                response = input(Colors.BOLD + "Folytatod a szinkronizálást? (i/n) [i]: " + Colors.ENDC).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print(Colors.WARNING + "\n⚠ Megszakítva. Szinkronizálás kihagyva." + Colors.ENDC)
                return False
            
            if response and response.startswith('n'):
                print(Colors.WARNING + "Szinkronizálás megszakítva felhasználó által." + Colors.ENDC)
                return False
                
            print(Colors.GREEN + "✓ Szinkronizálás jóváhagyva" + Colors.ENDC)
            return True
            
        except Exception as confirm_error:
            print(Colors.WARNING + f"⚠ Megerősítés hiba: {confirm_error}. Folytatás..." + Colors.ENDC)
            return True
        
    except Exception as e:
        print(Colors.FAIL + f"✗ Kritikus hiba a költségbecsléskor: {e}" + Colors.ENDC)
        return _show_fallback_cost_estimate(transcript_length, preferences)


def _show_fallback_cost_estimate(transcript_length: int, preferences: Dict) -> bool:
    """
    Show fallback cost estimation when main estimation fails.
    
    Args:
        transcript_length: Length of transcript in characters
        preferences: Dubbing preferences
    
    Returns:
        True if user wants to proceed, False otherwise
    """
    try:
        print(Colors.YELLOW + "\n" + "="*50 + Colors.ENDC)
        print(Colors.YELLOW + "           💰 ALAPÉRTELMEZETT BECSLÉS" + Colors.ENDC)
        print(Colors.YELLOW + "="*50 + Colors.ENDC)
        
        print(Colors.CYAN + f"📝 Átirat hossza: {transcript_length:,} karakter" + Colors.ENDC)
        
        # Simple fallback estimation
        enable_synthesis = preferences.get('enable_synthesis', False)
        enable_video_muxing = preferences.get('enable_video_muxing', False)
        
        # Basic cost estimation (rough estimates)
        translation_cost = transcript_length * 0.00001  # ~$0.01 per 1000 chars
        synthesis_cost = transcript_length * 0.0003 if enable_synthesis else 0  # ~$0.30 per 1000 chars (ElevenLabs rate)
        processing_cost = 0.01 if enable_video_muxing else 0  # Small fixed cost for video processing
        
        # If Google TTS is selected, use much lower rate
        tts_provider = preferences.get('tts_provider', TTSProviderEnum.AUTO)
        if enable_synthesis and (tts_provider == TTSProviderEnum.GOOGLE_TTS or tts_provider == TTSProviderEnum.AUTO):
            synthesis_cost = transcript_length * 0.000016  # Google TTS rate ~$0.016 per 1000 chars
        
        total_cost = translation_cost + synthesis_cost + processing_cost
        estimated_time = max(2.0, transcript_length / 200)  # Rough time estimate
        
        print(Colors.CYAN + "\n💸 Becslés lebontás:" + Colors.ENDC)
        print(Colors.CYAN + f"   ├─ Fordítás: ${translation_cost:.4f}" + Colors.ENDC)
        if enable_synthesis:
            provider_name = "Google TTS" if tts_provider == TTSProviderEnum.GOOGLE_TTS else "TTS"
            print(Colors.CYAN + f"   ├─ Hangszintézis ({provider_name}): ${synthesis_cost:.4f}" + Colors.ENDC)
        if enable_video_muxing:
            print(Colors.CYAN + f"   └─ Videó feldolgozás: ${processing_cost:.4f}" + Colors.ENDC)
        
        print(Colors.BOLD + Colors.GREEN + f"\n💵 Becsült teljes költség: ${total_cost:.4f}" + Colors.ENDC)
        print(Colors.CYAN + f"⏱️  Becsült idő: {estimated_time:.1f} perc" + Colors.ENDC)
        
        print(Colors.WARNING + "⚠ Ez csak becslés - a tényleges költség eltérhet!" + Colors.ENDC)
        print(Colors.YELLOW + "="*50 + Colors.ENDC)
        
        # Get confirmation
        try:
            if total_cost > 0.10:
                print(Colors.WARNING + f"\nFigyelem: A szinkronizálás költsége körülbelül ${total_cost:.4f} lesz." + Colors.ENDC)
            
            response = input(Colors.BOLD + "Folytatod a szinkronizálást? (i/n) [i]: " + Colors.ENDC).strip().lower()
            
            if response and response.startswith('n'):
                print(Colors.WARNING + "Szinkronizálás megszakítva." + Colors.ENDC)
                return False
                
            print(Colors.GREEN + "✓ Szinkronizálás jóváhagyva (becslés alapján)" + Colors.ENDC)
            return True
            
        except (EOFError, KeyboardInterrupt):
            print(Colors.WARNING + "\n⚠ Megszakítva. Szinkronizálás kihagyva." + Colors.ENDC)
            return False
            
    except Exception as e:
        print(Colors.FAIL + f"✗ Fallback becslés is sikertelen: {e}" + Colors.ENDC)
        print(Colors.CYAN + "Szinkronizálás folytatása alapértelmezett beállításokkal..." + Colors.ENDC)
        return True