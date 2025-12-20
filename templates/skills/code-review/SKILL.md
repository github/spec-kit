---
name: code-review
description: |
  Code review excellence - systematic approach to reviewing code for quality, security, and maintainability.
  Activate when: reviewing PRs, checking code quality, or when user mentions "review", "code quality", "PR".
triggers: ["review", "code review", "PR review", "quality check", "review this"]
---

# Code Review Excellence

> Systematic code review for quality, security, and maintainability.

## Review Checklist

### 1. Correctness
- [ ] Logic is correct and handles edge cases
- [ ] Error handling is appropriate
- [ ] No off-by-one errors or boundary issues

### 2. Security
- [ ] No hardcoded secrets or credentials
- [ ] Input is validated and sanitized
- [ ] No SQL injection or XSS vulnerabilities
- [ ] Auth/authz checks are in place

### 3. Performance
- [ ] No N+1 queries or unnecessary loops
- [ ] Resources are properly released
- [ ] No blocking operations in hot paths

### 4. Maintainability
- [ ] Code is readable and self-documenting
- [ ] Functions are single-purpose and small
- [ ] No code duplication
- [ ] Naming is clear and consistent

### 5. Testing
- [ ] Tests exist for new functionality
- [ ] Edge cases are tested
- [ ] Tests are meaningful, not just coverage

## Quick Reference

| Aspect | Look For |
|--------|----------|
| **Functions** | < 30 lines, single responsibility |
| **Parameters** | < 4 params, use objects for more |
| **Nesting** | < 3 levels deep |
| **Comments** | Explain "why", not "what" |

## Critical Don'ts

- Don't approve code with security vulnerabilities
- Don't skip reviewing test code
- Don't approve without understanding the change
- Don't nitpick style if linters handle it

## References

- For detailed checklist: Read references/review-checklist.md
- For security patterns: Read references/security-review.md
