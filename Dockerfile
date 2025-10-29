# Use a slim Python image as the base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# build-essential for compiling python packages, libpq-dev for PostgreSQL
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        python3-dev \
        libmagic1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only the dependency file first to leverage Docker cache
COPY pyproject.toml ./

# Install Python dependencies
# Using editable install to follow your pyproject.toml dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -e .

# Copy the rest of your application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/storage /app/logs /app/keys

# Health check script
COPY scripts/health_check.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/health_check.sh

# Expose the port FastAPI will run on
EXPOSE 8000

# Default command to run the FastAPI application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]