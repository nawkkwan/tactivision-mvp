# Azure Container Apps builds from the repository root. Keep this image aligned
# with backend/Dockerfile, which is used by the existing Render deployment.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_PATH=/app/backend/models/best.pt \
    MODEL_SHA256=DA6A85A5230E4ACFDB4BB10A82B6BB148EADFCF51F7F4AE8787E40CB25E5F47F \
    YOLO_CONFIG_DIR=/tmp/ultralytics

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
RUN cat /app/backend/models/chunks/best.pt.part-* > /app/backend/models/best.pt
RUN python -m backend.app.model_bootstrap

EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
