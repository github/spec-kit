---
description: Scan Python code for defensive programming gaps before PRs. Checks for missing None/type validation, shallow vs deep copy issues, error message accuracy, and parity between extension/preset systems.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). User can specify files or scope to review.

## Goal

Identify missing defensive programming checks that could lead to runtime errors, data corruption, or inconsistent behavior. This is especially important before creating PRs to catch issues that reviewers commonly flag.

## Operating Constraints

**READ-ONLY ANALYSIS**: Do **not** modify any files. Output a structured report with specific fix suggestions.

**Parity Enforcement**: The extension system (`extensions.py`) and preset system (`presets.py`) MUST have equivalent defensive patterns. Asymmetry is always an issue.

## Review Scope

Default behavior:
1. If there are staged changes: review `git diff --cached`
2. If no staged changes: review `git diff`
3. If user specifies files: review those files

For parity checks, always examine both `extensions.py` and `presets.py` when either is modified.

## Defensive Programming Checklist

### 1. Input Validation

| Pattern | Bad | Good |
|---------|-----|------|
| None check | `data["key"]` | `if data is None: raise` |
| Type check | `data.get("x")` on unknown | `if not isinstance(data, dict): raise` |
| Empty check | error says "non-empty" but accepts `{}` | error message matches actual validation |

### 2. Data Integrity

| Pattern | Bad | Good |
|---------|-----|------|
| Return mutable | `return self.data[id]` | `return copy.deepcopy(self.data[id])` |
| Store mutable | `self.data[id] = dict(input)` | `self.data[id] = copy.deepcopy(input)` |
| List return | `return self.data` | `return copy.deepcopy(self.data)` |

### 3. Error Handling

| Pattern | Bad | Good |
|---------|-----|------|
| Silent failure | `pass` on exception | Log or re-raise with context |
| Missing Raises | No docstring for exceptions | Document all raised exceptions |
| Corrupted state | Assume dict structure | Check `isinstance()` before access |

### 4. Code Parity (Extension/Preset)

Methods that MUST match between `ExtensionRegistry` and `PresetRegistry`:
- `get()` - both must return deep copy
- `list()` - both must return deep copy
- `update()` - both must preserve `installed_at`
- `restore()` - both must validate input and use deep copy
- `list_by_priority()` - both must handle corrupted entries

CLI commands that MUST match:
- `extension enable/disable` ↔ `preset enable/disable`
- `extension set-priority` ↔ `preset set-priority`
- Error messages, validation patterns, exit codes

## Execution Steps

### 1. Determine Review Scope

```bash
# Check for staged changes
git diff --cached --name-only

# If empty, check unstaged
git diff --name-only
```

### 2. Identify Files to Review

Filter for Python files in:
- `src/specify_cli/presets.py`
- `src/specify_cli/extensions.py`
- `src/specify_cli/__init__.py` (CLI commands)
- `tests/test_presets.py`
- `tests/test_extensions.py`

### 3. Run Detection Passes

#### A. Input Validation Pass
Scan for functions that:
- Accept `dict`, `list`, or `Optional` parameters
- Access dict keys without None/type checks
- Have error messages that don't match validation logic

#### B. Data Integrity Pass
Scan for methods that:
- Return internal data structures without deep copy
- Store input data with shallow copy (`dict()` instead of `deepcopy()`)
- Expose mutable state

#### C. Parity Pass
When `presets.py` or `extensions.py` is in scope:
1. List all methods in changed file
2. Find equivalent methods in the other file
3. Compare defensive patterns
4. Flag asymmetries

#### D. Test Coverage Pass
For each defensive check added:
- Verify corresponding test exists
- Check edge cases (None, wrong type, empty, corrupted)

### 4. Severity Assignment

- **CRITICAL**: Missing check that will cause crash or data corruption
- **IMPORTANT**: Missing parity, inconsistent error messages, missing deep copy
- **SUGGESTION**: Could be more defensive but unlikely to cause issues

## Output Format

## Defensive Programming Review

### Summary
- Files reviewed: N
- Issues found: N (X critical, Y important, Z suggestions)

### Critical Issues

| Location | Issue | Fix |
|----------|-------|-----|
| presets.py:320 | `restore()` uses shallow copy | Use `copy.deepcopy(metadata)` |

### Important Issues

| Location | Issue | Fix |
|----------|-------|-----|
| presets.py:320 | Error says "non-empty" but accepts `{}` | Change to "must be a dict" |

### Parity Issues

| Extension Location | Preset Location | Issue |
|--------------------|-----------------|-------|
| extensions.py:300 | presets.py:320 | Extension has validation, preset missing |

### Suggestions

(Lower priority improvements)

### Test Coverage

| Defensive Check | Test Exists? | Test Location |
|-----------------|--------------|---------------|
| restore() rejects None | Yes | test_presets.py:392 |

## Next Actions

Based on findings, suggest:
1. Specific code changes with line numbers
2. Tests to add
3. Files to check for parity
