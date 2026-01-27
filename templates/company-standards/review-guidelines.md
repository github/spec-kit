# Code Review Guidelines

## Goals

- Ensure code correctness and quality.
- Share knowledge across the team.
- Maintain consistency in style and architecture.

## Pull Request Standards

- **Size**: Keep PRs small (< 400 lines). Break large changes into smaller, logical commits.
- **Description**: clearly state WHAT changed, WHY it changed, and HOW to test it.
- **CI**: All automated tests must pass before requesting review.

## Reviewer Responsibilities

- **Turnaround**: Aim to review within 24 hours.
- **Tone**: Be constructive and respectful. Critique the code, not the author.
- **Scope**: Focus on logic, architecture, and security. Let linters handle style.

## Severity Levels

- **[BLOCKER]**: Major bug, security vulnerability, or build break. Must be fixed.
- **[MAJOR]**: Logic error, performance issue, or tech debt. Should be fixed.
- **[MINOR]**: Cleanliness, minor refactor, or clarification. Optional but recommended.
- **[NIT]**: Personal preference or very minor polish. Can be ignored.

## Feedback Template

```markdown
**Summary**: [LGTM / Request Changes]

**General Comments**:
...

**Specific Feedback**:
- [File/Line]: [Comment]
```
