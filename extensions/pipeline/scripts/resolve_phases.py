#!/usr/bin/env python3
"""CLI wrapper over the phase resolver for the Spec Kit `pipeline` extension.

Usage:
  resolve_phases.py [--skip a,b] [--add x,y] [--json]
  resolve_phases.py --list

Exit codes:
  0  success (ordered phase plan on stdout)
  2  usage error
  10 unknown phase name
  11 skip/add conflict
  12 add not insertable
  13 skip required phase
  14 dependency break
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from phase_registry import (  # noqa: E402
    REGISTRY,
    DEFAULTS,
    INSERTABLE,
    DepBreak,
    NotInsertable,
    RequiredPhaseSkip,
    SkipAddConflict,
    UnknownPhase,
    resolve,
)


def parse_csv(csv_str):
    if not csv_str:
        return set()
    return {item.strip() for item in csv_str.split(",") if item.strip()}


def _row(phase_id):
    p = REGISTRY[phase_id]
    gate = "gate" if p.interactive else "-"
    return f"{p.order}\t{phase_id}\t{p.command}\t{gate}\t{p.description}"


def main():
    parser = argparse.ArgumentParser(
        prog="resolve_phases.py",
        description="Deterministic phase resolver for the Spec Kit pipeline extension.",
    )
    parser.add_argument("--skip", type=str, default="", help="CSV list of phases to skip")
    parser.add_argument("--add", type=str, default="", help="CSV list of insertable phases to add")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--list", action="store_true", help="List all orderable phases and exit")

    try:
        args = parser.parse_args()
    except SystemExit as e:
        if e.code != 0:
            sys.exit(2)
        raise

    if args.list:
        orderable = sorted(
            (set(DEFAULTS) | set(INSERTABLE)), key=lambda p: REGISTRY[p].order
        )
        for phase_id in orderable:
            print(_row(phase_id))
        sys.exit(0)

    skip_set = parse_csv(args.skip)
    add_set = parse_csv(args.add)

    try:
        effective = resolve(skip_set, add_set)
    except (UnknownPhase, SkipAddConflict, NotInsertable, RequiredPhaseSkip, DepBreak) as e:
        print(str(e), file=sys.stderr)
        sys.exit(e.code)

    if args.json:
        output = [
            {
                "phase": phase_id,
                "order": REGISTRY[phase_id].order,
                "command": REGISTRY[phase_id].command,
                "interactive": REGISTRY[phase_id].interactive,
                "description": REGISTRY[phase_id].description,
            }
            for phase_id in effective
        ]
        print(json.dumps(output))
    else:
        for phase_id in effective:
            print(_row(phase_id))

    sys.exit(0)


if __name__ == "__main__":
    main()
