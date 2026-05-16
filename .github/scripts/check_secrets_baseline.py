"""Fail if new entries appear in the detect-secrets baseline without ack.

Mirrors ``check_bandit_baseline.py``: when ``.secrets.baseline`` grows on
a PR, the maintainer adding the new whitelist entry must label the PR
``secrets-baseline-change`` so reviewers see the expansion.

Identity is ``filename + line + type + hashed_secret`` — detect-secrets
already hashes the candidate, so identities are stable across runs and a
swap (remove one, add another with the same count) is still caught.

When the baseline file does not exist at the base ref, the PR is the one
that introduces it; no acknowledgement is required.

For the head side we read the working tree directly (the CI runner is
checked out at the PR head); this avoids fail-opening when
``git show <head_ref>:`` happens to fail.

Required environment variables:
- ``SECRETS_BASELINE_BASE``: git ref of the PR base
- ``SECRETS_BASELINE_LABELS``: comma-separated PR labels

Outside of PR events, all inputs may be empty and the script no-ops.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ".secrets.baseline"
ACK_LABEL = "secrets-baseline-change"


def _read_baseline_at(ref: str) -> tuple[dict, bool]:
    """Return (baseline_json, file_existed_at_ref). Base side only."""
    if not ref:
        return {"results": {}}, False
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
        return {"results": {}}, False
    try:
        return json.loads(blob), True
    except json.JSONDecodeError:
        print(f"Could not parse baseline at {ref}; treating as empty.", file=sys.stderr)
        return {"results": {}}, True


def _read_baseline_from_worktree() -> tuple[dict, bool]:
    """Return (baseline_json, file_exists_on_disk). Head side.

    Reading the working tree (rather than ``git show <head>:``) makes the
    head side fail-closed: a missing file blocks the gate, and a corrupt
    file raises SystemExit rather than being treated as empty (which
    would silently neutralize the gate).
    """
    path = REPO_ROOT / BASELINE_PATH
    if not path.exists():
        return {"results": {}}, False
    try:
        return json.loads(path.read_text(encoding="utf-8")), True
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Working-tree baseline at {BASELINE_PATH} is corrupt: {exc}. "
            f"Refusing to fail-open on a security gate."
        )


def _identities(baseline: dict) -> set[str]:
    """Flatten detect-secrets results to a set of stable identities."""
    ids: set[str] = set()
    results = baseline.get("results", {})
    if not isinstance(results, dict):
        return ids
    for filename, entries in results.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            ids.add(
                "|".join(
                    [
                        str(filename),
                        str(entry.get("line_number", "")),
                        str(entry.get("type", "")),
                        str(entry.get("hashed_secret", "")),
                    ]
                )
            )
    return ids


def main() -> int:
    base_ref = os.environ.get("SECRETS_BASELINE_BASE", "").strip()

    if not base_ref or set(base_ref) <= {"0"}:
        print("No PR base ref; secrets baseline diff check skipped.")
        return 0

    base_baseline, base_existed = _read_baseline_at(base_ref)
    head_baseline, head_existed = _read_baseline_from_worktree()

    if not base_existed:
        print(
            "Baseline file not present at base ref; treating this PR as the "
            "introduction of the baseline. No acknowledgement required."
        )
        return 0

    if not head_existed:
        print(
            f"Baseline file {BASELINE_PATH} existed at the base ref but is "
            f"missing in the working tree. Refusing to fail-open on a "
            f"security gate.",
            file=sys.stderr,
        )
        return 1

    base_ids = _identities(base_baseline)
    head_ids = _identities(head_baseline)

    new_ids = head_ids - base_ids
    if not new_ids:
        print(
            f"Secrets baseline entries: {len(base_ids)} -> {len(head_ids)} "
            f"(no new identities)."
        )
        return 0

    labels = {
        label.strip()
        for label in os.environ.get("SECRETS_BASELINE_LABELS", "").split(",")
        if label.strip()
    }
    if ACK_LABEL in labels:
        print(
            f"Secrets baseline gained {len(new_ids)} new identities; "
            f"acknowledged via label '{ACK_LABEL}'."
        )
        return 0

    print(
        f"Secrets baseline gained {len(new_ids)} new identities. "
        f"Audit the new entries — if they are genuine false positives "
        f"(SHA pins, docs examples, test fixtures), add label "
        f"'{ACK_LABEL}' to the PR to acknowledge them. If any are real "
        f"secrets, remove them from history before merging.",
        file=sys.stderr,
    )
    for identity in sorted(new_ids):
        print(f"  + {identity}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
