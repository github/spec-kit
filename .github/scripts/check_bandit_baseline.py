"""Fail if the Bandit baseline grew on this PR without explicit acknowledgement.

The bandit baseline whitelists known findings so they don't fail CI. If a
contributor adds a new entry, silent whitelisting becomes invisible in
review. This script counts the entries in the baseline at the PR head vs.
its base; if the count increased, the PR must carry the label
``security-baseline-change`` to confirm the addition is intentional.

Required environment variables:
- ``BANDIT_BASELINE_BASE``: git ref of the PR base (``github.event.pull_request.base.sha``)
- ``BANDIT_BASELINE_HEAD``: git ref of the PR head (``github.sha``)
- ``BANDIT_BASELINE_LABELS``: comma-separated PR labels (``join(github.event.pull_request.labels.*.name, ',')``)

Outside of PR events, all inputs may be empty and the script no-ops.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ".github/bandit-baseline.json"
ACK_LABEL = "security-baseline-change"


def _read_baseline_at(ref: str) -> dict:
    if not ref:
        return {"results": []}
    try:
        blob = subprocess.run(
            ["git", "show", f"{ref}:{BASELINE_PATH}"],
            check=True,
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout
    except subprocess.CalledProcessError:
        # File didn't exist at that ref (e.g. PR introducing the baseline).
        return {"results": []}
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        print(f"Could not parse baseline at {ref}; treating as empty.", file=sys.stderr)
        return {"results": []}


def main() -> int:
    base_ref = os.environ.get("BANDIT_BASELINE_BASE", "").strip()
    head_ref = os.environ.get("BANDIT_BASELINE_HEAD", "").strip() or "HEAD"

    if not base_ref or set(base_ref) <= {"0"}:
        # Not a PR event, or the base ref is the zero-SHA placeholder.
        print("No PR base ref; baseline diff check skipped.")
        return 0

    base_count = len(_read_baseline_at(base_ref).get("results", []))
    head_count = len(_read_baseline_at(head_ref).get("results", []))

    if head_count <= base_count:
        print(
            f"Bandit baseline entries: {base_count} -> {head_count} (no growth)."
        )
        return 0

    labels = {
        label.strip()
        for label in os.environ.get("BANDIT_BASELINE_LABELS", "").split(",")
        if label.strip()
    }
    if ACK_LABEL in labels:
        print(
            f"Bandit baseline grew from {base_count} to {head_count} entries; "
            f"acknowledged via label '{ACK_LABEL}'."
        )
        return 0

    print(
        f"Bandit baseline grew from {base_count} to {head_count} entries. "
        f"Add label '{ACK_LABEL}' to the PR to acknowledge that the new "
        f"whitelist entries are intentional.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
