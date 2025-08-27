"""Factory for creating TTS synthesizer instances."""

from typing import Optional, Dict, Any
from .tts_interface import AbstractTTSSynthesizer, TTSProvider, ProviderNotAvailableError
from ..config import settings
from ..utils.colors import Colors


class TTSFactory:
    """Factory class for creating TTS synthesizer instances."""
    
    _synthesizers: Dict[TTSProvider, AbstractTTSSynthesizer] = {}
    
    @classmethod
    def create_synthesizer(cls, provider: Optional[TTSProvider] = None) -> AbstractTTSSynthesizer:
        """
        Create a TTS synthesizer instance for the specified provider.
        
        Args:
            provider: TTS provider to use. If None, uses config default.
            
        Returns:
            AbstractTTSSynthesizer instance
            
        Raises:
            ProviderNotAvailableError: If provider is not available or configured
        """
        # Determine provider from config if not specified
        if provider is None:
            provider_str = getattr(settings, 'tts_provider', 'elevenlabs')
            try:
                provider = TTSProvider(provider_str)
            except ValueError:
                print(Colors.WARNING + f"⚠ Invalid TTS provider in config: {provider_str}" + Colors.ENDC)
                print(Colors.WARNING + "   Falling back to ElevenLabs" + Colors.ENDC)
                provider = TTSProvider.ELEVENLABS
        
        # Handle auto-selection
        if provider == TTSProvider.AUTO:
            provider = cls._auto_select_provider()
        
        # Return cached instance if available
        if provider in cls._synthesizers:
            synthesizer = cls._synthesizers[provider]
            if synthesizer.is_available:
                return synthesizer
            else:
                # Remove cached instance if no longer available
                del cls._synthesizers[provider]
        
        # Create new instance
        synthesizer = cls._create_provider_instance(provider)
        
        # Validate availability
        if not synthesizer.is_available:
            available_providers = cls.get_available_providers()
            if available_providers:
                fallback_provider = available_providers[0]
                print(Colors.WARNING + f"⚠ {provider.value} not available, using {fallback_provider.value}" + Colors.ENDC)
                synthesizer = cls._create_provider_instance(fallback_provider)
            else:
                raise ProviderNotAvailableError("No TTS providers are properly configured")
        
        # Cache and return
        cls._synthesizers[provider] = synthesizer
        return synthesizer
    
    @classmethod
    def _create_provider_instance(cls, provider: TTSProvider) -> AbstractTTSSynthesizer:
        """Create a specific provider instance."""
        if provider == TTSProvider.ELEVENLABS:
            from .synthesizer import ElevenLabsSynthesizerAdapter
            return ElevenLabsSynthesizerAdapter()
        elif provider == TTSProvider.GOOGLE_TTS:
            from .google_tts_synthesizer import GoogleTTSSynthesizer
            return GoogleTTSSynthesizer()
        else:
            raise ProviderNotAvailableError(f"Unsupported TTS provider: {provider}")
    
    @classmethod
    def _auto_select_provider(cls) -> TTSProvider:
        """
        Automatically select the best available TTS provider.
        
        Priority order:
        1. Google TTS (cost-effective, high quality)
        2. ElevenLabs (premium quality, higher cost)
        
        Returns:
            Selected TTSProvider
        """
        # Check Google TTS first (more cost-effective)
        try:
            google_synthesizer = cls._create_provider_instance(TTSProvider.GOOGLE_TTS)
            if google_synthesizer.is_available:
                print(Colors.GREEN + "✓ Auto-selected Google Cloud TTS (cost-effective)" + Colors.ENDC)
                return TTSProvider.GOOGLE_TTS
        except Exception:
            pass
        
        # Fallback to ElevenLabs
        try:
            elevenlabs_synthesizer = cls._create_provider_instance(TTSProvider.ELEVENLABS)
            if elevenlabs_synthesizer.is_available:
                print(Colors.YELLOW + "✓ Auto-selected ElevenLabs (premium quality)" + Colors.ENDC)
                return TTSProvider.ELEVENLABS
        except Exception:
            pass
        
        # No providers available
        raise ProviderNotAvailableError("No TTS providers are properly configured")
    
    @classmethod
    def get_available_providers(cls) -> list[TTSProvider]:
        """
        Get list of available and properly configured providers.
        
        Returns:
            List of available TTSProvider enums
        """
        available = []
        
        for provider in [TTSProvider.GOOGLE_TTS, TTSProvider.ELEVENLABS]:
            try:
                synthesizer = cls._create_provider_instance(provider)
                if synthesizer.is_available:
                    available.append(provider)
            except Exception:
                continue
        
        return available
    
    @classmethod
    def get_provider_info(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed information about all providers.
        
        Returns:
            Dictionary with provider information
        """
        info = {}
        
        for provider in TTSProvider:
            if provider == TTSProvider.AUTO:
                continue
                
            provider_info = {
                "name": cls._get_provider_display_name(provider),
                "description": cls._get_provider_description(provider),
                "available": False,
                "cost_per_1k_chars": 0.0,
                "voice_count": 0,
                "languages": []
            }
            
            try:
                synthesizer = cls._create_provider_instance(provider)
                provider_info["available"] = synthesizer.is_available
                
                if provider_info["available"]:
                    provider_info["cost_per_1k_chars"] = synthesizer.estimate_cost(1000)
                    voices = synthesizer.get_available_voices()
                    provider_info["voice_count"] = len(voices)
                    provider_info["languages"] = synthesizer.get_supported_languages()
                    
            except Exception as e:
                provider_info["error"] = str(e)
            
            info[provider.value] = provider_info
        
        return info
    
    @classmethod
    def _get_provider_display_name(cls, provider: TTSProvider) -> str:
        """Get human-readable provider name."""
        names = {
            TTSProvider.ELEVENLABS: "ElevenLabs",
            TTSProvider.GOOGLE_TTS: "Google Cloud Text-to-Speech",
        }
        return names.get(provider, provider.value)
    
    @classmethod
    def _get_provider_description(cls, provider: TTSProvider) -> str:
        """Get provider description."""
        descriptions = {
            TTSProvider.ELEVENLABS: "Premium neural voices with exceptional quality and expressiveness",
            TTSProvider.GOOGLE_TTS: "High-quality voices with excellent cost-effectiveness and broad language support",
        }
        return descriptions.get(provider, "")
    
    @classmethod
    def clear_cache(cls):
        """Clear cached synthesizer instances."""
        cls._synthesizers.clear()
    
    @classmethod 
    def get_voice_mapping(cls, 
                         from_provider: TTSProvider, 
                         to_provider: TTSProvider,
                         voice_id: str) -> Optional[str]:
        """
        Map a voice from one provider to equivalent voice in another provider.
        
        Args:
            from_provider: Source provider
            to_provider: Target provider  
            voice_id: Voice ID in source provider
            
        Returns:
            Equivalent voice ID in target provider, or None if no mapping
        """
        # ElevenLabs -> Google TTS mapping
        if from_provider == TTSProvider.ELEVENLABS and to_provider == TTSProvider.GOOGLE_TTS:
            mapping = {
                # Popular ElevenLabs voices -> Google Neural2 equivalents
                "21m00Tcm4TlvDq8ikWAM": "en-US-Neural2-F",  # Rachel -> Neural2-F (female, clear)
                "pNInz6obpgDQGcFmaJgB": "en-US-Neural2-D",  # Adam -> Neural2-D (male, deep)
                "yoZ06aMxZJJ28mfd3POQ": "en-US-Neural2-A",  # Sam -> Neural2-A (male, conversational)
                "piTKgcLEGmPE4e6mEKli": "en-US-Neural2-E",  # Nicole -> Neural2-E (female, warm)
                "TxGEqnHWrfWFTfGW9XjX": "en-US-Neural2-C",  # Josh -> Neural2-C (male, professional)
                "EXAVITQu4vr4xnSDxMaL": "en-US-Neural2-G",  # Bella -> Neural2-G (female, professional)
                "ThT5KcBeYPX3keUQqHPh": "en-GB-Neural2-A",  # Dorothy -> GB-Neural2-A (british)
                "ErXwobaYiN019PkySvjV": "en-US-Neural2-J",  # Antoni -> Neural2-J (male, versatile)
            }
            return mapping.get(voice_id)
        
        # Google TTS -> ElevenLabs mapping (reverse)
        elif from_provider == TTSProvider.GOOGLE_TTS and to_provider == TTSProvider.ELEVENLABS:
            reverse_mapping = {
                "en-US-Neural2-F": "21m00Tcm4TlvDq8ikWAM",  # Neural2-F -> Rachel
                "en-US-Neural2-D": "pNInz6obpgDQGcFmaJgB",  # Neural2-D -> Adam
                "en-US-Neural2-A": "yoZ06aMxZJJ28mfd3POQ",  # Neural2-A -> Sam
                "en-US-Neural2-E": "piTKgcLEGmPE4e6mEKli",  # Neural2-E -> Nicole
                "en-US-Neural2-C": "TxGEqnHWrfWFTfGW9XjX",  # Neural2-C -> Josh
                "en-US-Neural2-G": "EXAVITQu4vr4xnSDxMaL",  # Neural2-G -> Bella
                "en-GB-Neural2-A": "ThT5KcBeYPX3keUQqHPh",  # GB-Neural2-A -> Dorothy
                "en-US-Neural2-J": "ErXwobaYiN019PkySvjV",  # Neural2-J -> Antoni
            }
            return reverse_mapping.get(voice_id)
        
        return None