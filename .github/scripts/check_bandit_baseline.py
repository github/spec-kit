"""Fail if new entries appear in the Bandit baseline without acknowledgement.

The bandit baseline whitelists known findings so they don't fail CI. If a
contributor adds a new entry, silent whitelisting becomes invisible in
review. This script compares the set of result *identities* in the
baseline at the PR head against the baseline at its base; if any new
identity appears, the PR must carry the label ``security-baseline-change``
to confirm the addition is intentional.

We compare identities (filename + line + test_id + issue_severity +
issue_confidence + hash-of-code-snippet) rather than raw counts so a PR
cannot remove one existing entry and add a different new one to keep the
count constant — which would silently whitelist a new finding.

When the baseline file does not exist at the base ref, this is the PR
that introduces it; we treat all entries as the starting baseline and
do not require the label.

For the head side we read the working tree directly (the CI runner is
checked out at the PR head, so the working-tree file IS the head state).
Reading via ``git show <head_ref>:`` would fail-open on unfetched refs
or detached checkouts — for a security gate we want fail-closed.

Required environment variables:
- ``BANDIT_BASELINE_BASE``: git ref of the PR base
- ``BANDIT_BASELINE_LABELS``: comma-separated PR labels

Outside of PR events, all inputs may be empty and the script no-ops.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ".github/bandit-baseline.json"
ACK_LABEL = "security-baseline-change"


def _read_baseline_at(ref: str) -> tuple[dict, bool]:
    """Return (baseline_json, file_existed_at_ref).

    Used for the base side. The head side reads the working tree to avoid
    silently fail-opening on an unfetched/invalid head ref.
    """
    if not ref:
        return {"results": []}, False
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
        return {"results": []}, False
    try:
        return json.loads(blob), True
    except json.JSONDecodeError:
        print(f"Could not parse baseline at {ref}; treating as empty.", file=sys.stderr)
        return {"results": []}, True


def _read_baseline_from_worktree() -> tuple[dict, bool]:
    """Return (baseline_json, file_exists_on_disk).

    The CI runner is checked out at the PR head, so the working-tree
    file IS the head state. Reading it directly sidesteps spurious
    ``git show`` failures that would otherwise let an unreadable head
    silently pass the gate.

    Asymmetric with the base reader: a corrupt JSON on disk is the
    proposed PR state — we fail-closed there rather than treating
    it as an empty baseline (which would silently drop the gate).
    """
    path = REPO_ROOT / BASELINE_PATH
    if not path.exists():
        return {"results": []}, False
    try:
        return json.loads(path.read_text(encoding="utf-8")), True
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Working-tree baseline at {BASELINE_PATH} is corrupt: {exc}. "
            f"Refusing to fail-open on a security gate."
        )


_WHITESPACE_RE = re.compile(r"\s+")


def _identity(result: dict) -> str:
    """Stable identity for a baseline entry.

    Combines location, test, severity, confidence, and a hash of the
    pinned code snippet (whitespace-normalized) so reformatting changes
    or upstream bandit-output tweaks don't register as new findings,
    but a different finding at the same line does.
    """
    code = result.get("code", "") or ""
    normalized = _WHITESPACE_RE.sub(" ", code).strip()
    code_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return "|".join(
        [
            str(result.get("filename", "")),
            str(result.get("line_number", "")),
            str(result.get("test_id", "")),
            str(result.get("issue_severity", "")),
            str(result.get("issue_confidence", "")),
            code_hash,
        ]
    )


def main() -> int:
    base_ref = os.environ.get("BANDIT_BASELINE_BASE", "").strip()

    if not base_ref or set(base_ref) <= {"0"}:
        print("No PR base ref; baseline diff check skipped.")
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
        # Fail-closed: the file existed at base but is missing in the
        # working tree. Either the PR deleted it (suspicious — the gate
        # would no longer protect anything) or the workspace is incomplete.
        print(
            f"Baseline file {BASELINE_PATH} existed at the base ref but is "
            f"missing in the working tree. Refusing to fail-open on a "
            f"security gate.",
            file=sys.stderr,
        )
        return 1

    base_ids = {_identity(r) for r in base_baseline.get("results", [])}
    head_ids = {_identity(r) for r in head_baseline.get("results", [])}

    new_ids = head_ids - base_ids
    if not new_ids:
        print(
            f"Bandit baseline entries: {len(base_ids)} -> {len(head_ids)} "
            f"(no new identities)."
        )
        return 0

    labels = {
        label.strip()
        for label in os.environ.get("BANDIT_BASELINE_LABELS", "").split(",")
        if label.strip()
    }
    if ACK_LABEL in labels:
        print(
            f"Bandit baseline gained {len(new_ids)} new identities; "
            f"acknowledged via label '{ACK_LABEL}'."
        )
        return 0

    print(
        f"Bandit baseline gained {len(new_ids)} new identities. "
        f"Add label '{ACK_LABEL}' to the PR to acknowledge that the new "
        f"whitelist entries are intentional.",
        file=sys.stderr,
    )
    for identity in sorted(new_ids):
        print(f"  + {identity}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
