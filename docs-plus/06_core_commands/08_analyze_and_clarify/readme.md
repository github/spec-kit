# Step 7: [Clarify & Analyze Spec](https://www.youtube.com/watch?v=YD66SBpJY2M) Deep Dive

Two key commands that enhance the Spec Kit workflow are /clarify and /analyze. These commands help to mitigate the risk of "underspecification," where a lack of detail can lead to incorrect assumptions and rework.

**Goal:** keep your spec, plan, and task list honest by driving ambiguity to zero with `/clarify` and proving coverage with `/analyze` before you advance to planning or implementation.

## Core concepts

- **Clarification queue:** The /clarify command helps to resolve ambiguities in the specification by engaging the user in a structured dialogue. It presents a series of up to five questions with multiple-choice answers to refine underspecified areas. The user's selections are then logged in the specification, creating a clear record of the decisions made.

- **Coverage check:** /analyze command provides a crucial check for consistency across the various project artifacts. It examines the spec.md, plan.md, and tasks.md files to identify any inconsistencies, gaps, or violations of the project's defined "constitution" – a set of non-negotiable principles.

## Inputs

- Current `spec.md`, `plan.md`, `tasks.md`
- Latest `/clarify` transcript or log
- Most recent `/analyze` report
- Stakeholder feedback or product notes that triggered rework
- Relevant constitution clauses (change management, Article III test-first, Article IX integration-first)

## Actions

1. **Collect open questions**
   - Export the `/clarify` log and tag each item by theme (scope, UX, data, compliance).
   - Assign owners and due dates so nothing stalls.
2. **Run `/clarify` and resolve**
   - Execute `/clarify @specs/<feature>/spec.md` (include plan/tasks if required) to refresh the queue.
   - Capture answers directly in the spec or supporting docs; add ADRs when the decision is architectural.
   - Remove or annotate any `[NEEDS CLARIFICATION]` markers as you close them.
3. **Update downstream artifacts**
   - Sync `plan.md`, `data-model.md`, and `tasks.md` with the new rulings.
   - Update constitution notes if patterns suggest a new rule or amendment.
4. **Run `/analyze` for coverage**
   - Execute `/analyze @specs/<feature>/` and review every red or yellow item.
   - Add tasks, clarify requirements, or adjust tests until the report is clean.
5. **Lock the loop**
   - Mark the clarification log with final statuses (Open → Answered → Deferred).
   - Store the latest `/clarify` and `/analyze` outputs in `.specify/memory/` (or your docs location) for traceability.
   - Signal “Ready for Plan/Implementation” only when both queues are clear.

## Deliverables

- Updated spec/plan/tasks reflecting resolved questions and new decisions
- Clarification log summarizing questions, owners, outcomes, and links
- Clean `/analyze` report archived alongside the feature artifacts
- ADRs or constitution updates for any significant policy or architectural change

## Quality Gates ✅

- No unresolved items remain in `/clarify`; deferred questions have owners and deadlines
- `/analyze` reports zero blocking gaps; warnings are either fixed or explicitly accepted with rationale
- Commit history references the clarification or ADR that justified each change
- Constitution reflects any repeat insights discovered during the loop

## Common pitfalls

- Skipping `/clarify` after spec edits and letting assumptions leak into implementation
- Ignoring `/analyze` results or treating them as optional advice
- Leaving answers in chat logs instead of updating the spec or ADRs
- Forgetting to store transcripts, making decision trails impossible to audit

## References

- Spec Kit Plus repo: https://github.com/panaversity/spec-kit-plus
- PyPI package: https://pypi.org/project/specifyplus/
- Spec Kit Clarify/Analyze Demo (optional deep dive): https://www.youtube.com/watch?v=YD66SBpJY2M
- Spec Kit Nine Articles: https://github.com/panaversity/spec-kit-plus/blob/main/spec-driven.md#the-nine-articles-of-development
- Original Spec Kit repo: https://github.com/github/spec-kit

## Next Step

With clarifications resolved and coverage verified, proceed to [Step 8: Ship with `/sp.git.commit_pr`](../09_git_commit_pr/readme.md) to finalize the branch and open the pull request.
