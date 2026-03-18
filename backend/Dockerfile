FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml ./

# Install Python dependencies including Celery and Redis
RUN uv pip install --system -r pyproject.toml && pip install celery redis

# Copy application code
COPY app ./app
COPY scripts ./scripts

# Run celery worker by default
CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info"]
