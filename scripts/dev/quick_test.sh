#!/bin/bash
# Quick test script for development

set -e

echo "🧪 YouTube Transcription Service - Quick Test"
echo "=============================================="

# Check if API is running
echo "📡 Checking API availability..."
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✅ API is running"
else
    echo "❌ API not running. Starting with docker compose..."
    docker compose up -d
    echo "⏳ Waiting for API to be ready..."
    sleep 10
    
    if curl -f -s http://localhost:8000/health > /dev/null; then
        echo "✅ API is now running"
    else
        echo "❌ Failed to start API"
        exit 1
    fi
fi

# Submit test job
echo ""
echo "🎥 Submitting test transcription job..."
JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/v1/transcribe \
    -H "Content-Type: application/json" \
    -d '{
        "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "test_mode": true,
        "vertex_ai_model": "gemini-2.0-flash"
    }')

JOB_ID=$(echo "$JOB_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo "📋 Job submitted with ID: $JOB_ID"

# Monitor job progress
echo ""
echo "⏳ Monitoring job progress..."
while true; do
    STATUS_RESPONSE=$(curl -s http://localhost:8000/v1/jobs/$JOB_ID)
    STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
    PROGRESS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['progress'])")
    
    echo "📊 Status: $STATUS ($PROGRESS%)"
    
    if [ "$STATUS" = "completed" ]; then
        echo "✅ Job completed successfully!"
        
        # Download transcript
        echo ""
        echo "📄 Downloading transcript..."
        curl -s http://localhost:8000/v1/jobs/$JOB_ID/download -o "test_transcript_$JOB_ID.txt"
        
        WORD_COUNT=$(wc -w < "test_transcript_$JOB_ID.txt")
        echo "✅ Transcript saved: test_transcript_$JOB_ID.txt ($WORD_COUNT words)"
        
        # Show preview
        echo ""
        echo "👀 Preview (first 300 characters):"
        echo "-----------------------------------"
        head -c 300 "test_transcript_$JOB_ID.txt"
        echo "..."
        echo "-----------------------------------"
        break
        
    elif [ "$STATUS" = "failed" ]; then
        ERROR=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', 'Unknown error'))")
        echo "❌ Job failed: $ERROR"
        exit 1
    fi
    
    sleep 5
done

echo ""
echo "🎉 Quick test completed successfully!"
echo "💡 You can view API docs at: http://localhost:8000/docs"