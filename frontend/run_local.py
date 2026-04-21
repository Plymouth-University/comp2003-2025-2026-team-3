#!/usr/bin/env python3
"""Cross-platform Python equivalent of run_local.sh and run_local.ps1."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parent


def npm_executable() -> str:
    npm = shutil.which("npm")
    if npm is None:
        print("[run_local] npm not found; install Node.js/npm before starting the frontend.", file=sys.stderr)
        raise SystemExit(1)
    return npm


def main() -> None:
    subprocess.run(
        [npm_executable(), "run", "dev"],
        cwd=FRONTEND_DIR,
        check=True,
    )


if __name__ == "__main__":
    main()
