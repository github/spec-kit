---
description: Create or update the higher-level enterprise constitution that governs all project constitutions.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

You are updating the **enterprise constitution**, which is the **single source of truth**
for non‑negotiable, organization‑wide guiding principles and governance rules that all
project-level constitutions MUST obey.

- The enterprise constitution defines global values, constraints, and guardrails.
- It is typically stored in a dedicated governance or platform repository and may be
  **mirrored into individual projects** as a cached copy at `/memory/enterprise-constitution.md`.
- Every project constitution (for example `/memory/constitution.md`) is subordinate
  to this document and MUST NOT contradict it.
- Projects MAY further narrow or strengthen enterprise rules, but they MUST NOT
  weaken or violate them.

## Outline

Follow this execution flow:

1. **Load existing enterprise constitution (if any)**
   - Prefer loading from the **canonical governance repository** if its location
     is known (e.g., Git repo URL + path, or an HTTP/HTTPS URL to the file).
   - If you are working directly in that governance repo, load and parse the
     local file there (which will typically also be mirrored at
     `/memory/enterprise-constitution.md`).
   - Identify its current version, ratification date, last amended date, and
     existing principles and governance sections.
   - If no existing enterprise constitution can be found, you are creating
     version `1.0.0` of the enterprise constitution; ask the user (or infer)
     core organizational values and constraints and propose a canonical
     storage location (repository + file path).

2. **Collect/derive principles and governance elements**
   - Use user input first when it clearly expresses organization-wide values,
     non-negotiable rules, or governance expectations.
   - Otherwise, infer from repo context (e.g., `README.md`, `docs/*.md`,
     security, compliance, and contribution guidelines) to propose a coherent
     enterprise-level set of principles.
   - Define a small number of crisp, testable principles (for example,
     5–10 core principles) grouped under clear headings such as:
     - Mission & Outcomes
     - Safety, Security & Compliance
     - Quality & Reliability
     - Transparency & Accountability
     - Data & Privacy
     - AI & Automation (if applicable)
   - For governance, define at least:
     - Who can propose amendments.
     - How changes are reviewed and approved.
     - How often the constitution should be revisited.
     - How conflicts with project-level constitutions are resolved.

3. **Decide version bump**
   - If creating the constitution for the first time, set
     `CONSTITUTION_VERSION` to `1.0.0` and `RATIFICATION_DATE` to the
     organization’s chosen date (or `TODO(RATIFICATION_DATE)` if unknown).
   - If updating an existing enterprise constitution, determine the new
     semantic version:
     - MAJOR: Backward-incompatible changes to core values or removal/
       redefinition of principles.
     - MINOR: New principles or material expansions of governance.
     - PATCH: Clarifications, wording, or non-semantic refinements.
   - Set `LAST_AMENDED_DATE` to today (YYYY-MM-DD) if any changes are made;
     otherwise keep the existing date.

4. **Draft the updated enterprise constitution**
   - Use clear Markdown structure with top-level sections like:
     - Preamble
     - Principles
     - Governance
     - Compliance & Review
   - Each principle MUST:
     - Have a short, specific name.
     - State non‑negotiable rules using clear, declarative language.
     - Provide a brief rationale if not obvious from the rule itself.
   - Governance MUST explicitly state that:
     - All project constitutions MUST comply with the enterprise constitution.
     - Project constitutions MAY add stricter rules but not weaker ones.
     - In case of conflict, the enterprise constitution prevails.

5. **Produce an Enterprise Sync Impact Report**
   - Prepend an HTML comment block at the top of the canonical enterprise constitution
     file (and any mirrored `/memory/enterprise-constitution.md` copy, if used in this
     context) containing:
     - Version change: old → new.
     - List of added, modified, and removed principles.
     - Governance changes.
      - Where the canonical file is stored (repository + path, and commit/ref if known).
     - Any `TODO(...)` fields and why they were deferred.
   - This report is for humans; keep it concise and factual.

6. **Validation before final output**
   - Ensure dates use ISO format `YYYY-MM-DD`.
   - Ensure principles are:
     - Declarative and testable.
     - Free of vague language (avoid "just", "try", etc.).
     - Clearly applicable across all projects under the organization.
   - Ensure governance clearly describes how project-level constitutions are
     expected to align and how conflicts are handled.

7. **Write or propose the completed enterprise constitution**
   - If you are running inside the canonical governance repository:
     - Overwrite the canonical enterprise constitution file with the fully
       rendered Markdown, including the Enterprise Sync Impact Report comment
       at top.
     - If this environment also uses `/memory/enterprise-constitution.md` as a
       mirror, update that file to match.
   - If you are running inside a **consumer/project repository** (not the
     canonical governance repo):
     - Do **not** attempt to directly modify the remote canonical file.
     - Instead, generate:
       - The full updated enterprise constitution Markdown.
       - A clear, minimal patch or PR description that can be applied to the
         canonical repository (including target repo, file path, and a concise
         change summary if known).
     - Optionally write `/memory/enterprise-constitution.md` in this project as
       a **temporary mirror** of the proposed new version, clearly marking in
       the Enterprise Sync Impact Report that these changes are "pending
       upstream approval" in the canonical repo.

8. **Final summary to the user**
   - Report the new version and bump rationale.
   - Highlight the key enterprise principles that were added or changed.
   - Call out any TODOs requiring organizational input (e.g., ratification body,
     dates, or unresolved governance details).
   - Explicitly state whether you:
     - Updated the canonical file (when in the governance repo), or
     - Generated a patch/PR proposal that must be applied in the canonical repo.
   - Suggest a commit message such as:
     `docs: establish enterprise constitution vX.Y.Z (org-wide principles)`.
