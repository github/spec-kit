---
description: "Show approval gates configuration and enforcement status"
---

# Approval Gates Status

Display the current approval gates configuration.

## Steps

### Step 1: Check if Approval Gates are Configured

```bash
config_file=".specify/extensions/approval-gates/approval-gates-config.yml"

if [ ! -f "$config_file" ]; then
  echo "ℹ️  No approval gates configured"
  echo ""
  echo "To enable approval gates:"
  echo "  1. Create .specify/extensions/approval-gates/ directory"
  echo "  2. Copy the template: approval-gates-config.template.yml"
  echo "  3. Customize for your team's workflow"
  echo ""
  echo "See: extensions/approval-gates/README.md for setup instructions"
  exit 0
fi
```

### Step 2: Display Approval Gates Status

```bash
echo "✅ Approval gates enabled"
echo ""

# Parse YAML and display each phase
phases=$(yq eval 'keys[]' "$config_file" 2>/dev/null || echo "")

if [ -z "$phases" ]; then
  echo "⚠️  No phases configured in approval-gates-config.yml"
  exit 0
fi

for phase in $phases; do
  enabled=$(yq eval ".${phase}.enabled" "$config_file" 2>/dev/null)

  if [ "$enabled" = "true" ]; then
    min_approvals=$(yq eval ".${phase}.min_approvals // 1" "$config_file" 2>/dev/null)
    requires=$(yq eval ".${phase}.requires // []" "$config_file" 2>/dev/null)
    description=$(yq eval ".${phase}.description" "$config_file" 2>/dev/null)

    echo "  📋 $phase"
    echo "     • Status: ✅ ENFORCED"
    echo "     • Min approvals: $min_approvals"

    if [ -n "$description" ] && [ "$description" != "null" ]; then
      echo "     • Description: $description"
    fi

    echo ""
  else
    echo "  ⊘ $phase: disabled"
    echo ""
  fi
done
```

## Configuration

This command reads from `.specify/extensions/approval-gates/approval-gates-config.yml`.

### Example Configuration

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
  description: "Technical spec approval"

tasks:
  enabled: true
  requires: [tech_lead]
  min_approvals: 1
  description: "Task breakdown approval"

implement:
  enabled: false
```

### Configuration Fields

- **enabled** (boolean): Whether this phase requires approval
  - `true`: Approval is required
  - `false`: Phase can proceed without approval

- **min_approvals** (number): Minimum approvals needed from the required roles
  - Example: `1` (at least one person from `requires` must approve)

- **requires** (array): List of roles who can approve
  - Example: `[product_lead, architect, tech_lead]`

- **description** (string, optional): What this gate enforces
  - Example: "Technical spec approval"

## Examples

### Check Current Gates

```bash
> /speckit.approval-gates.status
```

Output:
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

  📋 tasks
     • Status: ✅ ENFORCED
     • Min approvals: 1
     • Description: Task breakdown approval

  ⊘ implement: disabled
```

### No Configuration

```bash
> /speckit.approval-gates.status
```

Output:
```
ℹ️  No approval gates configured

To enable approval gates:
  1. Create .specify/extensions/approval-gates/ directory
  2. Copy the template: approval-gates-config.template.yml
  3. Customize for your team's workflow

See: extensions/approval-gates/README.md for setup instructions
```

## Related Commands

- `/speckit.specify` — Create functional specification
- `/speckit.plan` — Create technical specification and task breakdown
- `/speckit.tasks` — Generate implementation tasks

