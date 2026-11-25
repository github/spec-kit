#!/usr/bin/env python3
"""Spec Kit autopilot: deterministic conductor, scheduler and gate.

Usage (from the project root, or an epic worktree for the pipe commands):

  Conductor (main checkout)
    autopilot.py preflight [--requirements DIR] [--baseline]
    autopilot.py plan-check [--reset]
    autopilot.py drive [--integration KEY] [--detach]
    autopilot.py status          stage, live drive, epic table, recent events
    autopilot.py stop | unstop   ask the drive to start no new pipes / undo
    autopilot.py report
    autopilot.py land
    autopilot.py reset EPIC_ID
    autopilot.py answer QUESTION_ID --text "..."   the product owner answers

  Pipe (inside one epic's checkout; used by the autopilot-epic workflow)
    autopilot.py consult --stage spec|design|build  file questions for the lead
    autopilot.py record --stage spec|design|build   publish the lead's answers
    autopilot.py check-spec
    autopilot.py gate
    autopilot.py decide
    autopilot.py pipe-result

  Setup
    autopilot.py checks          run the configured gate checks once

Every command prints one JSON object on stdout. Exit status is 0 on success;
1 means the step must stop the workflow (a failed precondition or a pipe that
did not pass). Progress goes to stderr and .specify/autopilot/log.jsonl.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autopilot_core import driver, gate, team  # noqa: E402
from autopilot_core.config import ConfigError, load_config  # noqa: E402
from autopilot_core.spec import FeatureError  # noqa: E402
from autopilot_core.util import GitError, repo_root  # noqa: E402


def _emit(code: int, payload: dict) -> int:
    print(json.dumps(payload, indent=None, sort_keys=False))
    return code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="autopilot.py", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    pre = sub.add_parser("preflight")
    pre.add_argument("--requirements", default=os.environ.get("AUTOPILOT_REQUIREMENTS", ""))
    pre.add_argument("--baseline", action="store_true", help="also run the gate checks on HEAD")
    plan = sub.add_parser("plan-check")
    plan.add_argument("--reset", action="store_true")
    drv = sub.add_parser("drive")
    drv.add_argument("--integration", default=os.environ.get("AUTOPILOT_INTEGRATION", ""))
    drv.add_argument("--detach", action="store_true", help="start in the background and return immediately")
    for name in ("status", "report", "land", "stop", "unstop", "check-spec", "gate", "decide", "pipe-result", "checks"):
        sub.add_parser(name)
    reset = sub.add_parser("reset")
    reset.add_argument("epic_id")
    for name in ("consult", "record"):
        step = sub.add_parser(name)
        step.add_argument("--stage", default="build", choices=["spec", "design", "build"])
    ans = sub.add_parser("answer", help="record the product owner's answer to a question")
    ans.add_argument("question_id")
    ans.add_argument("--text", required=True)
    return parser


def subcommands() -> set[str]:
    action = next(a for a in build_parser()._actions if isinstance(a, argparse._SubParsersAction))
    return set(action.choices)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        root = repo_root(Path.cwd())
        config = load_config(root)
        if args.command == "preflight":
            return _emit(*driver.preflight(root, config, args.requirements, args.baseline))
        if args.command == "plan-check":
            return _emit(*driver.plan_check(root, config, reset=args.reset))
        if args.command == "drive":
            if args.detach:
                return _emit(*driver.drive_detached(root, Path(__file__).resolve(), args.integration))
            return _emit(*driver.drive(root, config, integration=args.integration))
        if args.command == "status":
            return _emit(0, driver.run_status(root))
        if args.command in ("stop", "unstop"):
            path = driver.stop_file(root)
            path.parent.mkdir(parents=True, exist_ok=True)
            if args.command == "stop":
                path.write_text("stop requested\n", encoding="utf-8")
            else:
                path.unlink(missing_ok=True)
            return _emit(0, {"stop_requested": path.exists()})
        if args.command == "report":
            return _emit(*driver.report(root, config))
        if args.command == "land":
            return _emit(*driver.land(root, config))
        if args.command == "reset":
            return _emit(*driver.reset_epic(root, config, args.epic_id))
        if args.command == "consult":
            return _emit(0, team.collect(root, config, args.stage))
        if args.command == "record":
            return _emit(0, team.record(root, config, args.stage))
        if args.command == "answer":
            return _emit(*driver.answer(root, args.question_id, args.text))
        if args.command == "check-spec":
            return _emit(*gate.check_spec(root, config))
        if args.command == "gate":
            return _emit(0, gate.run_gate(root, config))
        if args.command == "decide":
            return _emit(0, gate.decide(root, config))
        if args.command == "pipe-result":
            return _emit(*gate.pipe_result(root))
        if args.command == "checks":
            results = gate.checks_only(root, config, None)
            return _emit(0 if all(r["passed"] for r in results) else 1, {"checks": results})
    except (ConfigError, FeatureError, GitError, gate.GateError, driver.DriverError, team.TeamError) as exc:
        print(f"[autopilot] error: {exc}", file=sys.stderr)
        return _emit(1, {"ok": False, "error": str(exc)})
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
