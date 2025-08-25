#!/bin/bash
set -e

# Use Railway's PORT environment variable, default to 8000
PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT"
exec uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT
