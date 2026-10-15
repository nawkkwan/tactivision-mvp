FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_PATH=/app/yolo11n.pt

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Keep the staging model in the immutable image so a Render restart does not
# need to download it again. The fine-tuned model remains outside Git and can
# replace MODEL_PATH in a later production image.
RUN python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"

COPY backend /app/backend
EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

