# fal.ai Realtime Deployment for Scope Runner

## ✅ fal.ai DOES Support Realtime Applications!

You were correct - fal.ai supports realtime streaming applications with WebSockets. This document explains how to properly deploy Scope Runner's realtime streaming architecture on fal.ai.

## Understanding fal.ai's Realtime Support

fal.ai provides several ways to deploy realtime applications:

1. **`@fal.realtime()` decorator** - For stateless realtime endpoints
2. **`@fal.endpoint(is_websocket=True)` decorator** - For raw WebSocket connections
3. **Container deployment** - Run custom Docker containers with GPU support
4. **`fal.App` class** - Application container model

## The Challenge

Scope Runner uses **Livepeer's ai-runner framework** which:
- Creates a FastAPI application with streaming endpoints
- Runs indefinitely as a server
- Handles WebSocket/HTTP streaming connections
- Manages the realtime video pipeline

The question is: **How do we deploy this existing FastAPI/ASGI app on fal.ai?**

## Deployment Options

### Option 1: Container Deployment (Recommended)

Deploy your existing Docker container on fal.ai using their container support.

**File: `fal_app.py`**

```python
import fal
from fal.container import ContainerImage

# Use your existing Docker image
custom_image = ContainerImage.from_registry(
    "your-dockerhub-username/scope-runner:latest",
)

class ScopeRunnerApp(fal.App, kind="container", image=custom_image):
    """
    Scope Runner deployed as a fal.ai container application.
    Runs the ai-runner streaming server with full WebSocket/realtime support.
    """
    
    machine_type = "GPU-A100"
    keep_alive = 300  # Keep warm for 5 minutes
    
    # The container will run: uv run scope-runner
    # which starts the ai-runner FastAPI server on port 8000
    # fal.ai will automatically expose this port
```

**Deploy:**
```bash
fal deploy fal_app.py
```

**Pros:**
- ✅ Uses your existing Docker image
- ✅ No code changes needed
- ✅ Full ai-runner functionality preserved
- ✅ All WebSocket/streaming endpoints work as-is

**Cons:**
- ⚠️ Requires Docker image in a registry
- ⚠️ Need to verify fal.ai's container port forwarding

### Option 2: Adapt to fal.ai's Realtime Decorators

Rewrite your application to use fal.ai's native realtime decorators.

**This requires significant refactoring** because you'd need to:
1. Extract the Scope pipeline logic
2. Implement fal.ai's realtime interface
3. Handle frame streaming using their protocol
4. Abandon the ai-runner framework

**Example structure:**

```python
import fal
from pydantic import BaseModel
from scope_runner.pipeline.pipeline import Scope
from scope_runner.pipeline.params import ScopeParams

class ScopeRealtimeApp(fal.App):
    def __init__(self):
        self.pipeline = Scope()
    
    @fal.realtime("/generate")
    async def generate_realtime(self, input_data: dict) -> dict:
        # Initialize pipeline with params
        await self.pipeline.initialize(**input_data)
        
        # Generate frames and stream back
        # This would need custom implementation
        # to fit fal.ai's realtime protocol
        pass
```

**Pros:**
- ✅ Native fal.ai integration
- ✅ Potentially better latency

**Cons:**
- ❌ Major refactoring required
- ❌ Lose ai-runner framework benefits
- ❌ Need to reimplement streaming logic
- ❌ Compatibility issues with Livepeer network

### Option 3: Hybrid Approach

Use fal.ai for the compute, but keep your existing architecture:

1. Deploy the Docker container on fal.ai
2. Use fal.ai's container deployment with custom startup command
3. Expose the ai-runner endpoints through fal.ai's routing

**File: `fal_app.py`**

```python
import fal
from fal.container import ContainerImage

custom_image = ContainerImage.from_registry(
    "your-dockerhub-username/scope-runner:latest",
)

class ScopeRunnerApp(fal.App, kind="container", image=custom_image):
    machine_type = "GPU-A100"
    keep_alive = 300
    exposed_port = 8000  # ai-runner's port
    
    def setup(self):
        """Verify GPU and environment."""
        import subprocess
        subprocess.run(["nvidia-smi"])
    
    # fal.ai should forward all requests to the container's port 8000
    # where ai-runner is listening
```

## Recommended Path

### Step 1: Verify fal.ai Container Support

Check fal.ai's documentation to confirm:
- [ ] Can they run long-lived containers?
- [ ] Do they support port forwarding from containers?
- [ ] Can containers run indefinitely (not just per-request)?

### Step 2: Test Container Deployment

```bash
# 1. Build and push your image
docker build -t your-dockerhub/scope-runner:latest .
docker push your-dockerhub/scope-runner:latest

# 2. Update fal_app.py with your image (see Option 1 above)

# 3. Deploy
fal deploy fal_app.py

# 4. Test the endpoints
curl https://your-fal-url/health
```

### Step 3: If Container Approach Doesn't Work

If fal.ai's containers don't support long-running servers:

**Use alternative platforms:**
- **RunPod** - Excellent for this use case (~$0.20-0.80/hour)
- **Vast.ai** - Cheapest option (~$0.15-0.50/hour)
- **Modal** - Similar to fal.ai but explicitly supports ASGI apps
- **Cloud VMs** - Traditional but reliable

See `DEPLOYMENT_ALTERNATIVES.md` for details on these options.

## Key Questions to Answer

Before proceeding, you need to determine:

1. **Does fal.ai support long-running containers?**
   - Or do containers only run per-request?

2. **Can fal.ai containers expose ports for external connections?**
   - The ai-runner needs to accept WebSocket connections

3. **What's the maximum runtime for a fal.ai container?**
   - Your app needs to run indefinitely

4. **Does fal.ai support ASGI/FastAPI app mounting?**
   - Some platforms have `@platform.asgi_app()` decorators

## Testing Locally

Before deploying to fal.ai, test your container:

```bash
# Run your existing Docker image
docker run --gpus all -p 8000:8000 scope-runner:latest

# In another terminal, test the endpoints
curl http://localhost:8000/health

# Test WebSocket connection (if you have a client)
# Connect to ws://localhost:8000/live or similar
```

## Next Steps

1. **Read fal.ai's container documentation**:
   - https://docs.fal.ai/examples/running-a-container
   - Check for examples of long-running services

2. **Check fal.ai's Discord/Support**:
   - Ask if they support indefinitely-running WebSocket servers
   - Request examples of similar deployments

3. **Try the container deployment**:
   - Use Option 1 above
   - See if it works with your streaming endpoints

4. **If fal.ai doesn't work**:
   - Use RunPod or Vast.ai (they definitely support this)
   - See `DEPLOYMENT_ALTERNATIVES.md`

## Comparison: fal.ai vs Alternatives

| Feature | fal.ai | RunPod | Vast.ai | Modal |
|---------|--------|--------|---------|-------|
| **Realtime Support** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Long-running** | ❓ TBD | ✅ Yes | ✅ Yes | ⚠️ 24h limit |
| **Container Support** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **ASGI/FastAPI** | ❓ TBD | ✅ Yes | ✅ Yes | ✅ Yes |
| **Setup Complexity** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Cost (A100)** | ~$1-2/hr | ~$0.50-0.80/hr | ~$0.40-0.60/hr | ~$1-2/hr |

## Conclusion

fal.ai **does** support realtime applications, but we need to verify if their container model supports:
1. Long-running (indefinite) processes
2. Exposed ports for WebSocket connections
3. The ai-runner server architecture

**Recommended action**: Try Option 1 (Container Deployment) and see if it works. If not, RunPod or Vast.ai are proven alternatives that definitely support your use case.

## Resources

- [fal.ai Container Documentation](https://docs.fal.ai/examples/running-a-container)
- [fal.ai Realtime Endpoints](https://docs.fal.ai/serverless/development/realtime)
- [fal.ai WebSocket Support](https://docs.fal.ai/serverless/development/streaming)
- [Livepeer ai-runner](https://github.com/livepeer/ai-runner)

