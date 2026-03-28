# Approval Gates

Enforce approval requirements between workflow phases to prevent "spec-less coding".

## Quick Start

### 1. Create Configuration

```bash
mkdir -p .speckit
cat > .speckit/approval-gates.yaml << 'EOF'
approval_gates:
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
EOF
```

### 2. Check Status

```bash
specify approval
```

Expected output:
```
✅ Approval gates enabled

  specify
    • Enabled: ✅
    • Min approvals: 1
  plan
    • Enabled: ✅
    • Min approvals: 2
  tasks
    • Enabled: ✅
    • Min approvals: 1
  implement: disabled
```

## Configuration

Edit `.speckit/approval-gates.yaml` to:
- **enabled**: true/false - Enable/disable this gate
- **requires**: [role1, role2] - Who can approve
- **min_approvals**: number - How many approvals needed
- **description**: string - What this gate is for

### Available Phases

- `constitution` — Project fundamentals
- `specify` — Functional specifications
- `plan` — Technical specifications
- `tasks` — Task breakdown
- `implement` — Implementation (optional)

## Why Use Approval Gates?

✅ **Prevents spec-less coding** — Requires approval before moving phases
✅ **Ensures alignment** — Teams must agree before proceeding
✅ **Creates clarity** — Clear approval requirements for each phase

## Commands

```bash
# Check gate status
specify approval

# Explicitly request status
specify approval --action status
specify approval -a status

# Show help
specify approval --help
```

## Examples

### Basic Setup (All Phases)
```yaml
approval_gates:
  specify:
    enabled: true
    min_approvals: 1
  plan:
    enabled: true
    min_approvals: 2
  tasks:
    enabled: true
    min_approvals: 1
```

### Minimal Setup (Only Specify)
```yaml
approval_gates:
  specify:
    enabled: true
    min_approvals: 1
```

### Strict Setup (High Approval Requirements)
```yaml
approval_gates:
  constitution:
    enabled: true
    requires: [owner]
    min_approvals: 1
  specify:
    enabled: true
    requires: [product_lead, architect]
    min_approvals: 2
  plan:
    enabled: true
    requires: [architect, tech_lead, security_lead]
    min_approvals: 3
```

## Troubleshooting

### Command not found
```bash
# Make sure you're in the spec-kit project
cd ~/spec-kit
uv run specify approval
```

### No approval gates configured
Create `.speckit/approval-gates.yaml` in your project root.

### YAML errors
Check YAML indentation — spaces matter! Use a YAML validator if unsure.

---

**Template:** See `docs/examples/approval-gates.yaml` for a full example.