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

from pathlib import Path

WORKFLOWS = Path(__file__).parent.parent / ".github" / "workflows"
BUG_FIX_MD = WORKFLOWS / "bug-fix.md"
BUG_FIX_LOCK = WORKFLOWS / "bug-fix.lock.yml"


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
    """The compiled harness invocation must allow both python and python3."""
    lock = BUG_FIX_LOCK.read_text(encoding="utf-8")
    assert "shell(python)" in lock
    assert "shell(python3)" in lock
    assert "shell(pytest)" in lock


def test_markdown_steers_pytest_off_venv_interpreter() -> None:
    """Prompt guidance is runtime-imported from the Markdown, so assert it there."""
    md = BUG_FIX_MD.read_text(encoding="utf-8")
    lock = BUG_FIX_LOCK.read_text(encoding="utf-8")
    assert "python3 -m pytest" in md
    assert ".venv/bin/python" in md
    assert "Permission denied" in md
    # The lock imports the Markdown body at runtime rather than embedding it,
    # which is why the guidance above governs the live prompt.
    assert "{{#runtime-import .github/workflows/bug-fix.md}}" in lock


def test_markdown_frontmatter_matches_compiled_lock() -> None:
    """Source frontmatter and compiled lock must agree (no stale lock)."""
    md = BUG_FIX_MD.read_text(encoding="utf-8")
    assert "max-ai-credits: 2000" in md
    assert '"python", "python3"' in md
