FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source code and assets
COPY src/ ./src/
COPY sample_data/ ./sample_data/
COPY .env.example .env

# Expose FastAPI port
EXPOSE 8000

ENV PYTHONPATH=/app

# Default command: start FastAPI web service
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
