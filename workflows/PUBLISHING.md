# Workflow Publishing Guide

This guide explains how to publish your workflow to the Spec Kit workflow catalog, making it discoverable by `specify workflow search`.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Prepare Your Workflow](#prepare-your-workflow)
3. [Submit to Catalog](#submit-to-catalog)
4. [Verification Process](#verification-process)
5. [Release Workflow](#release-workflow)
6. [Best Practices](#best-practices)

---

## Prerequisites

Before publishing a workflow, ensure you have:

1. **Valid Workflow**: A working `workflow.yml` that passes `specify workflow run` validation
2. **Git Repository**: Workflow hosted on GitHub (or other public git hosting)
3. **Documentation**: README.md with description, inputs, and step graph
4. **License**: Open source license file (MIT, Apache 2.0, etc.)
5. **Versioning**: Semantic versioning in the `workflow.version` field
6. **Testing**: Workflow tested on real projects

---

## Prepare Your Workflow

### 1. Workflow Structure

Host your workflow in a repository with this structure:

```text
your-workflow/
├── workflow.yml               # Required: Workflow definition
├── README.md                  # Required: Documentation
├── LICENSE                    # Required: License file
└── CHANGELOG.md               # Recommended: Version history
```

### 2. workflow.yml Validation

Verify your definition is valid:

```yaml
schema_version: "1.0"

workflow:
  id: "your-workflow"              # Unique lowercase-hyphenated ID
  name: "Your Workflow Name"       # Human-readable name
  version: "1.0.0"                 # Semantic version
  author: "Your Name or Organization"
  description: "Brief description (one sentence)"
  integration: claude              # Default integration (optional)
  model: "claude-sonnet-4-20250514"         # Default model (optional)

requires:
  speckit_version: ">=0.6.1"
  integrations:
    any: ["claude", "gemini"]      # At least one required

inputs:
  spec:
    type: string
    required: true
    prompt: "Describe what you want to build"
  scope:
    type: string
    default: "full"
    enum: ["full", "backend-only", "frontend-only"]

steps:
  - id: specify
    command: speckit.specify
    input:
      args: "{{ inputs.spec }}"

  - id: review
    type: gate
    message: "Review the output."
    options: [approve, reject]
    on_reject: abort
```

**Validation Checklist**:

- ✅ `id` is lowercase alphanumeric with hyphens (single-character IDs are allowed)
- ✅ `version` follows semantic versioning (X.Y.Z)
- ✅ `description` is concise
- ✅ All step IDs are unique
- ✅ Step types are valid: `command`, `prompt`, `shell`, `gate`, `if`, `switch`, `while`, `do-while`, `fan-out`, `fan-in`
- ✅ Required fields present per step type (e.g., `condition` for `if`, `expression` for `switch`)
- ✅ Input types are valid: `string`, `number`, `boolean`
- ✅ Step IDs do not contain `:` (reserved for engine-generated nested IDs like `parentId:childId`)

### 3. Test Locally

```bash
# Run with required inputs
specify workflow run ./workflow.yml --input spec="Build a user authentication system with OAuth support"

# Check validation
specify workflow info ./workflow.yml

# Resume after a gate pause
specify workflow resume <run_id>

# Check run status
specify workflow status <run_id>
```

### 4. Create GitHub Release

Create a GitHub release for your workflow version:

```bash
git tag v1.0.0
git push origin v1.0.0
```

The raw YAML URL will be:

```text
https://raw.githubusercontent.com/your-org/spec-kit-workflow-your-workflow/v1.0.0/workflow.yml
```

### 5. Test Installation from URL

```bash
specify workflow add your-workflow
# (once published to catalog)
```

---

## Submit to Catalog

### Understanding the Catalogs

Spec Kit uses a dual-catalog system:

- **`catalog.json`** — Official, verified workflows (install allowed by default)
- **`catalog.community.json`** — Community-contributed workflows (discovery only by default)

All community workflows should be submitted to `catalog.community.json`.

### 1. Fork the spec-kit Repository

```bash
git clone https://github.com/YOUR-USERNAME/spec-kit.git
cd spec-kit
```

### 2. Add Workflow to Community Catalog

Edit `workflows/catalog.community.json` and add your workflow.

> **⚠️ Entries must be sorted alphabetically by workflow ID.** Insert your workflow in the correct position within the `"workflows"` object.

```json
{
  "schema_version": "1.0",
  "updated_at": "2026-04-10T00:00:00Z",
  "catalog_url": "https://raw.githubusercontent.com/github/spec-kit/main/workflows/catalog.community.json",
  "workflows": {
    "your-workflow": {
      "id": "your-workflow",
      "name": "Your Workflow Name",
      "description": "Brief description of what your workflow automates",
      "author": "Your Name",
      "version": "1.0.0",
      "url": "https://raw.githubusercontent.com/your-org/spec-kit-workflow-your-workflow/v1.0.0/workflow.yml",
      "repository": "https://github.com/your-org/spec-kit-workflow-your-workflow",
      "license": "MIT",
      "requires": {
        "speckit_version": ">=0.15.0"
      },
      "tags": [
        "category",
        "automation"
      ],
      "created_at": "2026-04-10T00:00:00Z",
      "updated_at": "2026-04-10T00:00:00Z"
    }
  }
}
```

### 3. Submit Pull Request

```bash
git checkout -b add-your-workflow
git add workflows/catalog.community.json
git commit -m "Add your-workflow to community catalog

- Workflow ID: your-workflow
- Version: 1.0.0
- Author: Your Name
- Description: Brief description
"
git push origin add-your-workflow
```

**Pull Request Checklist**:

```markdown
## Workflow Submission

**Workflow Name**: Your Workflow Name
**Workflow ID**: your-workflow
**Version**: 1.0.0
**Repository**: https://github.com/your-org/spec-kit-workflow-your-workflow

### Checklist
- [ ] Valid workflow.yml (passes `specify workflow info`)
- [ ] README.md with description, inputs, and step graph
- [ ] LICENSE file included
- [ ] GitHub release created with raw YAML URL
- [ ] Workflow tested end-to-end with `specify workflow run`
- [ ] All gate steps have clear review messages
- [ ] Input prompts are descriptive
- [ ] Added to workflows/catalog.community.json (alphabetical order)
```

---

## Verification Process

After submission, maintainers will review:

1. **Definition validation** — valid `workflow.yml`, correct schema
2. **Step correctness** — all step types used correctly, no dangling references
3. **Input design** — clear prompts, sensible defaults and enums
4. **Security** — no malicious shell commands, safe operations
5. **Documentation** — clear README explaining what the workflow does and when to use it

Once verified, the workflow appears in `specify workflow search`.

---

## Release Workflow

When releasing a new version:

1. Update `version` in `workflow.yml`
2. Update CHANGELOG.md
3. Tag and push: `git tag v1.1.0 && git push origin v1.1.0`
4. Submit PR to update `version` and `url` in `workflows/catalog.community.json`

---

## Best Practices

### Step Design

- **Use gates at decision points** — place `gate` steps after each major output so users can review before proceeding
- **Keep steps focused** — each step should do one thing; prefer more steps over complex single steps
- **Provide clear gate messages** — explain what to review and what approve/reject means

### Inputs

- **Use descriptive prompts** — the `prompt` field is shown to users when running the workflow
- **Set sensible defaults** — optional inputs should have defaults that work for the common case
- **Constrain with enums** — when there's a fixed set of valid values, use `enum` for validation
- **Type appropriately** — use `number` for counts, `boolean` for flags, `string` for names

### Shell Steps

- **Avoid destructive commands** — don't delete files or directories without explicit confirmation via a gate
- **Quote variables** — use proper quoting in shell commands to handle spaces
- **Check exit codes** — shell step failures stop the workflow; make sure commands are robust

#### Security: shell steps execute arbitrary code

Workflow `shell` steps execute their `run` field through `/bin/sh` (POSIX) or the platform shell. There is no sandbox between the step and the user's machine: a malicious or buggy `run` block can read environment variables, modify files outside the project, exfiltrate data, or escalate privileges.

Catalog-listed workflows are reviewed at submission time (see [Verification Process](#verification-process)), but you should still treat every install as code-execution from an untrusted source until you have read the `workflow.yml`:

- **Before installing a workflow**, fetch the raw YAML and audit every `shell` step's `run` field directly. `specify workflow info <name>` only shows metadata (name, version, inputs, step IDs/types) — not the shell content that would actually execute.
- **Prefer explicit commands over interpolation** in `run` blocks: `{{ inputs.something }}` substitutions should be quoted and constrained via `enum` so a malicious input can't inject shell syntax.
- **Limit privilege**: shell steps inherit the user's environment. Workflows that need elevated access (sudo, secrets, GitHub tokens) should call them out explicitly in the README so reviewers can spot the requirement.
- **Authors**: if your workflow has shell steps that look risky out of context (deletions, network calls, credential reads), document the rationale in your README. Maintainers will reject submissions whose shell steps can't be justified at review time.

### Integration Flexibility

- **Set `integration` at workflow level** — use the `workflow.integration` field as the default
- **Allow per-step overrides** — let individual steps specify a different integration if needed
- **Document required integrations** — list which integrations must be installed in `requires.integrations`

### Expression References

- **Only reference prior steps** — expressions like `{{ steps.plan.output.file }}` only work if `plan` ran before the current step
- **Use `default` filter** — `{{ val | default('fallback') }}` prevents failures from missing values
- **Keep expressions simple** — complex logic should be in shell steps, not expressions
