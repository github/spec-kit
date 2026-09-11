# Approval Gates Extension

Extension to enforce approval requirements between spec-driven development phases.

## Installation

### 1. Install the Extension

```bash
specify extension add --dev extensions/approval-gates
```

### 2. Create Configuration

Copy the template to your project:

```bash
mkdir -p .specify/extensions/approval-gates
cp extensions/approval-gates/approval-gates-config.template.yml \
   .specify/extensions/approval-gates/approval-gates-config.yml
```

### 3. Customize for Your Team

Edit `.specify/extensions/approval-gates/approval-gates-config.yml` and set:

- Which phases require approval
- How many approvals are needed
- Who can approve each phase
- Descriptions for each gate

## Configuration

### Schema

```yaml
specify:
  enabled: bool                    # Enable/disable this gate
  requires: [role1, role2, ...]    # Who can approve
  min_approvals: int               # How many approvals required
  description: string              # (optional) What this gate enforces
```

### Example

```yaml
specify:
  enabled: true
  requires: [product_lead, architect]
  min_approvals: 1
  description: "Functional spec approval"

plan:
  enabled: true
  requires: [architect, tech_lead]
  min_approvals: 2
  description: "Technical plan approval"

tasks:
  enabled: false
```

## Usage

### Check Approval Gates Status

```bash
> /speckit.approval-gates.status
```

Shows which phases are gated and their approval requirements:

```
✅ Approval gates enabled

  📋 specify
     • Status: ✅ ENFORCED
     • Min approvals: 1
     • Description: Functional spec approval

  📋 plan
     • Status: ✅ ENFORCED
     • Min approvals: 2
     • Description: Technical spec approval
```

### After Tasks Phase

The extension integrates with the workflow:

```bash
> /speckit.tasks
# ... task generation ...
# Prompt appears:
# ❓ Check approval gates for next phase?
> Y
```

## Phases

Approval gates can be configured for the following phases:

- `constitution` — Project setup and context
- `specify` — Functional specification
- `plan` — Technical specification and architecture
- `tasks` — Task breakdown and planning
- `implement` — Implementation phase (optional)

## Troubleshooting

### Command Not Found

```
❌ Command not found: speckit.approval-gates.status
```

**Solution**: Reinstall the extension:

```bash
specify extension remove approval-gates
specify extension add --dev extensions/approval-gates
```

### Config Not Loading

```
ℹ️ No approval gates configured
```

**Solution**: Ensure the config file exists:

```bash
ls .specify/extensions/approval-gates/approval-gates-config.yml
# If missing, create it from template
```

### YAML Parse Error

```
❌ Error parsing approval-gates-config.yml
```

**Solution**: Validate YAML syntax:

```bash
yq eval '.' .specify/extensions/approval-gates/approval-gates-config.yml
```

Check for:
- Proper indentation (2 spaces)
- Quotes around strings
- No trailing colons

## Related Commands

- `/speckit.constitution` — Project setup
- `/speckit.specify` — Create specification
- `/speckit.plan` — Create plan
- `/speckit.tasks` — Generate tasks
