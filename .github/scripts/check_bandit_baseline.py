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

Required environment variables:
- ``BANDIT_BASELINE_BASE``: git ref of the PR base
- ``BANDIT_BASELINE_HEAD``: git ref of the PR head
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
    """Return (baseline_json, file_existed_at_ref)."""
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
    head_ref = os.environ.get("BANDIT_BASELINE_HEAD", "").strip() or "HEAD"

    if not base_ref or set(base_ref) <= {"0"}:
        print("No PR base ref; baseline diff check skipped.")
        return 0

    base_baseline, base_existed = _read_baseline_at(base_ref)
    head_baseline, _ = _read_baseline_at(head_ref)

    if not base_existed:
        print(
            "Baseline file not present at base ref; treating this PR as the "
            "introduction of the baseline. No acknowledgement required."
        )
        return 0

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
