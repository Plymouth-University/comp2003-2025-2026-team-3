#!/usr/bin/env python3
"""Cross-platform local frontend runner."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parent
VENV_DIR = FRONTEND_DIR / ".venv"


def venv_bin_dir() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts"
    return VENV_DIR / "bin"


def venv_environment() -> dict[str, str]:
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = str(VENV_DIR)
    env["PATH"] = str(venv_bin_dir()) + os.pathsep + env.get("PATH", "")
    return env


def ensure_virtual_environment() -> None:
    if not VENV_DIR.is_dir():
        print("[run_local] Creating frontend virtual environment...", flush=True)
        subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            cwd=FRONTEND_DIR,
            check=True,
        )
    print("[run_local] Using frontend virtual environment...", flush=True)


def npm_executable() -> str:
    npm = shutil.which("npm")
    if npm is None:
        print("[run_local] npm not found; install Node.js/npm before starting the frontend.", file=sys.stderr)
        raise SystemExit(1)
    return npm


def ensure_node_modules() -> None:
    if not (FRONTEND_DIR / "node_modules").is_dir():
        print(
            "[run_local] node_modules not found. Run 'npm install' in frontend before starting.",
            file=sys.stderr,
        )
        raise SystemExit(1)


def main() -> None:
    ensure_virtual_environment()
    ensure_node_modules()
    subprocess.run(
        [npm_executable(), "run", "dev"],
        cwd=FRONTEND_DIR,
        env=venv_environment(),
        check=True,
    )


if __name__ == "__main__":
    main()
