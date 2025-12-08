# AI Image Generation Platform

A clean, resilient NSFW/realistic/anime image generation system consisting of FastAPI backend, GPU service on RunPod with ComfyUI, and Telegram bot interface.

## Architecture Overview

The system is split into two main layers:

1. **Application Backend (FastAPI)** - Orchestration, validation, and client communication
2. **GPU Service (RunPod/ComfyUI)** - Heavy ML processing and image generation

```
Telegram Bot → Backend API → GPU Server → ComfyUI → Models
```

## MVP Scope (Current Implementation)

### Generation Modes
- ✅ **Free Generation**: Text-to-image with style selection (realism, lux, anime, chatgpt)
- ✅ **Clothes Removal**: Remove clothing while preserving pose and structure
- ⏳ **Face Swap**: (Post-MVP)
- ⏳ **NSFW Face**: (Post-MVP)

### Components
- **Backend**: FastAPI with 2 endpoints (`/health`, `/generate`)
- **GPU Server**: ComfyUI integration with 2 workflows
- **Telegram Bot**: Interactive bot with 2 conversation flows
- **SSH Manager**: Unified remote operations module

## Project Structure

```
generator-ai/
├── backend/                    # FastAPI backend
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   ├── clients/
│   └── utils/
├── gpu_server/                 # GPU service wrapper
│   ├── server.py
│   ├── comfy_client.py
│   ├── workflows/
│   └── models_config/
├── telegram_bot/               # Telegram bot
│   ├── bot.py
│   ├── config.py
│   ├── handlers/
│   └── utils/
├── infra/                      # Infrastructure management
│   ├── ssh_manager.py
│   └── ssh_config.json
├── startup.sh                  # POD auto-start script
├── DEPLOY_INSTRUCTIONS.md      # Deployment guide
└── README.md                   # This file
```

## Quick Start

### Prerequisites
- Python 3.10+
- RunPod account with GPU POD
- Telegram bot token
- SSH key configured

### Local Development

1. **Clone repository**
```bash
git clone <repository-url>
cd generator-ai
```

2. **Set up virtual environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
# Copy templates and fill in secrets
cp backend/.env.template backend/.env
cp telegram_bot/.env.template telegram_bot/.env
cp infra/ssh_config.json.template infra/ssh_config.json
```

5. **Run locally** (for testing without GPU)
```bash
# Backend
cd backend
uvicorn main:app --reload

# Telegram Bot
cd telegram_bot
python bot.py
```

### Deployment to RunPod

See [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md) for complete deployment guide.

**Quick deployment:**
```bash
# Connect to POD
python infra/ssh_manager.py shell

# Check services status
python infra/ssh_manager.py status

# View logs
python infra/ssh_manager.py logs backend
python infra/ssh_manager.py logs gpu_server

# Restart services
python infra/ssh_manager.py restart backend
```

## SSH Management

All remote operations go through the unified SSH manager:

```bash
# Interactive shell
python infra/ssh_manager.py shell

# Execute remote command
python infra/ssh_manager.py exec "ls -la /workspace"

# Service management
python infra/ssh_manager.py restart backend
python infra/ssh_manager.py logs gpu_server
python infra/ssh_manager.py status
```

## API Documentation

### POST /generate

Generate images based on mode and parameters.

**Free Generation Example:**
```json
{
  "mode": "free",
  "prompt": "a beautiful mountain landscape at sunset",
  "style": "realism",
  "extra_params": {
    "steps": 30,
    "cfg_scale": 7.5,
    "seed": -1
  }
}
```

**Clothes Removal Example:**
```json
{
  "mode": "clothes_removal",
  "target_image": "base64_encoded_image_data",
  "style": "realism"
}
```

**Response:**
```json
{
  "task_id": "uuid-string",
  "status": "done",
  "image": "base64_encoded_result",
  "error": null
}
```

### GET /health

Check service health and GPU availability.

**Response:**
```json
{
  "status": "healthy",
  "gpu_available": true,
  "timestamp": "2025-12-08T20:00:00Z"
}
```

## Telegram Bot Usage

1. Start bot: `/start`
2. Choose mode:
   - 🎨 **Free Generation**: Enter text prompt → Select style → Receive image
   - 👕 **Remove Clothes**: Send photo → Select style → Receive processed image

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend | FastAPI + Python 3.10+ | API orchestration |
| GPU Service | FastAPI/Flask | ComfyUI wrapper |
| Image Generation | ComfyUI | Workflow execution |
| Models | SDXL, SD 1.5, ControlNet | Image generation |
| Bot | python-telegram-bot | User interface |
| Infrastructure | OpenSSH, RunPod | Remote management |

## Configuration

### Backend Configuration

Located in `backend/.env`:
```env
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
GPU_SERVICE_URL=http://localhost:8001
LOG_LEVEL=INFO
REQUEST_TIMEOUT=180
```

### GPU Server Configuration

Located in `gpu_server/.env`:
```env
GPU_SERVER_HOST=0.0.0.0
GPU_SERVER_PORT=8001
COMFYUI_API_URL=http://localhost:8188
MODELS_PATH=/workspace/models
WORKFLOWS_PATH=/workspace/workflows
```

### Telegram Bot Configuration

Located in `telegram_bot/.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
BACKEND_API_URL=http://your_backend_url:8000
MAX_IMAGE_SIZE_MB=10
```

## Development Guidelines

### Code Organization Principles

- **Backend**: Orchestration and validation only, NO ML models
- **GPU Server**: Generation logic only
- **Workflows**: Model configuration only
- **Bot**: User interaction only

### Adding New Features

1. Start with design document update
2. Implement backend schema and service
3. Implement GPU server workflow support
4. Create ComfyUI workflow JSON
5. Update bot handlers (if needed)
6. Test end-to-end
7. Update documentation

## Troubleshooting

### Backend not starting
```bash
# Check logs
python infra/ssh_manager.py logs backend

# Check if port is in use
python infra/ssh_manager.py exec "netstat -tulpn | grep 8000"

# Restart service
python infra/ssh_manager.py restart backend
```

### GPU service not responding
```bash
# Check ComfyUI status
python infra/ssh_manager.py exec "curl http://localhost:8188"

# Check GPU server logs
python infra/ssh_manager.py logs gpu_server

# Check GPU availability
python infra/ssh_manager.py exec "nvidia-smi"
```

### Telegram bot not responding
```bash
# Verify bot token
# Check backend connectivity
curl http://your_backend_url:8000/health

# Check bot logs
tail -f telegram_bot/logs/bot.log
```

## Security Notes

⚠️ **Never commit:**
- `.env` files
- SSH private keys
- API tokens
- Model files

✅ **Always:**
- Keep secrets in `.env` files
- Use environment variables
- Review `.gitignore` before committing
- Rotate tokens if exposed

## Performance

### Generation Time Targets

| Mode | Target Time | Maximum Time |
|------|-------------|--------------|
| Free Generation | 15-30 seconds | 60 seconds |
| Clothes Removal | 45-90 seconds | 120 seconds |

### Resource Requirements

- **GPU**: NVIDIA GPU with 10GB+ VRAM
- **RAM**: 16GB+ recommended
- **Storage**: 100GB+ for models
- **Network**: Stable connection for API calls

## Contributing

This is a private project. For questions or issues, contact the project maintainer.

## License

Proprietary - All rights reserved

## Support

For deployment issues, see [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md)

For API documentation, see inline code documentation and design document.
