# Research: Customizable Branch Naming Templates

**Feature**: 001-custom-branch-templates  
**Date**: 2026-01-23

## Research Tasks

### 1. TOML Parsing in Bash

**Decision**: Use a simple line-by-line parser for the subset of TOML we need

**Rationale**:
- Settings file is simple (single `branch_template` key initially)
- No need for full TOML compliance (no arrays, nested tables, etc.)
- Bash doesn't have native TOML support
- External tools like `tomlq` are not universally installed
- A simple regex-based approach handles `key = "value"` patterns

**Alternatives Considered**:
- `tomlq` / `yq` - Requires additional installation, not portable
- `python -c` inline - Adds Python dependency to shell scripts
- JSON with `jq` - JSON lacks comments, poor for config files

**Implementation Approach**:
```bash
# Parse single key from TOML file
get_toml_value() {
    local file="$1" key="$2"
    grep -E "^${key}\s*=" "$file" 2>/dev/null | sed 's/.*=\s*"\([^"]*\)".*/\1/' | head -1
}
```

---

### 2. TOML Parsing in PowerShell

**Decision**: Use PowerShell's native text parsing with regex

**Rationale**:
- Same simple subset approach as Bash
- PowerShell has strong regex support built-in
- No external dependencies needed

**Implementation Approach**:
```powershell
function Get-TomlValue {
    param([string]$File, [string]$Key)
    $content = Get-Content $File -Raw -ErrorAction SilentlyContinue
    if ($content -match "$Key\s*=\s*`"([^`"]*)`"") { return $matches[1] }
    return $null
}
```

---

### 3. TOML Parsing in Python CLI

**Decision**: Use `tomllib` (stdlib in Python 3.11+)

**Rationale**:
- Spec Kit already requires Python 3.11+
- `tomllib` is part of standard library - no new dependency
- Full TOML compliance for future extensibility
- Already used pattern in Python ecosystem

**Alternatives Considered**:
- `tomli` - Only needed for Python 3.10 fallback (not our case)
- `configparser` - INI format, not TOML
- Manual parsing - Error-prone for a language with stdlib support

---

### 4. Git Username Resolution

**Decision**: Multi-level fallback chain

**Rationale**:
- Git config is the most common and expected source
- OS username provides reliable fallback
- Consistent behavior across platforms

**Resolution Order**:
1. `git config user.name` (normalized)
2. `$USER` (Unix) / `$env:USERNAME` (Windows)

**Normalization Rules** (per FR-005):
- Convert to lowercase
- Replace spaces with hyphens
- Remove characters not allowed in branch names: `~`, `^`, `:`, `?`, `*`, `[`, `\`
- Collapse multiple hyphens to single hyphen
- Trim leading/trailing hyphens

---

### 5. Per-User Number Scoping

**Decision**: Scan branches matching the resolved prefix pattern

**Rationale**:
- If template is `{username}/{number}-{short_name}`, scan only `johndoe/*` branches
- Each user gets their own independent sequence
- Simple to implement - just filter the branch list before finding max number

**Algorithm**:
1. Resolve template variables except `{number}` and `{short_name}`
2. Extract the prefix portion (everything before `{number}`)
3. Filter branches/specs matching that prefix pattern
4. Find highest number among filtered branches
5. Increment for new branch

**Example**:
- Template: `feature/{username}/{number}-{short_name}`
- Resolved prefix: `feature/johndoe/`
- Filter pattern: `feature/johndoe/[0-9]*`
- Matches: `feature/johndoe/001-login`, `feature/johndoe/002-settings`
- Next number: 003

---

### 6. Git Branch Name Validation

**Decision**: Validate against Git's documented rules

**Rationale**:
- Git rejects invalid branch names at checkout time
- Better UX to catch errors before attempting `git checkout -b`
- Rules are well-documented in `git-check-ref-format`

**Validation Rules** (per git-check-ref-format):
- Cannot start with `-`
- Cannot contain `..`
- Cannot contain `~`, `^`, `:`, `?`, `*`, `[`, `\`, or control chars
- Cannot end with `.lock`
- Cannot end with `/`
- Cannot contain `//`
- Cannot be empty
- Max length: 244 bytes (GitHub limit, already enforced)

---

### 7. Settings File Location

**Decision**: `.specify/settings.toml`

**Rationale**:
- Consistent with existing `.specify/` directory convention
- Keeps all Spec Kit configuration in one place
- TOML is already used by the project (`pyproject.toml`)
- `.toml` extension provides editor syntax highlighting

**Alternatives Considered**:
- `.specifyrc` - Less explicit about format
- `specify.config.json` - JSON lacks comments
- `~/.specify/settings.toml` - Global config complicates team sharing

---

## Summary

| Component | Decision | Dependency |
|-----------|----------|------------|
| Bash TOML parsing | Simple regex parser | None |
| PowerShell TOML parsing | Native regex | None |
| Python TOML parsing | `tomllib` (stdlib) | None (Python 3.11+) |
| Username resolution | Git config → OS username fallback | Git |
| Number scoping | Per-prefix branch filtering | Existing branch listing |
| Branch validation | Pre-validate against Git rules | None |
| Settings location | `.specify/settings.toml` | Existing `.specify/` directory |

All NEEDS CLARIFICATION items from Technical Context are now resolved.
