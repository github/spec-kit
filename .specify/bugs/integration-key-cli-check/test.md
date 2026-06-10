# Bug Verification: Extension argument-hint preserved in generated Claude skills

- **Slug**: integration-key-cli-check
- **Tested**: 2026-06-09T16:32:56Z
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

The post-fix reproduction-equivalent check passes: generated Claude extension `SKILL.md` frontmatter now retains `argument-hint`. New guardrail coverage and related skill-generation regression tests also pass, with no functional regressions observed in the executed scope.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reproduction (post-fix) | `source .venv/bin/activate && python -m pytest tests/test_extensions.py::TestExtensionManager::test_install_claude_ai_skills_preserves_extension_argument_hint -q` | pass | Reproduces the bug scenario via extension install path and asserts `argument-hint` exists post-fix. |
| New / updated tests | `source .venv/bin/activate && python -m pytest tests/test_extensions.py::TestExtensionManager::test_install_claude_ai_skills_filters_unknown_frontmatter_keys -q` | pass | Confirms unknown keys are still filtered while allowlisted metadata is preserved. |
| Regression suite | `source .venv/bin/activate && python -m pytest tests/test_extensions.py::TestCommandRegistrar::test_all_skill_agents_register_commands_with_resolved_placeholders tests/test_extensions.py::TestCommandRegistrar::test_command_with_aliases tests/test_extensions.py::TestCommandRegistrar::test_codex_skill_registration_writes_skill_frontmatter -q` | pass | Broader related skill-generation paths remain green (`8 passed`). |
| Lint / type-check | `source .venv/bin/activate && python -m ruff check src/specify_cli/agents.py src/specify_cli/extensions.py tests/test_extensions.py` | skipped | `ruff` is not installed in the current virtual environment (`No module named ruff`). |

## Output Excerpts

```text
tests/test_extensions.py .                                               [100%]
============================== 1 passed in 0.34s ===============================
```

```text
tests/test_extensions.py .                                               [100%]
============================== 1 passed in 0.28s ===============================
```

```text
tests/test_extensions.py ........                                        [100%]
============================== 8 passed in 0.58s ===============================
```

```text
/Users/benbtg/Developer/01-Projects/03-SpecKit/spec-kit/.venv/bin/python: No module named ruff
```

## Residual Risks

- Lint/static-style validation was not executed because `ruff` is unavailable in the current environment.
- Verification focused on unit/integration checks in `tests/test_extensions.py`; full-project regression was not run in this pass.

## Recommendation

Close the bug — verified end-to-end for the reported symptom in the extension install + Claude skills path, with additional guardrail and related regression checks passing. Optionally run the full repository test and lint suite in CI for broader confidence before release.
