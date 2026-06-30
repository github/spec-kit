from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "community"))

from validate_integration import Validation, validate_pr_body  # noqa: E402


def _write_body(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "pr-body.md"
    path.write_text(body, encoding="utf-8")
    return path


def _base_body(*, route: str, extra: str = "") -> str:
    return f"""
## Community Catalog Submission

- Submission route: {route}
- Catalog type: extension
- Source repository: https://github.com/example/spec-kit-example
- Source version: v1.2.3
- Source commit: 0123456789abcdef0123456789abcdef01234567
- Download URL: https://github.com/example/spec-kit-example/archive/refs/tags/v1.2.3.zip
- Related issue: n/a
{extra}
"""


def test_direct_pr_template_requires_maintainer_approval(tmp_path: Path) -> None:
    validation = Validation()
    body_path = _write_body(tmp_path, _base_body(route="pr-template"))

    validate_pr_body(body_path, "community/example-extension", validation)

    assert any("Maintainer direct PR approval" in error for error in validation.errors)


def test_direct_pr_template_accepts_maintainer_approval(tmp_path: Path) -> None:
    validation = Validation()
    body_path = _write_body(
        tmp_path,
        _base_body(
            route="pr-template",
            extra="- Maintainer direct PR approval: https://github.com/github/spec-kit/issues/123#issuecomment-456",
        ),
    )

    validate_pr_body(body_path, "community/example-extension", validation)

    assert validation.errors == []


def test_issue_template_route_requires_closing_issue(tmp_path: Path) -> None:
    validation = Validation()
    body_path = _write_body(
        tmp_path,
        """
## Community Catalog Submission

- Submission route: issue-template
- Catalog type: preset
- Source repository: n/a
- Source version: n/a
- Source commit: n/a
- Download URL: n/a
- Related issue: Closes #123
""",
    )

    validate_pr_body(body_path, "community/123-example-preset", validation)

    assert validation.errors == []
