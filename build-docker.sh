#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Get version
VERSION="$(bash print_version.sh)"

# Set base image arg if USE_LATEST_BASE is set to "trueish"
BASE_IMAGE_ARG=""
if [[ "${USE_LATEST_BASE:-}" =~ ^[Tt][Rr][Uu][Ee]|[Yy][Ee][Ss]|[Yy]|1$ ]]; then
  BASE_IMAGE_ARG="--build-arg BASE_IMAGE=livepeer/ai-runner:live-base"
fi

# Build the Docker image with tags and build args
docker build \
  -t daydreamlive/scope-runner \
  --build-arg VERSION="${VERSION}" \
  ${BASE_IMAGE_ARG} \
  .

