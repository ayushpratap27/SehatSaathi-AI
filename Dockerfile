# ============================================================
# SehatSaathi-AI — Backend Dockerfile (multi-stage)
# ============================================================
FROM python:3.12-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt


FROM python:3.12-slim AS runtime

# Non-root user
RUN useradd --create-home appuser && \
    apt-get update && apt-get install -y --no-install-recommends \
        curl && rm -rf /var/lib/apt/lists/*

USER appuser
WORKDIR /app

COPY --from=builder /install /usr/local
COPY --chown=appuser:appuser . .

RUN mkdir -p data/uploads data/processed data/temp data/vector_stores logs

# Pre-download the embedding model so it's baked into the image.
# This avoids a ~400MB download at runtime on every cold start.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('allenai-specter')"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
