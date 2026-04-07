---
description: "Generate an ordered task list for implementing a track. Writes tasks.md to the track directory."
argument-hint: "<track-name>"
handoffs:
  - label: "Implement Track"
    agent: "infrakit:implement"
  - label: "Analyze for Consistency"
    agent: "infrakit:analyze"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** parse the track name from `$ARGUMENTS`. If not provided, ask:

> "Which track would you like to generate tasks for?
> Example: `sql-instance-20260101-120000`"

**WAIT** for response before continuing.

---

## System Directive

You are generating an actionable, ordered task list for implementing an infrastructure track. Tasks will be written to `.infrakit/tracks/<track-name>/tasks.md` and will be executed by `/infrakit:implement`.

**Each task must be specific enough to execute without additional context.**

---

## Step 1: Setup Check

Verify required files exist:

| File | Path | Required |
|------|------|----------|
| Project Context | `.infrakit/context.md` | ✅ Yes |
| Spec | `.infrakit/tracks/<track-name>/spec.md` | ✅ Yes |
| Plan | `.infrakit/tracks/<track-name>/plan.md` | ✅ Yes |

**If context.md is missing:**
> "❌ Project context not found. Run `/infrakit:setup` first."
**HALT**

**If spec.md is missing:**
> "❌ `spec.md` not found.
>
> Run the spec generation command for your IaC tool:
> - Crossplane: `/infrakit:new_composition <track-name>`
> - Terraform: `/infrakit:create_terraform_code <track-name>`"
**HALT**

**If plan.md is missing:**
> "❌ `plan.md` not found. Run `/infrakit:plan <track-name>` to generate the plan."
**HALT**

---

## Step 2: Load Artifacts

Read the following files:

1. `.infrakit/context.md` — Project standards and naming conventions
2. `.infrakit/coding-style.md` — Coding standards (for task constraints)
3. `.infrakit/tagging-standard.md` — Tagging requirements (for tag tasks)
4. `.infrakit/tracks/<track-name>/spec.md` — Requirements and acceptance criteria
5. `.infrakit/tracks/<track-name>/plan.md` — File structure, managed resources, patch mappings

---

## Step 3: Detect IaC Tool

Read `.infrakit/config.yaml` to detect the IaC tool (crossplane, terraform, etc.). This determines the task phases and file names.

---

## Step 4: Generate Task List

### For Crossplane Projects

Break the plan into discrete, ordered tasks across 5 phases:

**Phase 1: XRD (definition.yaml)**
- Create the CompositeResourceDefinition with:
  - API group from context.md
  - XR Kind and Claim Kind from plan.md
  - OpenAPI v3 schema for each parameter in spec.md (type, required, default, description)
  - Status fields from spec.md
  - Connection secret keys (if applicable)

**Phase 2: Composition (composition.yaml)**
- Create the Composition in Pipeline mode with `crossplane-contrib-function-patch-and-transform`
- For each managed resource in plan.md: define with correct `apiVersion`, `kind`, and `forProvider` fields
- Add `FromCompositeFieldPath` patches for each input parameter → managed resource field mapping
- Add `ToCompositeFieldPath` patches for each status output ← `status.atProvider` field
- Add required tag patches per tagging-standard.md:
  - `crossplane.io/claim-name` from `metadata.name`
  - `crossplane.io/claim-namespace` from `metadata.namespace`
  - `managed-by: crossplane`
- Add `providerConfigRef: name: default` to every managed resource
- Configure `writeConnectionSecretToRef` (if resource has endpoints)

**Phase 3: Example Claim (claim.yaml)**
- Create an example claim with all required parameters populated and commented

**Phase 4: Documentation (README.md)**
- Document the resource purpose, all parameters, connection secrets, and usage examples

**Phase 5: Validation**
- Run `crossplane render claim.yaml composition.yaml definition.yaml` to validate output
- Verify all patches resolve correctly and no errors appear

### For Terraform Projects

Break the plan into discrete, ordered tasks across 5 phases:

**Phase 1: Provider & Version Constraints (versions.tf)**
- Create `versions.tf` declaring:
  - `terraform { required_version = "..." }` from plan.md
  - Provider source and version constraint (e.g., `hashicorp/aws ~> 5.0`)

**Phase 2: Input Variables (variables.tf)**
- Create `variables.tf` with all input variables from plan.md:
  - Each variable must have `type`, `description`, and `default` (if applicable)
  - Sensitive variables (passwords, tokens) must include `sensitive = true`
  - Add `validation` blocks for constrained values (environments, sizes, etc.)

**Phase 3: Resources (main.tf)**
- Create `main.tf` with all resource definitions from plan.md:
  - Apply required tags from `tagging-standard.md` (via `default_tags` for AWS or per-resource `tags`/`labels`)
  - Enable encryption at rest for all storage/database resources
  - Set public access to `false` by default; require explicit variable to override

**Phase 4: Outputs (outputs.tf)**
- Create `outputs.tf` with all output values from plan.md:
  - Each output must have a `description`
  - Sensitive outputs (credentials, endpoints with tokens) must include `sensitive = true`

**Phase 5: Documentation and Validation (README.md)**
- Create `README.md` documenting the module purpose, all variables, outputs, and usage examples
- Run `terraform init && terraform validate` to verify the module is syntactically correct

---

## Step 5: Write tasks.md

Write to `.infrakit/tracks/<track-name>/tasks.md`. Use the format matching the IaC tool from Step 3.

### Crossplane format:

```markdown
# Tasks: <track-name>

Generated from:
- `.infrakit/tracks/<track-name>/spec.md`
- `.infrakit/tracks/<track-name>/plan.md`

---

## Phase 1: XRD Definition

- [ ] T001 Create `<resource-dir>/definition.yaml` — CompositeResourceDefinition
  - Kind: `<XR Kind>` / Claim Kind: `<Claim Kind>`
  - API group: `<api-group>` (from context.md)
  - Parameters: <list each parameter with type>
  - Status fields: <list each output field>

---

## Phase 2: Composition

- [ ] T002 Create `<resource-dir>/composition.yaml` — Pipeline mode Composition
  - Composite type ref: `<XR Kind>.<api-group>`
  - Managed resources: <list each resource from plan.md>

- [ ] T003 [P] Add `FromCompositeFieldPath` patches for all input parameters
  <list each: spec.parameters.<param> → <managed-resource>.spec.forProvider.<field>>

- [ ] T004 [P] Add `ToCompositeFieldPath` patches for all status outputs
  <list each: <managed-resource>.status.atProvider.<field> → status.<field>>

- [ ] T005 Add required tag patches per tagging-standard.md to every managed resource
  - `crossplane.io/claim-name` from metadata.name
  - `crossplane.io/claim-namespace` from metadata.namespace
  - `managed-by: crossplane`

- [ ] T006 Add `providerConfigRef: name: default` to every managed resource

---

## Phase 3: Example Claim

- [ ] T007 Create `<resource-dir>/claim.yaml` — Example claim with all parameters and comments

---

## Phase 4: Documentation

- [ ] T008 Create `<resource-dir>/README.md` — Usage docs, parameter reference, connection secrets

---

## Phase 5: Validation

- [ ] T009 Run `crossplane render <resource-dir>/claim.yaml <resource-dir>/composition.yaml <resource-dir>/definition.yaml` and verify output

---

## Notes

- All code must follow `.infrakit/coding-style.md`
- Pipeline mode is mandatory — never use Resources mode
- Never hardcode secrets or credentials
- Apply all tags from `.infrakit/tagging-standard.md` to every managed resource
```

### Terraform format:

```markdown
# Tasks: <track-name>

Generated from:
- `.infrakit/tracks/<track-name>/spec.md`
- `.infrakit/tracks/<track-name>/plan.md`

---

## Phase 1: Provider & Version Constraints

- [ ] T001 Create `<module-dir>/versions.tf` — Terraform and provider version constraints
  - Terraform required_version: `<version>` (from plan.md)
  - Provider: `<provider>` version `<constraint>` (from plan.md)

---

## Phase 2: Input Variables

- [ ] T002 Create `<module-dir>/variables.tf` — All input variable declarations
  <list each variable with type, default, description, sensitive flag>

---

## Phase 3: Resources

- [ ] T003 Create `<module-dir>/main.tf` — All resource definitions
  <list each resource_type.name from plan.md>

- [ ] T004 [P] Apply required tags per tagging-standard.md to all resources
  - AWS: configure `default_tags` in provider block or per-resource `tags`
  - Azure/GCP: per-resource `tags` / `labels`

- [ ] T005 [P] Enable encryption at rest for all storage/database resources

---

## Phase 4: Outputs

- [ ] T006 Create `<module-dir>/outputs.tf` — All output value declarations
  <list each output with source expression and description>

---

## Phase 5: Documentation and Validation

- [ ] T007 Create `<module-dir>/README.md` — Module purpose, variable reference, outputs, usage examples
- [ ] T008 Run `terraform init && terraform validate` in `<module-dir>` and verify no errors

---

## Notes

- All code must follow `.infrakit/coding-style.md`
- Never hardcode secrets, passwords, or API keys — use `sensitive = true` variables
- Apply all tags from `.infrakit/tagging-standard.md` to every resource that supports tagging
```

---

## Step 6: Present Summary and Confirm

After writing tasks.md, show a phase summary appropriate for the IaC tool:

**Crossplane:**
> "✅ Tasks generated for track `<track-name>`.
>
> | Phase | Tasks | Description |
> |-------|-------|-------------|
> | Phase 1: XRD | 1 | definition.yaml |
> | Phase 2: Composition | N | composition.yaml with patches and tags |
> | Phase 3: Claim | 1 | claim.yaml example |
> | Phase 4: Docs | 1 | README.md |
> | Phase 5: Validation | 1 | crossplane render |
> | **Total** | **N** | |
>
> **File**: `.infrakit/tracks/<track-name>/tasks.md`
>
> Run `/infrakit:implement <track-name>` to begin implementation."

**Terraform:**
> "✅ Tasks generated for track `<track-name>`.
>
> | Phase | Tasks | Description |
> |-------|-------|-------------|
> | Phase 1: Versions | 1 | versions.tf |
> | Phase 2: Variables | 1 | variables.tf |
> | Phase 3: Resources | N | main.tf with tags and encryption |
> | Phase 4: Outputs | 1 | outputs.tf |
> | Phase 5: Docs & Validation | 2 | README.md + terraform validate |
> | **Total** | **N** | |
>
> **File**: `.infrakit/tracks/<track-name>/tasks.md`
>
> Run `/infrakit:implement <track-name>` to begin implementation."

---

## Error Handling

| Error | Action |
|-------|--------|
| Setup files missing | Halt, direct to `/infrakit:setup` |
| spec.md missing | Halt — Crossplane: direct to `/infrakit:new_composition <track-name>`; Terraform: direct to `/infrakit:create_terraform_code <track-name>` |
| plan.md missing | Halt, direct to `/infrakit:plan <track-name>` |
| tasks.md already exists | Ask: overwrite or append? |
