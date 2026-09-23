"""Shared setup for integration scaffold command tests."""

from pathlib import Path


def integration_repo_root(tmp_path: Path) -> Path:
    root = tmp_path / "spec-kit"
    (root / "src" / "specify_cli" / "integrations").mkdir(parents=True)
    (root / "tests" / "integrations").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname = \"specify-cli\"\n", encoding="utf-8")
    (root / "src" / "specify_cli" / "__init__.py").write_text("", encoding="utf-8")
    (root / "src" / "specify_cli" / "integrations" / "__init__.py").write_text(
        "",
        encoding="utf-8",
    )
    return root
