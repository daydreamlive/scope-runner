ARG BASE_IMAGE=livepeer/ai-runner:live-base-sha-v0.14.1
FROM ${BASE_IMAGE}

RUN apt update && apt install -yqq \
    wget git curl \
    build-essential software-properties-common \
    libcairo2-dev libgirepository1.0-dev pkg-config \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    python3-dev \
    && apt clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
# Copy stub for editable install validation
COPY src/scope_runner/pipeline/__init__.py ./src/scope_runner/pipeline/

RUN uv sync --locked --no-install-project

COPY src/scope_runner/ ./src/scope_runner/

RUN uv sync --locked

ENV HF_HUB_OFFLINE=1

ARG GIT_SHA
ARG VERSION="undefined"

ENV GIT_SHA="${GIT_SHA}" \
    VERSION="${VERSION}"

CMD ["uv", "run", "--frozen", "scope-runner"]
