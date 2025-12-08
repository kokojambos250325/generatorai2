# Deployment Instructions for RunPod

Complete guide for deploying the AI Image Generation Platform to RunPod POD.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial POD Setup](#initial-pod-setup)
3. [SSH Configuration](#ssh-configuration)
4. [Repository Deployment](#repository-deployment)
5. [Model Installation](#model-installation)
6. [Service Configuration](#service-configuration)
7. [Starting Services](#starting-services)
8. [Testing and Verification](#testing-and-verification)
9. [Monitoring and Maintenance](#monitoring-and-maintenance)
10. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisites

### Local Machine Requirements
- Python 3.10 or higher
- Git installed
- SSH client (OpenSSH on Windows 10/11)
- SSH key pair (ED25519 recommended)

### RunPod Requirements
- Active RunPod account
- POD with GPU (RTX 3090 or better recommended)
- Persistent volume mounted at `/workspace`
- Minimum 100GB storage for models

### Required Accounts/Tokens
- Telegram bot token from [@BotFather](https://t.me/BotFather)
- RunPod API key (optional, for automation)

---

## 2. Initial POD Setup

### 2.1 Create POD on RunPod

1. **Log in to RunPod Dashboard**
   - Visit https://www.runpod.io/console/pods

2. **Deploy New POD**
   - Click "Deploy" or "New POD"
   - Select GPU type (RTX 3090 or RTX 4090 recommended)
   - Choose template: "RunPod Pytorch" or "RunPod Fast-SD"

3. **Configure POD**
   - **Container Disk:** 50GB minimum
   - **Volume Disk:** 200GB+ (for models and data)
   - **Volume Mount Path:** `/workspace` (CRITICAL!)
   - **Expose Ports:** Add TCP port 22 for SSH

4. **Add SSH Public Key**
   - In POD configuration, find SSH keys section
   - Paste your ED25519 public key content
   - If you don't have a key yet, generate one:
     ```powershell
     ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519
     ```

5. **Deploy POD**
   - Click "Deploy" and wait for POD to start
   - Note the POD ID and connection details

### 2.2 Obtain Connection Details

After POD starts, note these details:

**SSH via RunPod Proxy:**
```
Host: ssh.runpod.io
User: <pod_id>-<unique_id>
Port: 22
Example: p8q2agahufxw4a-64410d8e@ssh.runpod.io
```

**SSH via Direct TCP:**
```
Host: <external_ip>
Port: <mapped_port>
User: root
Example: ssh root@38.147.83.26 -p 35108
```

---

## 3. SSH Configuration

### 3.1 Configure SSH on Local Machine

**On Windows:**

1. Create SSH config directory if needed:
   ```powershell
   mkdir -p $HOME\.ssh
   ```

2. Set correct permissions on SSH key:
   ```powershell
   icacls $HOME\.ssh\id_ed25519 /inheritance:r
   icacls $HOME\.ssh\id_ed25519 /grant:r "$($env:USERNAME):(R)"
   ```

3. Test SSH connection:
   ```powershell
   ssh p8q2agahufxw4a-64410d8e@ssh.runpod.io -i ~/.ssh/id_ed25519
   ```

### 3.2 Setup SSH Manager

1. Clone this repository locally:
   ```powershell
   git clone <repository-url>
   cd generator-ai
   ```

2. Create `infra/ssh_config.json` from template:
   ```powershell
   copy infra\ssh_config.json.template infra\ssh_config.json
   ```

3. Edit `infra/ssh_config.json` with your POD details:
   ```json
   {
     "connections": {
       "proxy": {
         "host": "ssh.runpod.io",
         "user": "YOUR_POD_ID",
         "port": 22,
         "key_path": "~/.ssh/id_ed25519"
       },
       "direct": {
         "host": "YOUR_EXTERNAL_IP",
         "user": "root",
         "port": YOUR_MAPPED_PORT,
         "key_path": "~/.ssh/id_ed25519"
       }
     },
     "default_connection": "proxy"
   }
   ```

4. Test SSH manager:
   ```powershell
   python infra/ssh_manager.py status
   ```

---

## 4. Repository Deployment

### 4.1 Connect to POD

```powershell
python infra/ssh_manager.py shell
```

### 4.2 Setup Workspace

Once connected to POD:

```bash
# Navigate to workspace
cd /workspace

# Install git if not present
apt-get update && apt-get install -y git

# Clone repository
git clone <repository-url> ai-generator
cd ai-generator

# Make startup script executable
chmod +x startup.sh
```

### 4.3 Create Virtual Environment

```bash
# Create venv
python3 -m venv /workspace/venv

# Activate venv
source /workspace/venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 4.4 Install Dependencies

```bash
# Backend dependencies
cd /workspace/ai-generator/backend
pip install -r requirements.txt

# GPU server dependencies
cd /workspace/ai-generator/gpu_server
pip install -r requirements.txt

# Telegram bot dependencies
cd /workspace/ai-generator/telegram_bot
pip install -r requirements.txt
```

---

## 5. Model Installation

### 5.1 Create Model Directory Structure

```bash
cd /workspace
mkdir -p models/{checkpoints,lora,vae,controlnet,ipadapter,insightface,upscale}
```

### 5.2 Download Required Models

**Base Checkpoints (Choose based on your needs):**

```bash
cd /workspace/models/checkpoints

# SDXL Base (for realism, lux, chatgpt styles)
wget https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors

# Anime Model (for anime style)
wget https://huggingface.co/Linaqruf/anything-v3.0/resolve/main/anything-v5.safetensors

# NSFW-friendly model (for clothes removal)
wget <chilloutmix_download_url>
```

**VAE Models:**

```bash
cd /workspace/models/vae

# SDXL VAE
wget https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors

# Anime VAE
wget <anime_vae_url>
```

**ControlNet Models (for clothes removal):**

```bash
cd /workspace/models/controlnet

# OpenPose
wget <controlnet_openpose_url>

# Depth
wget <controlnet_depth_url>

# Canny
wget <controlnet_canny_url>
```

**LoRA Weights (optional but recommended):**

```bash
cd /workspace/models/lora

# Download LoRAs for your styles
# Realistic vision, glossy lux, anime style, etc.
```

### 5.3 Verify Model Paths

Ensure models match paths in `gpu_server/models_config/models.json`.

---

## 6. Service Configuration

### 6.1 Backend Configuration

```bash
cd /workspace/ai-generator/backend

# Create .env from template
cp .env.template .env

# Edit .env
nano .env
```

**backend/.env:**
```
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
GPU_SERVICE_URL=http://localhost:8001
LOG_LEVEL=INFO
REQUEST_TIMEOUT=180
```

### 6.2 GPU Server Configuration

```bash
cd /workspace/ai-generator/gpu_server

# Create .env
cp .env.template .env

# Edit .env
nano .env
```

**gpu_server/.env:**
```
GPU_SERVER_HOST=0.0.0.0
GPU_SERVER_PORT=8001
COMFYUI_API_URL=http://localhost:8188
MODELS_PATH=/workspace/models
WORKFLOWS_PATH=/workspace/ai-generator/gpu_server/workflows
LOG_LEVEL=INFO
```

### 6.3 Telegram Bot Configuration

```bash
cd /workspace/ai-generator/telegram_bot

# Create .env
cp .env.template .env

# Edit .env
nano .env
```

**telegram_bot/.env:**
```
TELEGRAM_BOT_TOKEN=8420116928:AAEg1qPoL5ow6OaKzubFMXEQAuoTIEOpzXE
BACKEND_API_URL=http://localhost:8000
MAX_IMAGE_SIZE_MB=10
LOG_LEVEL=INFO
```

⚠️ **Replace with your actual bot token from @BotFather!**

### 6.4 Create Logs Directory

```bash
mkdir -p /workspace/logs
```

---

## 7. Starting Services

### 7.1 Manual Start (First Time)

**Start services manually to verify everything works:**

```bash
# Activate venv
source /workspace/venv/bin/activate

# Start GPU server (Terminal 1)
cd /workspace/ai-generator/gpu_server
python server.py

# Start backend (Terminal 2 - open new SSH session)
cd /workspace/ai-generator/backend
python main.py

# Start Telegram bot (Terminal 3 - open new SSH session)
cd /workspace/ai-generator/telegram_bot
python bot.py
```

**Verify each service starts without errors before proceeding.**

### 7.2 Automatic Start with startup.sh

Once manual start works:

```bash
# Copy startup script to workspace root
cp /workspace/ai-generator/startup.sh /workspace/

# Make executable
chmod +x /workspace/startup.sh

# Run startup script
/workspace/startup.sh
```

### 7.3 Configure Auto-Start on POD Boot

**Option A: Using RunPod Startup Script**

1. Go to RunPod dashboard
2. Edit your POD
3. Find "Docker Command" or "Startup Script" field
4. Add: `/workspace/startup.sh`

**Option B: Using cron**

```bash
# Edit crontab
crontab -e

# Add this line:
@reboot /workspace/startup.sh
```

---

## 8. Testing and Verification

### 8.1 Check Service Health

From your local machine:

```powershell
# Check all services
python infra/ssh_manager.py status

# Check backend health
curl http://<pod-ip>:8000/health

# Or via SSH:
python infra/ssh_manager.py exec "curl http://localhost:8000/health"
```

### 8.2 View Logs

```powershell
# Backend logs
python infra/ssh_manager.py logs backend 100

# GPU server logs
python infra/ssh_manager.py logs gpu_server 100

# All logs
python infra/ssh_manager.py exec "tail -f /workspace/logs/*.log"
```

### 8.3 Test Generation

**Via Telegram Bot:**
1. Open Telegram and find your bot
2. Send `/start`
3. Try "Free Generation" with a simple prompt
4. Try "Remove Clothes" with a test photo

**Via API (curl):**

```bash
# Test backend health
curl http://localhost:8000/health

# Test free generation
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"mode":"free","prompt":"test","style":"realism"}'
```

---

## 9. Monitoring and Maintenance

### 9.1 Regular Health Checks

Create a monitoring script or use:

```powershell
# Daily health check
python infra/ssh_manager.py status

# Check GPU usage
python infra/ssh_manager.py exec "nvidia-smi"

# Check disk space
python infra/ssh_manager.py exec "df -h /workspace"
```

### 9.2 Log Management

```bash
# Rotate logs (add to cron)
find /workspace/logs -name "*.log" -size +100M -exec truncate -s 50M {} \;

# Archive old logs
tar -czf /workspace/logs/archive-$(date +%Y%m%d).tar.gz /workspace/logs/*.log
```

### 9.3 Service Restart

```powershell
# Restart specific service
python infra/ssh_manager.py restart backend
python infra/ssh_manager.py restart gpu_server

# Restart all services
python infra/ssh_manager.py exec "/workspace/startup.sh"
```

---

## 10. Troubleshooting

### 10.1 Backend Not Starting

**Symptoms:** Backend fails to start or crashes immediately

**Solutions:**
```bash
# Check logs
tail -100 /workspace/logs/backend.log

# Verify GPU service is running
curl http://localhost:8001/health

# Check port availability
netstat -tulpn | grep 8000

# Restart manually
cd /workspace/ai-generator/backend
source /workspace/venv/bin/activate
python main.py
```

### 10.2 GPU Server Not Responding

**Symptoms:** Backend reports GPU unavailable

**Solutions:**
```bash
# Check ComfyUI status
curl http://localhost:8188/system_stats

# Check GPU server logs
tail -100 /workspace/logs/gpu_server.log

# Verify GPU is accessible
nvidia-smi

# Check model paths
ls -la /workspace/models/checkpoints/
```

### 10.3 Telegram Bot Not Responding

**Symptoms:** Bot doesn't respond to commands

**Solutions:**
```bash
# Check bot logs
tail -100 /workspace/logs/telegram_bot.log

# Verify bot token
python -c "from telegram_bot.config import get_settings; print(get_settings().telegram_bot_token)"

# Test backend connectivity from bot
curl http://localhost:8000/health

# Restart bot
python infra/ssh_manager.py restart telegram_bot
```

### 10.4 Generation Fails

**Symptoms:** Generation returns error

**Solutions:**
```bash
# Check specific error in logs
grep -i "error" /workspace/logs/*.log

# Verify models exist
ls -la /workspace/models/checkpoints/

# Test ComfyUI directly
curl -X POST http://localhost:8188/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt":{}}'

# Check GPU memory
nvidia-smi

# Check disk space
df -h /workspace
```

### 10.5 SSH Connection Issues

**Symptoms:** Cannot connect via SSH

**Solutions:**
1. Check POD is running in RunPod dashboard
2. Verify SSH key permissions (600)
3. Try direct TCP connection instead of proxy
4. Regenerate SSH key and update RunPod
5. Check firewall rules

### 10.6 Out of Memory

**Symptoms:** CUDA out of memory errors

**Solutions:**
- Use smaller models (SD 1.5 instead of SDXL)
- Reduce batch size to 1
- Lower resolution (512x512 instead of 1024x1024)
- Restart POD to clear GPU memory
- Upgrade to POD with more VRAM

---

## Quick Reference Commands

```powershell
# Connect to POD
python infra/ssh_manager.py shell

# Check status
python infra/ssh_manager.py status

# View logs
python infra/ssh_manager.py logs backend
python infra/ssh_manager.py logs gpu_server

# Restart services
python infra/ssh_manager.py restart backend
python infra/ssh_manager.py restart gpu_server

# Execute command
python infra/ssh_manager.py exec "nvidia-smi"
python infra/ssh_manager.py exec "df -h /workspace"
```

---

## Support

For issues not covered here:
1. Check logs: `/workspace/logs/*.log`
2. Review design document: `.qoder/quests/system-architecture-design.md`
3. Check implementation status: `IMPLEMENTATION_STATUS.md`

---

**Last Updated:** December 8, 2025  
**Version:** MVP 1.0
