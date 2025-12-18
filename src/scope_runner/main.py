import os
from pathlib import Path

from runner.app import start_app
from runner.live.pipelines import PipelineSpec

from scope.core.config import MODELS_DIR_ENV_VAR

# Monkey-patch the models dir env var for Scope so we support both Scope and ai-runner envs
SCOPE_MODELS_DIR = os.environ.get(MODELS_DIR_ENV_VAR)
RUNNER_MODELS_DIR = os.environ.get("MODEL_DIR")
if not SCOPE_MODELS_DIR and RUNNER_MODELS_DIR:
    os.environ[MODELS_DIR_ENV_VAR] = str(Path(RUNNER_MODELS_DIR) / "Scope--models")

pipeline_spec = PipelineSpec(
    name="scope",
    pipeline_cls="scope_runner.pipeline.pipeline:Scope",
    params_cls="scope_runner.pipeline.params:ScopeParams",
)

def main():
    start_app(pipeline=pipeline_spec)

if __name__ == "__main__":
    main()

