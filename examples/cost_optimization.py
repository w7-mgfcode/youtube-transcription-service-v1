#!/usr/bin/env python3
"""
💰 Cost Optimization Examples for Google TTS

This script demonstrates various cost optimization strategies
when using Google Cloud TTS for batch processing and large-scale
dubbing operations.

Usage:
    python examples/cost_optimization.py --strategy batch --videos 10
"""

import argparse
import json
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import random

@dataclass
class VideoProject:
    id: str
    title: str
    duration_minutes: int
    character_count: int
    language: str
    content_type: str
    
@dataclass 
class CostOptimizationResult:
    strategy: str
    original_cost: float
    optimized_cost: float
    savings_amount: float
    savings_percentage: float
    processing_time_hours: float
    recommendations: List[str]

class CostOptimizer:
    """Google TTS Cost Optimization Strategies"""
    
    def __init__(self):
        self.google_tts_rates = {
            "standard": 0.004 / 1000,    # $0.004 per 1K chars
            "wavenet": 0.016 / 1000,     # $0.016 per 1K chars  
            "neural2": 0.016 / 1000,     # $0.016 per 1K chars
            "studio": 0.016 / 1000       # $0.016 per 1K chars
        }
        
        self.elevenlabs_rate = 0.30 / 1000  # $0.30 per 1K chars
        
        # Sample video projects
        self.sample_projects = self._generate_sample_projects()
    
    def _generate_sample_projects(self) -> List[VideoProject]:
        """Generate sample video projects for demonstration"""
        projects = []
        
        project_templates = [
            {"title": "Hungarian History Documentary", "duration": 45, "chars": 33750, "lang": "hu-HU", "type": "educational"},
            {"title": "Tech Startup Pitch", "duration": 8, "chars": 6000, "lang": "en-US", "type": "business"},
            {"title": "Cooking Tutorial", "duration": 12, "chars": 9000, "lang": "en-US", "type": "lifestyle"},
            {"title": "Science Explainer", "duration": 20, "chars": 15000, "lang": "en-US", "type": "educational"},
            {"title": "Product Review", "duration": 15, "chars": 11250, "lang": "en-US", "type": "review"},
            {"title": "News Summary", "duration": 6, "chars": 4500, "lang": "hu-HU", "type": "news"},
            {"title": "Legal Analysis", "duration": 35, "chars": 26250, "lang": "en-US", "type": "professional"},
            {"title": "Meditation Guide", "duration": 25, "chars": 18750, "lang": "en-US", "type": "wellness"},
            {"title": "Gaming Stream Highlights", "duration": 18, "chars": 13500, "lang": "en-US", "type": "entertainment"},
            {"title": "Financial Planning Webinar", "duration": 55, "chars": 41250, "lang": "en-US", "type": "business"}
        ]
        
        for i, template in enumerate(project_templates):
            projects.append(VideoProject(
                id=f"video_{i+1:03d}",
                title=template["title"],
                duration_minutes=template["duration"],
                character_count=template["chars"],
                language=template["lang"],
                content_type=template["type"]
            ))
        
        return projects
    
    def strategy_batch_processing(self, videos: List[VideoProject]) -> CostOptimizationResult:
        """Batch processing cost optimization"""
        
        # Calculate original costs (assuming ElevenLabs)
        original_total = sum(video.character_count * self.elevenlabs_rate for video in videos)
        
        # Optimized cost with Google TTS Neural2
        optimized_total = sum(video.character_count * self.google_tts_rates["neural2"] for video in videos)
        
        # Additional batch savings (10% discount for 5+ videos)
        if len(videos) >= 5:
            batch_discount = optimized_total * 0.10
            optimized_total -= batch_discount
        
        savings = original_total - optimized_total
        savings_pct = (savings / original_total * 100) if original_total > 0 else 0
        
        # Estimated processing time
        total_chars = sum(video.character_count for video in videos)
        processing_time = (total_chars / 10000) * 0.5  # Estimate: 30 min per 10K chars with parallel processing
        
        recommendations = [
            "Use Google TTS Neural2 for 94% cost savings",
            f"Batch process {len(videos)} videos for additional 10% discount" if len(videos) >= 5 else "Consider batching more videos for additional discounts",
            "Process in parallel to reduce total time",
            "Use consistent voice across similar content types",
            "Enable chunked processing for long content"
        ]
        
        return CostOptimizationResult(
            strategy="batch_processing",
            original_cost=original_total,
            optimized_cost=optimized_total,
            savings_amount=savings,
            savings_percentage=savings_pct,
            processing_time_hours=processing_time,
            recommendations=recommendations
        )
    
    def strategy_quality_tiering(self, videos: List[VideoProject]) -> CostOptimizationResult:
        """Quality-based tiering optimization"""
        
        original_total = sum(video.character_count * self.elevenlabs_rate for video in videos)
        
        optimized_total = 0
        quality_distribution = {"standard": 0, "wavenet": 0, "neural2": 0}
        
        for video in videos:
            # Assign quality tier based on content type
            if video.content_type in ["business", "professional", "news"]:
                # High-quality for professional content
                tier = "neural2"
            elif video.content_type in ["educational", "review"]:
                # Medium-quality for general content  
                tier = "wavenet"
            else:
                # Standard quality for casual content
                tier = "standard"
            
            cost = video.character_count * self.google_tts_rates[tier]
            optimized_total += cost
            quality_distribution[tier] += 1
        
        savings = original_total - optimized_total
        savings_pct = (savings / original_total * 100) if original_total > 0 else 0
        
        processing_time = sum(video.duration_minutes for video in videos) / 60 * 0.1  # 10% of content duration
        
        recommendations = [
            f"Use Neural2 for {quality_distribution['neural2']} professional videos",
            f"Use WaveNet for {quality_distribution['wavenet']} general content videos", 
            f"Use Standard for {quality_distribution['standard']} casual content videos",
            "Match quality tier to content importance and budget",
            "Test quality tiers with preview mode first"
        ]
        
        return CostOptimizationResult(
            strategy="quality_tiering",
            original_cost=original_total,
            optimized_cost=optimized_total,
            savings_amount=savings,
            savings_percentage=savings_pct,
            processing_time_hours=processing_time,
            recommendations=recommendations
        )
    
    def strategy_preview_first(self, videos: List[VideoProject]) -> CostOptimizationResult:
        """Preview-first optimization strategy"""
        
        original_total = sum(video.character_count * self.elevenlabs_rate for video in videos)
        
        # Cost for previews (first 60 seconds, ~300 chars average)
        preview_chars_per_video = 300
        preview_cost = len(videos) * preview_chars_per_video * self.google_tts_rates["neural2"]
        
        # Assume 20% of videos need revisions after preview
        revision_rate = 0.2
        revision_cost = len(videos) * revision_rate * preview_chars_per_video * self.google_tts_rates["neural2"]
        
        # Main synthesis cost (after previews approved)
        main_synthesis_cost = sum(video.character_count * self.google_tts_rates["neural2"] for video in videos)
        
        optimized_total = preview_cost + revision_cost + main_synthesis_cost
        
        savings = original_total - optimized_total
        savings_pct = (savings / original_total * 100) if original_total > 0 else 0
        
        processing_time = len(videos) * 0.5 + sum(video.duration_minutes for video in videos) / 60 * 0.15
        
        recommendations = [
            "Generate 60-second previews for all videos first",
            "Get approval before full synthesis",
            "Use preview feedback to optimize voice selection", 
            "Prevents costly re-synthesis of full videos",
            f"Expect ~{revision_rate*100:.0f}% revision rate in preview phase"
        ]
        
        return CostOptimizationResult(
            strategy="preview_first",
            original_cost=original_total,
            optimized_cost=optimized_total,
            savings_amount=savings,
            savings_percentage=savings_pct,
            processing_time_hours=processing_time,
            recommendations=recommendations
        )
    
    def strategy_voice_reuse(self, videos: List[VideoProject]) -> CostOptimizationResult:
        """Voice reuse and consistency optimization"""
        
        original_total = sum(video.character_count * self.elevenlabs_rate for video in videos)
        
        # Google TTS with optimized voice selection
        optimized_total = sum(video.character_count * self.google_tts_rates["neural2"] for video in videos)
        
        # Group videos by content type for voice consistency
        content_groups = {}
        for video in videos:
            if video.content_type not in content_groups:
                content_groups[video.content_type] = []
            content_groups[video.content_type].append(video)
        
        # Voice selection cost savings (avoid re-testing voices)
        voice_selection_savings = (len(videos) - len(content_groups)) * 0.50  # $0.50 per voice test avoided
        optimized_total -= voice_selection_savings
        
        savings = original_total - optimized_total
        savings_pct = (savings / original_total * 100) if original_total > 0 else 0
        
        processing_time = sum(video.duration_minutes for video in videos) / 60 * 0.08  # Faster with consistent voices
        
        recommendations = [
            f"Group {len(videos)} videos into {len(content_groups)} content types",
            "Use consistent voice per content type/channel",
            "Avoid re-testing voices for similar content",
            "Create voice library for different content categories",
            "Document voice choices for future projects"
        ]
        
        return CostOptimizationResult(
            strategy="voice_reuse",
            original_cost=original_total,
            optimized_cost=optimized_total,
            savings_amount=savings,
            savings_percentage=savings_pct,
            processing_time_hours=processing_time,
            recommendations=recommendations
        )
    
    def generate_optimization_report(self, videos: List[VideoProject], strategies: List[str]) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        
        results = {}
        
        if "batch" in strategies:
            results["batch_processing"] = self.strategy_batch_processing(videos)
        
        if "quality" in strategies:
            results["quality_tiering"] = self.strategy_quality_tiering(videos)
        
        if "preview" in strategies:
            results["preview_first"] = self.strategy_preview_first(videos)
        
        if "voice" in strategies:
            results["voice_reuse"] = self.strategy_voice_reuse(videos)
        
        # Calculate combined optimization
        if len(results) > 1:
            results["combined"] = self._calculate_combined_optimization(videos, results)
        
        return {
            "project_summary": {
                "total_videos": len(videos),
                "total_characters": sum(v.character_count for v in videos),
                "total_duration_hours": sum(v.duration_minutes for v in videos) / 60,
                "languages": list(set(v.language for v in videos)),
                "content_types": list(set(v.content_type for v in videos))
            },
            "optimization_results": results,
            "recommendations": self._generate_final_recommendations(results),
            "generated_at": datetime.now().isoformat()
        }
    
    def _calculate_combined_optimization(self, videos: List[VideoProject], individual_results: Dict) -> CostOptimizationResult:
        """Calculate combined optimization strategy"""
        
        original_total = sum(video.character_count * self.elevenlabs_rate for video in videos)
        
        # Start with Google TTS Neural2 base cost
        optimized_total = sum(video.character_count * self.google_tts_rates["neural2"] for video in videos)
        
        # Apply combined savings
        batch_discount = optimized_total * 0.10 if len(videos) >= 5 else 0
        voice_testing_savings = (len(videos) - len(set(v.content_type for v in videos))) * 0.50
        
        optimized_total = optimized_total - batch_discount - voice_testing_savings
        
        savings = original_total - optimized_total
        savings_pct = (savings / original_total * 100) if original_total > 0 else 0
        
        processing_time = sum(video.duration_minutes for video in videos) / 60 * 0.08
        
        recommendations = [
            "Combine multiple optimization strategies for maximum savings",
            "Use Google TTS for 94% base cost savings",
            "Implement batch processing discounts",
            "Maintain voice consistency across projects",
            "Always use preview mode for quality validation"
        ]
        
        return CostOptimizationResult(
            strategy="combined_optimization",
            original_cost=original_total,
            optimized_cost=optimized_total,
            savings_amount=savings,
            savings_percentage=savings_pct,
            processing_time_hours=processing_time,
            recommendations=recommendations
        )
    
    def _generate_final_recommendations(self, results: Dict) -> List[str]:
        """Generate final optimization recommendations"""
        
        recommendations = [
            "🎯 PRIMARY RECOMMENDATION: Switch to Google Cloud TTS for 90%+ cost savings",
            "💰 BATCH PROCESSING: Process 5+ videos together for additional discounts",
            "🎭 VOICE CONSISTENCY: Reuse voices across similar content types",
            "👀 PREVIEW FIRST: Always generate previews before full synthesis",
            "⚖️ QUALITY TIERING: Match voice quality to content importance and budget"
        ]
        
        # Add specific recommendations based on results
        if "batch_processing" in results:
            batch_result = results["batch_processing"]
            recommendations.append(f"💡 BATCH SAVINGS: Save ${batch_result.savings_amount:.2f} ({batch_result.savings_percentage:.1f}%) with batch processing")
        
        if "combined" in results:
            combined_result = results["combined"]
            recommendations.append(f"🚀 MAXIMUM SAVINGS: Combined strategies save ${combined_result.savings_amount:.2f} ({combined_result.savings_percentage:.1f}%)")
        
        return recommendations

def main():
    """Main demo function"""
    parser = argparse.ArgumentParser(description="TTS Cost Optimization Demo")
    parser.add_argument("--strategy", choices=["batch", "quality", "preview", "voice", "all"], 
                       default="all", help="Optimization strategy to demonstrate")
    parser.add_argument("--videos", type=int, default=10, help="Number of videos to optimize")
    parser.add_argument("--output", help="Save results to JSON file")
    
    args = parser.parse_args()
    
    optimizer = CostOptimizer()
    
    # Select videos for optimization
    selected_videos = optimizer.sample_projects[:args.videos]
    
    # Determine strategies to run
    if args.strategy == "all":
        strategies = ["batch", "quality", "preview", "voice"]
    else:
        strategies = [args.strategy]
    
    print(f"""
💰 TTS Cost Optimization Demo
===============================

Analyzing {len(selected_videos)} video projects for cost optimization opportunities.
Strategies: {', '.join(strategies)}

""")
    
    # Generate optimization report
    report = optimizer.generate_optimization_report(selected_videos, strategies)
    
    # Display results
    print(f"📊 PROJECT SUMMARY")
    print(f"{'='*50}")
    summary = report["project_summary"]
    print(f"Total Videos: {summary['total_videos']}")
    print(f"Total Characters: {summary['total_characters']:,}")
    print(f"Total Duration: {summary['total_duration_hours']:.1f} hours")
    print(f"Languages: {', '.join(summary['languages'])}")
    print(f"Content Types: {', '.join(summary['content_types'])}")
    
    print(f"\n💡 OPTIMIZATION RESULTS")
    print(f"{'='*80}")
    print(f"{'Strategy':<20} {'Original':<12} {'Optimized':<12} {'Savings':<12} {'Time (hrs)':<12}")
    print(f"{'-'*80}")
    
    for strategy_name, result in report["optimization_results"].items():
        if isinstance(result, CostOptimizationResult):
            print(f"{strategy_name.replace('_', ' ').title():<20} "
                  f"${result.original_cost:.2f:<11} "
                  f"${result.optimized_cost:.2f:<11} "
                  f"{result.savings_percentage:.1f}%{'':<8} "
                  f"{result.processing_time_hours:.1f}")
    
    # Show detailed recommendations
    print(f"\n🎯 OPTIMIZATION RECOMMENDATIONS")
    print(f"{'='*50}")
    for i, recommendation in enumerate(report["recommendations"], 1):
        print(f"{i}. {recommendation}")
    
    # Show annual projections
    if "combined" in report["optimization_results"]:
        combined = report["optimization_results"]["combined"]
        annual_savings = combined.savings_amount * 12  # Assuming monthly processing
        print(f"\n📈 ANNUAL PROJECTIONS")
        print(f"{'='*30}")
        print(f"Monthly Savings: ${combined.savings_amount:.2f}")
        print(f"Annual Savings: ${annual_savings:.2f}")
        print(f"ROI on Google Cloud Setup: {annual_savings/100:.0f}x (assuming $100 setup cost)")
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            # Convert CostOptimizationResult objects to dictionaries for JSON serialization
            json_report = report.copy()
            for key, value in json_report["optimization_results"].items():
                if isinstance(value, CostOptimizationResult):
                    json_report["optimization_results"][key] = {
                        "strategy": value.strategy,
                        "original_cost": value.original_cost,
                        "optimized_cost": value.optimized_cost,
                        "savings_amount": value.savings_amount,
                        "savings_percentage": value.savings_percentage,
                        "processing_time_hours": value.processing_time_hours,
                        "recommendations": value.recommendations
                    }
            
            json.dump(json_report, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {args.output}")

if __name__ == "__main__":
    main()