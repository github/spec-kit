"""Guard the bug-fix workflow's credit cap and pytest PATH rules (#4472).

The workflow's ``max-ai-credits`` and ``tools.bash`` frontmatter is baked into
the *compiled* lock file (``bug-fix.lock.yml``) at compile time, so those
settings only take effect once the lock is regenerated with ``gh aw compile`` --
editing ``bug-fix.md`` alone leaves the running workflow unchanged. These tests
therefore assert the compiled lock (the artifact GitHub Actions actually runs)
for the credit cap and the shell allowlist.

The prompt guidance in the Markdown body is not embedded in the lock; the lock
imports it at runtime via ``{{#runtime-import .github/workflows/bug-fix.md}}``,
so that guidance is asserted against the Markdown source.
"""

import re
from pathlib import Path

WORKFLOWS = Path(__file__).parent.parent / ".github" / "workflows"
BUG_FIX_MD = WORKFLOWS / "bug-fix.md"
BUG_FIX_LOCK = WORKFLOWS / "bug-fix.lock.yml"


def _harness_command(lock: str) -> str:
    """Return the executable Copilot harness command line from the compiled lock.

    The agent job runs the harness via ``-- /bin/bash -c '<cmd>'``, and that
    command line is the only one referencing ``copilot_harness.cjs``. Isolating
    it lets assertions target the real ``--allow-tool`` arguments instead of the
    commented tool inventory the lock also emits (e.g. ``# --allow-tool
    shell(python)``), which would otherwise mask a dropped argument.
    """
    lines = [ln for ln in lock.splitlines() if "copilot_harness.cjs" in ln]
    assert len(lines) == 1, f"expected one harness command line, found {len(lines)}"
    return lines[0]


def _allow_tool(tool: str) -> str:
    """The executable ``--allow-tool shell(<tool>)`` argument as it appears in the lock.

    The harness args are nested inside ``bash -c '...'``, so each surrounding
    single quote is shell-escaped as ``'\\''`` in the generated command.
    """
    q = "'\\''"
    return f"--allow-tool {q}shell({tool}){q}"


def test_compiled_lock_pins_raised_credit_cap() -> None:
    """The compiled artifact must carry the 2000 cap, not the 1000 default."""
    lock = BUG_FIX_LOCK.read_text(encoding="utf-8")
    # Agent job inlines the literal cap into the firewall api-proxy config.
    assert '"maxAiCredits":2000' in lock
    # Summary job env carries the same literal cap.
    assert 'GH_AW_MAX_AI_CREDITS: "2000"' in lock
    # The agent/summary jobs must no longer fall back to the 1000 default.
    assert "GH_AW_DEFAULT_MAX_AI_CREDITS || '1000'" not in lock


def test_compiled_lock_allows_python_and_python3() -> None:
    """The executable harness invocation must allow python, python3 and pytest.

    Bare ``shell(python)`` substrings also appear in the lock's commented tool
    inventory, so asserting them against the whole file would still pass if
    compilation dropped the real ``--allow-tool`` arguments. Assert the full
    executable arguments on the harness command line so the permission-denied
    regression is actually guarded.
    """
    harness = _harness_command(BUG_FIX_LOCK.read_text(encoding="utf-8"))
    assert _allow_tool("python") in harness
    assert _allow_tool("python3") in harness
    assert _allow_tool("pytest") in harness


def test_markdown_steers_pytest_off_venv_interpreter() -> None:
    """Prompt guidance is runtime-imported from the Markdown, so assert it there.

    Checking ``python3 -m pytest``, ``.venv/bin/python`` and ``Permission
    denied`` as separate substrings would also pass wording that *recommends* the
    project interpreter. Assert the normalized prohibition as a single contiguous
    unit so the test fails if the guidance is reversed or the permission-denied
    explanation is split away from it.
    """
    md = BUG_FIX_MD.read_text(encoding="utf-8")
    normalized = re.sub(r"\s+", " ", md)
    prohibition = (
        "Do not invoke `.venv/bin/python`, `venv/bin/python`, or any "
        "project-local interpreter: the harness cannot grant execute permission "
        'on those binaries and fails with "Permission denied".'
    )
    assert prohibition in normalized
    # PATH-based invocation must remain the recommended path.
    assert "Prefer `python3 -m pytest` or `pytest` from PATH." in normalized
    # The lock imports the Markdown body at runtime rather than embedding it,
    # which is why the guidance above governs the live prompt.
    lock = BUG_FIX_LOCK.read_text(encoding="utf-8")
    assert "{{#runtime-import .github/workflows/bug-fix.md}}" in lock


def test_markdown_frontmatter_matches_compiled_lock() -> None:
    """Source frontmatter and compiled lock must agree (no stale lock)."""
    md = BUG_FIX_MD.read_text(encoding="utf-8")
    assert "max-ai-credits: 2000" in md
    assert '"python", "python3"' in md
