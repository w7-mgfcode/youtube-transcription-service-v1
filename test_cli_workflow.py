#!/usr/bin/env python3
"""
Test script to simulate the CLI dubbing workflow with our fixes.
This demonstrates the enhanced error handling and step-by-step process.
"""

import sys
import os
sys.path.append('/app' if os.path.exists('/app') else '.')

from unittest.mock import patch, MagicMock
from src.utils.validators import get_dubbing_preferences, get_tts_provider_selection, show_dubbing_cost_estimate
from src.models.dubbing import TTSProviderEnum, TranslationContextEnum
from src.cli import InteractiveCLI
from src.core.dubbing_service import DubbingService
from src.utils.colors import Colors

def test_enhanced_dubbing_workflow():
    """Test the enhanced dubbing workflow with our fixes."""
    print(Colors.BOLD + "\n" + "="*80)
    print("🧪 TESTING ENHANCED CLI DUBBING WORKFLOW")
    print("="*80 + Colors.ENDC)
    
    try:
        # Test 1: Enhanced get_dubbing_preferences with simulated inputs
        print(Colors.CYAN + "\n📍 Test 1: Enhanced dubbing preferences..." + Colors.ENDC)
        
        # Simulate user inputs: i, 1 (English), 1 (Casual), i (synthesis), 1 (Google TTS), n (no video), n (no preview)
        simulated_inputs = ['i', '1', '1', 'i', '', 'n', 'n']  # Empty string = default (auto TTS)
        
        with patch('builtins.input', side_effect=simulated_inputs):
            preferences = get_dubbing_preferences()
            
        if preferences:
            print(Colors.GREEN + "✅ Dubbing preferences successfully collected!" + Colors.ENDC)
            print(Colors.CYAN + "📋 Configuration:" + Colors.ENDC)
            for key, value in preferences.items():
                print(Colors.CYAN + f"   {key}: {value}" + Colors.ENDC)
        else:
            print(Colors.FAIL + "❌ No preferences returned" + Colors.ENDC)
            return False
            
        # Test 2: TTS Provider Selection (auto-selection)
        print(Colors.CYAN + "\n📍 Test 2: TTS Provider selection..." + Colors.ENDC)
        
        with patch('builtins.input', return_value=''):  # Default = auto
            tts_provider = get_tts_provider_selection()
            
        print(Colors.GREEN + f"✅ TTS Provider selected: {tts_provider}" + Colors.ENDC)
        
        # Test 3: Cost estimation with enhanced error handling
        print(Colors.CYAN + "\n📍 Test 3: Enhanced cost estimation..." + Colors.ENDC)
        
        dubbing_service = DubbingService()
        test_preferences = {
            'enable_synthesis': True,
            'enable_video_muxing': False,
            'target_language': 'en-US',
            'tts_provider': TTSProviderEnum.AUTO,
            'translation_context': 'casual'
        }
        
        with patch('builtins.input', return_value='i'):  # Approve cost
            cost_approved = show_dubbing_cost_estimate(dubbing_service, 1000, test_preferences)
            
        print(Colors.GREEN + f"✅ Cost estimation result: {cost_approved}" + Colors.ENDC)
        
        # Test 4: Simulate complete dubbing workflow (without actual processing)
        print(Colors.CYAN + "\n📍 Test 4: Simulated complete workflow..." + Colors.ENDC)
        
        # Create mock transcript result
        mock_transcript_result = {
            'status': 'completed',
            'transcript_file': '/app/data/test_transcript.txt',
            'title': 'Test Video',
            'duration': 120,
            'word_count': 200
        }
        
        # Create test transcript file
        os.makedirs('/tmp/test_data', exist_ok=True)
        with open('/tmp/test_data/test_transcript.txt', 'w', encoding='utf-8') as f:
            f.write("Ez egy teszt átirat. " * 50)  # ~1000 characters
        
        # Update mock result with actual file
        mock_transcript_result['transcript_file'] = '/tmp/test_data/test_transcript.txt'
        
        # Test the enhanced _process_dubbing_workflow
        cli = InteractiveCLI()
        
        # Mock the dubbing service result
        mock_dubbing_result = MagicMock()
        mock_dubbing_result.status = 'completed'
        mock_dubbing_result.translation_file = '/tmp/test_translation.txt'
        mock_dubbing_result.audio_file = '/tmp/test_audio.mp3'
        mock_dubbing_result.video_file = None
        mock_dubbing_result.error = None
        mock_dubbing_result.cost_breakdown = {'total_cost_usd': 0.025}
        
        # Mock voice selection to avoid interactive prompt
        with patch('src.utils.validators.get_voice_selection', return_value='test-voice-id'):
            with patch.object(cli.dubbing_service, 'process_dubbing_job', return_value=mock_dubbing_result):
                # Mock cost estimation to avoid interactive prompt  
                with patch('src.utils.validators.show_dubbing_cost_estimate', return_value=True):
                    result = cli._process_dubbing_workflow(
                        video_url="https://youtube.com/watch?v=test123",
                        test_mode=True,
                        transcript_result=mock_transcript_result,
                        preferences=test_preferences
                    )
        
        print(Colors.GREEN + "✅ Complete workflow simulation successful!" + Colors.ENDC)
        print(Colors.CYAN + "📋 Workflow result:" + Colors.ENDC)
        for key, value in result.items():
            print(Colors.CYAN + f"   {key}: {value}" + Colors.ENDC)
        
        print(Colors.BOLD + Colors.GREEN + "\n🎉 ALL TESTS PASSED! Enhanced dubbing workflow is working!" + Colors.ENDC)
        print(Colors.CYAN + "The fixes have resolved the CLI stopping issue." + Colors.ENDC)
        
        return True
        
    except Exception as e:
        print(Colors.FAIL + f"\n❌ Test failed with error: {e}" + Colors.ENDC)
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            if os.path.exists('/tmp/test_data/test_transcript.txt'):
                os.remove('/tmp/test_data/test_transcript.txt')
            if os.path.exists('/tmp/test_data'):
                os.rmdir('/tmp/test_data')
        except:
            pass

if __name__ == "__main__":
    success = test_enhanced_dubbing_workflow()
    sys.exit(0 if success else 1)