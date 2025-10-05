---
description: Decompose parent feature spec into atomic capabilities (200-500 LOC each)
scripts:
  sh: scripts/bash/decompose-feature.sh --json
  ps: scripts/powershell/decompose-feature.ps1 -Json
---

# Decompose - Break Feature into Atomic Capabilities

Given a parent feature specification, decompose it into independently-implementable capabilities.

## Pre-Decomposition Validation

1. **Verify parent spec exists**:
   - Run `{SCRIPT}` from repo root
   - Parse JSON for SPEC_PATH, CAPABILITIES_FILE, SPEC_DIR
   - Confirm parent spec.md is complete (no [NEEDS CLARIFICATION] markers)

2. **Load parent specification**:
   - Read parent spec.md
   - Extract all functional requirements (FR-001, FR-002, ...)
   - Identify key entities and user scenarios
   - Understand dependencies and constraints

3. **Load constitution** at `/memory/constitution.md` for constitutional requirements

## Decomposition Process

### Phase 1: Analyze & Group Requirements

**Think hard about decomposition strategy:**
- What are the natural bounded contexts in this feature?
- How can requirements be grouped to maximize independence?
- Which capabilities are foundational (enable others)?
- What dependencies exist between capability groups?
- How can we minimize coupling while maximizing cohesion?

**Grouping Strategies:**
1. **By Entity Lifecycle**: User CRUD, Project CRUD, Report CRUD
2. **By Workflow Stage**: Registration → Auth → Profile → Settings
3. **By API Cluster**: 3-5 related endpoints that share models/services
4. **By Technical Layer**: Data layer → Service layer → API layer (vertical slices preferred)

**Analyze functional requirements:**
- Group related FRs into bounded contexts
- Identify foundation requirements (infrastructure, base models)
- Map dependencies between requirement groups
- Estimate complexity per group

### Phase 2: Estimate LOC Per Capability

**For each identified group, estimate:**
| Component | Typical Range | Notes |
|-----------|---------------|-------|
| Contract tests | 50-100 LOC | ~20-25 LOC per endpoint/contract |
| Models | 50-100 LOC | ~50 LOC per entity with validation |
| Services | 100-200 LOC | CRUD + business logic |
| Integration tests | 50-100 LOC | E2E scenarios for the capability |
| CLI (if applicable) | 30-80 LOC | Command interface |

**Target total: 250-500 LOC per capability**

**Validation rules:**
- **<200 LOC**: Too small, consider merging with related capability
- **200-400 LOC**: ✓ Ideal range
- **400-500 LOC**: ✓ Acceptable, ensure well-scoped
- **>500 LOC**: ⚠️ Requires detailed justification OR further decomposition

### Phase 3: Order Capabilities

**Ordering criteria:**
1. **Infrastructure dependencies**: Database/storage → Services → APIs
2. **Business value**: High-value capabilities first (demonstrate value early)
3. **Technical risk**: Foundation/risky components early (de-risk fast)
4. **Team parallelization**: Independent capabilities can be developed concurrently

**Create dependency graph:**
- Identify foundation capabilities (no dependencies)
- Map capability-to-capability dependencies
- Validate no circular dependencies
- Identify parallel execution opportunities

### Phase 4: Generate Capability Breakdown

1. **Fill capabilities.md template**:
   - Load CAPABILITIES_FILE (already created by script)
   - Fill each capability section:
     - Cap-001, Cap-002, ... Cap-00X
     - Scope description
     - Dependencies
     - Business value
     - Component breakdown with LOC estimates
     - Justification if >500 LOC
   - Generate dependency graph
   - Document implementation strategy

2. **Create capability subdirectories**:
   ```bash
   For each capability (Cap-001 to Cap-00X):
     - Create directory: specs/[feature-id]/cap-00X-[name]/
     - Copy capability-spec-template.md to cap-00X-[name]/spec.md
     - Populate with scoped requirements from parent spec
   ```

3. **Populate scoped specs**:
   - For each capability directory, fill spec.md:
     - Link to parent spec
     - Extract relevant FRs from parent
     - Define capability boundaries (what's IN, what's OUT)
     - List dependencies on other capabilities
     - Scope user scenarios to this capability
     - Estimate component breakdown
     - Validate 200-500 LOC budget

### Phase 5: Validation

**Decomposition quality checks:**
- [ ] All capabilities fall within 200-500 LOC (or justified)
- [ ] Each capability independently testable
- [ ] No circular dependencies
- [ ] All parent FRs assigned to a capability (no orphans)
- [ ] Total capabilities ≤10 (prevent over-decomposition)
- [ ] Foundation capabilities identified
- [ ] Parallel execution opportunities documented

**Capability independence checks:**
- [ ] Each capability delivers vertical slice (contract + model + service + tests)
- [ ] Each capability has clear interfaces with other capabilities
- [ ] Each capability can be merged independently (given dependencies met)
- [ ] Each capability has measurable acceptance criteria

## Output Artifacts

After decomposition, the feature directory should contain:

```
specs/[jira-123.feature-name]/
├── spec.md                      # Parent feature spec (unchanged)
├── capabilities.md              # Decomposition breakdown (NEW)
├── cap-001-[name]/              # First capability (NEW)
│   └── spec.md                 # Scoped to Cap-001
├── cap-002-[name]/              # Second capability (NEW)
│   └── spec.md                 # Scoped to Cap-002
├── cap-00X-[name]/              # Additional capabilities (NEW)
│   └── spec.md                 # Scoped to Cap-00X
```

## Next Steps

**For each capability (can be done in parallel where dependencies allow):**

1. **Plan**: `/plan --capability cap-001` → generates cap-001/plan.md (200-500 LOC scoped)
2. **Tasks**: `/tasks` → generates cap-001/tasks.md (8-15 tasks)
3. **Implement**: `/implement` → atomic PR (200-500 LOC)
4. **Repeat** for cap-002, cap-003, etc.

## Example Workflow

```bash
# Step 1: Create parent spec
/specify "Build user management system with auth, profiles, and permissions"
→ specs/proj-123.user-system/spec.md

# Step 2: Decompose into capabilities
/decompose
→ specs/proj-123.user-system/capabilities.md
→ specs/proj-123.user-system/cap-001-auth/spec.md
→ specs/proj-123.user-system/cap-002-profiles/spec.md
→ specs/proj-123.user-system/cap-003-permissions/spec.md

# Step 3: Implement each capability (can be parallel)
cd specs/proj-123.user-system/cap-001-auth/
/plan "Use FastAPI + JWT tokens"
→ cap-001-auth/plan.md (380 LOC estimate)

/tasks
→ cap-001-auth/tasks.md (10 tasks)

/implement
→ PR #1: "feat(user): authentication capability" (380 LOC) ✓

# Repeat for cap-002, cap-003...
```

## Troubleshooting

**"Too many capabilities (>10)":**
- Validate each is truly independent
- Consider merging tightly-coupled capabilities
- Review if feature scope is too large (might need multiple parent features)

**"Capabilities too small (<200 LOC)":**
- Merge with related capabilities
- Ensure not over-decomposing simple features

**"Circular dependencies detected":**
- Review capability boundaries
- Extract shared components to foundation capability
- Reorder dependencies to break cycles

**"Cannot estimate LOC accurately":**
- Start with rough estimates (will refine during /plan)
- Use similar features as reference
- Document uncertainty, adjust during planning phase

## Success Criteria

Decomposition is complete when:
- [ ] capabilities.md fully populated
- [ ] All capability directories created (cap-001/ through cap-00X/)
- [ ] Each capability has scoped spec.md
- [ ] All validation checks passed
- [ ] Dependency graph is acyclic
- [ ] Team understands implementation order
- [ ] Ready to run `/plan --capability cap-001`
