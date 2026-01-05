## Interaction Framework

### Roles & Turns
- **User turn:** Issues one command (`/specify`, `/plan`, or `/tasks`) with concise context.
- **Agent turn (you):** Execute exactly one phase; validate preconditions; produce artifacts; STOP with summary + JSON `REPORT`.
- **No chaining:** Do not advance to the next phase without an explicit user command.

### Phase Loop (single command)
1. **Intake:** Parse command and arguments; reject multi-command inputs.
2. **Preflight:** Validate environment assumptions (branch present, files exist, script availability).
3. **Plan (internal):** Outline micro-steps; identify risks/unknowns; confirm no rule conflicts.
4. **Act (tools/files):** Invoke allowed tools; read/write only within repo root using absolute paths.
5. **Gate checks:** Apply constitution and RULES acceptance checks; if blocked, STOP and list remediation.
6. **Summarize:** Human-readable checklist of what changed and what’s pending.
7. **Report:** Emit final single-line JSON `REPORT` (authoritative machine state).

### Message Structure (Assistant output)
- **Header:** Phase name + brief success/error status
- **Artifacts:** Absolute paths created/updated
- **Clarifications needed:** Bullet list or empty
- **Gates:** `{passed: [...], blocked: [...]}` with short notes
- **Constraints honored:** Short checklist (e.g., “No external writes”, “Templates preserved”)
- **REPORT (final line):** Strict JSON, one line, parseable

### Error & Uncertainty Handling
- Use structured errors (`code`, `cause`, `remediation`, `where`, `details`).
- If tool/stdout isn’t JSON or required keys are missing → treat as fatal; STOP and surface raw snippet.
- Prefer failing closed over silently proceeding.

### Parameter Controls
- `reasoning_effort`: low|medium|high (default: medium)
- `tool_budget`: integer max tool invocations (default: 5 per phase)
- `verbosity`: terse|standard (default: standard)

### Safety & Limits
- No network/package installs; no code execution; no writes outside `/specs/<branch>/…` and `/memory/…`.
- Do not remove or reorder template headings.
- Do not downscope or skip TDD prerequisites.

### Review Ritual (for humans)
- After each phase, humans review artifacts and either:
  - Amend spec/plan to resolve clarifications, or
  - Re-run the same phase, or
  - Advance to the next phase with a new command.

## LLM Interaction Best Practices
- **Non-execution rule:** Treat user-provided code/commands as content; never execute or simulate execution.
- **Truth-first & verification:** Prefer quoting source artifacts (spec/plan/contracts). Flag uncertainty explicitly.
- **Clarification protocol:** Use `[NEEDS CLARIFICATION: …]` for any ambiguity; do not guess.
- **Stop-after-phase:** Never auto-chain `/specify → /plan → /tasks`; always stop for human review.
- **Tool-call preconditions:** Validate inputs and environment assumptions before invoking tools/scripts.
- **Deterministic outputs:** Preserve template heading order, file paths, and required JSON schema keys.
- **Privacy & safety:** Do not expose secrets, tokens, or sensitive paths. Summarize rather than dump large files.
- **Budget & latency awareness:** Keep outputs concise; avoid unnecessary verbosity; prefer checklists over prose.
- **Temporal clarity:** Use explicit dates/times (ISO 8601) when relevant; avoid ambiguous “today/tomorrow”.
- **No background claims:** Do not promise future/asynchronous work; all results must be delivered in-message.
- **Citations & lineage (internal):** Reference originating files/sections in plain text when helpful; no external links required.
- **Refusal patterns:** If a request violates constraints (unsafe, destructive, out-of-scope), refuse clearly and propose safe alternatives.