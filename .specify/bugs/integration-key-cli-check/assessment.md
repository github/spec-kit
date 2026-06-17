# Bug Assessment: Extension SKILL Frontmatter Drops argument-hint

- **Slug**: integration-key-cli-check
- **Created**: 2026-06-09T00:00:00Z
- **Source**: <https://github.com/github/spec-kit/issues/2903>
- **Verdict**: valid
- **Severity**: medium

## Report (verbatim or summarized)

URL trust policy record:

- URL: <https://github.com/github/spec-kit/issues/2903>
- Parsed host: github.com
- Policy branch: allowlisted

Issue summary (from #2903): extension-provided commands that include `argument-hint` in command frontmatter lose that field when `specify extension add` generates `.claude/skills/<name>/SKILL.md`. Core commands preserve `argument-hint` in generated Claude skills.

Expected: `argument-hint` (and ideally Claude flags) should be preserved for extension-generated skills the same way core skills are handled.

Actual: extension-generated skills keep only canonical skill keys (`name`, `description`, `compatibility`, `metadata`) before Claude post-processing, so `argument-hint` from extension command source is not carried through.

## Symptom

When installing an extension in a Claude + ai-skills project, the generated `SKILL.md` for extension commands does not include source frontmatter key `argument-hint`, while equivalent core command skills do include it.

## Reproduction

1. Configure project init options with Claude skill mode (`ai=claude`, `ai_skills=true`).
2. Create extension command markdown with frontmatter containing `description` and `argument-hint`.
3. Add extension via `specify extension add --dev <extension-dir>`.
4. Inspect generated `.claude/skills/speckit-<extension>-<command>/SKILL.md`.
5. Observe `argument-hint` is missing from generated frontmatter.

## Suspected Code Paths

- `src/specify_cli/extensions.py:839` — `_register_extension_skills()` is the extension-specific skill generation path used during `extension add` when ai-skills is enabled.
- `src/specify_cli/extensions.py:934` — extension skill frontmatter is rebuilt via `registrar.build_skill_frontmatter(...)`, which constructs a minimal canonical frontmatter and drops extra source keys.
- `src/specify_cli/agents.py:303` — `build_skill_frontmatter()` only returns `name`, `description`, `compatibility`, and `metadata`; it has no pass-through for `argument-hint` or Claude-specific flags.
- `src/specify_cli/integrations/claude/__init__.py:25` — `ARGUMENT_HINTS` map only covers bundled command stems; extension stems are not represented.
- `src/specify_cli/integrations/claude/__init__.py:230` — hint injection reads from `ARGUMENT_HINTS.get(stem)`, so extension-generated skill names receive no injected `argument-hint`.

## Root Cause Hypothesis

The extension installation path uses a different SKILL frontmatter construction flow than core command generation. Specifically, `_register_extension_skills()` rebuilds frontmatter from a fixed canonical schema and does not preserve source command frontmatter keys like `argument-hint`. Claude post-processing then injects hints only from a static map of built-in command stems, so extension commands have no second chance for hint propagation. Confidence: high.

## Proposed Remediation

**Preferred**: Make extension skill generation preserve a safe allowlist of source frontmatter keys when building SKILL frontmatter, including at minimum `argument-hint` (and optionally `user-invocable` / `disable-model-invocation` for parity). Implement this in one shared place to avoid drift:

- Option A: extend `CommandRegistrar.build_skill_frontmatter()` to accept optional `extra_fields` and merge allowed keys.
- Option B: in `_register_extension_skills()`, merge allowed keys from parsed source frontmatter into `frontmatter_data` before dump, then let integration post-processing run.

This keeps canonical required keys while preserving explicit author intent from extension command metadata.

**Alternatives** (optional):

- Teach `ClaudeIntegration.post_process_skill_content()` to derive `argument-hint` from skill body or source metadata. Trade-off: brittle and Claude-specific, does not solve cross-agent parity.
- Expand hardcoded `ARGUMENT_HINTS` dynamically for installed extension commands. Trade-off: operational complexity and still ignores non-Claude metadata.

**Files likely to change**:

- `src/specify_cli/extensions.py`
- `src/specify_cli/agents.py`
- `src/specify_cli/integrations/claude/__init__.py` (only if fallback behavior is added)
- `tests/test_extensions.py`

**Tests to add or update**:

- Add extension install test asserting extension command `argument-hint` is present in generated `.claude/skills/.../SKILL.md` when ai-skills is enabled.
- Add negative/control test confirming unknown frontmatter keys are still filtered if not in allowlist.
- Add parity test for `user-invocable` and `disable-model-invocation` behavior for extension skills (if adopted).

## Risks & Considerations

- Over-preserving frontmatter keys could leak unsupported metadata into skill files if allowlist boundaries are unclear.
- Changing shared skill-frontmatter logic may affect all SKILL agents; parity expectations across integrations should be validated.
- Existing tests currently emphasize canonical skill fields and may need updates to reflect intentional pass-through behavior.

## Open Questions

- [NEEDS CLARIFICATION: Should pass-through apply only to `argument-hint`, or also include `user-invocable` and `disable-model-invocation` for full parity?]
- [NEEDS CLARIFICATION: Should pass-through behavior apply to all SKILL agents, or remain Claude-specific?]
- [NEEDS CLARIFICATION: Is allowlist policy documented for extension command frontmatter fields beyond `description`?]
