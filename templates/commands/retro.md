---
description: Conduct a structured retrospective analysis of the completed development cycle with metrics, learnings, and improvement suggestions.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before retro)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_retro` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Outline.
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Goal

Conduct a structured retrospective analysis of the completed development cycle — from specification through shipping. Analyze what went well, what didn't, and generate actionable improvement suggestions for future iterations. Track metrics over time to identify trends and continuously improve the spec-driven development process.

## Operating Constraints

**CONSTRUCTIVE FOCUS**: The retrospective should be balanced — celebrating successes alongside identifying improvements. Avoid blame; focus on process improvements.

**DATA-DRIVEN**: Base analysis on actual artifacts, git history, and measurable outcomes rather than subjective impressions.

**OPTIONAL WRITES**: The retro report is always written. Updates to `constitution.md` with new learnings are offered but require explicit user approval.

## Outline

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Gather Retrospective Data**:
   Load all available artifacts from the development cycle:
   - **REQUIRED**: Read `spec.md` — original specification and requirements
   - **REQUIRED**: Read `tasks.md` — task breakdown and completion status
   - **IF EXISTS**: Read `plan.md` — technical plan and architecture decisions
   - **IF EXISTS**: Read review reports in FEATURE_DIR/reviews/ — code review findings
   - **IF EXISTS**: Read QA reports in FEATURE_DIR/qa/ — testing results
   - **IF EXISTS**: Read release artifacts in FEATURE_DIR/releases/ — shipping data
   - **IF EXISTS**: Read critique reports in FEATURE_DIR/critiques/ — pre-implementation review
   - **IF EXISTS**: Read previous retros in FEATURE_DIR/retros/ — historical context
   - **IF EXISTS**: Read `/memory/constitution.md` — project principles

3. **Collect Git Metrics**:
   Gather quantitative data from the git history:

   ```bash
   # Commit count for the feature
   git rev-list --count origin/{target_branch}..HEAD

   # Files changed
   git diff --stat origin/{target_branch}..HEAD

   # Lines added/removed
   git diff --shortstat origin/{target_branch}..HEAD

   # Number of authors
   git log origin/{target_branch}..HEAD --format='%an' | sort -u | wc -l

   # Date range (first commit to last)
   git log origin/{target_branch}..HEAD --format='%ai' | tail -1
   git log origin/{target_branch}..HEAD --format='%ai' | head -1
   ```

   If git data is not available (e.g., already merged), use artifact timestamps and content analysis as fallback.

4. **Specification Accuracy Analysis**:
   Compare the original spec against what was actually built:

   - **Requirements fulfilled**: Count of spec requirements that were fully implemented
   - **Requirements partially fulfilled**: Requirements that were implemented with deviations
   - **Requirements not implemented**: Spec items that were deferred or dropped
   - **Unplanned additions**: Features implemented that were NOT in the original spec (scope creep)
   - **Surprises**: Requirements that turned out to be much harder or easier than expected
   - **Accuracy score**: (fulfilled + partial×0.5) / total requirements × 100%

5. **Plan Effectiveness Analysis**:
   Evaluate how well the technical plan guided implementation:

   - **Architecture decisions validated**: Did the chosen patterns/stack work as planned?
   - **Architecture decisions revised**: Were any plan decisions changed during implementation?
   - **Task scoping accuracy**: Were tasks well-sized? Any tasks that were much larger/smaller than expected?
   - **Missing tasks**: Were any tasks added during implementation that weren't in the original breakdown?
   - **Task ordering issues**: Were there dependency problems or tasks that should have been reordered?
   - **Plan score**: Qualitative assessment (EXCELLENT / GOOD / ADEQUATE / NEEDS IMPROVEMENT)

6. **Implementation Quality Analysis**:
   Analyze the quality of the implementation based on review and QA data:

   - **Review findings summary**: Total findings by severity from review reports
   - **Blocker resolution**: Were all blockers resolved before shipping?
   - **QA results summary**: Pass/fail rates from QA testing
   - **Test coverage**: Test suite results and coverage metrics
   - **Code quality indicators**: Lines of code, test-to-code ratio, cyclomatic complexity (if available)
   - **Quality score**: Based on review verdict and QA pass rate

7. **Process Metrics Dashboard**:
   Compile a metrics summary:

   ```
   📊 Development Cycle Metrics
   ━━━━━━━━━━━━━━━━━━━━━━━━━━
   Feature:           {feature_name}
   Duration:          {first_commit} → {last_commit}
   
   📝 Specification
   Requirements:      {total} total, {fulfilled} fulfilled, {partial} partial
   Spec Accuracy:     {accuracy}%
   
   📋 Planning
   Tasks:             {total_tasks} total, {completed} completed
   Added during impl: {unplanned_tasks}
   Plan Score:        {plan_score}
   
   💻 Implementation
   Commits:           {commit_count}
   Files changed:     {files_changed}
   Lines:             +{additions} / -{deletions}
   Test/Code ratio:   {test_ratio}
   
   🔍 Quality
   Review findings:   🔴{blockers} 🟡{warnings} 🟢{suggestions}
   QA pass rate:      {qa_pass_rate}%
   Quality Score:     {quality_score}
   ```

8. **What Went Well** (Keep Doing):
   Identify and celebrate successes:
   - Aspects of the spec that were clear and led to smooth implementation
   - Architecture decisions that proved effective
   - Tasks that were well-scoped and completed without issues
   - Quality practices that caught real issues
   - Any particularly efficient or elegant solutions

9. **What Could Improve** (Start/Stop Doing):
   Identify areas for improvement:
   - Spec gaps that caused confusion or rework during implementation
   - Plan decisions that needed revision
   - Tasks that were poorly scoped or had missing dependencies
   - Quality issues that slipped through review/QA
   - Process friction points (tool issues, unclear workflows)

10. **Actionable Improvement Suggestions**:
    Generate specific, actionable suggestions:
    - Rank by impact (HIGH / MEDIUM / LOW)
    - Each suggestion should be concrete and implementable
    - Group by category: Specification, Planning, Implementation, Quality, Process

    Example format:
    ```
    IMP-001 [HIGH] Add data model validation to spec template
    → The spec lacked entity relationship details, causing 3 unplanned tasks during implementation.
    → Suggestion: Add a "Data Model" section to the spec template with entity, attribute, and relationship requirements.
    
    IMP-002 [MEDIUM] Include browser compatibility in QA checklist
    → QA missed a CSS rendering issue in Safari that was caught post-merge.
    → Suggestion: Add cross-browser testing scenarios to the QA test plan.
    ```

11. **Historical Trend Analysis** (if previous retros exist):
    If FEATURE_DIR/retros/ contains previous retrospective reports:
    - Compare key metrics across cycles (spec accuracy, QA pass rate, review findings)
    - Identify improving trends (celebrate!) and declining trends (flag for attention)
    - Check if previous improvement suggestions were adopted and whether they helped
    - Output a trend summary table

12. **Generate Retrospective Report**:
    Create the retro report at `FEATURE_DIR/retros/retro-{timestamp}.md` using the retrospective report template.

13. **Offer Constitution Update**:
    Based on the retrospective findings, offer to update `/memory/constitution.md` with new learnings:

    - "Based on this retrospective, I suggest adding the following principles to your constitution:"
    - List specific principle additions or modifications
    - **Wait for explicit user approval** before making any changes
    - If approved, append new principles with a "Learned from: {feature_name} retro" annotation

14. **Suggest Next Actions**:
    - If this was a successful cycle: "Great work! Consider starting your next feature with `/speckit.specify`"
    - If improvements were identified: List the top 3 most impactful improvements to adopt
    - If trends are declining: Recommend a process review or team discussion

**Check for extension hooks (after retro)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.after_retro` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently
