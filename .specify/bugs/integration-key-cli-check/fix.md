# Bug Fix: Preserve Extension argument-hint in Claude SKILL frontmatter

- **Slug**: integration-key-cli-check
- **Fixed**: 2026-06-09T16:30:49Z
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

Updated extension skill generation to preserve the allowlisted `argument-hint` field from extension command frontmatter when creating SKILL.md files. Added regression tests to ensure `argument-hint` is retained while unknown frontmatter keys remain filtered out.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `src/specify_cli/agents.py` | modified | Extended `build_skill_frontmatter()` with optional `extra_frontmatter` input to support safe pass-through fields. |
| `src/specify_cli/extensions.py` | modified | In `_register_extension_skills()`, copied allowlisted `argument-hint` from parsed extension command frontmatter into generated skill frontmatter. |
| `tests/test_extensions.py` | modified | Added two `TestExtensionManager` regression tests for preserve/filter behavior in Claude + ai-skills extension installs. |

## Diff Highlights (optional)

```python
# src/specify_cli/extensions.py
extra_skill_frontmatter: Dict[str, Any] = {}
argument_hint = frontmatter.get("argument-hint")
if isinstance(argument_hint, str) and argument_hint.strip():
    extra_skill_frontmatter["argument-hint"] = argument_hint

frontmatter_data = registrar.build_skill_frontmatter(
    selected_ai,
    skill_name,
    description,
    f"extension:{manifest.id}",
    extra_frontmatter=extra_skill_frontmatter,
)
```

## Tests Added or Updated

- `tests/test_extensions.py::TestExtensionManager::test_install_claude_ai_skills_preserves_extension_argument_hint` — verifies extension `argument-hint` survives into generated Claude SKILL frontmatter.
- `tests/test_extensions.py::TestExtensionManager::test_install_claude_ai_skills_filters_unknown_frontmatter_keys` — verifies non-allowlisted keys are not copied.

## Local Verification

- Commands run:
  - `pytest tests/test_extensions.py::TestExtensionManager::test_install_claude_ai_skills_preserves_extension_argument_hint tests/test_extensions.py::TestExtensionManager::test_install_claude_ai_skills_filters_unknown_frontmatter_keys` → failed (`pytest` not in PATH)
  - `python -m pytest ...` → failed (`python` not in PATH)
  - `python3 -m pytest ...` → failed (`No module named pytest` in system Python)
  - `source .venv/bin/activate && python -m pytest tests/test_extensions.py::TestExtensionManager::test_install_claude_ai_skills_preserves_extension_argument_hint tests/test_extensions.py::TestExtensionManager::test_install_claude_ai_skills_filters_unknown_frontmatter_keys` → passed (2 passed)
- Manual checks: none

## Deviations from Assessment

None.

## Follow-ups

- Run the broader extension test subset (or full suite) in the same virtual environment before merge to confirm no cross-agent regressions.
