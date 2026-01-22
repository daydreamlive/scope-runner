# Scope Runner Documentation

## Overview

**Scope Runner** is an integration layer that connects the **Scope** video generation pipeline with the **ai-runner** framework to run Scope pipelines over the Livepeer network. It enables text-to-video generation capabilities on the decentralized Livepeer network by adapting Scope's LongLive models to work with Livepeer's AI infrastructure.

| Property | Value |
|----------|-------|
| Status | Alpha |
| License | CC BY-NC-SA 4.0 |
| Organization | Daydream Live |
| Primary Use Case | Video generation on decentralized networks |

---

## Architecture

```mermaid
graph TB
    subgraph "External Network"
        Client[HTTP/WebSocket Client]
    end

    subgraph "ai-runner Framework"
        FastAPI[FastAPI Server<br/>Port 8000]
        PipelineInterface[Pipeline Interface]
        TrickleIO[Trickle I/O<br/>VideoFrame / VideoOutput]
    end

    subgraph "Scope Runner"
        Main[main.py<br/>Entry Point]
        ScopePipeline[Scope Pipeline<br/>Adapter]
        ScopeParams[ScopeParams<br/>Pydantic Model]
        FrameQueue[AsyncIO Queue<br/>Frame Buffer]
    end

    subgraph "Daydream Scope"
        LongLive[LongLive Pipeline<br/>1.3B Parameters]
        ModelDownload[Model Downloader]
        ConfigManager[Config Manager]
    end

    subgraph "GPU Runtime"
        PyTorch[PyTorch 2.8.0<br/>CUDA 12.8]
        Models[Model Weights<br/>bfloat16]
    end

    Client <-->|HTTP/WS| FastAPI
    FastAPI --> PipelineInterface
    PipelineInterface --> TrickleIO
    TrickleIO <--> ScopePipeline
    Main --> FastAPI
    Main -.->|Monkey Patch| ConfigManager
    ScopePipeline --> ScopeParams
    ScopePipeline --> FrameQueue
    ScopePipeline --> LongLive
    LongLive --> PyTorch
    PyTorch --> Models
    ModelDownload --> Models
```

---

## Data Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant AR as ai-runner
    participant SP as Scope Pipeline
    participant Q as Frame Queue
    participant LL as LongLive Model
    participant GPU as CUDA GPU

    C->>AR: Input VideoFrame (trigger)
    AR->>SP: put_video_frame()
    SP->>SP: Submit to ThreadPool

    rect rgb(40, 40, 80)
        Note over SP,GPU: Synchronous Generation (Worker Thread)
        SP->>LL: _generate_sync()
        LL->>GPU: Forward Pass (bfloat16)
        GPU-->>LL: Output Tensor (T,H,W,C)
        LL-->>SP: Generated Frames
    end

    loop For each frame in batch
        SP->>Q: Queue VideoFrame
        Note right of Q: Incremented timestamps
    end

    AR->>SP: get_processed_video_frame()
    SP->>Q: Await frame
    Q-->>SP: VideoFrame
    SP-->>AR: VideoOutput
    AR-->>C: Output VideoFrame
```

---

## Component Interaction

```mermaid
flowchart LR
    subgraph Entry["Entry Point"]
        main[main.py]
    end

    subgraph Pipeline["Pipeline Layer"]
        pipeline[pipeline.py<br/>Scope class]
        params[params.py<br/>ScopeParams]
    end

    subgraph External["External Libraries"]
        airunner[ai-runner<br/>Pipeline Interface]
        scope[daydream-scope<br/>LongLive]
        torch[PyTorch<br/>CUDA]
    end

    main -->|start_app| airunner
    main -->|monkey patch| scope
    pipeline -->|implements| airunner
    pipeline -->|uses| scope
    pipeline -->|validates| params
    params -->|extends| airunner
    scope -->|uses| torch
```

---

## Pipeline Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Uninitialized: Application Start

    Uninitialized --> Initialized: initialize(params)
    Note right of Initialized: Load LongLive Model<br/>Validate ScopeParams

    Initialized --> Processing: put_video_frame()
    Processing --> Processing: Generate & Queue Frames
    Processing --> Initialized: Queue Empty

    Initialized --> Reloading: update_params()<br/>(pipeline/size change)
    Reloading --> Initialized: _reload_pipeline()

    Processing --> Stopped: stop()
    Initialized --> Stopped: stop()
    Stopped --> [*]
```

---

## Key Components

### 1. Main Entry Point (`src/scope_runner/main.py`)

- Initializes model directory configuration
- Monkey-patches Scope's config to support ai-runner's `MODEL_DIR` environment variable
- Creates `PipelineSpec` for pipeline registration
- Starts the FastAPI application via `runner.app.start_app()`

### 2. Pipeline Adapter (`src/scope_runner/pipeline/pipeline.py`)

The `Scope` class implements the ai-runner `Pipeline` interface:

| Method | Purpose |
|--------|---------|
| `initialize(**params)` | Load LongLive model, validate parameters |
| `put_video_frame(frame, request_id)` | Trigger video generation (async) |
| `get_processed_video_frame()` | Retrieve generated frames from queue |
| `update_params(**params)` | Update generation parameters at runtime |
| `stop()` | Clean up resources |
| `prepare_models()` | Download models for offline use |

### 3. Parameters (`src/scope_runner/pipeline/params.py`)

```python
class ScopeParams(BaseParams):
    pipeline: Literal["longlive"] = "longlive"
    prompts: List[Union[str, WeightedPrompt]]
    seed: int = 42

class WeightedPrompt(BaseModel):
    text: str
    weight: int = 100
```

---

## External Interfaces

### ai-runner Framework (Livepeer)

```mermaid
classDiagram
    class Pipeline {
        <<interface>>
        +initialize(**params) async
        +put_video_frame(frame, request_id) async
        +get_processed_video_frame() async VideoOutput
        +update_params(**params) async
        +stop() async
        +prepare_models() classmethod
    }

    class BaseParams {
        <<abstract>>
    }

    class VideoFrame {
        +ndarray frame
        +Fraction time_base
        +int pts
    }

    class VideoOutput {
        +VideoFrame frame
    }

    class PipelineSpec {
        +str name
        +type pipeline_class
    }

    Scope --|> Pipeline : implements
    ScopeParams --|> BaseParams : extends
    Scope ..> VideoFrame : consumes
    Scope ..> VideoOutput : produces
```

| Interface | Import Path | Purpose |
|-----------|-------------|---------|
| `Pipeline` | `runner.live.pipelines` | Base async pipeline interface |
| `BaseParams` | `runner.live.pipelines` | Parameter validation base |
| `PipelineSpec` | `runner.live.pipelines` | Pipeline registration |
| `VideoFrame` | `runner.live.trickle` | Input/output frame structure |
| `VideoOutput` | `runner.live.trickle` | Output wrapper |
| `start_app()` | `runner.app` | FastAPI application launcher |

### Daydream Scope Library

```mermaid
classDiagram
    class ScopePipeline {
        <<interface>>
        +generate(prompts) Tensor
    }

    class LongLivePipeline {
        +generate(prompts) Tensor
        +shutdown()
    }

    class ConfigModule {
        +get_models_dir() Path
        +MODELS_DIR_ENV_VAR str
    }

    class DownloadModule {
        +download_models()
    }

    LongLivePipeline --|> ScopePipeline
    Scope ..> LongLivePipeline : uses
    Scope ..> ConfigModule : patches
    Scope ..> DownloadModule : uses
```

| Interface | Import Path | Purpose |
|-----------|-------------|---------|
| `Pipeline` | `scope.core.pipelines.interface` | Scope pipeline interface |
| `LongLivePipeline` | `scope.core.pipelines` | Video generation model |
| `get_models_dir()` | `scope.core.config` | Model directory path |
| `MODELS_DIR_ENV_VAR` | `scope.core.config` | Environment variable name |
| `download_models()` | `scope.server.download_models` | Model downloader |

### PyTorch Interface

| Interface | Purpose |
|-----------|---------|
| `torch.Tensor` | Frame data in (T, H, W, C) format |
| `torch.cuda.is_available()` | GPU availability check |
| `torch.bfloat16` | Model precision |
| `asyncio.get_running_loop().run_in_executor()` | Offload generation to thread |

### Configuration Interface

| Environment Variable | Purpose | Default |
|---------------------|---------|---------|
| `DAYDREAM_SCOPE_MODELS_DIR` | Scope models directory | `~/.daydream-scope/models/` |
| `MODEL_DIR` | ai-runner orchestrator model dir | - |
| `HF_HUB_OFFLINE` | Disable HuggingFace online access | `1` (in Docker) |

---

## Dependencies

```mermaid
graph TD
    subgraph "Scope Runner"
        SR[scope-pipeline v0.1.1]
    end

    subgraph "Core Dependencies"
        AIR[ai-runner v0.14.1<br/>realtime flavor]
        DS[daydream-scope v0.1.0a7]
    end

    subgraph "ML Stack"
        PT[PyTorch 2.8.0<br/>CUDA 12.8]
        ACC[accelerate 1.12.0]
        ST[safetensors]
    end

    subgraph "Web Stack"
        FA[FastAPI ≥0.116.1]
        UV[uvicorn]
        PY[pydantic]
    end

    subgraph "Runtime"
        PYR[Python 3.10.12 - 3.11]
        OC[omegaconf]
    end

    SR --> AIR
    SR --> DS
    AIR --> FA
    AIR --> UV
    AIR --> PY
    DS --> PT
    DS --> ACC
    DS --> ST
    DS --> OC
    PT --> PYR
```

| Dependency | Version | Source | Purpose |
|------------|---------|--------|---------|
| `ai-runner[realtime]` | 0.14.1 | Livepeer GitHub | Framework, HTTP server |
| `daydream-scope` | 0.1.0a7 | Daydream GitHub | Video generation models |
| `torch` | 2.8.0+cu128 | PyPI | GPU computation |
| `accelerate` | 1.12.0 | PyPI | Multi-device support |
| `fastapi` | ≥0.116.1 | PyPI | Web framework |
| `pydantic` | ≥2.0 | PyPI | Data validation |
| `omegaconf` | Latest | PyPI | Configuration |

---

## Model Architecture

```mermaid
graph LR
    subgraph "Input"
        P[Text Prompts<br/>+ Weights]
    end

    subgraph "Text Processing"
        TOK[UMT5-XXL<br/>Tokenizer]
        ENC[UMT5-XXL<br/>Encoder fp8]
    end

    subgraph "Generation"
        GEN[LongLive-1.3B<br/>Base Model]
        LORA[LoRA Adapter]
    end

    subgraph "Output"
        OUT[Video Frames<br/>T×H×W×C]
    end

    P --> TOK
    TOK --> ENC
    ENC --> GEN
    LORA --> GEN
    GEN --> OUT
```

| Component | File | Purpose |
|-----------|------|---------|
| Generator | `LongLive-1.3B/models/longlive_base.pt` | Base video model |
| LoRA | `LongLive-1.3B/models/lora.pt` | Adapter weights |
| Text Encoder | `WanVideo_comfy/umt5-xxl-enc-fp8_e4m3fn.safetensors` | Text embedding |
| Tokenizer | `Wan2.1-T2V-1.3B/google/umt5-xxl` | Text tokenization |

---

## Deployment

### Docker

```mermaid
graph TD
    subgraph "Base Image"
        BASE[livepeer/ai-runner:live-base-v0.14.1]
    end

    subgraph "Build"
        UV[uv Package Manager]
        SRC[Source Code]
        DEPS[Dependencies]
    end

    subgraph "Runtime"
        CMD[uv run --frozen scope-runner]
        ENV[HF_HUB_OFFLINE=1]
    end

    BASE --> UV
    UV --> SRC
    UV --> DEPS
    SRC --> CMD
    DEPS --> CMD
    ENV --> CMD
```

### Image Tags

| Tag | Trigger | Purpose |
|-----|---------|---------|
| `daydreamlive/scope-runner:main` | Push to main | Staging |
| `daydreamlive/scope-runner:latest` | Git tag | Production |
| `daydreamlive/scope-runner:v0.1.1` | Git tag v0.1.1 | Version pin |

---

## Usage

### Running the Server

```bash
# Start the server
uv run scope-runner

# Prepare models for offline use
uv run scope-runner --prepare-models
```

### API

The server exposes a FastAPI application on port 8000 with endpoints inherited from ai-runner for real-time video streaming via HTTP and WebSocket.

---

## Design Patterns

| Pattern | Implementation |
|---------|----------------|
| **Adapter** | `Scope` class adapts ai-runner interface to Scope |
| **Producer-Consumer** | AsyncIO queue decouples generation from output |
| **Thread Pool** | GPU generation offloaded to worker thread |
| **Lazy Loading** | Models loaded on `initialize()`, not import |
| **Configuration Injection** | Environment variables for deployment flexibility |
