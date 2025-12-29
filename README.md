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

## Testing with go-livepeer Box

The [go-livepeer box](https://github.com/livepeer/go-livepeer/blob/master/box/box.md) provides an easy way to test the full Livepeer AI stack locally.

### Using Local Runner

Run scope-runner locally and point the box to it:

1. Start scope-runner locally:

   ```bash
   uv run scope-runner
   # Starts on http://localhost:8000
   ```

2. Create an `aiModels.json` file:

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
   cd /path/to/go-livepeer/box
   export DOCKER=true
   export AI_MODELS_JSON=/path/to/aiModels.json
   make box
   ```

4. Stream and playback:

   ```bash
   make box-stream    # Start streaming
   make box-playback  # View the output
   ```

   On remote/headless machines, set `RTMP_OUTPUT` to stream to an external endpoint instead:

   ```bash
   export RTMP_OUTPUT=rtmp://rtmp.livepeer.com/live/$STREAM_KEY
   make box-stream
   ```

### Using Docker

You can also use it to test the full docker pipeline:

```bash
# Prepare Scope models (first time only)
cd /path/to/ai-runner/runner
PIPELINE=scope ./dl_checkpoints.sh --tensorrt
export AI_MODELS_DIR=$(pwd)/models

# Start the box with Scope pipeline
cd /path/to/go-livepeer
export DOCKER=true
export PIPELINE=scope
make box
```

This builds the `../scope-runner` Docker image and starts it. You can also set `REBUILD=false` to avoid rebuilding everything when the box starts, and instead rebuild and restart only the runner with the box running in background:

```bash
REBUILD=false make box &
make box-runner
```

For more details on creating custom pipelines, see the [ai-runner custom pipeline guide](https://github.com/livepeer/ai-runner/blob/main/docs/custom-pipeline.md).

## License

See [LICENSE.md](LICENSE.md).
