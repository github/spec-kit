# Research: Company Standards & AGENTS.md Unification

## Decisions

### 1. Template Structure for Company Standards
**Decision**: Implement the company standards templates in `templates/company-standards/` with the following structure:
```
templates/company-standards/
├── constitution-template.md
├── code-style/
│   ├── javascript.md
│   ├── python.md
│   ├── java.md
│   └── go.md
├── security-checklist.md
├── review-guidelines.md
└── incident-response.md
```
**Rationale**: This structure maps directly to the user stories and requirements. Grouping code styles keeps the root cleaner.
**Alternatives Considered**: Flat structure (all files in `company-standards/`). Rejected because adding more languages would clutter the folder.

### 2. AGENTS.md Standardization in CLI
**Decision**: Modify `src/specify_cli/__init__.py` to:
1.  Always generate `AGENTS.md` in the project root during `init`.
2.  For agents that require specific file paths (e.g., Cursor, Windsurf), generate a "pointer" file that references `AGENTS.md`.
3.  For agents that can look at root (e.g., Claude), rely on `AGENTS.md`.
**Rationale**: Centralizes context to a single file (`AGENTS.md`), reducing maintenance and "context drift" between different agents.
**Alternatives Considered**: Keep separate files but sync them. Rejected because synchronization is error-prone and hard to implement reliably without a complex watcher.

### 3. Update Scripts Logic
**Decision**: Modify `scripts/bash/update-agent-context.sh` and `scripts/powershell/update-agent-context.ps1` to:
1.  Detect if `AGENTS.md` exists.
2.  If it exists, append context updates there.
3.  If not (legacy projects), fall back to existing behavior (updating specific files) or warn.
**Rationale**: Ensures backward compatibility while promoting the new standard.

### 4. Template Source for AGENTS.md
**Decision**: Use `templates/agent-file-template.md` as the source for `AGENTS.md`.
**Rationale**: Reuse existing template logic.

## Unknowns Resolved
- **Language/Version**: Python 3.10+ (for CLI), Bash/PowerShell (for scripts), Markdown (for templates).
- **Dependencies**: `typer`, `rich` (existing CLI deps). No new external deps.
- **Testing**: `pytest` for CLI logic. Manual verification for generated templates.
