"""Check that committed security audit requirements are up to date."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMMITTED_REQUIREMENTS = REPO_ROOT / ".github" / "security-audit-requirements.txt"
DEPENDENCY_INPUTS = ("pyproject.toml", ".github/security-audit-requirements.txt")


def _dependency_diff_refs() -> tuple[str, str]:
    base_ref = os.environ.get("DEPENDENCY_DIFF_BASE", "").strip()
    head_ref = os.environ.get("DEPENDENCY_DIFF_HEAD", "").strip() or "HEAD"
    if base_ref and not set(base_ref) <= {"0"}:
        return base_ref, head_ref
    return "HEAD^", "HEAD"


def _dependency_inputs_changed() -> bool:
    base_ref, head_ref = _dependency_diff_refs()
    try:
        result = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                base_ref,
                head_ref,
                "--",
                *DEPENDENCY_INPUTS,
            ],
            check=True,
            cwd=REPO_ROOT,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        print(
            "Could not determine changed dependency inputs; checking requirements.",
            file=sys.stderr,
        )
        if exc.stderr:
            print(exc.stderr.strip(), file=sys.stderr)
        return True

    changed_inputs = [line for line in result.stdout.splitlines() if line]
    if not changed_inputs:
        print("Dependency audit inputs unchanged; sync check skipped.")
        return False

    print(f"Dependency audit inputs changed: {', '.join(changed_inputs)}")
    return True


def main() -> int:
    if not _dependency_inputs_changed():
        return 0

    generated_requirements = Path(os.environ["GENERATED_REQUIREMENTS"])
    generated_requirements.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "uv",
            "pip",
            "compile",
            "pyproject.toml",
            "--extra",
            "test",
            "--universal",
            "--upgrade",
            "--generate-hashes",
            "--quiet",
            "--no-header",
            "--output-file",
            str(generated_requirements),
        ],
        check=True,
        cwd=REPO_ROOT,
    )

    committed = COMMITTED_REQUIREMENTS.read_text(encoding="utf-8")
    generated = generated_requirements.read_text(encoding="utf-8")
    if committed == generated:
        return 0

    print(
        "Regenerate .github/security-audit-requirements.txt with the documented "
        "uv pip compile command.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
