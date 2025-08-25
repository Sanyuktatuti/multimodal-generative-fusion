#!/bin/bash
set -e

# Use Railway's PORT environment variable, default to 8000
PORT=${PORT:-8000}

echo "=== RAILWAY DEPLOYMENT DEBUG ==="
echo "PORT environment variable: $PORT"
echo "All PORT-related environment variables:"
env | grep -i port || echo "No PORT variables found"
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"
echo "Python path: $PYTHONPATH"
echo "Railway variables:"
env | grep RAILWAY || echo "No RAILWAY variables"
echo "================================"

echo "Testing Python imports..."
python -c "import sys; print('Python sys.path:', sys.path)" || echo "Python import failed"
python -c "import apps.api.main; print('Main app import successful')" || echo "Main app import failed"

echo "Starting uvicorn on host 0.0.0.0 port $PORT"
exec uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT
