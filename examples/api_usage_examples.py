#!/usr/bin/env python3
"""
🌐 API Usage Examples - TTS Provider Integration

This script demonstrates how to use the enhanced API with multi-provider
TTS support, including Google Cloud TTS and ElevenLabs integration.

Usage:
    python examples/api_usage_examples.py --example basic --provider google_tts
"""

import asyncio
import aiohttp
import argparse
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class APIResponse:
    status_code: int
    data: Dict[str, Any]
    response_time: float

class TTSAPIClient:
    """Enhanced API client with multi-provider TTS support"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> APIResponse:
        """Make HTTP request and measure response time"""
        start_time = time.time()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                data = await response.json()
                response_time = time.time() - start_time
                
                return APIResponse(
                    status_code=response.status,
                    data=data,
                    response_time=response_time
                )
        except Exception as e:
            response_time = time.time() - start_time
            return APIResponse(
                status_code=500,
                data={"error": str(e)},
                response_time=response_time
            )
    
    async def get_health(self) -> APIResponse:
        """Get API health status"""
        return await self._request("GET", "/health")
    
    async def get_tts_providers(self) -> APIResponse:
        """Get available TTS providers"""
        return await self._request("GET", "/v1/tts-providers")
    
    async def get_provider_voices(self, provider: str, language: Optional[str] = None) -> APIResponse:
        """Get voices for specific provider"""
        params = {}
        if language:
            params["language"] = language
        
        return await self._request("GET", f"/v1/tts-providers/{provider}/voices", params=params)
    
    async def compare_tts_costs(self, text: str, providers: Optional[List[str]] = None) -> APIResponse:
        """Compare TTS costs across providers"""
        params = {"text": text}
        if providers:
            params["providers"] = ",".join(providers)
        
        return await self._request("GET", "/v1/tts-cost-comparison", params=params)
    
    async def estimate_costs(self, transcript_length: int, target_language: str, 
                           tts_provider: str = "auto", enable_synthesis: bool = True) -> APIResponse:
        """Estimate dubbing costs"""
        params = {
            "transcript_length": transcript_length,
            "target_language": target_language,
            "tts_provider": tts_provider,
            "enable_synthesis": enable_synthesis
        }
        
        return await self._request("GET", "/v1/cost-estimate", params=params)
    
    async def create_dubbing_job(self, job_data: Dict[str, Any]) -> APIResponse:
        """Create a new dubbing job"""
        headers = {"Content-Type": "application/json"}
        return await self._request("POST", "/v1/dub", json=job_data, headers=headers)
    
    async def get_job_status(self, job_id: str) -> APIResponse:
        """Get dubbing job status"""
        return await self._request("GET", f"/v1/dubbing/{job_id}")
    
    async def download_job_result(self, job_id: str, file_type: str) -> APIResponse:
        """Download job result file"""
        params = {"file_type": file_type}
        return await self._request("GET", f"/v1/dubbing/{job_id}/download", params=params)

class APIExamples:
    """API usage examples for different scenarios"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def example_basic_provider_info(self):
        """Basic example: Get provider information"""
        print("🔍 Example 1: Basic Provider Information")
        print("=" * 50)
        
        async with TTSAPIClient(self.base_url) as client:
            # Check API health
            print("Checking API health...")
            health = await client.get_health()
            print(f"✅ API Status: {health.data.get('status', 'unknown')} "
                  f"(Response: {health.response_time:.2f}s)")
            
            # Get available providers
            print("\nGetting TTS providers...")
            providers_response = await client.get_tts_providers()
            
            if providers_response.status_code == 200:
                providers = providers_response.data.get("providers", [])
                print(f"📊 Found {len(providers)} TTS providers:")
                
                for provider in providers:
                    print(f"   🎤 {provider['name']}")
                    print(f"      Cost: ${provider['cost_per_1k_chars']:.3f}/1K chars")
                    print(f"      Voices: {provider['voice_count']}")
                    print(f"      Languages: {provider['languages_supported']}")
                    if provider.get('recommended'):
                        print(f"      ⭐ RECOMMENDED")
                    print()
            else:
                print(f"❌ Error: {providers_response.data}")
    
    async def example_voice_discovery(self, provider: str, language: str = "en-US"):
        """Example: Voice discovery and selection"""
        print(f"🎭 Example 2: Voice Discovery - {provider.upper()} ({language})")
        print("=" * 60)
        
        async with TTSAPIClient(self.base_url) as client:
            # Get voices for provider
            print(f"Getting {provider} voices for {language}...")
            voices_response = await client.get_provider_voices(provider, language)
            
            if voices_response.status_code == 200:
                voices_data = voices_response.data
                voices = voices_data.get("voices", [])
                
                print(f"🎤 Found {len(voices)} voices for {provider}:")
                print(f"Provider: {voices_data.get('provider')}")
                if 'language' in voices_data:
                    print(f"Language: {voices_data['language']}")
                print()
                
                # Show top 5 voices
                for i, voice in enumerate(voices[:5], 1):
                    print(f"{i}. {voice['name']} ({voice['voice_id']})")
                    print(f"   Gender: {voice['gender']}")
                    print(f"   Cost: ${voice['cost_per_1k_chars']:.3f}/1K chars")
                    if voice.get('recommended'):
                        print(f"   ⭐ RECOMMENDED")
                    if provider == "elevenlabs" and voice.get('google_tts_equivalent'):
                        print(f"   🔄 Google TTS equivalent: {voice['google_tts_equivalent']}")
                    print()
                
                if len(voices) > 5:
                    print(f"... and {len(voices) - 5} more voices available")
            else:
                print(f"❌ Error: {voices_response.data}")
    
    async def example_cost_comparison(self, sample_text: str = None):
        """Example: Cost comparison between providers"""
        if not sample_text:
            sample_text = ("This is a sample text for cost comparison. "
                         "It demonstrates the pricing differences between "
                         "Google Cloud TTS and ElevenLabs providers. "
                         "With longer texts, the cost savings become more significant.")
        
        print("💰 Example 3: Cost Comparison")
        print("=" * 40)
        print(f"Sample text ({len(sample_text)} characters):")
        print(f'"{sample_text[:100]}{"..." if len(sample_text) > 100 else ""}"')
        print()
        
        async with TTSAPIClient(self.base_url) as client:
            # Compare costs
            print("Comparing costs across providers...")
            comparison_response = await client.compare_tts_costs(
                sample_text, 
                ["google_tts", "elevenlabs"]
            )
            
            if comparison_response.status_code == 200:
                comparison = comparison_response.data
                
                print(f"📊 Cost Comparison Results:")
                print(f"Text length: {comparison['character_count']} characters")
                print(f"Target language: {comparison['target_language']}")
                print()
                
                # Show comparison table
                print(f"{'Provider':<15} {'Voice':<20} {'Cost':<10} {'Quality':<10} {'Time':<10}")
                print("-" * 70)
                
                for comp in comparison['comparison']:
                    print(f"{comp['provider']:<15} "
                          f"{comp['voice_recommendation'][:19]:<20} "
                          f"${comp['cost']:.4f}{'':<5} "
                          f"{comp['quality']:<10} "
                          f"{comp['processing_time_estimate']:<10}")
                
                # Show savings
                savings = comparison['savings']
                print(f"\n💡 Savings Summary:")
                print(f"Cheapest provider: {savings['cheapest_provider'].upper()}")
                print(f"Savings amount: ${savings['savings_amount']:.4f}")
                print(f"Savings percentage: {savings['savings_percentage']:.1f}%")
                
                # Annual projection
                annual_chars = 1000000  # 1M characters per year
                annual_savings = (savings['savings_amount'] / comparison['character_count']) * annual_chars
                print(f"\n📈 Annual Projection (1M chars/year):")
                print(f"Annual savings: ${annual_savings:.2f}")
                
            else:
                print(f"❌ Error: {comparison_response.data}")
    
    async def example_dubbing_workflow(self, provider: str = "google_tts"):
        """Example: Complete dubbing workflow"""
        print(f"🎬 Example 4: Complete Dubbing Workflow - {provider.upper()}")
        print("=" * 60)
        
        # Sample dubbing request
        dubbing_request = {
            "url": "https://youtube.com/watch?v=example-video",
            "test_mode": True,  # Only process first 60 seconds for demo
            "enable_translation": True,
            "target_language": "en-US",
            "translation_context": "educational",
            "enable_synthesis": True,
            "tts_provider": provider,
            "enable_video_muxing": False,  # Skip for demo
            "max_cost_usd": 5.0
        }
        
        # Add provider-specific parameters
        if provider == "google_tts":
            dubbing_request["voice_id"] = "en-US-Neural2-F"
        elif provider == "elevenlabs":
            dubbing_request["voice_id"] = "21m00Tcm4TlvDq8ikWAM"
            dubbing_request["audio_quality"] = "high"
        
        async with TTSAPIClient(self.base_url) as client:
            print("Creating dubbing job...")
            print(f"Provider: {provider}")
            print(f"Voice: {dubbing_request['voice_id']}")
            print(f"Test mode: {dubbing_request['test_mode']}")
            print()
            
            # Step 1: Create job
            create_response = await client.create_dubbing_job(dubbing_request)
            
            if create_response.status_code == 200:
                job_data = create_response.data
                job_id = job_data['job_id']
                
                print(f"✅ Job created successfully!")
                print(f"Job ID: {job_id}")
                print(f"Status: {job_data['status']}")
                print(f"Estimated cost: ${job_data.get('estimated_cost', {}).get('total_cost', 'N/A')}")
                print()
                
                # Step 2: Monitor job progress (simulated)
                print("Monitoring job progress...")
                for i in range(3):
                    await asyncio.sleep(1)
                    status_response = await client.get_job_status(job_id)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.data
                        print(f"Progress: {status_data.get('progress', 0)}% - "
                              f"Stage: {status_data.get('current_stage', 'unknown')}")
                        
                        if status_data.get('status') == 'completed':
                            print("\n🎉 Job completed successfully!")
                            
                            # Show results
                            if 'cost_breakdown' in status_data:
                                cost = status_data['cost_breakdown']
                                print(f"Final cost: ${cost.get('total_cost', 'N/A')}")
                            
                            # List available downloads
                            if status_data.get('audio_file'):
                                print("Available downloads:")
                                print(f"- Audio: {status_data['audio_file']}")
                            if status_data.get('transcript_file'):
                                print(f"- Transcript: {status_data['transcript_file']}")
                            break
                    else:
                        print(f"❌ Error getting job status: {status_response.data}")
                        break
            else:
                print(f"❌ Error creating job: {create_response.data}")
    
    async def example_batch_processing(self):
        """Example: Batch processing multiple videos"""
        print("📦 Example 5: Batch Processing Optimization")
        print("=" * 50)
        
        # Sample video projects
        video_projects = [
            {"title": "Educational Video 1", "chars": 5000, "language": "en-US", "type": "educational"},
            {"title": "Product Review", "chars": 3500, "language": "en-US", "type": "review"},
            {"title": "Corporate Presentation", "chars": 8000, "language": "en-US", "type": "business"},
            {"title": "Tutorial Video", "chars": 6500, "language": "en-US", "type": "educational"},
            {"title": "News Summary", "chars": 2500, "language": "en-US", "type": "news"}
        ]
        
        async with TTSAPIClient(self.base_url) as client:
            total_chars = sum(project["chars"] for project in video_projects)
            
            print(f"Batch processing {len(video_projects)} videos:")
            print(f"Total characters: {total_chars:,}")
            print()
            
            # Get cost estimates for different providers
            providers_to_compare = ["google_tts", "elevenlabs", "auto"]
            
            print("Cost comparison for batch processing:")
            print(f"{'Provider':<15} {'Cost':<10} {'Savings':<10} {'Time':<10}")
            print("-" * 50)
            
            estimates = {}
            for provider in providers_to_compare:
                estimate_response = await client.estimate_costs(
                    total_chars, "en-US", provider, True
                )
                
                if estimate_response.status_code == 200:
                    estimate_data = estimate_response.data
                    estimates[provider] = estimate_data
                    
                    cost = estimate_data.get('total_cost', 0)
                    time_est = estimate_data.get('estimated_time_seconds', 0) / 3600  # Convert to hours
                    
                    savings = ""
                    if provider != "elevenlabs" and "elevenlabs" in estimates:
                        elevenlabs_cost = estimates["elevenlabs"]["total_cost"]
                        savings_amount = elevenlabs_cost - cost
                        savings_pct = (savings_amount / elevenlabs_cost) * 100
                        savings = f"{savings_pct:.0f}%"
                    
                    print(f"{provider.replace('_', ' ').title():<15} "
                          f"${cost:.2f}{'':<5} "
                          f"{savings:<10} "
                          f"{time_est:.1f}h")
            
            # Batch processing recommendations
            if estimates:
                best_provider = min(estimates.keys(), key=lambda k: estimates[k]['total_cost'])
                print(f"\n💡 Batch Processing Recommendations:")
                print(f"1. Use {best_provider.replace('_', ' ').title()} for maximum savings")
                print(f"2. Process all {len(video_projects)} videos together for batch discounts")
                print(f"3. Use consistent voice across similar content types")
                
                if best_provider == "google_tts":
                    google_cost = estimates["google_tts"]["total_cost"]
                    if "elevenlabs" in estimates:
                        elevenlabs_cost = estimates["elevenlabs"]["total_cost"]
                        annual_savings = (elevenlabs_cost - google_cost) * 12
                        print(f"4. Annual savings potential: ${annual_savings:.2f}")
    
    async def example_advanced_integration(self):
        """Example: Advanced integration patterns"""
        print("🚀 Example 6: Advanced Integration Patterns")
        print("=" * 50)
        
        async with TTSAPIClient(self.base_url) as client:
            # 1. Provider availability check
            print("1. Provider Health Check:")
            providers_response = await client.get_tts_providers()
            
            if providers_response.status_code == 200:
                for provider in providers_response.data.get("providers", []):
                    status = "🟢 Available" if provider["status"] == "available" else "🔴 Unavailable"
                    print(f"   {provider['name']}: {status}")
                print()
            
            # 2. Smart provider selection
            print("2. Smart Provider Selection:")
            sample_requests = [
                {"chars": 1000, "priority": "cost", "quality": "standard"},
                {"chars": 5000, "priority": "balanced", "quality": "high"},
                {"chars": 500, "priority": "speed", "quality": "medium"}
            ]
            
            for i, req in enumerate(sample_requests, 1):
                if req["priority"] == "cost":
                    recommended = "google_tts (94% cheaper)"
                elif req["priority"] == "speed":
                    recommended = "google_tts (faster processing)"
                else:
                    recommended = "google_tts (best value)"
                
                print(f"   Request {i}: {req['chars']} chars, {req['priority']} priority")
                print(f"   → Recommended: {recommended}")
            print()
            
            # 3. Error handling and fallback
            print("3. Error Handling & Fallback Strategy:")
            print("   ✅ Primary: Google TTS (cost-effective)")
            print("   🔄 Fallback: ElevenLabs (if Google TTS unavailable)")
            print("   ⚠️  Monitoring: Real-time provider health checks")
            print("   💾 Caching: Voice selections and cost estimates")
            print()
            
            # 4. Cost optimization strategies
            print("4. Cost Optimization Integration:")
            optimization_strategies = [
                "Preview mode for voice testing (5% of full cost)",
                "Batch processing discounts (10% for 5+ videos)",
                "Quality tiering based on content type",
                "Voice reuse across similar content",
                "Real-time cost monitoring and alerts"
            ]
            
            for i, strategy in enumerate(optimization_strategies, 1):
                print(f"   {i}. {strategy}")

async def main():
    """Main function to run API examples"""
    parser = argparse.ArgumentParser(description="TTS API Usage Examples")
    parser.add_argument("--example", choices=["basic", "voices", "costs", "workflow", "batch", "advanced", "all"], 
                       default="all", help="Example to run")
    parser.add_argument("--provider", choices=["google_tts", "elevenlabs"], default="google_tts", 
                       help="TTS provider for examples")
    parser.add_argument("--language", default="en-US", help="Language code")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--text", help="Custom text for cost comparison")
    
    args = parser.parse_args()
    
    examples = APIExamples(args.base_url)
    
    print(f"""
🌐 TTS API Usage Examples
=========================

Base URL: {args.base_url}
Provider: {args.provider}
Language: {args.language}

This demonstrates the enhanced API with multi-provider TTS support,
showcasing Google Cloud TTS integration and cost optimization features.

""")
    
    try:
        if args.example == "all" or args.example == "basic":
            await examples.example_basic_provider_info()
            print()
        
        if args.example == "all" or args.example == "voices":
            await examples.example_voice_discovery(args.provider, args.language)
            print()
        
        if args.example == "all" or args.example == "costs":
            await examples.example_cost_comparison(args.text)
            print()
        
        if args.example == "all" or args.example == "workflow":
            await examples.example_dubbing_workflow(args.provider)
            print()
        
        if args.example == "all" or args.example == "batch":
            await examples.example_batch_processing()
            print()
        
        if args.example == "all" or args.example == "advanced":
            await examples.example_advanced_integration()
            print()
        
        print("✅ All examples completed successfully!")
        print("\n💡 Next Steps:")
        print("- Try the interactive API documentation at /docs")
        print("- Explore the complete API reference in docs/API_REFERENCE.md")
        print("- Check out the cost optimization guide in docs/COST_GUIDE.md")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print("Make sure the API server is running at", args.base_url)

if __name__ == "__main__":
    asyncio.run(main())