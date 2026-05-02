#!/usr/bin/env python3
"""Reset backend/data/tickets.json from a baseline fixture copy."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = BACKEND_DIR / "data" / "tickets.seed.json"
DEFAULT_TARGET = BACKEND_DIR / "data" / "tickets.json"


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reset ticket fixture file from a baseline copy."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Baseline source JSON file.",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help="Target ticket JSON file to overwrite.",
    )
    return parser.parse_args()


def main() -> None:
    args = build_args()
    if not args.source.exists():
        raise FileNotFoundError(f"Baseline source not found: {args.source}")
    args.target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.source, args.target)
    print(f"Reset complete: {args.target} <- {args.source}")


if __name__ == "__main__":
    main()
