"""Contract checks for closed-vocabulary analysis guidance."""

from pathlib import Path


ANALYZE_TEMPLATE = Path(__file__).parent.parent / "templates" / "commands" / "analyze.md"


def test_analyze_checks_repeated_closed_vocabularies() -> None:
    content = ANALYZE_TEMPLATE.read_text(encoding="utf-8")

    assert "Closed-vocabulary inventory" in content
    assert "#### G. Closed Vocabulary Consistency" in content
    assert "symmetric difference" in content
    assert "explicitly identified subset" in content
    assert "Closed Vocabulary Mismatch Count" in content
