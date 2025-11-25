#!/usr/bin/env bash
set -euo pipefail
echo "Starting backend (bash) - ensure .venv and dependencies are installed"
if [ ! -d ".venv" ]; then
  python -m venv .venv
fi
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
echo "Launching uvicorn..."
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
