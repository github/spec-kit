---
id: {{ID}}
title: {{TITLE}}
stage: {{STAGE}}
date: {{DATE_ISO}}
surface: {{SURFACE}}
model: {{MODEL}}
feature: {{FEATURE}}
branch: {{BRANCH}}
user: {{USER}}
command: {{COMMAND}}
labels: [{{LABELS}}]
links:
  spec: {{LINKS_SPEC}}
  ticket: {{LINKS_TICKET}}
  adr: {{LINKS_ADR}}
  pr: {{LINKS_PR}}
files:
{{FILES_YAML}}
tests:
{{TESTS_YAML}}
---

## Prompt

{{PROMPT_TEXT}}

## Response snapshot

{{RESPONSE_TEXT}}

## Outcome

- ✅ Impact: {{OUTCOME_IMPACT}}
- 🧪 Tests: {{TESTS_SUMMARY}}
- 📁 Files: {{FILES_SUMMARY}}
- 🔁 Next prompts: {{NEXT_PROMPTS}}
- 🧠 Reflection: {{REFLECTION_NOTE}}---
id: {{ID}}
title: {{TITLE}}
stage: {{STAGE}}
date: {{DATE_ISO}}
surface: {{SURFACE}}
model: {{MODEL}}
repo_ref: {{BRANCH}}
feature: {{FEATURE}}
command: {{COMMAND}}
user: {{USER}}
sha_before: {{SHA_BEFORE}}
sha_after: {{SHA_AFTER}}
scope_files:
{{SCOPE_FILES}}
links:
  spec: {{LINKS_SPEC}}
  adr: {{LINKS_ADR}}
  issue: {{LINKS_ISSUE}}
  pr: {{LINKS_PR}}
acceptance:
{{ACCEPTANCE}}
constraints:
{{CONSTRAINTS}}
out_of_scope:
{{OUT_OF_SCOPE}}
secrets_policy: "{{SECRETS}}"
labels: [{{LABELS}}]
---

{{PROMPT_TEXT}}

### Response (excerpt)
{{RESPONSE_TEXT}}

### Outcome
- Files changed: {{FILES_CHANGED}}
- Tests added: {{TESTS_ADDED}}
- Next prompts: {{NEXT_PROMPTS}}
- Notes: {{NOTES}}
