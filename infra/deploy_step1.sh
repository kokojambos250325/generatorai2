#!/bin/sh
set -e
cd /workspace
echo "=== Current directory ==="
pwd
ls -la

echo ""
echo "=== Creating backend structure ==="
mkdir -p backend/routers backend/schemas backend/services backend/clients backend/utils
touch backend/__init__.py
touch backend/routers/__init__.py backend/schemas/__init__.py
touch backend/services/__init__.py backend/clients/__init__.py backend/utils/__init__.py

echo ""
echo "=== Creating gpu_server structure ==="
mkdir -p gpu_server/workflows gpu_server/schemas gpu_server/services
touch gpu_server/__init__.py gpu_server/workflows/__init__.py
touch gpu_server/schemas/__init__.py gpu_server/services/__init__.py

echo ""
echo "=== Creating logs directory ==="
mkdir -p logs

echo ""
echo "=== Structure created ==="
ls -R backend gpu_server
