---
name: code-review
description: Reviews Spec Kit code changes for consistency with applicable design documents, positive and negative test coverage, regression evidence for bug fixes, and consistent repository terminology. Use when reviewing a diff or pull request. Do not use for implementing changes or posting GitHub review actions.
argument-hint: 'Diff or pull request to review'
---

# Code Review

1. Ensure each code change has test cases that verify what the code should do and what it should prevent.
2. Ensure bug-fix pull requests include a regression test that demonstrates the bug was reproducible before the change and is fixed afterward; if the reviewer cannot run the comparison, use available evidence and state that limitation.
3. Ensure wording changes use repository-consistent terms; exclude community-authored catalog content and its generated documentation from this check.
4. Identify the affected domains and read the applicable documents in `design/` before evaluating architectural consistency. For CLI command changes, use `design/cli.md`; for agent integrations, use `design/integration.md`; for workflow step types, use `design/workflow-step.md`. Read other design documents when relevant, not every document for every PR.
5. Check the changes against the applicable design requirements, including implementation boundaries, ownership, lifecycle, and delivery requirements. Reference the documents rather than duplicating their rules in this skill. Cite the document and section for each reported mismatch.
6. Distinguish an unexplained design violation from an intentional design change. Evaluate the rationale and evidence for an intentional change; updating the design document alone does not establish that the implementation is justified.
