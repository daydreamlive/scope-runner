# Deploy to fal.ai - Quick Start

## TL;DR

```bash
# 1. Install fal CLI
pip install fal-client
fal auth login

# 2. Update fal_app.py with your Docker image name

# 3. Deploy
fal deploy fal_app.py

# 4. Test
curl https://your-fal-url/health
```

## Prerequisites

- [ ] Docker image built and pushed to a registry
- [ ] fal.ai account (sign up at https://fal.ai)
- [ ] fal CLI installed (`pip install fal-client`)

## Step-by-Step

### 1. Prepare Your Docker Image

```bash
# Build
docker build -t your-dockerhub-username/scope-runner:latest .

# Push to Docker Hub (or your registry)
docker push your-dockerhub-username/scope-runner:latest
```

### 2. Update Deployment File

Edit `fal_app.py`:

```python
# Change this line:
DOCKER_IMAGE = "your-dockerhub-username/scope-runner:latest"
```

### 3. Authenticate with fal.ai

```bash
# Option A: Interactive login
fal auth login

# Option B: Use API key
export FAL_KEY="your-fal-api-key"
```

Get your API key from: https://fal.ai/dashboard/keys

### 4. Deploy

```bash
fal deploy fal_app.py
```

You'll get a URL like: `https://your-username-scope-runner.fal.run`

### 5. Test

```bash
# Health check
curl https://your-fal-url/health

# Check if server is responding
curl https://your-fal-url/

# Test WebSocket (if you have a client)
# Connect to: ws://your-fal-url/live
```

## Configuration Options

Edit `fal_app.py` to customize:

```python
class ScopeRunnerApp(fal.App, kind="container", image=custom_image):
    # GPU type
    machine_type = "GPU-A100"  # or "GPU-A100-80GB"
    
    # Keep instance warm (seconds)
    keep_alive = 300  # 5 minutes
    
    # Port your app listens on
    exposed_port = 8000
```

### GPU Options

- `"GPU-T4"` - 16GB VRAM (may be insufficient)
- `"GPU-A10G"` - 24GB VRAM
- `"GPU-A100"` - 40GB VRAM (recommended)
- `"GPU-A100-80GB"` - 80GB VRAM (for large models)

### Keep Alive Options

- `0` - No warm instances (coldest start, cheapest)
- `300` - 5 minutes (balanced)
- `3600` - 1 hour (fastest, more expensive)

## Troubleshooting

### "Image not found"

Make sure your Docker image is:
- Pushed to a public registry, OR
- Configure private registry credentials in `fal_app.py`

### "GPU not available"

Check that:
- Your Docker image includes NVIDIA drivers
- You're using a CUDA base image
- `nvidia-smi` works in the container

### "Port not accessible"

Verify:
- `exposed_port = 8000` matches your app's port
- ai-runner is actually listening on that port
- fal.ai supports port forwarding (check their docs)

### "Container exits immediately"

Check logs with:
```bash
fal logs your-username/scope-runner
```

Common issues:
- Missing models (models not in image)
- Environment variables not set
- CMD in Dockerfile is incorrect

## Monitoring

### View Logs

```bash
fal logs your-username/scope-runner
```

### Check Status

```bash
fal status your-username/scope-runner
```

### View Metrics

Go to: https://fal.ai/dashboard

## Cost Estimation

**A100 GPU:**
- Compute: ~$0.0015/second (~$5.40/hour)
- Keep alive (5 min): ~$0.45/hour baseline
- Per request: Variable based on generation time

**Example costs:**
- Always on (24/7): ~$3,900/month
- With keep_alive (busy hours): ~$500-1,500/month
- Pure pay-per-use: ~$0.10-0.50 per video

## Alternative: If fal.ai Doesn't Work

If you encounter issues with fal.ai's container model:

### RunPod (Proven Alternative)

```bash
# 1. Go to runpod.io
# 2. Deploy → GPU Pod
# 3. Select: RTX A5000 or A100
# 4. Docker Image: your-dockerhub-username/scope-runner:latest
# 5. Expose Port: 8000
# 6. Deploy
```

Cost: ~$0.20-0.80/hour
Setup time: 5 minutes

See `DEPLOYMENT_ALTERNATIVES.md` for more options.

## Next Steps

After successful deployment:

1. **Test thoroughly**
   - Health endpoints
   - WebSocket connections
   - Video generation
   - Performance under load

2. **Monitor costs**
   - Check fal.ai dashboard
   - Adjust keep_alive if needed
   - Consider alternatives if too expensive

3. **Set up CI/CD** (optional)
   - Use `.github/workflows/deploy-fal.yml`
   - Automate deployments on push

4. **Document your endpoint**
   - Share URL with team
   - Document API usage
   - Set up monitoring/alerts

## Resources

- **Complete guide**: `FAL_REALTIME_DEPLOYMENT.md`
- **Alternatives**: `DEPLOYMENT_ALTERNATIVES.md`
- **Corrections**: `FAL_INTEGRATION_CORRECTED.md`
- **fal.ai docs**: https://docs.fal.ai
- **Support**: https://fal.ai/support

## Quick Reference

```bash
# Deploy
fal deploy fal_app.py

# Check logs
fal logs your-username/scope-runner

# Check status
fal status your-username/scope-runner

# Update deployment
# (edit fal_app.py, then)
fal deploy fal_app.py

# Remove deployment
fal delete your-username/scope-runner
```

## Success Checklist

- [ ] Docker image built and pushed
- [ ] fal CLI installed and authenticated
- [ ] `fal_app.py` updated with image name
- [ ] Deployed successfully
- [ ] Health endpoint responds
- [ ] WebSocket connections work
- [ ] Video generation works
- [ ] Costs are acceptable
- [ ] Monitoring set up

## Need Help?

- **fal.ai issues**: https://fal.ai/support or Discord
- **Scope Runner issues**: GitHub Issues
- **Architecture questions**: `FAL_REALTIME_DEPLOYMENT.md`

---

**Remember:** This is a realtime streaming server, not a simple function. Make sure fal.ai's container model supports indefinite runtime before committing to production use.

