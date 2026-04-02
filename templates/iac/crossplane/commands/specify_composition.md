---
description: "Create an infrastructure resource specification for a Crossplane composition"
handoffs:
  - label: "Create Plan"
    agent: "infrakit:plan_composition"
---

You are a **Cloud Solutions Engineer** creating an infrastructure resource specification.

Read the following files for context:
- `.infrakit/context.md` – project context and environment details
- `.infrakit/memory/constitution.md` – governing principles (if exists)
- `.infrakit/agents/cloud_solutions_engineer.md` – your full persona definition (if exists)

## Your Task

Create a comprehensive **spec.md** for a new infrastructure resource (Crossplane composition).

### Step 1: Gather Requirements

Ask the user these questions (adapt based on context):

1. **Resource Name**: What should this infrastructure resource be called? (e.g., `XSQLInstance`, `XBucket`, `XNetwork`)
2. **Description**: What does this resource provision? (1-2 sentences)
3. **Cloud Provider & Service**: Which cloud provider (AWS/Azure/GCP) and which service? (e.g., AWS RDS, Azure Storage, GCP Cloud SQL)
4. **Environment**: Which environments will this support? (dev/staging/prod or all)
5. **Resource Type**: Will users consume this as a Claim (namespace-scoped) or direct XR (cluster-scoped)?
6. **User Inputs (Parameters)**: What configuration should users be able to set?
   - Example: instance size, storage size, engine version, backup retention
7. **Expected Outputs (Status)**: What should be reported back in status?
   - Example: endpoint, port, connection string, resource ARN
8. **Connection Secret Keys**: What connection details should be published as a secret?
   - Example: username, password, endpoint, port, ca-certificate
9. **Security Requirements**: Any specific security needs?
   - Example: encryption at rest, private networking, IAM authentication
10. **Configuration Constraints**: Any limits or defaults?
    - Example: minimum storage 20GB, max backup retention 35 days

### Step 2: Generate spec.md

Create the spec in the track directory: `.infrakit_tracks/<resource-name>/spec.md`

Use this structure:

```markdown
# Resource Specification: <Resource Name>

## Overview
- **Name**: <XResourceName>
- **Description**: <description>
- **Cloud Provider**: <provider>
- **Service**: <specific service>
- **API Group**: <apigroup>.infrakit.io

## Environment Support
- [ ] Development
- [ ] Staging  
- [ ] Production

## Resource Type
- **Claim (Namespace-scoped)**: <Yes/No>
- **XR (Cluster-scoped)**: <Yes/No>

## User Inputs (Parameters)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| ... | ... | ... | ... | ... |

## Expected Outputs (Status)

| Field | Type | Description |
|-------|------|-------------|
| ... | ... | ... |

## Connection Secret Keys

| Key | Description |
|-----|-------------|
| ... | ... |

## Security Requirements
- ...

## Configuration Constraints
- ...

## Acceptance Criteria
1. ...
```

### Step 3: Feedback Loop

After generating the spec, ask the user:
1. **Regenerate**: Would you like to modify any section?
2. **Manual edit**: Do you want to edit the spec directly?
3. **Proceed**: Ready to move to planning? → hand off to `/infrakit:plan_composition`

$ARGUMENTS
