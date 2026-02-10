#!/bin/bash
set -e

# Default to port 8000 if not set
PORT=${PORT:-8000}

echo "Starting ClarityCheck API on port $PORT..."
exec python -m uvicorn backend.api.main:app --host 0.0.0.0 --port "$PORT"
