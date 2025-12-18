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

## License

See [LICENSE.md](LICENSE.md).
