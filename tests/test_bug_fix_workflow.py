"""Pin bug-fix workflow credits and pytest PATH rules (#4472)."""

from pathlib import Path

BUG_FIX = Path(__file__).parent.parent / ".github" / "workflows" / "bug-fix.md"


def test_bug_fix_workflow_has_credit_headroom_and_pytest_path() -> None:
    text = BUG_FIX.read_text(encoding="utf-8")
    assert "max-ai-credits: 2000" in text
    assert '"python"' in text or "python3" in text
    # Allowlist must include both python and python3 (harness argv[0] matching).
    assert "python3" in text
    assert '"python"' in text or ", \"python\"" in text or '["python"' in text or '"python",' in text
    assert ".venv/bin/python" in text
    assert "Permission denied" in text
