#!/bin/bash
# MVP Deployment Script for RunPod POD
# Executes on the POD to set up backend and gpu_server structure

set -e

echo "=== Starting MVP Deployment to /workspace ==="

# Navigate to workspace
cd /workspace

# Create directory structure
echo "Creating directory structure..."
mkdir -p backend/routers backend/schemas backend/services backend/clients backend/utils
mkdir -p gpu_server/workflows gpu_server/schemas gpu_server/services
mkdir -p logs

# Create __init__.py files
touch backend/__init__.py
touch backend/routers/__init__.py
touch backend/schemas/__init__.py
touch backend/services/__init__.py
touch backend/clients/__init__.py
touch backend/utils/__init__.py

touch gpu_server/__init__.py
touch gpu_server/workflows/__init__.py
touch gpu_server/schemas/__init__.py
touch gpu_server/services/__init__.py

echo "Directory structure created successfully"
echo ""
echo "=== Directory Tree ===" 
ls -R /workspace/backend
echo ""
ls -R /workspace/gpu_server

echo ""
echo "=== MVP Deployment Complete ==="
echo "Next: Upload Python files to complete implementation"
