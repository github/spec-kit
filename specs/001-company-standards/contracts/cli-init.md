# CLI Contract: Specify Init

## Command: `specify init`

### Updated Behavior for Agent Context

**Pre-condition**: User runs `specify init` (with or without `--ai`).

**Logic**:
1.  **Generate `AGENTS.md`**:
    -   Source: `templates/agent-file-template.md`.
    -   Location: `./AGENTS.md` (Project Root).
    -   Content: Populated with project info.

2.  **Handle Specific Agent Requirements**:
    -   **Cursor**:
        -   Create `.cursor/rules/specify-rules.mdc`.
        -   Content: Reference to `AGENTS.md`.
    -   **Windsurf**:
        -   Create `.windsurf/rules/specify-rules.md`.
        -   Content: Reference to `AGENTS.md`.
    -   **Others (Claude, Gemini, etc.)**:
        -   Do NOT create `CLAUDE.md` / `GEMINI.md`.
        -   Assume agent reads `AGENTS.md` from root.

**Post-condition**:
-   `AGENTS.md` exists.
-   Agent-specific pointer files exist (if applicable).
-   Legacy files (`CLAUDE.md`, etc.) are NOT created for new projects.
