# GCS Emulator Backend Dockerfile
FROM python:3.12-slim

LABEL maintainer="GCS Emulator Team"
LABEL description="Google Cloud Storage Emulator Backend"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir flask-cors

# Copy application code
COPY . .

# Create storage directory
RUN mkdir -p storage

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Set default environment variables
ENV DATABASE_URL=postgresql://postgres:postgres@postgres:5432/gcs_emulator \
    STORAGE_EMULATOR_HOST=http://0.0.0.0:8080 \
    FLASK_ENV=production

# Run the application
CMD ["python", "run.py"]
