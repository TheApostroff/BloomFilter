#!/usr/bin/env bash
set -euo pipefail
echo "Starting backend and frontend..."

# Start backend in background
cd backend
if [ ! -d ".venv" ]; then
  python -m venv .venv
fi
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend health check to pass
echo "Waiting for backend at http://localhost:8000/api/health..."
for i in {1..30}; do
  if curl -s -f http://127.0.0.1:8000/api/health >/dev/null; then
    echo "Backend is ready"
    break
  else
    echo "Backend not ready yet - retrying... ($i/30)"
    sleep 1
  fi
done

if ! curl -s -f http://127.0.0.1:8000/api/health >/dev/null; then
  echo "Timeout waiting for backend to be ready. Frontend will still start, but may fail to fetch initially."
fi

# Start frontend in background
cd ../frontend
npm install
npm run dev &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID, Frontend PID: $FRONTEND_PID"
wait $BACKEND_PID $FRONTEND_PID
exit 0
