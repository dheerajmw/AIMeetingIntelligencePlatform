# MeetIQ Phase 5 API — Docker (Render, Railway, local)
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STORAGE_ROOT=/app/storage \
    DATABASE_URL=sqlite:////app/data/app.db

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# CPU-only PyTorch keeps the image smaller than the default CUDA wheel.
RUN pip install --upgrade pip \
    && pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt

COPY app ./app
COPY deploy/storage ./storage
COPY scripts/start.sh ./scripts/start.sh
RUN chmod +x ./scripts/start.sh \
    && mkdir -p /app/data /app/storage/uploads

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8002/health')" || exit 1

CMD ["./scripts/start.sh"]
