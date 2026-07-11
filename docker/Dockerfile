# ===========================================================================
# SehatSaathi-AI — Dockerfile (multi-stage)
# ===========================================================================
# Stage 1: build — install dependencies into a clean layer
# Stage 2: runtime — copy only the installed packages + application code
# ===========================================================================

# ---- Stage 1: dependency build ------------------------------------------ #
FROM python:3.12-slim AS builder

WORKDIR /build

# System deps required to compile some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ---- Stage 2: runtime image --------------------------------------------- #
FROM python:3.12-slim AS runtime

# Non-root user for security
RUN useradd --create-home appuser
USER appuser

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=appuser:appuser . .

# Ensure required runtime directories exist
RUN mkdir -p data/uploads data/processed data/temp logs

EXPOSE 8000

# Entrypoint — can be overridden in docker-compose
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
