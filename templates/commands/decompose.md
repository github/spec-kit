---
description: Decompose parent feature spec into atomic capabilities (400-1000 LOC total each)
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
| Component | Implementation LOC | Test LOC | Notes |
|-----------|-------------------|----------|-------|
| Models | 50-100 | 50-80 | Entities + validation tests |
| Services | 100-200 | 100-150 | CRUD + business logic + service tests |
| API/CLI | 50-100 | 50-100 | Endpoints/commands + contract tests |
| Integration | N/A | 50-100 | E2E scenarios |

**Target totals per capability:**
- Implementation: 200-400 LOC
- Tests: 200-400 LOC
- **Total: 400-800 LOC**

**Validation rules:**
- **<400 LOC total**: Too small, consider merging with related capability
- **400-600 LOC**: ✓ Ideal range (200-300 impl + 200-300 tests)
- **600-800 LOC**: ✓ Acceptable, well-scoped (300-400 impl + 300-400 tests)
- **800-1000 LOC**: ✓ Acceptable with justification (400-500 impl + 400-500 tests)
- **>1000 LOC OR impl >500 OR tests >500**: ⚠️ Requires detailed justification OR further decomposition

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

1. **Fill capabilities.md template using UTF-8 encoding**:
   - Load CAPABILITIES_FILE (already created by script)
   - Fill each capability section:
     - Cap-001, Cap-002, ... Cap-00X
     - Scope description
     - Dependencies
     - Business value
     - Component breakdown with implementation and test LOC estimates
     - Justification if impl >500 OR tests >500 OR total >1000
   - Generate dependency graph
   - Document implementation strategy

2. **Create capability subdirectories**:
   ```bash
   For each capability (Cap-001 to Cap-00X):
     - Create directory: specs/[feature-id]/cap-00X-[name]/
     - Copy capability-spec-template.md to cap-00X-[name]/spec.md
     - Populate with scoped requirements from parent spec
   ```

3. **Populate scoped specs using UTF-8 encoding**:
   - For each capability directory, fill spec.md:
     - Link to parent spec
     - Extract relevant FRs from parent
     - Define capability boundaries (what's IN, what's OUT)
     - List dependencies on other capabilities
     - Scope user scenarios to this capability
     - Estimate component breakdown
     - Validate dual LOC budget (impl ≤500, tests ≤500, total ≤1000)

### Phase 5: Validation

**Decomposition quality checks:**
- [ ] All capabilities: impl ≤500, tests ≤500, total ≤1000 (or justified)
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

1. **Plan**: `/plan --capability cap-001` → generates cap-001/plan.md (400-1000 LOC scoped)
2. **Tasks**: `/tasks` → generates cap-001/tasks.md (8-15 tasks)
3. **Implement**: `/implement` → atomic PR (400-1000 LOC total)
4. **Repeat** for cap-002, cap-003, etc.

## Example Workflow

```bash
# Step 1: Create parent spec (on branch: username/proj-123.user-system)
/specify "Build user management system with auth, profiles, and permissions"
→ Creates branch: username/proj-123.user-system
→ specs/proj-123.user-system/spec.md

# Step 2: Decompose into capabilities (on parent branch)
/decompose
→ specs/proj-123.user-system/capabilities.md
→ specs/proj-123.user-system/cap-001-auth/spec.md
→ specs/proj-123.user-system/cap-002-profiles/spec.md
→ specs/proj-123.user-system/cap-003-permissions/spec.md

# Step 3: Implement Cap-001 (creates NEW branch)
/plan --capability cap-001 "Use FastAPI + JWT tokens"
→ Creates branch: username/proj-123.user-system-cap-001
→ cap-001-auth/plan.md (380 LOC estimate)

/tasks
→ cap-001-auth/tasks.md (10 tasks)

/implement
→ Implement on cap-001 branch (380 LOC)

# Create atomic PR to main
gh pr create --base main --title "feat(auth): Cap-001 authentication capability"
→ PR #1: cap-001 branch → main (380 LOC) ✓ MERGED

# Step 4: Back to parent, sync, implement Cap-002
git checkout username/proj-123.user-system
git pull origin main

/plan --capability cap-002 "Use FastAPI + Pydantic models"
→ Creates branch: username/proj-123.user-system-cap-002
→ cap-002-profiles/plan.md (320 LOC estimate)

/tasks → /implement
→ PR #2: cap-002 branch → main (320 LOC) ✓ MERGED

# Step 5: Repeat for cap-003...
# Each capability = separate branch + atomic PR (400-1000 LOC total)
```

**Key Points:**
- Parent branch holds all capability specs
- Each capability gets its own branch from parent
- PRs go from capability branch → main (not to parent)
- After merge, sync parent with main before next capability

## Troubleshooting

**"Too many capabilities (>10)":**
- Validate each is truly independent
- Consider merging tightly-coupled capabilities
- Review if feature scope is too large (might need multiple parent features)

**"Capabilities too small (<400 LOC total)":**
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
