# fal.ai Deployment Guide

## Overview

Scope Runner is a **realtime streaming video generation server** that can be deployed on fal.ai's serverless platform using their container support.

## Quick Start

```bash
# 1. Install fal CLI
pip install fal-client
fal auth login

# 2. Update fal_app.py with your Docker image
# Edit DOCKER_IMAGE = "your-dockerhub-username/scope-runner:latest"

# 3. Deploy
fal deploy fal_app.py

# 4. Test
curl https://your-fal-url/health
```

## Files

- **`fal_app.py`** - fal.ai deployment configuration (container-based)
- **`DEPLOY_TO_FAL_QUICKSTART.md`** - Detailed quick start guide
- **`FAL_REALTIME_DEPLOYMENT.md`** - Complete deployment documentation
- **`DEPLOYMENT_ALTERNATIVES.md`** - Alternative platforms (RunPod, Vast.ai, etc.)

## How It Works

fal.ai supports realtime applications through their container deployment model:

1. Your existing Docker image is deployed on fal.ai
2. Container starts with GPU (A100)
3. Runs: `uv run scope-runner` (starts ai-runner server)
4. fal.ai forwards requests to your server's port 8000
5. WebSocket connections work as normal

## Requirements

- Docker image in a registry (Docker Hub, etc.)
- fal.ai account and API key
- GPU-enabled container (A100 recommended)

## Configuration

Edit `fal_app.py` to customize:

```python
class ScopeRunnerApp(fal.App, kind="container", image=custom_image):
    machine_type = "GPU-A100"  # GPU type
    keep_alive = 300           # Keep warm (seconds)
    exposed_port = 8000        # ai-runner port
```

## Alternatives

If fal.ai doesn't meet your needs:

- **RunPod** - Proven to work, ~$0.20-0.80/hour
- **Vast.ai** - Cheapest option, ~$0.15-0.50/hour
- **AWS/GCP/Azure** - Production-grade VMs
- **Kubernetes** - Enterprise scale

See `DEPLOYMENT_ALTERNATIVES.md` for details.

## Documentation

- **Quick Start**: `DEPLOY_TO_FAL_QUICKSTART.md`
- **Complete Guide**: `FAL_REALTIME_DEPLOYMENT.md`
- **Alternatives**: `DEPLOYMENT_ALTERNATIVES.md`
- **Original Setup**: `README.md`

## Support

- fal.ai: https://fal.ai/support
- Scope Runner: GitHub Issues
- ai-runner: https://github.com/livepeer/ai-runner

