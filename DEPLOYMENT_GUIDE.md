# RunPod MVP Deployment Guide

## Current Situation

Due to RunPod SSH proxy limitations (PTY requirement), automated file transfer via SCP or SSH commands is blocked. All files exist locally in `C:\projekt\generator -ai\` but need manual deployment.

## Deployment Method

Use **interactive SSH session** and **copy-paste** approach or **git clone**.

---

## Option 1: Git Clone (Recommended)

1. SSH into POD:
```bash
ssh p8q2agahufxw4a-64410d8e@ssh.runpod.io -i ~/.ssh/id_ed25519
```

2. Clone repository to /workspace:
```bash
cd /workspace
git clone <your-repo-url> temp_deploy
cp -r temp_deploy/backend ./
cp -r temp_deploy/gpu_server ./
cp temp_deploy/startup.sh ./
rm -rf temp_deploy
```

3. Set up environment:
```bash
cd /workspace

# Create venv if doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install GPU server dependencies  
cd ../gpu_server
pip install -r requirements.txt

# Create .env files
cd /workspace/backend
cp .env.template .env

cd /workspace/gpu_server
cp .env.template .env

# Make startup script executable
chmod +x /workspace/startup.sh
```

4. Start services:
```bash
cd /workspace
./startup.sh
```

5. Verify:
```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

---

## Option 2: Manual File Creation

If git is not available, create files manually via SSH session.

### Step 1: SSH into POD

```bash
ssh p8q2agahufxw4a-64410d8e@ssh.runpod.io -i ~/.ssh/id_ed25519
```

### Step 2: Create Directory Structure

```bash
cd /workspace

# Backend structure
mkdir -p backend/routers backend/schemas backend/services backend/clients backend/utils
touch backend/__init__.py backend/routers/__init__.py backend/schemas/__init__.py
touch backend/services/__init__.py backend/clients/__init__.py backend/utils/__init__.py

# GPU server structure
mkdir -p gpu_server/workflows gpu_server/schemas gpu_server/services  
touch gpu_server/__init__.py gpu_server/workflows/__init__.py
touch gpu_server/schemas/__init__.py gpu_server/services/__init__.py

# Logs directory
mkdir -p logs
```

### Step 3: Create Files Using Cat/Vim

For each file below, use:
```bash
cat > /workspace/backend/main.py << 'ENDOFFILE'
[paste content here]
ENDOFFILE
```

Or use `vi` editor.

---

## Files to Deploy

### Backend Files (/workspace/backend/)

1. **main.py** - see local file
2. **config.py** - see local file  
3. **requirements.txt** - see local file
4. **.env.template** - see local file
5. **routers/health.py** - see local file
6. **routers/generate.py** - see local file
7. **routers/__init__.py** - empty
8. **schemas/request_free.py** - see local file
9. **schemas/request_clothes.py** - see local file
10. **schemas/response_generate.py** - see local file
11. **services/generation_router.py** - see local file
12. **clients/gpu_client.py** - see local file
13. **utils/logging.py** - see local file

### GPU Server Files (/workspace/gpu_server/)

1. **server.py** - see local file
2. **config.py** - see local file
3. **comfy_client.py** - see local file
4. **requirements.txt** - see local file
5. **.env.template** - see local file

### Root Files (/workspace/)

1. **startup.sh** - see local file

---

## Quick Deployment Script

Save this as `/workspace/quick_deploy.sh` and run in SSH session:

```bash
#!/bin/bash
cd /workspace

echo "Creating directory structure..."
mkdir -p backend/routers backend/schemas backend/services backend/clients backend/utils
mkdir -p gpu_server/workflows gpu_server/schemas gpu_server/services logs

echo "Creating __init__.py files..."
touch backend/{__init__.py,routers/__init__.py,schemas/__init__.py,services/__init__.py,clients/__init__.py,utils/__init__.py}
touch gpu_server/{__init__.py,workflows/__init__.py,schemas/__init__.py,services/__init__.py}

echo "Structure created. Now copy files from local machine."
echo "Directory tree:"
ls -R backend gpu_server
```

---

## Verification Checklist

After deployment, verify:

- [ ] `/workspace/venv` exists and activated
- [ ] `/workspace/backend/main.py` exists
- [ ] `/workspace/gpu_server/server.py` exists  
- [ ] Dependencies installed in both services
- [ ] `.env` files created from templates
- [ ] `startup.sh` is executable
- [ ] Both services start without errors
- [ ] Health endpoints respond:
  - `curl http://localhost:8000/health` returns 200
  - `curl http://localhost:8001/health` returns 200

---

## Troubleshooting

**Services won't start:**
1. Check logs: `tail -f /workspace/logs/backend.log`
2. Verify venv activated: `which python`
3. Check dependencies: `pip list | grep fastapi`

**Port already in use:**
```bash
kill $(cat /workspace/backend.pid)
kill $(cat /workspace/gpu_server.pid)
```

**Permission denied on startup.sh:**
```bash
chmod +x /workspace/startup.sh
```
