#!/bin/bash
# Real-time log monitoring for debugging

echo "=== MONITORING LOGS ==="
echo "Press Ctrl+C to stop"
echo ""

# Show last errors first
echo "=== Recent Backend Errors ==="
tail -50 /workspace/logs/backend.log | grep -A 5 ERROR || echo "No errors found"

echo ""
echo "=== Recent GPU Server Errors ==="
tail -50 /workspace/logs/gpu_server.log | grep -A 5 ERROR || echo "No errors found"

echo ""
echo "=== Recent Bot Errors ==="
tail -50 /workspace/logs/telegram_bot.log | grep -A 5 ERROR || echo "No errors found"

echo ""
echo "=== WATCHING LOGS IN REAL-TIME ==="
echo "Backend + GPU Server + Bot (combined)"
echo ""

tail -f /workspace/logs/backend.log /workspace/logs/gpu_server.log /workspace/logs/telegram_bot.log
