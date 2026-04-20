#!/usr/bin/env python3
"""Expand tickets.json deterministically for load/oversight testing.

Rules enforced:
- only the three SecOps analysts are used for resource assignment
- tickets can be fully unassigned (primary + secondary = null)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ALLOWED_ANALYSTS = ("Alex Johnson", "John Smith", "Priya Patel")


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Expand ticket fixture data.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("backend/data/tickets.json"),
        help="Path to the source tickets JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("backend/data/tickets.json"),
        help="Path to write the expanded tickets JSON file.",
    )
    parser.add_argument(
        "--multiplier",
        type=int,
        default=5,
        help="How many times to replicate the source tickets.",
    )
    parser.add_argument(
        "--start-id",
        type=int,
        default=100001,
        help="Starting autotask_ticket_id for regenerated records.",
    )
    return parser.parse_args()


def assign_resources(global_index: int) -> tuple[str | None, str | None]:
    # Every 4th ticket is fully unassigned to exercise AI auto-assignment.
    if global_index % 4 == 0:
        return None, None

    primary = ALLOWED_ANALYSTS[global_index % len(ALLOWED_ANALYSTS)]

    # Keep some single-owner tickets while others have a secondary.
    if global_index % 5 == 0:
        return primary, None

    secondary = ALLOWED_ANALYSTS[(global_index + 2) % len(ALLOWED_ANALYSTS)]
    return primary, secondary


def main() -> None:
    args = build_args()
    if args.multiplier < 1:
        raise ValueError("multiplier must be >= 1")

    source = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(source, list):
        raise ValueError("Expected tickets JSON root to be an array")

    expanded: list[dict] = []
    for block in range(args.multiplier):
        for index, ticket in enumerate(source):
            global_index = block * len(source) + index
            new_ticket = dict(ticket)
            new_ticket["autotask_ticket_id"] = args.start_id + global_index
            new_ticket["ticket_number"] = f"TCK-2025-{global_index + 1:04d}"

            primary, secondary = assign_resources(global_index)
            new_ticket["primary_resource"] = primary
            new_ticket["secondary_resource"] = secondary

            expanded.append(new_ticket)

    args.output.write_text(json.dumps(expanded, indent=2) + "\n", encoding="utf-8")

    unassigned_count = sum(
        1 for ticket in expanded if ticket.get("primary_resource") is None
    )
    print(f"Expanded {len(source)} -> {len(expanded)} tickets")
    print(f"Primary unassigned tickets: {unassigned_count}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
