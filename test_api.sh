#!/bin/bash
echo "Testing API endpoints..."
echo ""
echo "1. Testing /health:"
curl -s http://localhost:3000/health | head -5
echo ""
echo ""
echo "2. Testing /api/generate (should work):"
curl -s -X POST http://localhost:3000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"mode":"free","prompt":"test"}' | head -5
echo ""
