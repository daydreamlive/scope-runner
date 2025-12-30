# Scope Runner

Integration of [Scope](https://github.com/daydreamlive/scope) with [ai-runner](https://github.com/livepeer/ai-runner) for running Scope pipelines over the Livepeer network.

🚧 This project is currently in **alpha**. 🚧

## System Requirements

- [uv](https://docs.astral.sh/uv/) package manager
- NVIDIA GPU with >= 24GB VRAM

## Install

```bash
git clone https://github.com/daydreamlive/scope-runner.git
cd scope-runner
uv sync
```

## Prepare Models

Download required models before running:

```bash
mkdir -p ~/.daydream-scope/models
uv run scope-runner --prepare-models
```

Models are stored in `~/.daydream-scope/models` by default. It can be overridden by either `DAYDREAM_SCOPE_MODELS_DIR` env or `MODEL_DIR`. When `MODEL_DIR` is set (e.g. when ran by Orchestrators), models go to `$MODEL_DIR/Scope--models/`.

## Run

```bash
uv run scope-runner
```

The server starts on port 8000.

## Docker

```bash
# Build
docker build -t scope-runner .

# Run
docker run --gpus all -v /path/to/models:/models -p 8000:8000 scope-runner
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pipeline` | string | `"longlive"` | Pipeline type |
| `prompts` | array | - | List of prompts (string or `{"text": "...", "weight": 100}`) |
| `seed` | int | `42` | Random seed |
| `width` | int | - | Output width |
| `height` | int | - | Output height |

## E2E testing with The Box

The [go-livepeer box](https://github.com/livepeer/go-livepeer/blob/master/box/box.md) provides an easy way to test the full Livepeer AI stack locally.

Common setup for both methods below (local or dockerized):

```bash
cd /path/to/go-livepeer
export PIPELINE=scope
# Easier to get started, uses docker for go-livepeer nodes; may skip if you have already set up the local go-livepeer dev env
export DOCKER=true
```

### Method 1: Using Local Runner

Start `scope-runner` locally and point the box to it:

1. Start scope-runner locally:

   ```bash
   uv run scope-runner
   # Starts on http://localhost:8000
   ```

2. Create an `aiModels.json` file to point to your local runner:

   ```json
   [
     {
       "pipeline": "live-video-to-video",
       "model_id": "scope",
       "url": "http://localhost:8000"
     }
   ]
   ```

3. Start the box with your config:

   ```bash
   export AI_MODELS_JSON=/path/to/aiModels.json
   REBUILD=false make box
   ```

   `REBUILD=false` skips building Docker images since we're running the pipeline locally. It might download `go-livepeer` docker image instead if not available locally.

4. Stream and playback:

   ```bash
   make box-stream    # Start streaming
   make box-playback  # Watch the output
   ```

   On remote/headless machines, set `RTMP_OUTPUT` to stream to an external endpoint instead:

   ```bash
   export RTMP_OUTPUT=rtmp://rtmp.livepeer.com/live/$STREAM_KEY
   make box-stream
   ```

### Method 2: Using Docker

Test the full docker pipeline. More similar to production and catches issues like missing dependencies, models, etc.

1. Prepare Scope models (first time only):

   ```bash
   cd /path/to/ai-runner/runner
   PIPELINE=scope ./dl_checkpoints.sh --tensorrt
   export AI_MODELS_DIR=$(pwd)/models
   ```

2. Start the box.

   Change to `go-livepeer` directory and:

   **Option A** - Full rebuild (slower, first time or after major changes):

   ```bash
   make box
   ```

   **Option B** - Incremental rebuild (faster, for iterating on scope-runner):

   ```bash
   REBUILD=false make box &  # Start box in background without rebuilding
   make box-runner           # Rebuild and restart only the runner
   ```

3. Stream and playback (same as local runner):

   ```bash
   make box-stream    # Start streaming
   make box-playback  # Watch the output
   ```

   You can similarly use the `RTMP_OUTPUT` on a headless machine.

For more details on creating custom pipelines, see the [ai-runner custom pipeline guide](https://github.com/livepeer/ai-runner/blob/main/docs/custom-pipeline.md). For more information on using the `go-livepeer` box see [its guide](https://github.com/livepeer/go-livepeer/blob/master/box/box.md).

## Release Process

Scope Runner uses a two-stage deployment process managed via [livepeer-infra](https://github.com/livepeer/livepeer-infra):

| Environment | Image Tag | Trigger |
|-------------|-----------|---------|
| Staging | `daydreamlive/scope-runner:main` | Push to `main` branch |
| Production | `daydreamlive/scope-runner:latest` | Git tag (e.g. ideally a semver like `v0.2.0`) |

### Staging

Merging to `main` automatically builds and pushes the `:main` Docker image. This is auto-deployed to staging orchestrators.

### Production

To release to production:

1. **Tag the release** on git:

   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

The tagged build creates the `:latest` image which production Orchestrators use (including public Os).

2. **Create a GitHub Release** at [releases page](https://github.com/daydreamlive/scope-runner/releases) with release notes. This is a good practice to share some metadata about the release.

## License

See [LICENSE.md](LICENSE.md).
