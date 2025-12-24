#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Build base image if BUILD_BASE is set to "trueish"
if [[ "${BUILD_BASE:-}" =~ ^[Tt][Rr][Uu][Ee]|[Yy][Ee][Ss]|[Yy]|1$ ]]; then
  AI_RUNNER_DIR="${AI_RUNNER_DIR:-$SCRIPT_DIR/../ai-runner}"
  if [ ! -d "$AI_RUNNER_DIR/runner" ]; then
    echo "Error: AI_RUNNER_DIR not found at $AI_RUNNER_DIR/runner" >&2
    exit 1
  fi
  cd "$AI_RUNNER_DIR/runner"
  docker build -t livepeer/ai-runner:live-base -f docker/Dockerfile.live-base .
  cd "$SCRIPT_DIR"
fi

# Get version
VERSION="$(git describe --tags --always --dirty 2>/dev/null || echo 'dev')"

# Build the Docker image with tags and build args
docker build \
  -t daydreamlive/scope-runner \
  --build-arg VERSION="${VERSION}" \
  .

