# Corporate Guidelines & Branch Configuration - Implementation Plan

**Status:** Phase 1 In Progress
**Created:** 2025-01-06
**Last Updated:** 2025-01-06
**Related Issue/PR:** [Add link when created]

---

## 📋 Executive Summary

**Goal:** Enable corporate customization of Spec Kit through configurable guidelines for:
1. Tech stack standards (scaffolding, libraries, patterns, security)
2. Branch naming conventions (prefix, Jira format, numbering)
3. Multi-stack project support (React + Java, etc.)

**Priority:** Constitution > Corporate Guidelines > Spec Kit Defaults

**Phased Implementation:**
- ✅ Phase 1: Foundation (guidelines templates + prompt integration) - **IN PROGRESS**
- ⏳ Phase 2: Branch configuration migration (make branch naming configurable)
- ⏳ Phase 3: Multi-stack support (load multiple guidelines contextually)
- 📋 Phase 4: Advanced features (deferred to IMPROVEMENTS.md)

---

## 🎯 Business Context

### The Problem

**Current State:**
- Jira format hardcoded: `C12345-7890`
- Branch pattern hardcoded: `feature/001-C12345-7890-shortname`
- Tech stack standards not documented or enforced
- Corporate tooling (Artifactory, corporate SDKs) not addressed
- Teams can't customize to their corporate standards

**Real-World Corporate Needs:**
- Companies use internal package registries (Artifactory, Nexus)
- Companies mandate corporate libraries (@acmecorp/ui-components, corporate SDKs)
- Companies have unique branch naming conventions
- Companies have different Jira/ticket formats (or no Jira)
- Companies have scaffolding commands (`npx @company/create-react-app`)
- Multi-stack projects are common (React frontend + Java backend)

**Example: Enterprise React Project**

Traditional (won't work in corporate):
```bash
npx create-react-app my-app  # ❌ Blocked by firewall
npm install react-router-dom  # ❌ Can't reach public npm
```

Corporate approach:
```bash
npx @acmecorp/create-react-app my-app --template=enterprise
npm config set registry https://artifactory.acmecorp.com/...
npm install @acmecorp/ui-components  # Mandatory corporate library
```

---

## 🏗️ Technical Architecture

### Guidelines Hierarchy

```
Priority: Constitution > Corporate Guidelines > Spec Kit Defaults

Constitution (.specify/memory/constitution.md):
  └─ High-level project principles
  └─ "Why we do things this way"
  └─ Non-negotiable rules (e.g., "No ORMs")
     │
     ├─ Corporate Guidelines (.guidelines/*.md)
     │   └─ Tech stack standards and tooling
     │   └─ "How we build with this stack"
     │   └─ Mandatory for compliance
     │      │
     │      └─ Spec Kit Defaults (built-in)
     │          └─ Public/standard approaches
     │          └─ Fallback when no guidelines exist
```

### File Structure

```
.guidelines/
├── README.md                          # How to customize guidelines
├── branching-guidelines.md            # Branch strategy documentation
├── branch-config.json                 # Branch pattern configuration (Phase 2)
├── reactjs-guidelines.md              # React: setup, libs, patterns
├── java-guidelines.md                 # Java: Spring Boot, Maven, etc.
├── dotnet-guidelines.md               # .NET: NuGet, Entity Framework, etc.
├── nodejs-guidelines.md               # Node.js: Express, npm, etc.
├── python-guidelines.md               # Python: pip, Django/Flask, etc.
└── examples/                          # Reference examples
    ├── enterprise-react-example.md
    └── enterprise-java-example.md
```

### Prompt Integration Points

| Prompt | Priority | What Guidelines Provide | Why |
|--------|----------|-------------------------|-----|
| **plan.md** | 🔴 CRITICAL | Scaffolding commands, corporate libraries, architecture patterns | Decisions made here affect everything |
| **implement.md** | 🔴 CRITICAL | Coding standards, import statements, component usage | Every line of code must follow guidelines |
| **analyze.md** | 🟡 IMPORTANT | Compliance rules, banned libraries, violations | Validate guideline adherence |
| **tasks.md** | 🟡 IMPORTANT | Task structure, file paths, setup tasks | Ensure consistency |
| clarify.md | 🟢 OPTIONAL | Tech stack questions, template selection | Only if ambiguous |

---

## 📅 Phase 1: Foundation (CURRENT)

### Status: ✅ IN PROGRESS

### Scope

**What we're building:**
1. ✅ Create guideline file templates (7 files)
2. ✅ Add guideline reading to plan.md (CRITICAL)
3. ✅ Add guideline reading to implement.md (CRITICAL)
4. ✅ Add guideline reading to analyze.md (IMPORTANT)
5. ✅ Add guideline reading to tasks.md (IMPORTANT)
6. ✅ Document in AGENTS.md (pre-commit guidelines)
7. ✅ Fix plan.md specs folder bug (BLOCKER)
8. ✅ Add to IMPROVEMENTS.md (track future work)

**What we're NOT building yet:**
- ❌ Branch configuration (Phase 2)
- ❌ Multi-stack detection (Phase 3)
- ❌ JSON parsing in scripts (Phase 2)

### Deliverables

**New Files:**
```
.guidelines/
├── README.md
├── branching-guidelines.md
├── reactjs-guidelines.md
├── java-guidelines.md
├── dotnet-guidelines.md
├── nodejs-guidelines.md
└── python-guidelines.md
```

**Modified Files:**
```
templates/commands/plan.md          # Add guideline reading section
templates/commands/implement.md     # Add guideline reading section
templates/commands/analyze.md       # Add compliance checking
templates/commands/tasks.md         # Add guideline awareness
AGENTS.md                           # Document guidelines usage
IMPROVEMENTS.md                     # Track Phase 2, 3, 4 items
```

### Guideline Template Structure

Each tech stack guideline follows this structure:

```markdown
# [Stack] Corporate Guidelines Template

Version: 1.0.0
Status: TEMPLATE - Customize before use
Priority: After Constitution, before defaults

---

## 🚀 Project Initialization (READ FIRST)

### Scaffolding Command
[How to create new projects - customize with corporate generator]

### Package Registry
[Configure Artifactory/Nexus - customize with corporate URLs]

---

## 📦 Corporate Libraries (MANDATORY)

### Required Dependencies
[List corporate packages: @yourcompany/ui-components, etc.]

### Banned Public Libraries
[List public packages to avoid: lodash → @yourcompany/utils]

---

## 🏛️ Architecture Patterns

### Folder Structure
[Define corporate folder conventions]

### Design Patterns
[Specify required patterns: MVC, Clean Architecture, etc.]

---

## 🔐 Security & Compliance

### Data Classification
[PII handling, encryption, audit logging]

### Dependency Security
[Vulnerability scanning, license compliance]

---

## 📚 Resources

- Internal Wiki: [URL]
- Support: [Email/Slack]
- Examples: [Link to example projects]
```

### Tech Stack Detection Strategy

**Priority order:**

1. **Auto-detect from codebase files:**
   ```
   package.json → Node.js/React (check dependencies for specifics)
   pom.xml → Java
   *.csproj → .NET
   requirements.txt → Python
   go.mod → Go
   ```

2. **Check constitution for declaration:**
   ```markdown
   TECH_STACK: java
   FRONTEND_STACK: reactjs
   ```

3. **Ask user in plan.md if unclear:**
   ```
   "I couldn't detect the tech stack. What are you using?
   - Java / .NET / React.js / Node.js / Python / Other"
   ```

### Prompt Integration Pattern

**Common pattern across all prompts:**

```markdown
## 🏢 Tech Stack Guidelines (MANDATORY)

**BEFORE PROCEEDING:**

1. **Detect tech stack:**
   - Check for indicator files (package.json, pom.xml, etc.)
   - Check constitution for TECH_STACK declaration
   - Ask user if still unclear

2. **Load guidelines:**
   - `.guidelines/<stack>-guidelines.md` (e.g., reactjs-guidelines.md)
   - If file exists, read it in FULL
   - If multiple stacks detected, load all relevant

3. **Apply guidelines:**
   - Follow scaffolding commands
   - Use corporate libraries (NOT public equivalents)
   - Apply architecture patterns
   - Follow security requirements

4. **Priority order:**
   - Constitution (highest)
   - Corporate guidelines (medium)
   - Spec Kit defaults (lowest)

**Verification:**
"✓ Loaded [stack] corporate guidelines - Following corporate standards"

**If guidelines don't exist:**
Proceed with public/standard approaches (fallback behavior)
```

### Bug Fix: plan.md Specs Folder

**Issue reported:**
- Claude 4.5: Creates `specs/001-C12345-7890-shortname` ✅ Correct
- Claude 4.0: Creates `specs/feature/001-C12345-7890-shortname` ❌ Wrong

**Root cause:**
- Plan.md might be creating folders manually instead of letting specify.md handle it
- Different model versions interpret instructions differently

**Fix strategy:**
1. Search plan.md for: mkdir, specs/, feature/, directory creation
2. Remove any manual directory creation logic
3. Add clear instruction: "DO NOT create specs folders - handled by specify.md"
4. Plan.md should only READ from existing specs folder

**Verification:**
- Test with Claude 4.0 and 4.5
- Ensure folder created without feature/ prefix
- Ensure consistent behavior across models

### Success Criteria

**Phase 1 is complete when:**
- ✅ All 7 guideline templates created with examples
- ✅ plan.md reads and applies guidelines
- ✅ implement.md reads and applies guidelines
- ✅ analyze.md validates guideline compliance
- ✅ tasks.md aware of guidelines
- ✅ Documentation in AGENTS.md
- ✅ Specs folder bug fixed
- ✅ Future phases tracked in IMPROVEMENTS.md
- ✅ Tested with Claude 4.0 and 4.5
- ✅ All markdownlint checks passing

### Confidence Level

**85%** - High confidence for Phase 1

**Risks:**
- ⚠️ Model interpretation differences (4.0 vs 4.5)
- ⚠️ Token usage increase with guideline loading
- ⚠️ Guidelines might conflict with each other

**Mitigation:**
- Test with multiple models
- Keep guidelines concise (summaries at top)
- Clear priority: Constitution > Guidelines > Defaults

---

## 📅 Phase 2: Branch Configuration (NEXT PR)

### Status: ⏳ PLANNED

### Scope

**What we're building:**
1. Create `branch-config.json` (machine-readable config)
2. Refactor `create-new-feature.sh` to read JSON config
3. Refactor `create-new-feature.ps1` to read JSON config
4. Make Jira format configurable (regex pattern)
5. Make Jira optional (for teams without Jira)
6. Support custom branch patterns
7. Backward compatibility (default to current pattern if no config)
8. Update specify.md documentation
9. Extensive testing with various patterns

**What we're NOT building yet:**
- ❌ Multi-stack detection (Phase 3)
- ❌ Dynamic regex validation (Phase 4)

### Branch Configuration Schema

**File:** `.guidelines/branch-config.json`

```json
{
  "version": "1.0",
  "branch_pattern": "feature/<num>-<jira>-<shortname>",
  "branch_prefix": "feature/",
  "number_format": {
    "digits": 3,
    "zero_padded": true
  },
  "jira": {
    "required": true,
    "format": "C12345-7890",
    "regex": "^C[0-9]{5}-[0-9]{4}$",
    "placeholder": "<jira>"
  },
  "separator": "-",
  "directory": {
    "includes_prefix": false,
    "base_path": "specs"
  }
}
```

**Custom Examples:**

Example 1: No Jira, no prefix
```json
{
  "branch_pattern": "<num>-<shortname>",
  "branch_prefix": "",
  "jira": { "required": false }
}
```
Result: `001-user-auth`

Example 2: Different ticket format
```json
{
  "branch_pattern": "feature/<num>-<jira>-<shortname>",
  "jira": {
    "required": true,
    "regex": "^PROJ-[0-9]{4}$"
  }
}
```
Result: `feature/001-PROJ-1234-user-auth`

Example 3: Custom prefix
```json
{
  "branch_pattern": "feat/<num>-<shortname>",
  "branch_prefix": "feat/"
}
```
Result: `feat/001-user-auth`

### Script Refactoring

**Bash script changes:**
```bash
# Load configuration
if [ -f ".guidelines/branch-config.json" ]; then
    # Parse JSON (requires jq or manual parsing)
    BRANCH_PREFIX=$(jq -r '.branch_prefix' .guidelines/branch-config.json)
    JIRA_REQUIRED=$(jq -r '.jira.required' .guidelines/branch-config.json)
    JIRA_REGEX=$(jq -r '.jira.regex' .guidelines/branch-config.json)
else
    # Fallback to defaults
    BRANCH_PREFIX="feature/"
    JIRA_REQUIRED=true
    JIRA_REGEX="^C[0-9]{5}-[0-9]{4}$"
fi

# Validate Jira if required
if [ "$JIRA_REQUIRED" = "true" ] && [ -n "$JIRA_NUMBER" ]; then
    if ! [[ "$JIRA_NUMBER" =~ $JIRA_REGEX ]]; then
        echo "Error: Jira format doesn't match pattern" >&2
        exit 1
    fi
fi
```

**PowerShell script changes:**
```powershell
# Load configuration
$configPath = ".guidelines/branch-config.json"
if (Test-Path $configPath) {
    $config = Get-Content $configPath | ConvertFrom-Json
    $branchPrefix = $config.branch_prefix
    $jiraRequired = $config.jira.required
    $jiraRegex = $config.jira.regex
} else {
    # Fallback to defaults
    $branchPrefix = "feature/"
    $jiraRequired = $true
    $jiraRegex = "^C[0-9]{5}-[0-9]{4}$"
}

# Validate Jira if required
if ($jiraRequired -and $JiraNumber) {
    if ($JiraNumber -notmatch $jiraRegex) {
        Write-Error "Jira format doesn't match pattern"
        exit 1
    }
}
```

### JSON Parsing Options

**Option 1: Require jq (RECOMMENDED)**
- Pros: Clean, reliable, well-tested
- Cons: Adds dependency
- Install: `sudo apt-get install jq` (Linux), `brew install jq` (Mac)

**Option 2: Manual bash parsing**
- Pros: No dependencies
- Cons: Error-prone, complex regex
- Use: `grep`, `sed`, `awk` to extract values

**Option 3: Python helper script**
- Pros: Reliable JSON parsing
- Cons: Adds Python dependency (usually available)

**Recommendation:** Option 1 (jq) with fallback to defaults if not available

### Backward Compatibility Strategy

**Ensure old projects still work:**

1. **If config doesn't exist:** Use current hardcoded defaults
2. **If jq not available:** Fall back to defaults, warn user
3. **If Jira not required:** Skip validation, allow empty
4. **Version check:** Add config version field for future migrations

```bash
# Graceful degradation
if [ ! -f ".guidelines/branch-config.json" ]; then
    # No config - use defaults
    BRANCH_PREFIX="feature/"
    JIRA_REGEX="^C[0-9]{5}-[0-9]{4}$"
elif ! command -v jq &> /dev/null; then
    # jq not available - warn and use defaults
    echo "Warning: jq not installed, using default branch pattern" >&2
    BRANCH_PREFIX="feature/"
    JIRA_REGEX="^C[0-9]{5}-[0-9]{4}$"
else
    # Load from config
    # ...
fi
```

### Testing Strategy

**Test cases:**
1. Default pattern (no config): `feature/001-C12345-7890-name`
2. No Jira pattern: `feature/001-name`
3. Custom Jira pattern: `feature/001-PROJ-1234-name`
4. No prefix pattern: `001-C12345-7890-name`
5. Custom prefix: `feat/001-C12345-7890-name`
6. Backward compat: Old projects without config still work

**Test with:**
- Claude 4.0
- Claude 4.5
- Bash script manually
- PowerShell script manually

### Success Criteria

**Phase 2 is complete when:**
- ✅ branch-config.json schema defined
- ✅ Bash script reads and applies config
- ✅ PowerShell script reads and applies config
- ✅ Jira validation uses custom regex
- ✅ Jira is optional when configured
- ✅ Backward compatibility verified
- ✅ Documentation updated
- ✅ All test cases pass
- ✅ Works with Claude 4.0 and 4.5

### Confidence Level

**70-75%** - Medium-high confidence

**Risks:**
- 🔴 JSON parsing complexity in bash
- 🟡 Regex escaping issues
- 🟡 Testing burden (many combinations)
- 🟡 Backward compatibility edge cases

**Mitigation:**
- Document jq requirement clearly
- Provide fallback for missing jq
- Extensive testing with various patterns
- Clear error messages

---

## 📅 Phase 3: Multi-Stack Support (FUTURE PR)

### Status: ⏳ PLANNED (Lower Priority)

### Scope

**What we're building:**
1. Detect multiple tech stacks in same project
2. Load multiple guideline files
3. Apply guidelines contextually (frontend vs backend)
4. File-to-stack mapping
5. Token usage optimization
6. Update tasks.md for multi-stack
7. Update analyze.md for multi-stack compliance

**Challenges:**
- How to determine which guideline applies to which file?
- Token usage (loading 2+ guideline files)
- Contextual application logic is complex
- Edge cases (shared code, utilities)

### Multi-Stack Detection

**Scenario 1: React + Java (common monorepo)**
```
project/
├── frontend/          # React
│   └── package.json
├── backend/           # Java
│   └── pom.xml
```

**Detection:**
```markdown
Detected stacks:
- reactjs (frontend/package.json)
- java (backend/pom.xml)

Load guidelines:
- .guidelines/reactjs-guidelines.md
- .guidelines/java-guidelines.md
```

**Contextual Application:**
```markdown
When planning frontend features:
  → Apply reactjs-guidelines.md

When planning backend features:
  → Apply java-guidelines.md

When planning full-stack features:
  → Apply both contextually
```

### File-to-Stack Mapping

**Strategy 1: Path-based (RECOMMENDED)**
```
frontend/* → React guidelines
backend/* → Java guidelines
shared/* → Both (or ask user)
```

**Strategy 2: File extension**
```
*.tsx, *.jsx → React guidelines
*.java → Java guidelines
*.py → Python guidelines
```

**Strategy 3: Declaration in plan.md**
```markdown
Tech Stacks:
- Frontend: React (guidelines: reactjs-guidelines.md)
- Backend: Java (guidelines: java-guidelines.md)

Path mapping:
- src/frontend/* → React
- src/backend/* → Java
```

### Token Usage Optimization

**Problem:** Loading 2+ guideline files = high token usage

**Solutions:**

1. **Summary sections:** Load only summary (first 50 lines)
2. **On-demand loading:** Load details only when needed
3. **Caching:** Load once, reference throughout session
4. **Selective loading:** Only load relevant sections per prompt

**Example optimization:**
```markdown
## Summary (First 30 lines - always load)
- Architecture: Spring Boot with Clean Architecture
- Database: PostgreSQL with JPA
- Testing: JUnit 5 + Mockito

## Detailed Guidelines (Load on demand)
[Full documentation...]
```

### Success Criteria

**Phase 3 is complete when:**
- ✅ Multi-stack detection working
- ✅ Multiple guidelines load correctly
- ✅ Contextual application logic clear
- ✅ File-to-stack mapping defined
- ✅ Token usage acceptable (<10% increase)
- ✅ Documentation clear
- ✅ Tested with common combinations (React+Java, React+Node, etc.)

### Confidence Level

**55-60%** - Medium confidence (DEFER until proven need)

**Risks:**
- 🔴 Contextual application is very complex
- 🔴 Ambiguous file-to-stack mapping
- 🔴 High token usage
- 🟡 Might confuse AI agents
- 🟡 Testing complexity exponentially increases

**Recommendation:**
- Add to IMPROVEMENTS.md
- Wait for real-world usage feedback from Phase 1 & 2
- Consider simpler approaches first
- Only implement if strong user demand

---

## 📅 Phase 4: Advanced Features (DEFERRED)

### Status: 📋 IMPROVEMENTS.md

**Deferred to future based on user feedback:**

1. **Constitution vs Guidelines conflict detection**
   - Analyze phase automatically flags conflicts
   - Show priority resolution
   - Confidence: 50%

2. **Dynamic regex pattern validation**
   - Test custom regex patterns before applying
   - Validate branch names match pattern
   - Confidence: 60%

3. **Guideline versioning**
   - Track guideline file versions
   - Detect when code written under old guidelines
   - Migration support
   - Confidence: 55%

4. **Full CI/CD integration examples**
   - Jenkins pipeline examples
   - GitHub Actions examples
   - GitLab CI examples
   - Confidence: 70%

5. **Compliance scoring system**
   - Score projects on guideline adherence
   - Dashboard/report generation
   - Trend tracking
   - Confidence: 45%

**Add all to IMPROVEMENTS.md with rationale and effort estimates**

---

## 🔄 Session Continuity

### Context Required for Future Sessions

**Essential context to provide when resuming:**

1. **What phase we're on:** "Continue Phase 2: Branch Configuration"
2. **What was completed:** "Phase 1 is merged (PR #XXX)"
3. **Current state:** "Branch naming is hardcoded, need to make configurable"
4. **This document:** "Read GUIDELINES-IMPLEMENTATION-PLAN.md for full context"
5. **Related files:** Point to Phase 1 PR for implementation examples

### Resume Prompts

#### **Resume Prompt for Phase 2: Branch Configuration**

```
I want to continue implementing the Corporate Guidelines feature for spec-kit.

CONTEXT:
- Phase 1 is complete and merged (PR #XXX)
- Guideline templates are created in .guidelines/
- Prompts now read and apply guidelines
- Document: Read /GUIDELINES-IMPLEMENTATION-PLAN.md for full context

CURRENT TASK: Phase 2 - Branch Configuration
- Make branch naming patterns configurable
- Move hardcoded Jira format to branch-config.json
- Refactor create-new-feature.sh and .ps1 to read JSON config
- Support optional Jira, custom prefixes, custom patterns
- Maintain backward compatibility

SCOPE: See "Phase 2" section in GUIDELINES-IMPLEMENTATION-PLAN.md

REQUIREMENTS:
1. Create .guidelines/branch-config.json with schema
2. Update create-new-feature.sh to parse JSON (use jq or fallback)
3. Update create-new-feature.ps1 to parse JSON
4. Make Jira validation use config regex
5. Support Jira optional mode
6. Default to current pattern if no config exists
7. Update specify.md documentation
8. Test with various patterns

QUESTIONS:
- Should we require jq for bash JSON parsing, or implement fallback?
- How strict should backward compatibility be?

Please analyze Phase 2 requirements and start implementation.
```

#### **Resume Prompt for Phase 3: Multi-Stack Support**

```
I want to continue implementing the Corporate Guidelines feature for spec-kit.

CONTEXT:
- Phase 1 is complete (guideline templates + prompt integration)
- Phase 2 is complete (branch configuration is now customizable)
- Document: Read /GUIDELINES-IMPLEMENTATION-PLAN.md for full context

CURRENT TASK: Phase 3 - Multi-Stack Support
- Support projects with multiple tech stacks (React + Java, etc.)
- Load multiple guideline files
- Apply guidelines contextually based on file paths
- Optimize token usage

SCOPE: See "Phase 3" section in GUIDELINES-IMPLEMENTATION-PLAN.md

REQUIREMENTS:
1. Detect multiple tech stacks in same project
2. Load multiple .guidelines/*.md files
3. Define file-to-stack mapping strategy
4. Apply guidelines contextually (frontend code → React guidelines)
5. Optimize token usage (summaries, on-demand loading)
6. Update plan.md, implement.md, tasks.md for multi-stack
7. Test with common combinations

QUESTIONS:
- How should we map files to stacks (path-based? extension-based?)
- What's acceptable token usage increase?
- Should we implement this or defer based on Phase 2 feedback?

Please analyze Phase 3 requirements and provide recommendations before implementing.
```

### How to Use Resume Prompts

**Step 1: Start new session**
- Open new Claude Code session or create new PR branch

**Step 2: Provide context**
- Copy the appropriate resume prompt above
- Paste it at the start of your conversation

**Step 3: Reference this document**
- Agent will read GUIDELINES-IMPLEMENTATION-PLAN.md
- Agent will understand current state and requirements

**Step 4: Clarify any changes**
- If requirements changed since last session, mention them
- If Phase 1/2 had issues, describe them
- If user feedback suggests changes, share it

**Step 5: Begin implementation**
- Agent will analyze requirements
- Agent will ask clarifying questions
- Agent will implement according to plan

**Example full session start:**
```
[Paste Resume Prompt for Phase 2]

Additional context:
- Phase 1 PR #123 was merged yesterday
- User feedback: Teams want even more flexible branch patterns
- Change request: Also support date-based branch numbers (20250106-001)

Please review Phase 2 requirements and let me know if we should adjust scope.
```

---

## 📊 Success Metrics

### Phase 1 Success Metrics

**Functional:**
- ✅ Guideline templates created and documented
- ✅ Prompts read guidelines when they exist
- ✅ Prompts fall back gracefully when guidelines missing
- ✅ Specs folder bug fixed (consistent across models)

**Quality:**
- ✅ All markdownlint checks passing
- ✅ Documentation clear in AGENTS.md
- ✅ Examples provided in guideline templates
- ✅ Tested with Claude 4.0 and 4.5

**User Experience:**
- ✅ Teams can customize guidelines
- ✅ Defaults work out-of-box (no config needed)
- ✅ Clear priority: Constitution > Guidelines > Defaults
- ✅ Error messages helpful when guidelines malformed

### Phase 2 Success Metrics

**Functional:**
- ✅ branch-config.json schema defined
- ✅ Scripts read config and apply patterns
- ✅ Jira format customizable
- ✅ Jira can be optional
- ✅ Backward compatibility maintained

**Quality:**
- ✅ All test cases pass
- ✅ Works with and without jq
- ✅ Clear error messages for config issues
- ✅ Documentation updated

**User Experience:**
- ✅ Teams can use their branch patterns
- ✅ Teams without Jira can disable it
- ✅ Old projects still work without changes

### Phase 3 Success Metrics

**Functional:**
- ✅ Multi-stack detection working
- ✅ Multiple guidelines load correctly
- ✅ Contextual application clear
- ✅ Token usage acceptable

**Quality:**
- ✅ File-to-stack mapping documented
- ✅ Edge cases handled (shared code)
- ✅ Tested with common combinations

**User Experience:**
- ✅ Full-stack projects well supported
- ✅ Performance acceptable (no major slowdown)
- ✅ Clear documentation for setup

---

## 🚨 Known Issues & Risks

### Current Issues (Phase 1)

**Issue 1: Plan.md Specs Folder Bug**
- Status: 🔴 BLOCKER - Must fix in Phase 1
- Description: Claude 4.0 creates `specs/feature/001-...` (wrong), 4.5 creates `specs/001-...` (correct)
- Impact: Inconsistent folder structure across model versions
- Fix: Remove manual folder creation from plan.md, document that specify.md handles it

**Issue 2: Model Interpretation Differences**
- Status: 🟡 MONITOR
- Description: Different Claude versions interpret same prompt differently
- Impact: Need to test with multiple models
- Mitigation: Clear, explicit instructions; test with 4.0 and 4.5

### Risks (All Phases)

**Risk 1: Complexity Overload** 🔴
- Constitution + AGENTS.md + Guidelines = 3 instruction layers
- AI agents might get confused
- Token usage increases significantly
- Mitigation: Keep guidelines concise, clear priority order, summaries at top

**Risk 2: Backward Compatibility** 🟡
- Old projects must still work
- Config changes might break workflows
- Mitigation: Always check if file exists, default to current behavior

**Risk 3: Maintenance Burden** 🟡
- More files to keep in sync
- Teams might customize incorrectly
- Support complexity increases
- Mitigation: Excellent docs, validation in analyze.md, community support

**Risk 4: JSON Parsing in Bash** 🟡 (Phase 2)
- Bash JSON parsing is tricky without jq
- Regex escaping issues
- Mitigation: Require jq, provide clear installation docs, fallback to defaults

**Risk 5: Multi-Stack Complexity** 🔴 (Phase 3)
- File-to-stack mapping ambiguous
- Contextual application logic complex
- High token usage
- Mitigation: Start simple (path-based), defer if not needed

---

## 📚 References

### Related Documents

- **IMPROVEMENTS.md** - Future enhancements tracking
- **AGENTS.md** - Pre-commit guidelines, general practices
- **.guidelines/README.md** - How to customize guidelines (created in Phase 1)
- **branching-guidelines.md** - Branch strategy documentation (Phase 1)
- **branch-config.json** - Branch configuration (Phase 2)

### Related Issues/PRs

- Phase 1 PR: [Add link when created]
- Phase 2 PR: [Add link when created]
- Phase 3 PR: [Add link when created]
- Related issue: [Add link if exists]

### External Resources

- Markdownlint docs: https://github.com/DavidAnson/markdownlint
- jq documentation: https://stedolan.github.io/jq/
- JSON schema: https://json-schema.org/

---

## 🔄 Change Log

### 2025-01-06 - Initial Plan Created
- Documented full 4-phase implementation plan
- Created resume prompts for Phase 2 and 3
- Defined success criteria and risks
- Ready to begin Phase 1 implementation

### [Future Date] - Phase 1 Complete
- [Add summary of what was implemented]
- [Add link to PR]
- [Add any deviations from plan]
- [Add lessons learned]

### [Future Date] - Phase 2 Started
- [Add context from Phase 1 completion]
- [Add any scope changes]
- [Add new risks discovered]

---

**END OF IMPLEMENTATION PLAN**

*This document is the single source of truth for the Corporate Guidelines implementation.*
*Update this document as phases complete and new information is discovered.*
