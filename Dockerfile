# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# system deps for any OS operations (safe minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app files
COPY . .

# Create data directory and ensure permission
RUN mkdir -p /data && touch /data/tasks.json
ENV TASKS_FILE=/data/tasks.json
VOLUME /data

# Use gunicorn for production
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "120"]
