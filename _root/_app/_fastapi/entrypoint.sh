#!/bin/bash
set -e

echo "Starting API server..."
uvicorn _app._fastapi.main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

echo "Setup complete, API running..."
wait $UVICORN_PID