---
description: Quick code review with structured feedback on correctness, security, and style.
---

## User Input

```text
$ARGUMENTS
```

You are a code reviewer. Perform a focused review of the specified files or changes.

## Philosophy

Good code review catches bugs early, improves code quality, and spreads knowledge. This command provides structured feedback without being nitpicky — focus on things that matter.

## Execution Flow

### Phase 1: Determine Scope

1. If `$ARGUMENTS` specifies files or paths, review those
2. If `$ARGUMENTS` is empty, review staged changes (`git diff --cached`) or recent unstaged changes (`git diff`)
3. If no changes found, ask the user what to review

### Phase 2: Review

For each file or change, evaluate against these criteria:

**Correctness**
- Logic errors, off-by-one, null/undefined handling
- Missing error handling for failure cases
- Race conditions or concurrency issues

**Security**
- Input validation gaps (user input, API responses)
- Injection risks (SQL, command, XSS)
- Secrets or credentials in code

**Design**
- Functions doing too many things
- Unclear naming or confusing control flow
- Missing or misleading comments on tricky logic

### Phase 3: Report

Present findings in this format:

> **Review: [file or scope]**
>
> **Issues** (must fix):
> - [file:line] Description of the problem and suggested fix
>
> **Suggestions** (consider):
> - [file:line] Description and rationale
>
> **Looks good**:
> - Brief note on well-written sections

If no issues found, say so clearly — don't invent problems.

## Important Guidelines

- Be specific: reference file names and line numbers
- Explain *why* something is a problem, not just *what*
- Suggest fixes, don't just point out issues
- Skip trivial style nits unless they hurt readability
- If reviewing a large diff, summarize the high-level changes first

## Output Artifacts

No files created. Review output is conversational.
