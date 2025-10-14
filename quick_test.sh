#!/bin/bash

# Quick test script for mono_gen API
echo "🧪 Quick API Test..."

# Test health endpoint
echo "Testing health endpoint..."
curl -s http://127.0.0.1:8888/healthz

echo ""
echo "Testing generate endpoint..."
curl -X POST http://127.0.0.1:8888/generate \
  -H 'Content-Type: application/json' \
  -d '{"seconds":2,"fps":8,"out_res":256,"anchors":3,"strength":2.0,"sharpen":false}'

echo ""
echo "✅ Test complete! Check the job_id and poll /status/{job_id} for progress"