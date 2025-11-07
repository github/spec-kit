# AI Doc: [FEATURE NAME]

**Branch**: `[###-feature-name]` | **Updated**: [DATE] | **Status**: [Draft/Complete]
**Related**: [spec.md](./spec.md) · [plan.md](./plan.md) · [tasks.md](./tasks.md)

> **Purpose**: Token-optimized documentation for AI/LLM context. Focuses on actual implementation, not plans.

## Overview

**What**: [One sentence describing what this feature does]

**Key capabilities**:
- [Capability 1]
- [Capability 2]
- [Capability 3]

## Code Map

### Implementation Files

```
path/to/file1.ext          - Purpose
path/to/file2.ext          - Purpose
path/to/file3.ext          - Purpose
tests/test_file.ext        - Tests what
```

### Entry Points

- `file.ext:123` - `functionName()` - Triggered when [condition]
- `file.ext:456` - `className.method()` - Handles [what]

### Public APIs

- `function/class @ file:line` - Purpose, params, return

## Architecture

### Component Map

```
[Component A] → [Component B] → [Component C]
     ↓              ↓
[Component D]   [Component E]
```

### Responsibilities

| Component | Location | Purpose | Depends On |
|-----------|----------|---------|------------|
| CompA | file:line | Does X | CompB, lib1 |
| CompB | file:line | Does Y | lib2 |

## Data Flow

**Primary flow**:
1. Input: [source] → [format]
2. Process: `ComponentA.method()` transforms to [format]
3. Process: `ComponentB.method()` validates/enriches
4. Output: [destination] → [format]

**State**: [Where stored] - [Key elements]

## Key Components

### Component1 @ file:line

**Purpose**: [What it does]
**Key methods**: `method1()`, `method2()`, `method3()`
**Deps**: lib1, lib2
**Pattern**: [Why implemented this way]

### Component2 @ file:line

**Purpose**: [What it does]
**Key methods**: `method1()`, `method2()`
**Deps**: Component1, lib3

## Integration Points

**External deps**:
- `library@version` - Used for [purpose]
- `library2@version` - Used for [purpose]

**Storage** (if applicable):
- Type: [DB/file/memory]
- Schema: `table1(field1, field2)`, `table2(field1, field2)`

**APIs** (if applicable):
- `POST /endpoint` - Purpose
- `GET /endpoint` - Purpose

## Testing

**Run tests**: `command here`

**Test files**:
- `test_file.ext` - Covers [what]

**Coverage**: [X%] | **Gaps**: [What's not tested]

**Critical setup**: [Only if non-obvious]

## Modification Guide

**Add [feature/capability]**:
1. Modify `file:line` - [what to change]
2. Add test in `test_file:line`
3. Update [related file]

**Change [behavior]**:
1. Config at `file:line`
2. Impact: [what else changes]

**Common patterns**:
- **Pattern1**: Used when [scenario] - See `file:line`
- **Pattern2**: Used when [scenario] - See `file:line`

## Gotchas

**[Non-obvious behavior 1]**:
- What: [Description]
- Why: [Reason]
- Where: `file:line`
- Impact: [What breaks if you don't know this]

**[Edge case 1]**:
- Scenario: [When]
- Behavior: [What happens]
- Location: `file:line`

**Performance**:
- Bottleneck: [Operation] at `file:line` - [Why/mitigation]

**Security/Privacy** (if applicable):
- [Concern]: [How handled] - `file:line`

## AI Guidance

**Before modifying**:
- [ ] Read [specific file/section]
- [ ] Understand [key concept]
- [ ] Check [dependency/integration]

**Must preserve**:
- [Invariant 1]: [Why critical]
- [Invariant 2]: [Why critical]

**Safe to change**:
- [What can be modified without breaking things]

**Common issues**:

| Symptom | Cause | Fix | Location |
|---------|-------|-----|----------|
| [Issue 1] | [Root cause] | [Solution] | file:line |
| [Issue 2] | [Root cause] | [Solution] | file:line |

## Appendix

**Config files**: `file1`, `file2` - [Key settings]
**Env vars**: `VAR1=value` - [Purpose]
**Dependencies docs**: [link1], [link2] - [When needed]

---

**Last analyzed**: [DATE] | **Implementation status**: [Complete/Partial]
