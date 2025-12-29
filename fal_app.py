"""
fal.ai deployment for Scope Runner.

This deploys the ai-runner streaming server as a fal.ai container application.
The container runs indefinitely, handling realtime WebSocket connections.

Based on: https://docs.fal.ai/examples/serverless/deploy-models-with-custom-containers
"""

import fal
from fal.container import ContainerImage

# Configuration
DOCKER_IMAGE = "livepeer/ai-runner:live-app-scope-sha-d7da222"

# Create a Dockerfile that uses your existing image as base
dockerfile_str = f"""
FROM {DOCKER_IMAGE}

# The base image already has everything configured
# Ensure the working directory and dependencies are available
WORKDIR /app

# Make sure uv and dependencies are in the PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Verify the installation is accessible
RUN python -c "from scope.core.config import MODELS_DIR_ENV_VAR; print('Scope installed')" || \
    (cd /app && uv sync --locked)
"""

# For private registries, configure registries parameter:
# REGISTRY_CONFIG = {
#     "https://my.registry.io/": {
#         "username": "your_username",
#         "password": "your_password",
#     },
# }

# Create container image from Dockerfile string
custom_image = ContainerImage.from_dockerfile_str(
    dockerfile_str,
    # registries=REGISTRY_CONFIG,  # Uncomment if using private registry
)

class ScopeRunnerApp(fal.App, keep_alive=300):
    """
    Scope Runner realtime streaming server on fal.ai.
    
    This runs your existing Docker container which starts the ai-runner server.
    The server handles WebSocket connections for realtime video generation.
    
    Configuration:
    - GPU: A100 (24GB+ VRAM required)
    - Custom Image: Uses livepeer/ai-runner Docker image
    - Port: 8000 (ai-runner default)
    """
    
    # Set custom Docker image
    image = custom_image
    
    # GPU configuration
    machine_type = "GPU-H100"  # Will use GPU, fal will assign appropriate type
    
    # Additional requirements needed for the setup code
    requirements = [
        "requests",  # For health check
    ]
    
    # Track if a websocket connection is currently in use
    _websocket_in_use = False
    
    def setup(self):
        """
        Setup runs when the container starts.
        Verifies GPU and starts the ai-runner server.
        """
        import subprocess
        import logging
        import os
        import time
        import threading
        from pathlib import Path
        
        logger = logging.getLogger(__name__)
        print("Starting Scope Runner container setup...")
        
        # Verify GPU is available
        try:
            result = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"GPU Status:\n{result.stdout}")
        except Exception as e:
            logger.error(f"GPU check failed: {e}")
            raise
        
        # Set up environment for scope runner
        # Import inside the function to ensure the image's Python environment is used
        
        # Prepare models before starting the server
        print("Preparing models...")
        prepare_env = os.environ.copy()
        prepare_env["PIPELINE"] = "scope"
        prepare_env["MODEL_DIR"] = "/data/models"
        prepare_env["HF_HUB_OFFLINE"] = "0"
        
        # Create models directory if it doesn't exist
        models_dir = "/data/models/Scope--models"
        os.makedirs(models_dir, exist_ok=True)
        print(f"Created models directory: {models_dir}")
        
        try:
            result = subprocess.run(
                ["uv", "run", "scope-runner", "--prepare-models"],
                env=prepare_env,
                cwd="/app",
                capture_output=True,
                text=True,
                check=True,
            )
            print(f"Models prepared successfully:\n{result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to prepare models: {e}\nStdout: {e.stdout}\nStderr: {e.stderr}")
            raise

        # Check disk usage of downloaded models
        try:
            du_result = subprocess.run(
                ["du", "-h", "/data/models/Scope--models"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"Models disk usage:\n{du_result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Could not check models disk usage: {e}")
        
        # Start the ai-runner server in a background thread
        def start_server():
            print("Starting ai-runner server...")
            try:
                # Use subprocess to run the server with uv, ensuring the correct environment
                import sys
                # The container has uv and the project installed
                subprocess.run(
                    ["uv", "run", "--frozen", "scope-runner"],
                    cwd="/app",
                    check=True,
                    env=prepare_env,
                )
            except Exception as e:
                logger.error(f"Failed to start ai-runner server: {e}")
                raise
        
        # Start server in background thread
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Wait a bit for the server to start
        print("Waiting for ai-runner server to start...")
        time.sleep(5)
        
        # Verify server is running
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ ai-runner server is running on port 8000")
            else:
                logger.warning(f"ai-runner server responded with status {response.status_code}")
        except Exception as e:
            logger.warning(f"Could not verify ai-runner server: {e}")
            print("Server may still be initializing...")
        
        print("Scope Runner container setup complete")
    
    @fal.endpoint("/")
    def index(self):
        """
        Health check endpoint.
        The actual ai-runner server runs on port 8000 with endpoints:
        - /health - Health check
        - /live - WebSocket streaming endpoint
        - /sessions - Session management
        """
        import requests
        try:
            # Check if ai-runner server is responding
            response = requests.get("http://localhost:8000/health", timeout=2)
            ai_runner_status = "running" if response.status_code == 200 else "error"
        except:
            ai_runner_status = "not_responding"
        
        return {
            "status": "running",
            "app": "Scope Runner",
            "description": "Realtime video generation streaming server",
            "ai_runner_status": ai_runner_status,
            "ai_runner_port": 8000,
            "endpoints": {
                "health": "http://localhost:8000/health",
                "live": "ws://localhost:8000/live",
                "sessions": "http://localhost:8000/sessions"
            }
        }
    
    from fastapi import WebSocket

    @fal.endpoint("/live-video-to-video", is_websocket=True)
    async def live_video_to_video(self, websocket: WebSocket) -> None:
        """
        Raw WebSocket endpoint for live video-to-video requests.
        Keeps a persistent WebSocket connection open and forwards JSON messages 
        to the local ai-runner server.
        
        This uses a raw WebSocket (not fal.realtime) so it's compatible with
        standard WebSocket clients like Postman, browser WebSocket API, etc.
        """
        import requests
        import logging
        import json
        import time
        import asyncio
        
        logger = logging.getLogger(__name__)
        
        try:
            # Check if a websocket is already in use
            if ScopeRunnerApp._websocket_in_use:
                print("⚠️ Rejecting connection: a websocket is already in use")
                await websocket.close(code=1008, reason="Another connection is already in progress")
                return
            
            # Accept the WebSocket connection
            print("Attempting to accept WebSocket connection...")
            await websocket.accept()
            print("✅ WebSocket connection accepted")
            
            # Mark websocket as in use
            ScopeRunnerApp._websocket_in_use = True
            print("WebSocket marked as in use")
            
            # Check if ai-runner server is running (with retry loop)
            health_check_success = False
            start_time = time.time()
            timeout_seconds = 300  # 5 minutes
            retry_interval = 2  # seconds between retries
            
            while not health_check_success and (time.time() - start_time) < timeout_seconds:
                try:
                    health_check = requests.get("http://localhost:8000/health", timeout=2)
                    print(f"ai-runner health check: {health_check.status_code}")
                    if health_check.status_code == 200:
                        health_check_success = True
                        print("✅ ai-runner health check succeeded")
                    else:
                        logger.warning(f"ai-runner health check returned non-200 status: {health_check.status_code}")
                        time.sleep(retry_interval)
                except Exception as health_error:
                    elapsed = time.time() - start_time
                    logger.warning(f"ai-runner health check failed (elapsed: {elapsed:.1f}s): {health_error}")
                    if (time.time() - start_time) < timeout_seconds:
                        time.sleep(retry_interval)
            
            if not health_check_success:
                logger.error(f"ai-runner health check failed after {timeout_seconds}s timeout")
            
            # Send initial connection acknowledgment
            await websocket.send_json({
                "type": "connection_established",
                "message": "WebSocket connection ready for live video-to-video"
            })
            print("✅ Sent initial acknowledgment")
        except Exception as accept_error:
            logger.error(f"Failed to accept WebSocket connection: {accept_error}")
            raise
        
        try:
            
            # Keep connection open and process incoming messages
            while True:
                # Receive message as text/JSON
                message_text = await websocket.receive_text()
                print(f"Received message via WebSocket: {message_text}")
                
                try:
                    # Parse the JSON message
                    request_data = json.loads(message_text)
                    
                    # Forward the request to the local ai-runner server
                    response = requests.post(
                        "http://localhost:8000/live-video-to-video",
                        json=request_data,
                        timeout=30
                    )
                    
                    # Stream the response back via WebSocket
                    response.raise_for_status()
                    result = response.json()
                    
                    await websocket.send_json({
                        "type": "result",
                        "data": result
                    })
                    
                    while True:
                        # Send health check every 5 seconds
                        await asyncio.sleep(5)
                        try:
                            health_response = requests.get("http://localhost:8000/health", timeout=2)
                            await websocket.send_json({
                                "type": "health_check",
                                "status": health_response.status_code,
                                "data": health_response.json() if health_response.status_code == 200 else None
                            })
                        except Exception as health_error:
                            logger.warning(f"Health check failed: {health_error}")
                            await websocket.send_json({
                                "type": "health_check",
                                "status": "error",
                                "error": str(health_error)
                            })
                    
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e),
                        "message": "Invalid JSON format"
                    })
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error proxying request to ai-runner: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e),
                        "message": "Failed to proxy request to ai-runner server"
                    })
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            try:
                await websocket.send_json({
                    "type": "error",
                    "error": str(e),
                    "message": "WebSocket connection error"
                })
            except:
                pass  # Connection might already be closed
        finally:
            # Mark websocket as no longer in use
            ScopeRunnerApp._websocket_in_use = False
            print("WebSocket marked as no longer in use")
            
            await websocket.close()
            print("WebSocket connection closed for live-video-to-video")


# Deployment:
#   1. Run: fal run fal_app.py (for local testing)
#   2. Run: fal deploy fal_app.py (to deploy to fal.ai)
#   3. fal.ai will provide you with a URL
#   4. The ai-runner server runs on port 8000 with endpoints like /health, /live, etc.

