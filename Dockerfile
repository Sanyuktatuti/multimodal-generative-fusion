# Lightweight Railway deployment Dockerfile - API only
FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create lightweight requirements for API only
COPY requirements.txt requirements-full.txt
RUN echo "fastapi==0.104.1" > requirements-api.txt && \
    echo "uvicorn[standard]==0.24.0" >> requirements-api.txt && \
    echo "pydantic==1.10.13" >> requirements-api.txt && \
    echo "redis==5.0.1" >> requirements-api.txt && \
    echo "boto3==1.34.0" >> requirements-api.txt && \
    echo "celery==5.3.4" >> requirements-api.txt && \
    echo "python-dotenv==1.0.0" >> requirements-api.txt && \
    echo "python-multipart==0.0.6" >> requirements-api.txt

# Install only API dependencies (no ML libraries)
RUN pip install --no-cache-dir -r requirements-api.txt && \
    pip cache purge

# Copy only API code and shared schemas
COPY apps/api/ apps/api/
COPY apps/api/routes/ apps/api/routes/
COPY workers/env_gen/tasks.py workers/env_gen/tasks.py
COPY shared/ shared/
COPY workers/__init__.py workers/__init__.py
COPY workers/env_gen/__init__.py workers/env_gen/__init__.py

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]