#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

START_DOCKER=1
RUN_MIGRATIONS=1
START_SERVER=1

for arg in "$@"; do
  case "$arg" in
    --skip-docker)
      START_DOCKER=0
      ;;
    --skip-migrations)
      RUN_MIGRATIONS=0
      ;;
    --no-server)
      START_SERVER=0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      echo "Usage: ./run_local.sh [--skip-docker] [--skip-migrations] [--no-server]" >&2
      exit 1
      ;;
  esac
done

if [[ ! -d .venv ]]; then
  echo "[run_local] Creating virtual environment..."
  python3 -m venv .venv
fi

echo "[run_local] Activating virtual environment..."
source .venv/bin/activate

if [[ "$START_DOCKER" -eq 1 ]]; then
  if command -v docker >/dev/null 2>&1; then
    echo "[run_local] Ensuring Postgres containers are up..."
    docker compose -f compose.yml up -d
  else
    echo "[run_local] Docker not found; skipping container startup."
  fi
fi

if [[ "$RUN_MIGRATIONS" -eq 1 ]]; then
  echo "[run_local] Applying Alembic migrations for all DB instances..."
  ./scripts/migrate_all_databases.sh
fi

if [[ "$START_SERVER" -eq 1 ]]; then
  echo "[run_local] Starting FastAPI server on http://0.0.0.0:8000"
  echo "[run_local] This process runs in the foreground. Press Ctrl+C to stop."
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
else
  echo "[run_local] Preflight complete (server launch skipped)."
fi
