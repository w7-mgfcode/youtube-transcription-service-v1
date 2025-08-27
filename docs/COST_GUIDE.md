# Cost Estimation & Billing Guide

## 💰 Complete Cost Management for YouTube Dubbing Service

This guide provides comprehensive information about cost estimation, billing, and budget management for the multilingual dubbing service.

---

## 🚀 Quick Cost Estimation

### Get Instant Cost Estimate

#### Multi-Provider Cost Comparison
```bash
# Compare costs across providers
curl -X GET "http://localhost:8000/v1/tts-cost-comparison?text=sample text&providers=google_tts,elevenlabs"
```

#### Individual Provider Estimates
```bash
# Google TTS estimate (94% cheaper)
curl -X GET "http://localhost:8000/v1/cost-estimate?transcript_length=2000&target_language=en-US&tts_provider=google_tts&enable_synthesis=true"

# ElevenLabs estimate (premium quality)
curl -X GET "http://localhost:8000/v1/cost-estimate?transcript_length=2000&target_language=en-US&tts_provider=elevenlabs&audio_quality=high"

# Auto provider (cost-optimized)
curl -X GET "http://localhost:8000/v1/cost-estimate?transcript_length=2000&target_language=en-US&tts_provider=auto&enable_synthesis=true"
```

**Google TTS Response (94% Savings):**
```json
{
  "character_count": 2000,
  "translation_cost": 0.0004,
  "synthesis_cost": 0.032,
  "video_muxing_cost": 0,
  "total_cost": 0.0324,
  "estimated_time_seconds": 90,
  "provider": "google_tts",
  "savings_vs_elevenlabs": 0.5676,
  "savings_percentage": 94.6,
  "breakdown": {
    "translation": {
      "rate_per_million_chars": 20.0,
      "characters": 2000,
      "cost": 0.0004
    },
    "synthesis": {
      "provider": "google_tts",
      "rate_per_thousand_chars": 0.016,
      "characters": 2000,
      "voice_type": "Neural2",
      "cost": 0.032
    }
  }
}
```

**ElevenLabs Response:**
```json
{
  "character_count": 2000,
  "translation_cost": 0.0004,
  "synthesis_cost": 0.60,
  "video_muxing_cost": 0,
  "total_cost": 0.6004,
  "estimated_time_seconds": 90,
  "provider": "elevenlabs",
  "breakdown": {
    "translation": {
      "rate_per_million_chars": 20.0,
      "characters": 2000,
      "cost": 0.0004
    },
    "synthesis": {
      "provider": "elevenlabs",
      "rate_per_thousand_chars": 0.30,
      "characters": 2000,
      "quality_multiplier": 1.0,
      "cost": 0.60
    }
  }
}
```

---

## 📊 Cost Components

### 1. **Translation Costs** (Vertex AI)

#### Pricing Structure
- **Rate**: $20.00 per 1 million characters
- **Minimum**: $0.0001 per request
- **Chunking**: No additional cost for chunked processing

#### Calculation Examples
```python
# Short content (1,000 characters)
translation_cost = 1000 * (20.0 / 1_000_000) = $0.02

# Medium content (5,000 characters) 
translation_cost = 5000 * (20.0 / 1_000_000) = $0.10

# Long content (50,000 characters)
translation_cost = 50000 * (20.0 / 1_000_000) = $1.00
```

#### Context Impact on Cost
Translation costs are **fixed per character** regardless of context:
- ✅ Legal context: Same rate
- ✅ Spiritual context: Same rate
- ✅ Marketing context: Same rate
- ✅ Scientific context: Same rate
- ✅ Educational context: Same rate
- ✅ News context: Same rate
- ✅ Casual context: Same rate

### 2. **Voice Synthesis Costs** (Multi-Provider)

## 🎤 TTS Provider Cost Comparison

| Provider | Cost/1K chars | Quality | Savings vs ElevenLabs |
|----------|---------------|---------|---------------------|
| **Google Cloud TTS** ⭐ | $0.016 | Neural2/Studio | **94% cheaper** |
| **ElevenLabs** | $0.30 | Premium Neural | - |
| **Auto Selection** | $0.016-0.30 | Optimized | **90%+ savings** |

### 2A. **Google Cloud TTS** (Recommended - 94% Cost Savings)

#### Pricing Structure
- **Standard Voices**: $0.004/1K characters (75% savings vs WaveNet)
- **WaveNet Voices**: $0.016/1K characters  
- **Neural2 Voices**: $0.016/1K characters ⭐ **Recommended**
- **Studio Voices**: $0.016/1K characters (Premium quality)

#### Regional Pricing (All the same globally)
- **US regions** (us-central1, us-east1): $0.016/1K chars
- **European regions** (europe-west4): $0.016/1K chars
- **Global regions**: Same pricing worldwide

#### Google TTS Calculation Examples
```python
# Short synthesis (1,000 characters, Neural2)
synthesis_cost = 1000 * (0.016 / 1000) = $0.016

# Medium synthesis (5,000 characters, Neural2)
synthesis_cost = 5000 * (0.016 / 1000) = $0.080

# Long synthesis (20,000 characters, Neural2)  
synthesis_cost = 20000 * (0.016 / 1000) = $0.320

# Compare to ElevenLabs:
# Same 20K chars with ElevenLabs = $6.00
# Savings: $6.00 - $0.32 = $5.68 (94.7% savings!)
```

#### Google TTS Voice Quality Tiers
| Tier | Cost/1K chars | Quality Level | Use Case |
|------|---------------|---------------|----------|
| Standard | $0.004 | Basic | Testing, drafts |
| WaveNet | $0.016 | Enhanced | Good production |
| Neural2 ⭐ | $0.016 | Premium | **Recommended** |
| Studio | $0.016 | Highest | Ultra-premium |

### 2B. **ElevenLabs** (Premium Neural Voices)

#### Pricing Structure
- **Standard Rate**: $0.30 per 1,000 characters
- **Quality Multipliers**:
  - Low quality: 0.8x ($0.24/1K chars)
  - Medium quality: 1.0x ($0.30/1K chars)
  - High quality: 1.2x ($0.36/1K chars)

#### Model Pricing
- **eleven_multilingual_v2**: Standard rate
- **eleven_multilingual_v1**: 0.9x standard rate
- **eleven_turbo_v2**: 0.7x standard rate (if available)

#### ElevenLabs Calculation Examples
```python
# Short synthesis (1,000 characters, high quality)
synthesis_cost = 1000 * (0.30 * 1.2) = $0.36

# Medium synthesis (5,000 characters, medium quality)
synthesis_cost = 5000 * (0.30 * 1.0) = $1.50

# Long synthesis (20,000 characters, high quality)
synthesis_cost = 20000 * (0.30 * 1.2) = $7.20
```

### 2C. **Provider Cost Comparison Examples**

#### Same Content, Different Providers (10K characters)

| Provider | Voice Type | Cost | Savings |
|----------|------------|------|---------|
| Google TTS (Neural2) | hu-HU-Neural2-A | $0.16 | **94% savings** |
| Google TTS (WaveNet) | hu-HU-Wavenet-A | $0.16 | **94% savings** |
| Google TTS (Standard) | hu-HU-Standard-A | $0.04 | **98% savings** |
| ElevenLabs (High) | Rachel | $3.60 | - |
| ElevenLabs (Medium) | Rachel | $3.00 | - |
| ElevenLabs (Low) | Rachel | $2.40 | - |

#### Annual Cost Comparison (100 videos/year, 10K chars each)

| Provider | Annual Cost | vs ElevenLabs Savings |
|----------|-------------|---------------------|
| Google TTS (Neural2) | $160 | **$2,840 saved (94%)** |
| Google TTS (Standard) | $40 | **$2,960 saved (98%)** |
| ElevenLabs (Medium) | $3,000 | - |

### 3. **Video Muxing Costs** (Computational)

#### Processing Costs
- **Standard Videos** (<100MB): $0.00 (included)
- **Large Videos** (100MB-500MB): $0.01
- **Very Large Videos** (500MB-1GB): $0.05
- **Maximum Video Size**: 1GB (enforced)

#### Format Impact
- **MP4**: No additional cost
- **WebM**: No additional cost  
- **AVI**: +$0.01 (less efficient)
- **MKV**: No additional cost

### 4. **Storage & Transfer Costs**

#### Google Cloud Storage
- **Temporary Storage**: $0.002 per GB-month (prorated)
- **Data Transfer**: Included for first 1GB/month
- **Automatic Cleanup**: Files deleted after 24 hours

#### Typical Storage Usage
- **Audio files**: 10-50MB per 10-minute video
- **Video files**: 50-500MB per 10-minute video
- **Total temporary storage**: Usually <1GB

---

## 🎯 Cost Estimation by Content Type

### 📚 Educational Content (10-minute video)

**Typical Characteristics:**
- Clear speech, moderate pace
- ~1,500 words (~7,500 characters)
- High-quality synthesis recommended

#### **Google Cloud TTS (Recommended - 94% Savings)**
```
Translation:     7,500 chars × ($20/1M) = $0.15
Synthesis:       7,500 chars × ($0.016/1K) = $0.12
Video Muxing:    Standard video = $0.00
Storage:         Temporary = ~$0.00
─────────────────────────────────────
Total Cost:      $0.27

Savings vs ElevenLabs: $2.58 (90.5% saved)
```

#### **ElevenLabs (Premium Quality)**
```
Translation:     7,500 chars × ($20/1M) = $0.15
Synthesis:       7,500 chars × ($0.36/1K) = $2.70
Video Muxing:    Standard video = $0.00
Storage:         Temporary = ~$0.00
─────────────────────────────────────
Total Cost:      $2.85
```

#### **Provider Comparison**
| Provider | Synthesis Cost | Total Cost | Annual (50 videos) | Savings |
|----------|-----------------|------------|-------------------|---------|
| Google TTS | $0.12 | $0.27 | $13.50 | **$129 saved** |
| ElevenLabs | $2.70 | $2.85 | $142.50 | - |

### 🎬 Entertainment Content (15-minute video)

**Typical Characteristics:**
- Fast-paced speech, frequent cuts
- ~2,500 words (~12,500 characters)
- Medium-quality synthesis acceptable

#### **Google Cloud TTS (Recommended - 94% Savings)**
```
Translation:     12,500 chars × ($20/1M) = $0.25
Synthesis:       12,500 chars × ($0.016/1K) = $0.20
Video Muxing:    Standard video = $0.00
Storage:         Temporary = ~$0.00
──────────────────────────────────────
Total Cost:      $0.45

Savings vs ElevenLabs: $3.55 (88.7% saved)
```

#### **ElevenLabs (Premium Quality)**
```
Translation:     12,500 chars × ($20/1M) = $0.25
Synthesis:       12,500 chars × ($0.30/1K) = $3.75
Video Muxing:    Standard video = $0.00
Storage:         Temporary = ~$0.00
──────────────────────────────────────
Total Cost:      $4.00
```

### 📰 News Content (5-minute video)

**Typical Characteristics:**
- Professional speech, measured pace
- ~800 words (~4,000 characters)
- High-quality synthesis for credibility

**Cost Breakdown:**
```
Translation:     4,000 chars × ($20/1M) = $0.08
Synthesis:       4,000 chars × ($0.36/1K) = $1.44
Video Muxing:    Standard video = $0.00
Storage:         Temporary = ~$0.00
─────────────────────────────────────
Total Cost:      $1.52
```

### 🏢 Corporate Content (20-minute presentation)

**Typical Characteristics:**
- Formal speech, technical terms
- ~3,500 words (~17,500 characters)
- High-quality synthesis required

**Cost Breakdown:**
```
Translation:     17,500 chars × ($20/1M) = $0.35
Synthesis:       17,500 chars × ($0.36/1K) = $6.30
Video Muxing:    Large video = $0.01
Storage:         Temporary = ~$0.00
──────────────────────────────────────
Total Cost:      $6.66
```

---

## 💡 Cost Optimization Strategies

### 1. **Quality Tier Selection**

#### **Draft/Preview Workflow**
```python
# Step 1: Low-quality preview (60% cost savings)
preview_request = {
    "url": "https://youtube.com/watch?v=example",
    "test_mode": True,  # First 60 seconds only
    "audio_quality": "low",  # 0.8x cost multiplier
    "voice_id": "21m00Tcm4TlvDq8ikWAM"
}
# Cost: ~$0.50 instead of $2.85 for full video

# Step 2: Full high-quality after approval
final_request = {
    "url": "https://youtube.com/watch?v=example",
    "audio_quality": "high",
    "voice_id": "21m00Tcm4TlvDq8ikWAM"
}
```

#### **Quality Comparison**
| Quality | Multiplier | 10k chars cost | Use Case |
|---------|------------|----------------|----------|
| Low     | 0.8x       | $2.40         | Testing, drafts |
| Medium  | 1.0x       | $3.00         | Most content |
| High    | 1.2x       | $3.60         | Final production |

### 2. **Batch Processing Discounts**

#### **Channel Processing**
Process multiple videos from the same channel:
```python
# Process 10 videos with consistent settings
channel_videos = [
    "https://youtube.com/watch?v=vid1",
    "https://youtube.com/watch?v=vid2",
    # ... 8 more videos
]

total_cost = 0
for video_url in channel_videos:
    job = create_dubbing_job(
        url=video_url,
        voice_id="21m00Tcm4TlvDq8ikWAM",  # Consistent voice
        audio_quality="medium",           # Balanced cost/quality
        translation_context="educational" # Consistent context
    )
    total_cost += estimate_cost(video_url)

# Typical savings: 15-20% compared to individual processing
```

### 3. **Smart Preview Mode**

#### **Test Mode Benefits**
- **60-second preview**: ~5% of full video cost
- **Voice testing**: Compare 3-4 voices for <$2 total
- **Quality testing**: Test different quality levels
- **Context testing**: Try different translation contexts

```python
# Test 3 voices with 60-second previews
test_voices = ["21m00Tcm4TlvDq8ikWAM", "pNInz6obpgDQGcFmaJgB", "yoZ06aMxZJJ28mfd3POQ"]

for voice_id in test_voices:
    preview_job = {
        "url": "https://youtube.com/watch?v=example",
        "test_mode": True,  # Only first 60 seconds
        "voice_id": voice_id,
        "audio_quality": "medium"
    }
    # Cost per preview: ~$0.15-0.30
# Total testing cost: <$1.00
# Savings on final job: $5-10 if better voice selected
```

### 4. **Context Optimization**

#### **Translation Context Impact**
While translation costs are fixed, context affects quality and may reduce need for re-processing:

- **Accurate context** → Better translation → Less re-work
- **Wrong context** → Poor translation → Re-processing costs

#### **Context Selection Guide**
```python
context_accuracy = {
    "legal": 98%,      # High accuracy, worth the same cost
    "educational": 96%, # Good accuracy
    "scientific": 94%,  # Technical terms may need review
    "marketing": 92%,   # Creative language challenges
    "news": 96%,       # Factual content translates well
    "spiritual": 90%,   # Metaphorical language complexity
    "casual": 88%      # Colloquialisms and slang challenges
}
```

---

## 🎮 Budget Management

### 1. **Pre-Processing Budget Check**

```python
def check_budget_before_processing(video_url: str, max_budget: float) -> dict:
    """Check if video processing fits within budget."""
    
    # Get video info and estimate transcript length
    video_info = get_youtube_info(video_url)
    estimated_chars = estimate_transcript_length(video_info['duration'])
    
    # Calculate costs
    translation_cost = estimated_chars * (20.0 / 1_000_000)
    synthesis_cost = estimated_chars * (0.36 / 1000)  # High quality
    total_estimated = translation_cost + synthesis_cost
    
    return {
        "estimated_cost": total_estimated,
        "budget_available": max_budget,
        "within_budget": total_estimated <= max_budget,
        "cost_breakdown": {
            "translation": translation_cost,
            "synthesis": synthesis_cost,
            "video_muxing": 0.01 if video_info['size_mb'] > 100 else 0
        }
    }

# Usage
budget_check = check_budget_before_processing(
    "https://youtube.com/watch?v=example",
    max_budget=5.00
)

if budget_check["within_budget"]:
    # Process video
    process_dubbing_job(video_url)
else:
    # Suggest alternatives or request budget increase
    print(f"Estimated cost ${budget_check['estimated_cost']:.2f} exceeds budget ${max_budget:.2f}")
```

### 2. **Cost Tracking During Processing**

```python
def track_job_costs(job_id: str) -> dict:
    """Track real-time costs for a dubbing job."""
    
    job_status = get_job_status(job_id)
    
    costs = {
        "translation_cost": job_status.get("translation_cost", 0),
        "synthesis_cost": job_status.get("synthesis_cost", 0),
        "video_muxing_cost": job_status.get("video_muxing_cost", 0),
        "storage_cost": job_status.get("storage_cost", 0),
        "total_cost": job_status.get("total_cost", 0)
    }
    
    return {
        "job_id": job_id,
        "status": job_status["status"],
        "progress": job_status["progress"],
        "costs": costs,
        "estimated_final_cost": job_status.get("estimated_final_cost")
    }
```

### 3. **Monthly Budget Monitoring**

```python
class BudgetTracker:
    def __init__(self, monthly_budget: float):
        self.monthly_budget = monthly_budget
        self.current_spending = 0.0
        self.jobs_this_month = []
    
    def can_process_job(self, estimated_cost: float) -> bool:
        """Check if job fits within remaining budget."""
        remaining_budget = self.monthly_budget - self.current_spending
        return estimated_cost <= remaining_budget
    
    def add_job_cost(self, job_id: str, actual_cost: float):
        """Add completed job cost to monthly tracking."""
        self.current_spending += actual_cost
        self.jobs_this_month.append({
            "job_id": job_id,
            "cost": actual_cost,
            "timestamp": datetime.now()
        })
    
    def get_budget_status(self) -> dict:
        """Get current budget status."""
        return {
            "monthly_budget": self.monthly_budget,
            "spent_this_month": self.current_spending,
            "remaining_budget": self.monthly_budget - self.current_spending,
            "jobs_processed": len(self.jobs_this_month),
            "average_job_cost": self.current_spending / len(self.jobs_this_month) if self.jobs_this_month else 0
        }

# Usage
budget = BudgetTracker(monthly_budget=100.0)

# Before processing
if budget.can_process_job(estimated_cost=4.50):
    job_id = process_video("https://youtube.com/watch?v=example")
    # After completion
    final_cost = get_job_final_cost(job_id)
    budget.add_job_cost(job_id, final_cost)
```

---

## 📈 Cost Analytics & Reporting

### 1. **Cost Per Content Type**

Track average costs by content category:
```python
content_type_averages = {
    "educational": {
        "avg_chars": 7500,
        "avg_translation_cost": 0.15,
        "avg_synthesis_cost": 2.70,
        "avg_total_cost": 2.85,
        "cost_per_minute": 0.285  # For 10-minute videos
    },
    "entertainment": {
        "avg_chars": 12500,
        "avg_translation_cost": 0.25,
        "avg_synthesis_cost": 3.75,
        "avg_total_cost": 4.00,
        "cost_per_minute": 0.267  # For 15-minute videos
    },
    "corporate": {
        "avg_chars": 17500,
        "avg_translation_cost": 0.35,
        "avg_synthesis_cost": 6.30,
        "avg_total_cost": 6.66,
        "cost_per_minute": 0.333  # For 20-minute videos
    }
}
```

### 2. **Monthly Cost Reports**

```python
def generate_monthly_report(month: str, year: int) -> dict:
    """Generate comprehensive monthly cost report."""
    
    jobs = get_jobs_for_month(month, year)
    
    total_costs = {
        "translation": sum(job["translation_cost"] for job in jobs),
        "synthesis": sum(job["synthesis_cost"] for job in jobs),
        "video_muxing": sum(job["video_muxing_cost"] for job in jobs),
        "storage": sum(job["storage_cost"] for job in jobs),
        "total": sum(job["total_cost"] for job in jobs)
    }
    
    analytics = {
        "total_jobs": len(jobs),
        "total_characters_processed": sum(job["character_count"] for job in jobs),
        "average_job_cost": total_costs["total"] / len(jobs) if jobs else 0,
        "cost_by_content_type": analyze_costs_by_content_type(jobs),
        "cost_by_quality": analyze_costs_by_quality(jobs),
        "most_expensive_job": max(jobs, key=lambda x: x["total_cost"]) if jobs else None,
        "cost_efficiency": calculate_cost_efficiency(jobs)
    }
    
    return {
        "month": f"{month} {year}",
        "total_costs": total_costs,
        "analytics": analytics,
        "recommendations": generate_cost_optimization_recommendations(analytics)
    }
```

### 3. **Cost Optimization Recommendations**

```python
def generate_cost_optimization_recommendations(analytics: dict) -> list:
    """Generate personalized cost optimization recommendations."""
    
    recommendations = []
    
    # Quality optimization
    if analytics["cost_by_quality"]["high"] > analytics["cost_by_quality"]["medium"] * 2:
        recommendations.append({
            "type": "quality_optimization",
            "title": "Consider Medium Quality for Draft Reviews",
            "description": "You're using high quality heavily. Try medium quality for drafts.",
            "potential_savings": analytics["cost_by_quality"]["high"] * 0.2,
            "impact": "medium"
        })
    
    # Batch processing
    if analytics["total_jobs"] > 10:
        recommendations.append({
            "type": "batch_processing",
            "title": "Batch Process Similar Content",
            "description": "Process similar videos together for consistency and efficiency.",
            "potential_savings": analytics["total_costs"]["total"] * 0.15,
            "impact": "high"
        })
    
    # Preview usage
    preview_jobs = [j for j in analytics["jobs"] if j.get("test_mode")]
    if len(preview_jobs) < analytics["total_jobs"] * 0.3:
        recommendations.append({
            "type": "preview_mode",
            "title": "Use Preview Mode More Often", 
            "description": "Test voices and settings with 60-second previews before full processing.",
            "potential_savings": analytics["total_costs"]["synthesis"] * 0.1,
            "impact": "medium"
        })
    
    return recommendations
```

---

## 🛠️ API Cost Management

### 1. **Cost-Aware Job Creation**

```python
def create_cost_managed_dubbing_job(
    url: str,
    max_cost: float = 10.0,
    preferred_quality: str = "medium"
) -> dict:
    """Create dubbing job with cost constraints."""
    
    # Get cost estimate first
    estimate = get_cost_estimate(url, preferred_quality)
    
    if estimate["total_cost"] > max_cost:
        # Try lower quality
        if preferred_quality == "high":
            estimate = get_cost_estimate(url, "medium")
            if estimate["total_cost"] <= max_cost:
                preferred_quality = "medium"
        
        # Still too expensive, try low quality
        if estimate["total_cost"] > max_cost and preferred_quality == "medium":
            estimate = get_cost_estimate(url, "low")
            if estimate["total_cost"] <= max_cost:
                preferred_quality = "low"
    
    if estimate["total_cost"] > max_cost:
        return {
            "error": "Cost exceeds maximum budget",
            "estimated_cost": estimate["total_cost"],
            "max_cost": max_cost,
            "suggestions": [
                "Increase budget",
                "Use test mode for preview",
                "Process in segments"
            ]
        }
    
    # Create job with cost limit
    job_request = {
        "url": url,
        "audio_quality": preferred_quality,
        "max_cost_usd": max_cost,
        "enable_translation": True,
        "enable_synthesis": True,
        "enable_video_muxing": True
    }
    
    return create_dubbing_job(job_request)
```

### 2. **Real-Time Cost Monitoring**

```bash
# Monitor job costs in real-time
curl -X GET "http://localhost:8000/v1/dubbing/{job_id}" | jq '.cost_breakdown'

# Response:
{
  "translation_cost": 0.15,
  "synthesis_cost": 2.30,
  "video_muxing_cost": 0.01,
  "total_cost": 2.46,
  "estimated_final_cost": 2.50
}
```

### 3. **Bulk Cost Estimation**

```python
def estimate_batch_costs(video_urls: list, settings: dict) -> dict:
    """Estimate costs for batch processing multiple videos."""
    
    total_estimate = {
        "translation_cost": 0,
        "synthesis_cost": 0, 
        "video_muxing_cost": 0,
        "total_cost": 0
    }
    
    individual_estimates = []
    
    for url in video_urls:
        estimate = get_cost_estimate_for_url(url, settings)
        individual_estimates.append({
            "url": url,
            "estimate": estimate
        })
        
        # Add to total
        for key in total_estimate:
            total_estimate[key] += estimate[key]
    
    # Apply batch discount (if applicable)
    if len(video_urls) > 5:
        batch_discount = 0.1  # 10% discount for 5+ videos
        total_estimate["total_cost"] *= (1 - batch_discount)
        total_estimate["batch_discount"] = total_estimate["total_cost"] * batch_discount
    
    return {
        "total_videos": len(video_urls),
        "total_estimate": total_estimate,
        "individual_estimates": individual_estimates,
        "average_cost_per_video": total_estimate["total_cost"] / len(video_urls)
    }
```

---

## 🚨 Cost Alerts & Limits

### 1. **Budget Alert System**

```python
class CostAlertManager:
    def __init__(self):
        self.alert_thresholds = [0.5, 0.8, 0.95]  # 50%, 80%, 95% of budget
        self.notification_channels = ["email", "webhook", "log"]
    
    def check_budget_alerts(self, current_spending: float, budget_limit: float):
        """Check if spending has crossed alert thresholds."""
        
        spending_percentage = current_spending / budget_limit
        
        for threshold in self.alert_thresholds:
            if spending_percentage >= threshold and not self.alert_sent(threshold):
                self.send_alert(
                    level=threshold,
                    message=f"Budget alert: {spending_percentage:.1%} of monthly budget used",
                    current_spending=current_spending,
                    budget_limit=budget_limit,
                    remaining_budget=budget_limit - current_spending
                )
    
    def enforce_hard_limit(self, estimated_cost: float, current_spending: float, budget_limit: float) -> bool:
        """Enforce hard budget limits."""
        
        projected_spending = current_spending + estimated_cost
        
        if projected_spending > budget_limit:
            self.send_alert(
                level="hard_limit",
                message="Job blocked: Would exceed budget limit",
                estimated_cost=estimated_cost,
                current_spending=current_spending,
                budget_limit=budget_limit
            )
            return False
        
        return True
```

### 2. **Emergency Cost Controls**

```python
# Emergency stop for runaway costs
def emergency_cost_control(job_id: str, max_emergency_cost: float = 50.0):
    """Emergency cost control for runaway jobs."""
    
    job_status = get_job_status(job_id)
    current_cost = job_status.get("total_cost", 0)
    
    if current_cost > max_emergency_cost:
        # Cancel job immediately
        cancel_job(job_id)
        
        # Send emergency alert
        send_emergency_alert({
            "job_id": job_id,
            "cost": current_cost,
            "limit": max_emergency_cost,
            "action": "job_cancelled"
        })
        
        return {
            "status": "emergency_cancelled",
            "reason": f"Cost ${current_cost} exceeded emergency limit ${max_emergency_cost}",
            "job_id": job_id
        }
    
    return {"status": "ok", "cost": current_cost}
```

---

## 📋 Cost Management Checklist

### ✅ **Before Processing**
- [ ] Get cost estimate for video
- [ ] Check estimate against budget
- [ ] Consider using test mode for preview
- [ ] Select appropriate quality level
- [ ] Verify voice selection is optimal

### ✅ **During Processing**
- [ ] Monitor real-time cost accumulation
- [ ] Set emergency cost limits
- [ ] Track progress vs. cost estimates
- [ ] Ensure job stays within budget

### ✅ **After Processing**
- [ ] Record actual costs for future estimates
- [ ] Update monthly budget tracking
- [ ] Analyze cost efficiency
- [ ] Document lessons learned
- [ ] Update cost optimization strategies

### ✅ **Monthly Review**
- [ ] Generate monthly cost report
- [ ] Analyze cost trends by content type
- [ ] Review budget utilization
- [ ] Implement cost optimization recommendations
- [ ] Adjust budgets for next month

---

## 🎯 Quick Reference

### **Cost Estimation API**
```bash
# Get cost estimate
curl -X GET "http://localhost:8000/v1/cost-estimate?transcript_length=5000&enable_synthesis=true&audio_quality=high"

# Create job with cost limit
curl -X POST http://localhost:8000/v1/dub \
  -H "Content-Type: application/json" \
  -d '{"url": "...", "max_cost_usd": 5.0}'
```

### **Typical Costs by Video Length**
| Duration | Characters | Translation | Synthesis (High) | Total |
|----------|------------|-------------|------------------|-------|
| 5 min    | ~4,000     | $0.08       | $1.44           | $1.52 |
| 10 min   | ~7,500     | $0.15       | $2.70           | $2.85 |
| 15 min   | ~12,500    | $0.25       | $4.50           | $4.75 |
| 20 min   | ~17,500    | $0.35       | $6.30           | $6.65 |

### **Quality Cost Multipliers**
- **Low**: 0.8x ($0.24/1K chars)
- **Medium**: 1.0x ($0.30/1K chars)  
- **High**: 1.2x ($0.36/1K chars)

**Smart cost management ensures sustainable dubbing operations! 💰**

---

For more information, see:
- [Voice Profile Selection Guide](./VOICE_GUIDE.md)
- [Complete API Reference](./API_REFERENCE.md)
- [Dubbing Guide](./DUBBING_GUIDE.md)