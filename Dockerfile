ARG BASE_IMAGE=livepeer/ai-runner:live-base-v0.14.1
FROM ${BASE_IMAGE}

# Install Python 3.12 and gcc-13 FIRST before creating venv
RUN apt update && apt install -yqq \
    wget git curl \
    build-essential software-properties-common \
    libcairo2-dev libgirepository1.0-dev pkg-config \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    python3-dev \
    && apt clean && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && add-apt-repository ppa:ubuntu-toolchain-r/test -y \
    && apt-get update \
    && apt-get install -y \
        python3.12 \
        python3.12-dev \
        python3.12-venv \
        gcc-13 \
        g++-13 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.12 as the default python3 and set up compiler alternatives
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 \
    && update-alternatives --set python3 /usr/bin/python3.12 \
    && ln -sf /usr/bin/python3.12 /usr/bin/python \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-13 100 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-13 100

WORKDIR /app

COPY pyproject.toml uv.lock ./
# Copy stub for editable install validation
COPY src/scope_runner/pipeline/__init__.py ./src/scope_runner/pipeline/

# Now sync with Python 3.12 and gcc-13
RUN uv sync --locked --no-install-project

COPY src/scope_runner/ ./src/scope_runner/

RUN uv sync --locked

# Force rebuild sageattention from source with the new environment (Python 3.12 + gcc-13)
# This replaces the precompiled wheel with a version built for this container
RUN uv pip install --force-reinstall --no-binary sageattention sageattention

ENV HF_HUB_OFFLINE=1

ARG GIT_SHA
ARG VERSION="undefined"

ENV GIT_SHA="${GIT_SHA}" \
    VERSION="${VERSION}"

# Use the venv binary directly to avoid uv reinstalling the precompiled sageattention wheel
CMD ["/app/.venv/bin/scope-runner"]
