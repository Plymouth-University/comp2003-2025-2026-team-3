#!/usr/bin/env bash
set -euo pipefail

# Run every Alembic migration tree against every configured database URL.
cd "$(dirname "$0")/.."

run_core_tree() {
  local label="$1"
  local db_url="$2"

  if [[ -z "$db_url" ]]; then
    echo "[ERROR] Missing database URL for ${label}" >&2
    exit 1
  fi

  echo "[INFO] Migrating ${label} with alembic.ini"
  ALEMBIC_DATABASE_URL="$db_url" alembic -c alembic.ini upgrade head
}

run_logs_tree() {
  local db_url="$1"

  if [[ -z "$db_url" ]]; then
    echo "[ERROR] Missing database URL for logs DB" >&2
    exit 1
  fi

  echo "[INFO] Migrating logs database with alembic_logs.ini"
  ALEMBIC_DATABASE_URL="$db_url" alembic -c alembic_logs.ini upgrade head
}

run_core_tree "legacy DB" "${DATABASE_URL:-postgresql+asyncpg://postgres:password@localhost:5432/mydb}"
run_core_tree "profile DB" "${PROFILE_DATABASE_URL:-postgresql+asyncpg://postgres:password@localhost:5433/profile_db}"
run_core_tree "ai DB" "${AI_DATABASE_URL:-postgresql+asyncpg://postgres:password@localhost:5434/ai_db}"
run_logs_tree "${LOG_DATABASE_URL:-postgresql+asyncpg://postgres:password@localhost:5435/logsdb}"

echo "[INFO] All database migrations completed"
