# Template File Synchronization Required

## Status: PARTIAL - Manual Sync Needed

The file `.github/prompts/speckit.bicep.prompt.md` has been successfully updated with comprehensive enhancements, but the template file `templates/commands/speckit.bicep.md` still needs to be synchronized.

## Changes Made to Prompt File

✅ **COMPLETED** in `.github/prompts/speckit.bicep.prompt.md`:

### 1. Comprehensive Pre-Generation Questions (Added before line 321)
- **Location**: Inserted between directory structure and "Step 1: Create Generation Plan"
- **Size**: ~300 lines
- **Content**:
  - Critical checkpoint: "DO NOT Generate Templates Yet!"
  - Pre-generation checklist
  - Question Set 1: Deployment Strategy & Ev2 (ALWAYS ask about Ev2)
  - Question Set 2: Scale & Redundancy (user count, scaling, availability zones)
  - Question Set 3: Security & Identity (MSI, private endpoints, secrets management)
  - Question Set 4: Environment & Cost (environments, cost optimization)
  - Configuration summary and confirmation

### 2. Enhanced Design Principles
- **Location**: Replaced existing "Design Principles" section
- **Content**:
  - Core Philosophy: "Simplicity First"
  - Simplicity Guidelines (PREFER/AVOID/DOCUMENT)
  - Simplicity Checklist
  - Example: Simple vs. Complex code comparison

### 3. Structured Task Plan with Priorities
- **Location**: Replaced "Resource Modules to Generate" and "Resource Dependencies" sections
- **Content**:
  - Priority Matrix (HIGH/MEDIUM/LOW with rationale)
  - Task Dependency Graph (visual ASCII diagram)
  - Critical Path identification
  - Task Complexity Assessment
  - Detailed dependency rules

### 4. Validation Gates in TODO.md Template
- **Location**: Replaced "Step 2: Create Progress Tracker" section
- **Size**: ~350 lines
- **Content**:
  - Enhanced TODO.md with validation gates after EACH template
  - Validation gate structure:
    - Syntax check (az bicep build)
    - Security review
    - Best practices check
    - Simplicity check
    - Critique/review section
    - STATUS: BLOCKED/WARNINGS/PASS
  - Validation Gate Rules (NO progression until PASS)
  - Validation Results Log
  - Examples for networking, key-vault, storage, app-service modules

### 5. GitHub Copilot Instructions Integration
- **Location**: Added after Infrastructure Report section, before final recommendations
- **Size**: ~200 lines
- **Content**:
  - Detection workflow for `.github/copilot-instructions.md`
  - Offer to update existing file
  - Offer to create new file if doesn't exist
  - Complete infrastructure section template with:
    - Azure Resources table
    - Deployment Strategy
    - Security Patterns
    - Naming Conventions
    - Bicep Templates structure
    - Deployment Commands
    - Common Infrastructure Tasks
  - Integration timing guidelines

## Required Synchronization Steps

### Method 1: Copy Entire Sections (Recommended)

1. **Open both files**:
   - Source: `.github/prompts/speckit.bicep.prompt.md`
   - Target: `templates/commands/speckit.bicep.md`

2. **Find insertion point in target file**:
   - Line ~320: `### 📋 Step 1: Create Generation Plan (README.md)`

3. **Copy comprehensive questions section**:
   - From source file lines 320-620 (the entire "CRITICAL: DO NOT Generate Templates Yet!" through "AFTER Confirmation: Create Structured Plan")
   - Insert BEFORE line 321 in target file

4. **Replace Design Principles section**:
   - Find "## 🎨 Design Principles" in target file
   - Replace with enhanced version from source file (includes simplicity guidelines)

5. **Replace Resource Modules/Dependencies sections**:
   - Find "## 📝 Resource Modules to Generate" in target file
   - Replace through "## 🔗 Resource Dependencies" with new structured planning section from source file

6. **Replace TODO.md template section**:
   - Find "### ✅ Step 2: Create Progress Tracker (TODO.md)" in target file
   - Replace entire section with validation gates version from source file

7. **Add GitHub Copilot Integration section**:
   - Find "**Critical Timing Requirements**:" section in target file
   - After this section, add the entire "## 🤖 GitHub Copilot Instructions Integration" section from source file

### Method 2: Use Multi-Replace Tool

Create a series of `replace_string_in_file` calls to sync each major section:

1. Pre-generation questions
2. Design principles
3. Structured planning
4. TODO.md with validation gates
5. Copilot integration

### Method 3: Regenerate Template File

If easier, you could:
1. Copy the ENTIRE `.github/prompts/speckit.bicep.prompt.md` file
2. Replace `templates/commands/speckit.bicep.md` with it
3. Then perform any template-specific adjustments if needed

## Verification Steps

After synchronization, verify:

1. **Both files have identical sections**:
   - Comprehensive pre-generation questions
   - Enhanced design principles with simplicity
   - Structured task plan with priorities
   - TODO.md with validation gates
   - GitHub Copilot integration

2. **Line count comparison**:
   - Prompt file: ~2186 lines
   - Template file after sync: Should be similar (~2100-2200 lines)

3. **Key phrases present in both files**:
   - "CRITICAL: DO NOT Generate Templates Yet!"
   - "MANDATORY Pre-Generation Questions"
   - "Simplicity First"
   - "🚦 VALIDATION GATE"
   - "GitHub Copilot Instructions Integration"

## Documentation Updates Still Needed

After template file is synced, update:

1. **CHANGELOG.md**: Add v0.0.22 entry with new features
2. **pyproject.toml**: Bump version to 0.0.22
3. **docs/bicep-generator/PROJECT-SUMMARY.md**: Update line counts and features
4. **EV2-INTEGRATION-SUMMARY.md**: Emphasize "always ask about Ev2"
5. **README.md**: Mention enterprise-grade planning capabilities

## Summary of User Request Fulfillment

✅ **COMPLETED**:
- Comprehensive pre-generation questions covering Ev2/SDP, users, regions, redundancy, availability zones, load balancing, MSI
- ALWAYS ask about Ev2 (not conditional on detection)
- Structured plan with task priorities and dependencies
- Validation gate after EACH template (blocks progression until error-free)
- GitHub Copilot instructions integration workflow
- Emphasis on simplicity and clean implementation

⏳ **PENDING**:
- Synchronize template file `templates/commands/speckit.bicep.md`
- Update documentation files (CHANGELOG, version, etc.)

## Estimated Time

- Template file sync: 15-20 minutes (manual copy/paste)
- Documentation updates: 10 minutes
- Testing: 5 minutes
- **Total**: ~35 minutes

## Priority

**HIGH** - The prompt file is updated and working, but the template file must be synced for consistency across release packages.
