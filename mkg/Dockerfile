# MKG Service Dockerfile
# Multi-stage build: slim Python image with only production deps

FROM python:3.11-slim AS base

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mkg/ /app/mkg/

# Default command: run the API
ENV PYTHONPATH=/app
EXPOSE 8001

CMD ["uvicorn", "mkg.api.app:app", "--host", "0.0.0.0", "--port", "8001"]
