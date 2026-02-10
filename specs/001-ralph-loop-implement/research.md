# Research: Ralph Loop Implementation Support

**Feature**: 001-ralph-loop-implement  
**Date**: 2026-01-18  
**Updated**: 2026-01-18 (Copilot CLI + Custom Agents research complete)

## Research Questions

### 1. GitHub Copilot CLI Capabilities

**Decision**: Use standalone `copilot` CLI with `-p` (prompt) flag and `--agent` for custom agent context

**Rationale**: 
- GitHub Copilot CLI is a standalone tool (`copilot`), NOT `gh copilot suggest`
- Supports non-interactive mode: `copilot -p "prompt" --allow-all-tools`
- Full code generation capabilities (not just shell suggestions)
- **Custom agent support via `--agent` flag** - ensures correct context for implementation
- Model selection via `--model` flag with multiple model choices

**Available Models** (via `--model` flag):
- `claude-sonnet-4.5` (default)
- `claude-haiku-4.5`
- `claude-opus-4.5`
- `claude-sonnet-4`
- `gpt-5.2-codex`, `gpt-5.1-codex`, `gpt-5.1-codex-max`, `gpt-5.1-codex-mini`
- `gpt-5.2`, `gpt-5.1`, `gpt-5`, `gpt-5-mini`
- `gpt-4.1`
- `gemini-3-pro-preview`

**Alternatives Considered**:
- `gh copilot suggest`: Rejected - only for shell command suggestions, not code generation
- VS Code extension API: Rejected - requires IDE, doesn't support headless operation
- Direct OpenAI API: Rejected - different model, different auth, not "Copilot"
- GitHub Models API: Possible future option but not the same as Copilot CLI experience

### 2. Custom Agents for Ralph Loop Context

**Decision**: Use `--agent speckit.implement` + iteration prompt via `-p` flag

**Rationale**:
- **Two-layer context**: Agent profile provides "how to implement" (TDD, phases, patterns), iteration prompt provides "scope and commit rules"
- `.github/agents/speckit.implement.agent.md` exists with full implementation workflow
- Iteration prompt (`templates/ralph-prompt.md`) adds:
  - One user story maximum per iteration (prevents context rot)
  - Commit boundary instructions (commit after completing each user story)
  - Progress logging format with iteration context
  - Feature-specific paths filled via placeholders

**Agent Discovery Locations** (in precedence order):
1. Repository-level: `.github/agents/*.agent.md` (our use case)
2. User-level: `~/.copilot/agents/*.agent.md`
3. Organization-level: `<org>/.github-private/agents/*.agent.md`

**Key Agent Profile Properties** (YAML frontmatter):
- `name`: Display name (optional, defaults to filename)
- `description`: **Required** - agent purpose and capabilities
- `tools`: List of tools available (`["read", "edit", "search", "shell"]` or `["*"]` for all)
- `model`: Preferred AI model (VS Code/IDE only, ignored in CLI)
- `target`: Environment (`vscode`, `github-copilot`, or both)
- `infer`: Allow auto-selection based on context (default: true)

**Command Pattern with Custom Agent + Iteration Prompt**:
```powershell
# Load iteration prompt with placeholders filled
$prompt = Get-Content "templates/ralph-prompt.md" -Raw
$prompt = $prompt -replace '{FEATURE_NAME}', $featureName
$prompt = $prompt -replace '{ITERATION_NUMBER}', $iteration
# ... fill other placeholders ...

# Invoke with agent profile + iteration-specific prompt
copilot --agent speckit.implement -p $prompt --model $model --allow-all-tools -s
```

**Alternatives Considered**:
- Embedding full context in `-p` flag only: Rejected - prompt too large, no reusable agent context
- Using agent profile only (no `-p`): Rejected - missing iteration-specific scope limits and commit rules
- Using AGENTS.md only: Rejected - general-purpose, doesn't have SDD workflow or commit boundaries

### 3. Loop Orchestration Pattern

**Decision**: Script-based loop (PowerShell/Bash) invoked by Python CLI

**Rationale**:
- Matches existing Spec Kit architecture (Python CLI → shell scripts)
- Shell scripts handle process management better than Python subprocess for long-running loops
- Cross-platform parity already established in project (parallel ps1/sh scripts)
- Signal handling (Ctrl+C) more natural in shell

**Alternatives Considered**:
- Pure Python loop with subprocess: Rejected - more complex signal handling, less consistent with existing patterns
- Python asyncio: Rejected - overkill for sequential iteration pattern
- Make/Task runners: Rejected - adds dependency, less portable

### 4. Copilot CLI Invocation Details

**Decision**: Use `--agent` + `-p` + `--allow-all-tools` for contextualized autonomous operation

**Key Command Pattern**:
```powershell
# RECOMMENDED: Use custom agent for proper SDD context
copilot --agent speckit.implement -p "Execute next task from tasks.md" --model claude-sonnet-4.5 --allow-all-tools -s

# Alternative: Full permissions mode
copilot --agent speckit.implement -p "Execute next task from tasks.md" --yolo -s
```

**Flags Used**:
- `--agent <name>`: Load custom agent profile (e.g., `speckit.implement` → `.github/agents/speckit.implement.agent.md`)
- `-p, --prompt <text>`: Execute prompt in non-interactive mode (exits after completion)
- `--model <model>`: Select AI model (see model list above)
- `--allow-all-tools`: Allow all tools without confirmation (required for non-interactive)
- `--allow-all-paths`: Disable path verification (allow access to any path)
- `--allow-all-urls`: Allow all URL access without confirmation
- `--allow-all` / `--yolo`: Enable all permissions (tools + paths + URLs)
- `-s, --silent`: Output only agent response (no stats), useful for scripting
- `--add-dir <directory>`: Add additional directories to allowed list
- `--no-custom-instructions`: Disable loading AGENTS.md and related files if needed

**Tool Permissions (granular control)**:
```powershell
# Allow specific tools
copilot --allow-tool 'write' --allow-tool 'shell(git:*)'

# Deny specific tools
copilot --deny-tool 'shell(rm)' --deny-tool 'shell(git push)'

# Allow all but deny dangerous commands
copilot --allow-all-tools --deny-tool 'shell(rm -rf)'
```

**Authentication**:
- Uses `GH_TOKEN` or `GITHUB_TOKEN` environment variable (in order of precedence)
- Or interactive `/login` command on first use
- Fine-grained PAT requires "Copilot Requests" permission

### 5. Task Completion Detection

**Decision**: Parse tasks.md for checkbox state changes between iterations

**Rationale**:
- tasks.md already uses markdown checkboxes (`- [ ]` / `- [x]`)
- Simple regex parsing: `\[x\]` vs `\[ \]`
- Agent naturally updates markdown as part of implementation
- Human-readable progress visible in git diffs

**Implementation**:
```powershell
# Count incomplete tasks
$incomplete = (Get-Content tasks.md | Select-String '\- \[ \]').Count
```

```bash
# Count incomplete tasks
incomplete=$(grep -c '\- \[ \]' tasks.md)
```

### 6. Completion Signal Detection

**Decision**: Detect `<promise>COMPLETE</promise>` token in agent stdout

**Rationale**:
- Proven pattern from reference Ralph implementation
- Unambiguous signal (unlikely to appear in normal output)
- Agent-controlled termination (knows when truly done)
- Simple grep/Select-String detection

**Implementation**:
```powershell
if ($output -match '<promise>COMPLETE</promise>') {
    Write-Host "Ralph completed all tasks!"
    exit 0
}
```

```bash
if echo "$OUTPUT" | grep -q '<promise>COMPLETE</promise>'; then
    echo "Ralph completed all tasks!"
    exit 0
fi
```

### 7. Progress File Format

**Decision**: Append-only markdown with structured sections per iteration

**Rationale**:
- Human-readable for debugging and review
- Markdown renders nicely in editors and GitHub
- Structured enough for agents to parse if needed
- Append-only prevents data loss on crashes

**Format**:
```markdown
# Ralph Progress Log

Started: 2026-01-18 10:30:00

---

## Iteration 1 - 2026-01-18 10:30:05
**Task**: T001 Create project structure
**Status**: ✅ Completed
**Files Changed**: 
- src/specify_cli/__init__.py
- scripts/powershell/ralph-loop.ps1
**Learnings**:
- Discovered existing pattern for CLI commands in __init__.py
---
```

### 8. Error Handling and Recovery

**Decision**: Log failures, increment iteration, continue to next task

**Rationale**:
- Transient failures shouldn't stop entire loop
- Progress file preserves state for resumption
- After 3 consecutive failures on same task, skip and warn
- User can manually fix and resume

**Implementation**:
- Track `$lastFailedTask` and `$failCount` variables
- Reset `$failCount` when different task is attempted
- Skip task when `$failCount >= 3`

## Technology Constraints

### GitHub Copilot CLI Considerations

1. **Requires active Copilot subscription**: Copilot Pro, Pro+, Business, or Enterprise
2. **Organization policy**: If via organization, CLI policy must be enabled in settings
3. **Windows requires PowerShell 6+**: PowerShell 5.1 experimental, prefer PS 6+
4. **Rate limits**: Unknown specific limits, may need throttling between iterations
5. **Trusted directories**: First use in a directory requires trust confirmation (can pre-trust via config)

**Mitigation**: 
- Pre-configure trusted directories in `~/.copilot/config.json`
- Use `GH_TOKEN` environment variable for headless authentication
- Add configurable delay parameter for rate limit handling

### Cross-Platform Considerations

1. **Path separators**: Use `Join-Path` (PS) / proper quoting (Bash)
2. **Signal handling**: Different Ctrl+C behavior; use trap (Bash) / try-finally (PS)
3. **Process spawning**: Different syntax for capturing output with exit codes
4. **Copilot CLI installation**: Different per platform (WinGet, Homebrew, npm)

## Dependencies

| Dependency | Purpose | Version | Notes |
|------------|---------|---------|-------|
| Python 3.11+ | CLI entry point | Existing | Already required by Specify CLI |
| Typer | CLI framework | Existing | Already in pyproject.toml |
| Rich | Terminal UI | Existing | Already in pyproject.toml |
| copilot | GitHub Copilot CLI | Latest | Standalone CLI, NOT `gh copilot` |
| PowerShell | Windows orchestration | 6.0+ | PS 5.1 experimental on Windows |
| Bash | Unix orchestration | 4.0+ | Standard on macOS/Linux |

**Installation Methods** (copilot CLI):
- **Windows**: `winget install GitHub.Copilot`
- **macOS/Linux**: `brew install copilot-cli`
- **All platforms**: `npm install -g @github/copilot` (requires Node.js 22+)
- **Direct download**: https://github.com/github/copilot-cli/releases/

## Open Questions Resolved

| Question | Resolution |
|----------|------------|
| How to invoke Copilot headlessly? | `copilot -p "prompt" --allow-all-tools -s` |
| How to select model? | `--model <model>` flag (e.g., `--model gpt-5.1`) |
| Where to store progress? | `specs/{feature}/progress.txt` alongside tasks.md |
| How to detect completion? | `<promise>COMPLETE</promise>` token in stdout |
| How to handle failures? | Log, continue, skip after 3 consecutive failures |
| Cross-platform script parity? | Parallel PowerShell and Bash implementations |

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| User lacks Copilot subscription | High | Low | Clear prerequisite documentation; error handling in CLI |
| Rate limiting on Copilot | Medium | Low | Add configurable delay between iterations |
| Agent fails to update tasks.md | Medium | Medium | Prompt template explicitly instructs checkbox updates |
| Complex tasks exceed context | High | Medium | User education on task sizing; warning in quickstart |
