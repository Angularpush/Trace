FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PyMuPDF, PostgreSQL, and build utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmupdf-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy ML models and datasets
COPY ml/ /app/ml/

# Copy sample raw documents for testing & seeding
COPY sample_data/ /app/sample_data/

# Copy backend application source
COPY backend/ /app/

# Set Python path and storage environment variables
ENV PYTHONPATH="/app:/app/ml:${PYTHONPATH}"
ENV STORAGE_DIR="/app/storage"
ENV UPLOAD_DIR="/app/storage"

# Create persistent storage directory
RUN mkdir -p /app/storage

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
