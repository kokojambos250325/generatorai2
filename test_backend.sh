#!/bin/bash
# Test generation API directly on server

echo "=== TESTING BACKEND API ==="
echo ""

# Test data
TEST_JSON='{
  "mode": "free",
  "prompt": "beautiful mountain sunset, photorealistic",
  "style": "realism",
  "add_face": false,
  "extra_params": {
    "steps": 26,
    "cfg_scale": 7.5,
    "seed": -1
  }
}'

echo "Request JSON:"
echo "$TEST_JSON"
echo ""
echo "Sending POST to http://localhost:8000/generate ..."
echo ""

# Execute request
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d "$TEST_JSON" \
  -w "\n\nHTTP Status: %{http_code}\n" \
  -s

echo ""
echo "=== Checking Backend Logs ==="
tail -30 /workspace/logs/backend.log | grep -A 10 "ERROR\|generate\|Generation"
