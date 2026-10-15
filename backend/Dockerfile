FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_PATH=/app/backend/models/best.pt \
    MODEL_SOURCE_URL=https://drive.google.com/drive/folders/1kcQ2iX54u2-L1bbyucHKRryzd1ASyl9y?usp=sharing \
    MODEL_SHA256=DA6A85A5230E4ACFDB4BB10A82B6BB148EADFCF51F7F4AE8787E40CB25E5F47F

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
# Download the versioned fine-tuned model once during the image build. The
# checksum prevents a changed or incomplete Drive artifact from being deployed.
RUN python -m backend.app.model_bootstrap
EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

