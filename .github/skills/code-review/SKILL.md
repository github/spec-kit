---
name: code-review
description: Reviews Spec Kit code changes for positive and negative test coverage, regression evidence for bug fixes, and consistent repository terminology. Use when reviewing a diff or pull request. Do not use for implementing changes or posting GitHub review actions.
argument-hint: 'Diff or pull request to review'
---

# Code Review

1. Ensure each code change has test cases that verify what the code should do and what it should prevent.
2. Ensure bug-fix pull requests include a regression test that demonstrates the bug was reproducible before the change and is fixed afterward; if the reviewer cannot run the comparison, use available evidence and state that limitation.
3. Ensure wording changes use repository-consistent terms; exclude community-authored catalog content and its generated documentation from this check.
