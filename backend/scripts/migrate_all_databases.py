#!/usr/bin/env python3
"""Run every Alembic migration tree against every configured database URL.

This is the cross-platform Python equivalent of migrate_all_databases.sh.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


DEFAULT_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/mydb"
DEFAULT_PROFILE_DATABASE_URL = (
    "postgresql+asyncpg://postgres:password@localhost:5433/profile_db"
)
DEFAULT_AI_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5434/ai_db"
DEFAULT_LOG_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5435/logsdb"

BACKEND_DIR = Path(__file__).resolve().parents[1]


def get_database_url(name: str, default: str) -> str:
    """Match Bash ${VAR:-default}: use default when unset or empty."""
    return os.environ.get(name) or default


def run_alembic(config_file: str, db_url: str) -> None:
    env = os.environ.copy()
    env["ALEMBIC_DATABASE_URL"] = db_url

    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", config_file, "upgrade", "head"],
        cwd=BACKEND_DIR,
        env=env,
        check=True,
    )


def run_core_tree(label: str, db_url: str) -> None:
    if not db_url:
        print(f"[ERROR] Missing database URL for {label}", file=sys.stderr)
        raise SystemExit(1)

    print(f"[INFO] Migrating {label} with alembic.ini", flush=True)
    run_alembic("alembic.ini", db_url)


def run_logs_tree(db_url: str) -> None:
    if not db_url:
        print("[ERROR] Missing database URL for logs DB", file=sys.stderr)
        raise SystemExit(1)

    print("[INFO] Migrating logs database with alembic_logs.ini", flush=True)
    run_alembic("alembic_logs.ini", db_url)


def main() -> None:
    run_core_tree(
        "legacy DB",
        get_database_url("DATABASE_URL", DEFAULT_DATABASE_URL),
    )
    run_core_tree(
        "profile DB",
        get_database_url("PROFILE_DATABASE_URL", DEFAULT_PROFILE_DATABASE_URL),
    )
    run_core_tree(
        "ai DB",
        get_database_url("AI_DATABASE_URL", DEFAULT_AI_DATABASE_URL),
    )
    run_logs_tree(get_database_url("LOG_DATABASE_URL", DEFAULT_LOG_DATABASE_URL))

    print("[INFO] All database migrations completed")


if __name__ == "__main__":
    main()
