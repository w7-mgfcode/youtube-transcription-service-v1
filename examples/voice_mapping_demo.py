#!/usr/bin/env python3
"""
🎭 Voice Mapping Demo - ElevenLabs to Google TTS Conversion

This script demonstrates the voice mapping system that enables seamless
migration from ElevenLabs to Google Cloud TTS while preserving voice
characteristics and maintaining consistency.

Usage:
    python examples/voice_mapping_demo.py --mapping rachel --language en-US
"""

import argparse
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import json

@dataclass
class VoiceProfile:
    id: str
    name: str
    gender: str
    accent: str
    age: str
    description: str
    use_case: str
    provider: str
    cost_per_1k_chars: float
    
@dataclass
class VoiceMappingResult:
    elevenlabs_voice: VoiceProfile
    google_tts_equivalent: VoiceProfile
    similarity_score: float
    cost_savings: float
    cost_savings_percentage: float
    mapping_confidence: str
    characteristics_match: Dict[str, bool]
    recommendations: List[str]

class VoiceMappingDemo:
    """Demonstrate voice mapping between ElevenLabs and Google TTS"""
    
    def __init__(self):
        self.elevenlabs_voices = self._initialize_elevenlabs_voices()
        self.google_tts_voices = self._initialize_google_tts_voices()
        self.voice_mappings = self._create_voice_mappings()
    
    def _initialize_elevenlabs_voices(self) -> Dict[str, VoiceProfile]:
        """Initialize ElevenLabs voice profiles"""
        return {
            "rachel": VoiceProfile(
                id="21m00Tcm4TlvDq8ikWAM",
                name="Rachel",
                gender="female",
                accent="american",
                age="young_adult",
                description="calm, clear, professional, educational",
                use_case="educational, documentary, professional",
                provider="elevenlabs",
                cost_per_1k_chars=0.30
            ),
            "adam": VoiceProfile(
                id="pNInz6obpgDQGcFmaJgB",
                name="Adam",
                gender="male",
                accent="american", 
                age="middle_aged",
                description="deep, authoritative, confident, professional",
                use_case="documentary, news, serious content",
                provider="elevenlabs",
                cost_per_1k_chars=0.30
            ),
            "sam": VoiceProfile(
                id="yoZ06aMxZJJ28mfd3POQ",
                name="Sam",
                gender="male",
                accent="american",
                age="young_adult",
                description="friendly, conversational, energetic, casual",
                use_case="vlogs, entertainment, casual content",
                provider="elevenlabs",
                cost_per_1k_chars=0.30
            ),
            "bella": VoiceProfile(
                id="EXAVITQu4vr4xnSDxMaL",
                name="Bella",
                gender="female",
                accent="american",
                age="young_adult", 
                description="friendly, approachable, versatile, warm",
                use_case="lifestyle, personal stories, reviews",
                provider="elevenlabs",
                cost_per_1k_chars=0.30
            ),
            "antoni": VoiceProfile(
                id="ErXwobaYiN019PkySvjV",
                name="Antoni",
                gender="male",
                accent="american",
                age="adult",
                description="energetic, versatile, adaptable, dynamic",
                use_case="entertainment, vlogs, dynamic content",
                provider="elevenlabs",
                cost_per_1k_chars=0.30
            ),
            "dorothy": VoiceProfile(
                id="ThT5KcBeYPX3keUQqHPh",
                name="Dorothy",
                gender="female",
                accent="british",
                age="adult",
                description="sophisticated, clear, cultured, refined",
                use_case="british content, formal presentations",
                provider="elevenlabs",
                cost_per_1k_chars=0.30
            )
        }
    
    def _initialize_google_tts_voices(self) -> Dict[str, VoiceProfile]:
        """Initialize Google TTS voice profiles"""
        return {
            "en_us_neural2_f": VoiceProfile(
                id="en-US-Neural2-F",
                name="Neural2 Female F",
                gender="female",
                accent="american",
                age="young_adult",
                description="professional, clear, educational, natural",
                use_case="educational, professional, documentary",
                provider="google_tts",
                cost_per_1k_chars=0.016
            ),
            "en_us_neural2_d": VoiceProfile(
                id="en-US-Neural2-D",
                name="Neural2 Male D",
                gender="male",
                accent="american",
                age="middle_aged",
                description="conversational, warm, engaging, authoritative",
                use_case="casual content, narratives, presentations",
                provider="google_tts",
                cost_per_1k_chars=0.016
            ),
            "en_us_neural2_a": VoiceProfile(
                id="en-US-Neural2-A",
                name="Neural2 Male A",
                gender="male",
                accent="american",
                age="adult",
                description="authoritative, confident, professional, clear",
                use_case="news, documentaries, serious content",
                provider="google_tts",
                cost_per_1k_chars=0.016
            ),
            "en_us_neural2_g": VoiceProfile(
                id="en-US-Neural2-G",
                name="Neural2 Female G",
                gender="female",
                accent="american",
                age="young_adult",
                description="friendly, approachable, versatile, warm",
                use_case="lifestyle, personal stories, casual content",
                provider="google_tts",
                cost_per_1k_chars=0.016
            ),
            "en_us_neural2_j": VoiceProfile(
                id="en-US-Neural2-J",
                name="Neural2 Male J",
                gender="male",
                accent="american",
                age="adult",
                description="energetic, versatile, adaptable, dynamic",
                use_case="entertainment, vlogs, dynamic content",
                provider="google_tts",
                cost_per_1k_chars=0.016
            ),
            "en_gb_neural2_a": VoiceProfile(
                id="en-GB-Neural2-A",
                name="Neural2 Female A (British)",
                gender="female",
                accent="british",
                age="adult",
                description="sophisticated, clear, cultured, professional",
                use_case="british content, formal presentations",
                provider="google_tts",
                cost_per_1k_chars=0.016
            ),
            "hu_hu_neural2_a": VoiceProfile(
                id="hu-HU-Neural2-A",
                name="Neural2 Female A (Hungarian)",
                gender="female",
                accent="hungarian",
                age="adult",
                description="clear, natural, professional, authoritative",
                use_case="hungarian content, educational, professional",
                provider="google_tts",
                cost_per_1k_chars=0.016
            ),
            "hu_hu_neural2_b": VoiceProfile(
                id="hu-HU-Neural2-B",
                name="Neural2 Male B (Hungarian)",
                gender="male",
                accent="hungarian",
                age="adult",
                description="authoritative, clear, trustworthy, professional",
                use_case="hungarian content, business, documentary",
                provider="google_tts",
                cost_per_1k_chars=0.016
            )
        }
    
    def _create_voice_mappings(self) -> Dict[str, str]:
        """Create voice mapping between ElevenLabs and Google TTS"""
        return {
            "rachel": "en_us_neural2_f",      # Professional female
            "adam": "en_us_neural2_d",        # Conversational male (better match than A)
            "sam": "en_us_neural2_a",         # Authoritative male  
            "bella": "en_us_neural2_g",       # Friendly female
            "antoni": "en_us_neural2_j",      # Energetic male
            "dorothy": "en_gb_neural2_a"      # British female
        }
    
    def analyze_voice_mapping(self, elevenlabs_voice_key: str) -> VoiceMappingResult:
        """Analyze voice mapping between ElevenLabs and Google TTS"""
        
        if elevenlabs_voice_key not in self.elevenlabs_voices:
            raise ValueError(f"ElevenLabs voice '{elevenlabs_voice_key}' not found")
        
        elevenlabs_voice = self.elevenlabs_voices[elevenlabs_voice_key]
        
        if elevenlabs_voice_key not in self.voice_mappings:
            raise ValueError(f"No mapping found for ElevenLabs voice '{elevenlabs_voice_key}'")
        
        google_voice_key = self.voice_mappings[elevenlabs_voice_key]
        google_voice = self.google_tts_voices[google_voice_key]
        
        # Calculate similarity score
        similarity_score = self._calculate_similarity_score(elevenlabs_voice, google_voice)
        
        # Calculate cost savings
        cost_savings = elevenlabs_voice.cost_per_1k_chars - google_voice.cost_per_1k_chars
        cost_savings_pct = (cost_savings / elevenlabs_voice.cost_per_1k_chars) * 100
        
        # Analyze characteristic matches
        characteristics_match = self._analyze_characteristics(elevenlabs_voice, google_voice)
        
        # Determine mapping confidence
        mapping_confidence = self._determine_mapping_confidence(similarity_score, characteristics_match)
        
        # Generate recommendations
        recommendations = self._generate_mapping_recommendations(
            elevenlabs_voice, google_voice, similarity_score, characteristics_match
        )
        
        return VoiceMappingResult(
            elevenlabs_voice=elevenlabs_voice,
            google_tts_equivalent=google_voice,
            similarity_score=similarity_score,
            cost_savings=cost_savings,
            cost_savings_percentage=cost_savings_pct,
            mapping_confidence=mapping_confidence,
            characteristics_match=characteristics_match,
            recommendations=recommendations
        )
    
    def _calculate_similarity_score(self, voice1: VoiceProfile, voice2: VoiceProfile) -> float:
        """Calculate similarity score between two voices"""
        
        score = 0.0
        total_weight = 0.0
        
        # Gender match (weight: 30%)
        if voice1.gender == voice2.gender:
            score += 30
        total_weight += 30
        
        # Accent match (weight: 25%)
        if voice1.accent == voice2.accent:
            score += 25
        elif voice1.accent == "american" and voice2.accent == "american":
            score += 25
        total_weight += 25
        
        # Age similarity (weight: 15%)
        age_compatibility = {
            ("young_adult", "young_adult"): 15,
            ("adult", "adult"): 15,
            ("middle_aged", "middle_aged"): 15,
            ("young_adult", "adult"): 10,
            ("adult", "young_adult"): 10,
        }
        age_key = (voice1.age, voice2.age)
        if age_key in age_compatibility:
            score += age_compatibility[age_key]
        elif age_key[::-1] in age_compatibility:
            score += age_compatibility[age_key[::-1]]
        total_weight += 15
        
        # Use case similarity (weight: 20%)
        voice1_uses = set(voice1.use_case.split(", "))
        voice2_uses = set(voice2.use_case.split(", "))
        common_uses = voice1_uses.intersection(voice2_uses)
        use_case_score = (len(common_uses) / len(voice1_uses.union(voice2_uses))) * 20
        score += use_case_score
        total_weight += 20
        
        # Description similarity (weight: 10%)
        voice1_desc = set(voice1.description.split(", "))
        voice2_desc = set(voice2.description.split(", "))
        common_desc = voice1_desc.intersection(voice2_desc)
        desc_score = (len(common_desc) / len(voice1_desc.union(voice2_desc))) * 10
        score += desc_score
        total_weight += 10
        
        return min(score / total_weight * 100, 100.0)
    
    def _analyze_characteristics(self, voice1: VoiceProfile, voice2: VoiceProfile) -> Dict[str, bool]:
        """Analyze which characteristics match between voices"""
        
        return {
            "gender_match": voice1.gender == voice2.gender,
            "accent_match": voice1.accent == voice2.accent,
            "age_compatible": self._are_ages_compatible(voice1.age, voice2.age),
            "use_case_overlap": bool(set(voice1.use_case.split(", ")).intersection(
                set(voice2.use_case.split(", "))
            )),
            "description_overlap": bool(set(voice1.description.split(", ")).intersection(
                set(voice2.description.split(", "))
            ))
        }
    
    def _are_ages_compatible(self, age1: str, age2: str) -> bool:
        """Check if ages are compatible"""
        compatible_ages = [
            ("young_adult", "adult"),
            ("adult", "young_adult"),
            ("young_adult", "young_adult"),
            ("adult", "adult"),
            ("middle_aged", "middle_aged")
        ]
        return (age1, age2) in compatible_ages
    
    def _determine_mapping_confidence(self, similarity_score: float, characteristics: Dict[str, bool]) -> str:
        """Determine mapping confidence level"""
        
        if similarity_score >= 85 and sum(characteristics.values()) >= 4:
            return "excellent"
        elif similarity_score >= 70 and sum(characteristics.values()) >= 3:
            return "good"
        elif similarity_score >= 55:
            return "acceptable"
        else:
            return "poor"
    
    def _generate_mapping_recommendations(
        self, 
        elevenlabs_voice: VoiceProfile, 
        google_voice: VoiceProfile,
        similarity_score: float,
        characteristics: Dict[str, bool]
    ) -> List[str]:
        """Generate mapping recommendations"""
        
        recommendations = []
        
        # Cost savings recommendation
        cost_savings_pct = ((elevenlabs_voice.cost_per_1k_chars - google_voice.cost_per_1k_chars) / 
                           elevenlabs_voice.cost_per_1k_chars) * 100
        recommendations.append(f"💰 Save {cost_savings_pct:.1f}% on synthesis costs by switching to Google TTS")
        
        # Quality recommendation
        if similarity_score >= 80:
            recommendations.append("✅ Excellent voice match - seamless migration possible")
        elif similarity_score >= 65:
            recommendations.append("👍 Good voice match - minor adjustments may be needed")
        else:
            recommendations.append("⚠️ Moderate match - consider voice testing before full migration")
        
        # Specific characteristic recommendations
        if not characteristics["gender_match"]:
            recommendations.append("⚠️ Gender mismatch - consider if this affects your brand consistency")
        
        if not characteristics["accent_match"] and "british" in [elevenlabs_voice.accent, google_voice.accent]:
            recommendations.append("🇬🇧 Accent change from British to American (or vice versa)")
        
        if characteristics["use_case_overlap"]:
            recommendations.append("🎯 Use cases align well - voice suitable for your content type")
        
        # Migration strategy
        if similarity_score >= 70:
            recommendations.append("🚀 Recommended migration strategy: Direct replacement")
        else:
            recommendations.append("🔄 Recommended migration strategy: Gradual transition with A/B testing")
        
        # Testing recommendation
        recommendations.append("🎧 Always test with your actual content before full migration")
        
        return recommendations
    
    def demonstrate_all_mappings(self) -> Dict[str, VoiceMappingResult]:
        """Demonstrate all available voice mappings"""
        
        results = {}
        
        print(f"🎭 Voice Mapping Analysis")
        print(f"{'='*80}")
        print(f"Analyzing all ElevenLabs to Google TTS voice mappings...\n")
        
        for elevenlabs_key in self.voice_mappings:
            result = self.analyze_voice_mapping(elevenlabs_key)
            results[elevenlabs_key] = result
            
            # Display individual result
            self._display_mapping_result(result)
            print()
        
        return results
    
    def _display_mapping_result(self, result: VoiceMappingResult):
        """Display voice mapping result"""
        
        el_voice = result.elevenlabs_voice
        gt_voice = result.google_tts_equivalent
        
        print(f"🎤 {el_voice.name} → {gt_voice.name}")
        print(f"   ElevenLabs: {el_voice.id}")
        print(f"   Google TTS: {gt_voice.id}")
        print(f"   Similarity: {result.similarity_score:.1f}% | Confidence: {result.mapping_confidence.title()}")
        print(f"   Cost: ${el_voice.cost_per_1k_chars:.3f} → ${gt_voice.cost_per_1k_chars:.3f} "
              f"({result.cost_savings_percentage:.1f}% savings)")
        
        # Show characteristics
        matches = [k for k, v in result.characteristics_match.items() if v]
        print(f"   Matches: {', '.join(matches).replace('_', ' ').title()}")
        
        # Show top recommendation
        if result.recommendations:
            print(f"   💡 {result.recommendations[0]}")
    
    def migration_cost_calculator(self, monthly_characters: int, voices_used: List[str]) -> Dict[str, Any]:
        """Calculate migration cost savings"""
        
        elevenlabs_monthly_cost = 0
        google_tts_monthly_cost = 0
        
        migration_analysis = {}
        
        for voice_key in voices_used:
            if voice_key in self.elevenlabs_voices and voice_key in self.voice_mappings:
                el_voice = self.elevenlabs_voices[voice_key]
                gt_voice_key = self.voice_mappings[voice_key]
                gt_voice = self.google_tts_voices[gt_voice_key]
                
                voice_chars = monthly_characters // len(voices_used)  # Distribute evenly
                
                el_cost = voice_chars * el_voice.cost_per_1k_chars
                gt_cost = voice_chars * gt_voice.cost_per_1k_chars
                
                elevenlabs_monthly_cost += el_cost
                google_tts_monthly_cost += gt_cost
                
                migration_analysis[voice_key] = {
                    "elevenlabs_cost": el_cost,
                    "google_tts_cost": gt_cost,
                    "savings": el_cost - gt_cost,
                    "savings_percentage": ((el_cost - gt_cost) / el_cost * 100) if el_cost > 0 else 0
                }
        
        total_savings = elevenlabs_monthly_cost - google_tts_monthly_cost
        total_savings_pct = (total_savings / elevenlabs_monthly_cost * 100) if elevenlabs_monthly_cost > 0 else 0
        
        return {
            "monthly_analysis": {
                "elevenlabs_cost": elevenlabs_monthly_cost,
                "google_tts_cost": google_tts_monthly_cost,
                "savings_amount": total_savings,
                "savings_percentage": total_savings_pct
            },
            "annual_projections": {
                "elevenlabs_cost": elevenlabs_monthly_cost * 12,
                "google_tts_cost": google_tts_monthly_cost * 12,
                "savings_amount": total_savings * 12,
                "roi_months": 1 if total_savings > 0 else float('inf')  # Immediate ROI
            },
            "voice_analysis": migration_analysis,
            "characters_processed": monthly_characters,
            "voices_analyzed": len(voices_used)
        }

def main():
    """Main demo function"""
    parser = argparse.ArgumentParser(description="Voice Mapping Demo")
    parser.add_argument("--mapping", choices=["rachel", "adam", "sam", "bella", "antoni", "dorothy", "all"], 
                       default="all", help="Voice mapping to demonstrate")
    parser.add_argument("--language", choices=["en-US", "hu-HU", "en-GB"], default="en-US", help="Target language")
    parser.add_argument("--characters", type=int, default=100000, help="Monthly characters for cost calculation")
    parser.add_argument("--output", help="Save results to JSON file")
    
    args = parser.parse_args()
    
    demo = VoiceMappingDemo()
    
    print(f"""
🎭 Voice Mapping Demo - ElevenLabs to Google TTS
================================================

This demo shows how to migrate from ElevenLabs to Google Cloud TTS
while maintaining voice consistency and achieving 94% cost savings.

Language: {args.language}
Monthly Characters: {args.characters:,}

""")
    
    if args.mapping == "all":
        # Demonstrate all mappings
        results = demo.demonstrate_all_mappings()
        
        # Show cost calculation
        all_voices = ["rachel", "adam", "sam", "bella", "antoni"]
        cost_analysis = demo.migration_cost_calculator(args.characters, all_voices)
        
        print(f"💰 MIGRATION COST ANALYSIS")
        print(f"{'='*50}")
        print(f"Monthly Characters: {args.characters:,}")
        print(f"ElevenLabs Cost: ${cost_analysis['monthly_analysis']['elevenlabs_cost']:.2f}")
        print(f"Google TTS Cost: ${cost_analysis['monthly_analysis']['google_tts_cost']:.2f}")
        print(f"Monthly Savings: ${cost_analysis['monthly_analysis']['savings_amount']:.2f} "
              f"({cost_analysis['monthly_analysis']['savings_percentage']:.1f}%)")
        print(f"Annual Savings: ${cost_analysis['annual_projections']['savings_amount']:.2f}")
        
    else:
        # Demonstrate specific mapping
        result = demo.analyze_voice_mapping(args.mapping)
        demo._display_mapping_result(result)
        
        # Show detailed recommendations
        print(f"\n🎯 DETAILED RECOMMENDATIONS")
        print(f"{'='*40}")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"{i}. {rec}")
        
        # Cost calculation for single voice
        cost_analysis = demo.migration_cost_calculator(args.characters, [args.mapping])
        print(f"\n💰 COST SAVINGS PROJECTION")
        print(f"{'='*30}")
        print(f"Monthly: ${cost_analysis['monthly_analysis']['savings_amount']:.2f}")
        print(f"Annual: ${cost_analysis['annual_projections']['savings_amount']:.2f}")
        
        results = {args.mapping: result}
    
    # Save results if requested
    if args.output:
        # Convert results to JSON-serializable format
        json_results = {}
        for key, result in results.items():
            if isinstance(result, VoiceMappingResult):
                json_results[key] = {
                    "elevenlabs_voice": result.elevenlabs_voice.__dict__,
                    "google_tts_equivalent": result.google_tts_equivalent.__dict__,
                    "similarity_score": result.similarity_score,
                    "cost_savings": result.cost_savings,
                    "cost_savings_percentage": result.cost_savings_percentage,
                    "mapping_confidence": result.mapping_confidence,
                    "characteristics_match": result.characteristics_match,
                    "recommendations": result.recommendations
                }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {args.output}")

if __name__ == "__main__":
    main()