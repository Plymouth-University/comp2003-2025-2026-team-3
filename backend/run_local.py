#!/usr/bin/env python3
"""Cross-platform local backend runner."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
VENV_DIR = BACKEND_DIR / ".venv"
USAGE = "Usage: python run_local.py [--skip-docker] [--skip-migrations] [--no-server]"


def parse_args(args: list[str]) -> tuple[bool, bool, bool]:
    start_docker = True
    run_migrations = True
    start_server = True

    for arg in args:
        if arg == "--skip-docker":
            start_docker = False
        elif arg == "--skip-migrations":
            run_migrations = False
        elif arg == "--no-server":
            start_server = False
        else:
            print(f"Unknown option: {arg}", file=sys.stderr)
            print(USAGE, file=sys.stderr)
            raise SystemExit(1)

    return start_docker, run_migrations, start_server


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def venv_bin_dir() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts"
    return VENV_DIR / "bin"


def venv_environment() -> dict[str, str]:
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = str(VENV_DIR)
    env["PATH"] = str(venv_bin_dir()) + os.pathsep + env.get("PATH", "")
    return env


def run(command: list[str], env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=BACKEND_DIR, env=env, check=True)


def ensure_virtual_environment() -> Path:
    if not VENV_DIR.is_dir():
        print("[run_local] Creating virtual environment...", flush=True)
        run([sys.executable, "-m", "venv", str(VENV_DIR)])

    print("[run_local] Activating virtual environment...", flush=True)
    return venv_python()


def ensure_docker_containers(env: dict[str, str]) -> None:
    if shutil.which("docker") is None:
        print("[run_local] Docker not found; skipping container startup.")
        return

    print("[run_local] Ensuring Postgres containers are up...", flush=True)
    run(["docker", "compose", "-f", "compose.yml", "up", "-d"], env=env)


def run_migrations(python_executable: Path, env: dict[str, str]) -> None:
    print("[run_local] Applying Alembic migrations for core and logs databases...", flush=True)
    run([str(python_executable), "scripts/migrate_all_databases.py"], env=env)


def start_fastapi_server(python_executable: Path, env: dict[str, str]) -> None:
    print("[run_local] Starting FastAPI server on http://0.0.0.0:8000", flush=True)
    print("[run_local] This process runs in the foreground. Press Ctrl+C to stop.", flush=True)
    run(
        [
            str(python_executable),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ],
        env=env,
    )


def main() -> None:
    start_docker, should_run_migrations, should_start_server = parse_args(sys.argv[1:])
    python_executable = ensure_virtual_environment()
    env = venv_environment()

    if start_docker:
        ensure_docker_containers(env)

    if should_run_migrations:
        run_migrations(python_executable, env)

    if should_start_server:
        start_fastapi_server(python_executable, env)
    else:
        print("[run_local] Preflight complete (server launch skipped).")


if __name__ == "__main__":
    main()
