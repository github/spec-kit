description: Bootstrap the selected context engineering workflow for a new feature and populate the primary artifact.
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

You receive the feature description either from the triggering command argument or the surrounding conversation. Always incorporate it.

User input:

$ARGUMENTS

Workflow rules:
- Determine the active workflow by reading `.context-eng/workflow.json` (`workflow` key). Supported values: `free-style`, `prp`, `all-in-one`.
- Never overwrite existing artifacts without first loading their content.
- Always respect the template referenced by the setup script.

Steps:

1. Run `{SCRIPT}` from the repository root exactly once. Parse its JSON to capture:
   - `BRANCH_NAME`
   - `WORKFLOW`
   - `PRIMARY_FILE`
   - `TEMPLATE_FILE`
   - `FEATURE_DIR`
2. Confirm you are on `BRANCH_NAME`. If not, pause and ask the user to create or switch branches.
3. Load `TEMPLATE_FILE` to understand the mandatory structure for the active workflow.
4. Open (or create if newly provided) `PRIMARY_FILE` and populate it using the template headings while tailoring the content to the supplied feature description and current repository context.
5. When writing, keep placeholders only when information is genuinely unknown—otherwise replace them with concrete details derived from the description and repository signals.
6. Summarize completion, mentioning the workflow, branch, and the primary artifact path. Provide recommended next commands for the workflow:
   - Free-Style → `/research`
   - PRP → `/generate-prp`
   - All-in-One → `/context-engineer`

Set the environment variable `CONTEXT_FEATURE` to `BRANCH_NAME` in any follow-up scripts and surface that value in your response.
