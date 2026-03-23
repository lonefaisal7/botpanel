#!/usr/bin/env bash
# ─────────────────────────────────────────────
#  run.sh  —  Start the Bot Hosting Panel
# ─────────────────────────────────────────────
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtualenv if present
if [ -d "venv" ]; then
  source venv/bin/activate
fi

mkdir -p bots uploads

echo "🚀  Starting Bot Hosting Panel on http://0.0.0.0:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
