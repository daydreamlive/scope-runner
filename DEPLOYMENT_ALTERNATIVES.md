# Deployment Alternatives for Scope Runner

Since Scope Runner is a **realtime streaming video generation application**, it requires infrastructure that supports long-running processes and persistent connections. This document outlines suitable deployment options.

## Architecture Overview

Scope Runner:
- Runs indefinitely as a server (not request/response)
- Uses `ai-runner[realtime]` framework
- Processes streaming video frames continuously
- Requires persistent connections (WebSocket or similar)
- GPU-intensive workload (24GB+ VRAM)

## ❌ Why NOT fal.ai Serverless

fal.ai serverless functions are designed for:
- ✅ Short-lived, stateless operations
- ✅ Request → Process → Response patterns
- ✅ Single video/image generation tasks

They do NOT support:
- ❌ Long-running processes
- ❌ Persistent WebSocket connections
- ❌ Continuous streaming
- ❌ Indefinite execution

## ✅ Recommended Deployment Options

### Option 1: Cloud VM with GPU (Recommended for Production)

Deploy on a cloud provider with GPU instances:

#### AWS EC2

```bash
# Launch GPU instance (g5.xlarge or p3.2xlarge)
# Amazon Linux 2 or Ubuntu 22.04
# Install Docker and NVIDIA Container Toolkit

# Pull or build image
docker pull your-registry/scope-runner:latest

# Run with GPU
docker run -d --gpus all \
  --restart unless-stopped \
  -v /data/models:/models \
  -p 8000:8000 \
  --name scope-runner \
  your-registry/scope-runner:latest
```

**Pros:**
- ✅ Full control over infrastructure
- ✅ Persistent connections supported
- ✅ Suitable for 24/7 operation
- ✅ Multiple GPU options (A10G, A100, etc.)

**Cons:**
- ⚠️ Fixed costs (even when idle)
- ⚠️ Requires infrastructure management
- ⚠️ Must handle scaling manually

**Cost:** ~$1-4/hour depending on GPU

#### Google Cloud Compute Engine

```bash
# Create instance with GPU
gcloud compute instances create scope-runner \
  --zone=us-central1-a \
  --machine-type=n1-standard-4 \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=100GB

# SSH and deploy
gcloud compute ssh scope-runner --zone=us-central1-a
# Install Docker, NVIDIA drivers, and run container
```

**Cost:** ~$0.35-1.5/hour depending on GPU

#### Azure Virtual Machines

```bash
# Create NC-series VM with GPU
az vm create \
  --resource-group scope-runner-rg \
  --name scope-runner-vm \
  --size Standard_NC6s_v3 \
  --image Ubuntu2204 \
  --admin-username azureuser \
  --generate-ssh-keys

# Deploy container
ssh azureuser@<vm-ip>
# Install Docker, NVIDIA drivers, and run container
```

**Cost:** ~$0.90-3/hour depending on GPU

### Option 2: Kubernetes with GPU Nodes

For production-grade deployments with auto-scaling:

#### Google Kubernetes Engine (GKE)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scope-runner
spec:
  replicas: 1
  selector:
    matchLabels:
      app: scope-runner
  template:
    metadata:
      labels:
        app: scope-runner
    spec:
      nodeSelector:
        cloud.google.com/gke-accelerator: nvidia-tesla-t4
      containers:
      - name: scope-runner
        image: your-registry/scope-runner:latest
        resources:
          limits:
            nvidia.com/gpu: 1
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: models
          mountPath: /models
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: models-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: scope-runner-service
spec:
  type: LoadBalancer
  ports:
  - port: 8000
    targetPort: 8000
  selector:
    app: scope-runner
```

```bash
# Create GPU node pool
gcloud container node-pools create gpu-pool \
  --cluster=my-cluster \
  --machine-type=n1-standard-4 \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --num-nodes=1

# Deploy
kubectl apply -f deployment.yaml
```

**Pros:**
- ✅ Production-ready
- ✅ Auto-scaling support
- ✅ Rolling updates
- ✅ Health checks and auto-restart

**Cons:**
- ⚠️ Complex setup
- ⚠️ Kubernetes learning curve
- ⚠️ Higher base costs

### Option 3: RunPod / Vast.ai (Cost-Effective GPU Rental)

Specialized GPU cloud providers with better pricing:

#### RunPod

```bash
# Use RunPod's container deployment
# 1. Go to runpod.io
# 2. Create pod with GPU (RTX 3090, 4090, A4000, A5000, A6000)
# 3. Use Docker template
# 4. Deploy your image

# Or use RunPod API
curl -X POST https://api.runpod.io/v1/pods \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "cloudType": "SECURE",
    "gpuTypeId": "NVIDIA RTX A5000",
    "name": "scope-runner",
    "dockerImage": "your-registry/scope-runner:latest",
    "ports": "8000/http",
    "volumeInGb": 50
  }'
```

**Pros:**
- ✅ Much cheaper than AWS/GCP/Azure
- ✅ Wide GPU selection
- ✅ Simple deployment
- ✅ Pay-per-minute pricing

**Cons:**
- ⚠️ Less reliable than major clouds
- ⚠️ Community GPUs may have availability issues
- ⚠️ Limited SLA

**Cost:** ~$0.20-0.80/hour for suitable GPUs

#### Vast.ai

```bash
# Browse available GPUs at vast.ai
# Select instance with 24GB+ VRAM
# Use your Docker image
# Connect via SSH or expose ports
```

**Pros:**
- ✅ Extremely cheap ($0.15-0.50/hour)
- ✅ Spot pricing available
- ✅ Large GPU marketplace

**Cons:**
- ⚠️ No SLA
- ⚠️ Instances can be interrupted
- ⚠️ Best for development/testing

### Option 4: Modal (Serverless Containers)

Modal supports long-running containers with GPUs:

```python
# modal_app.py
import modal

app = modal.App("scope-runner")

# Create image with dependencies
image = modal.Image.from_registry(
    "your-registry/scope-runner:latest",
    add_python="3.10"
)

@app.function(
    image=image,
    gpu="A100",
    keep_warm=1,  # Keep 1 instance always running
    allow_concurrent_inputs=100,
    timeout=86400,  # 24 hours
)
@modal.asgi_app()
def serve():
    # Your FastAPI/ASGI app from ai-runner
    from scope_runner.main import create_app
    return create_app()
```

```bash
modal deploy modal_app.py
```

**Pros:**
- ✅ Simpler than Kubernetes
- ✅ Good GPU support
- ✅ Can keep instances warm
- ✅ Built-in monitoring

**Cons:**
- ⚠️ Still has time limits (24h max)
- ⚠️ May not support all streaming patterns
- ⚠️ New platform (less mature)

**Cost:** Similar to major clouds

### Option 5: Replicate (If Willing to Adapt)

If you can modify your architecture to batch/async:

```python
# cog.yaml
build:
  gpu: true
  python_version: "3.10"
  system_packages:
    - "libgl1-mesa-glx"
  python_packages:
    - "torch>=2.0.0"
predict: "predict.py:Predictor"

# predict.py
from cog import BasePredictor, Input
class Predictor(BasePredictor):
    def setup(self):
        # Load your pipeline once
        from scope_runner.pipeline.pipeline import _load_longlive_pipeline
        self.pipe = _load_longlive_pipeline(...)
    
    def predict(
        self,
        prompt: str = Input(description="Prompt"),
        # ... other inputs
    ) -> Path:
        # Generate and return video
        pass
```

**Pros:**
- ✅ Easy deployment
- ✅ Built-in API
- ✅ Public model hosting

**Cons:**
- ⚠️ Requires architecture change
- ⚠️ Not for streaming/realtime
- ⚠️ 60s timeout per request

## Comparison Matrix

| Option | Monthly Cost* | Setup Time | Streaming Support | Reliability | Best For |
|--------|--------------|------------|-------------------|-------------|----------|
| **AWS EC2** | $730-2,920 | 2-4 hours | ✅ Full | ⭐⭐⭐⭐⭐ | Production |
| **GCP Compute** | $250-1,100 | 2-4 hours | ✅ Full | ⭐⭐⭐⭐⭐ | Production |
| **Azure VM** | $650-2,200 | 2-4 hours | ✅ Full | ⭐⭐⭐⭐⭐ | Production |
| **Kubernetes** | $500-2,000+ | 1-2 days | ✅ Full | ⭐⭐⭐⭐⭐ | Enterprise |
| **RunPod** | $150-580 | 30 min | ✅ Full | ⭐⭐⭐⭐ | Cost-effective |
| **Vast.ai** | $110-360 | 30 min | ✅ Full | ⭐⭐⭐ | Dev/Testing |
| **Modal** | $730-2,920 | 1 hour | ⚠️ Limited | ⭐⭐⭐⭐ | Hybrid |
| **Replicate** | Pay-per-use | 2 hours | ❌ None | ⭐⭐⭐⭐ | Single videos |

*Assuming 24/7 operation for one instance

## Recommended Path

### For Development/Testing
1. **Start with Vast.ai or RunPod** - Cheap GPU rental
2. Test your streaming endpoints
3. Validate performance

### For Production
1. **RunPod for initial production** - Good balance of cost/reliability
2. **Move to AWS/GCP/Azure** if you need:
   - Higher reliability guarantees
   - Better networking
   - Integration with other services
   - Enterprise SLAs

### For Scale
1. **Kubernetes (GKE/EKS/AKS)** when you need:
   - Multiple instances
   - Auto-scaling
   - High availability
   - Geographic distribution

## Example: Quick Start with RunPod

```bash
# 1. Build and push your image
docker build -t your-dockerhub/scope-runner:latest .
docker push your-dockerhub/scope-runner:latest

# 2. Go to runpod.io
# 3. Deploy → GPU Pod
# 4. Select GPU: RTX A5000 or better (24GB+ VRAM)
# 5. Docker Image: your-dockerhub/scope-runner:latest
# 6. Expose Port: 8000
# 7. Deploy

# 8. Access via provided URL
curl https://your-pod-id.runpod.io:8000/health
```

## Monitoring & Maintenance

Regardless of platform, implement:

1. **Health Checks**: Ensure server is responsive
2. **GPU Monitoring**: Track VRAM usage
3. **Auto-Restart**: Handle crashes gracefully
4. **Logging**: Centralized logs (CloudWatch, Stackdriver, etc.)
5. **Alerts**: Notify on failures
6. **Backups**: Model files and configuration

## Need Help Choosing?

Answer these questions:

1. **Budget**: <$200/mo → Vast.ai, $200-500/mo → RunPod, >$500/mo → Cloud VMs
2. **Reliability**: Testing → Vast.ai, Production → RunPod/Cloud, Mission-critical → GCP/AWS
3. **Scale**: Single instance → VM, Multiple → Kubernetes
4. **Team size**: Solo → RunPod, Small team → Cloud VM, Large → Kubernetes

## Summary

For your realtime streaming Scope Runner:

- ✅ **Start with RunPod** - Best cost/reliability balance
- ✅ **Use your existing Docker container** - No code changes needed
- ✅ **Keep the streaming architecture** - It works as designed
- ❌ **Don't use serverless functions** - They're not suitable for streaming

Your app will run exactly as intended (`uv run scope-runner`) on persistent GPU infrastructure.

