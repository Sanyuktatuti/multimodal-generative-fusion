#!/bin/bash
set -e

# Use Railway's PORT environment variable, default to 8000
PORT=${PORT:-8000}

echo "=== RAILWAY DEPLOYMENT DEBUG ==="
echo "PORT environment variable: $PORT"
echo "All environment variables:"
env | grep -E "(PORT|RAILWAY)" || echo "No PORT/RAILWAY vars found"
echo "================================"

echo "Starting uvicorn on host 0.0.0.0 port $PORT"
exec uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT
