#!/bin/bash
cd /workspace/ai-generator
echo "# Deploy key test" > test_deploy.txt
git add test_deploy.txt
git commit -m "Test deploy key push from RunPod"
git push origin main
echo "Push completed!"
