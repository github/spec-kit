# Spec-Kit Three-Tier Upgrade (v0.2.0)

## Overview

Spec-Kit has been upgraded from a two-tier system (Specification → Implementation) to a **three-tier hierarchy** aligned with industry standards for product development. This upgrade adds strategic product planning capabilities while maintaining the framework's core principles.

## What Changed

### Three-Tier Hierarchy

**Tier 1: Product Vision (NEW)**
- **Command**: `/product-vision`
- **Output**: `docs/product-vision.md`
- **Purpose**: Strategic product planning (WHAT/WHY only, ZERO technical content)
- **Contains**: Problem statement, personas, success metrics, product-wide NFRs
- **When to use**: Complex products, 0-to-1 development, multi-feature products
- **When to skip**: Simple tools, single-feature projects

**Tier 2: Feature Specification (ENHANCED)**
- **Command**: `/specify` (existing, now enhanced)
- **Output**: `specs/{jira-id.feature-name}/spec.md`
- **Purpose**: Requirements + Constraints (Industry Tier 2 alignment)
- **New sections**: Non-Functional Requirements, Technical Constraints
- **New behavior**: Inherits from product vision and system architecture when they exist

**Tier 3: Implementation Plan (ENHANCED)**
- **Command**: `/plan` (existing, now enhanced)
- **Output**: `specs/{jira-id.feature-name}/plan.md` + `docs/system-architecture.md`
- **Purpose**: Architecture decisions (HOW to build)
- **New sections**: Architecture Impact Assessment, System Architecture Update
- **New behavior**: Tracks architecture evolution with semantic versioning

## New Files Created

### Templates

1. **`templates/product-vision-template.md`**
   - Strategic PRD template for Tier 1
   - Enforces zero technical content through validation gates
   - Sections: Problem, Personas, Success Metrics, Product-wide NFRs, Business Risks

2. **`templates/system-architecture-template.md`**
   - Tracks system architecture evolution across all features
   - Semantic versioning (v1.0.0, v1.1.0, etc.)
   - Architecture Decision Records (ADRs)
   - Evolution history with impact tracking

3. **`templates/commands/product-vision.md`**
   - Command definition for `/product-vision`
   - Parallel research agents for market/user/competitive analysis
   - Validation gates to prevent technical content

### Scripts

4. **`scripts/bash/setup-product-vision.sh`**
   - Creates `docs/` directory if needed
   - Copies product-vision-template.md to `docs/product-vision.md`
   - Returns JSON with file path

5. **`scripts/powershell/setup-product-vision.ps1`**
   - PowerShell version of setup script
   - Cross-platform support for Windows users

## Modified Files

### Templates

1. **`templates/spec-template.md`**
   - **Added**: Product Context input reference (`docs/product-vision.md`)
   - **Added**: System Architecture input reference (`docs/system-architecture.md`)
   - **Added**: Phase 0 context loading in execution flow
   - **Added**: Non-Functional Requirements section (performance, security, scalability, availability, compliance)
   - **Added**: Technical Constraints section (what exists vs what to build)
   - **Added**: Source tracking for inherited vs feature-specific requirements

2. **`templates/commands/specify.md`**
   - **Added**: Phase 0: Context Loading (before research)
   - **Added**: Product context check (inherits personas, product-wide NFRs)
   - **Added**: System architecture check (notes technology and integration constraints)
   - **Enhanced**: Research phase now skips market research if product vision exists

3. **`templates/plan-template.md`**
   - **Added**: Phase -1: Architecture Context Loading
   - **Added**: Architecture Impact Assessment (3 levels: Work Within, Extend, Refactor)
   - **Added**: System Architecture Update section with detailed checklists
   - **Added**: Semantic versioning for architecture evolution
   - **Enhanced**: Technology Choices section now links decisions to requirements

### Documentation

4. **`spec-driven.md`**
   - **Added**: Comprehensive "The Three-Tier Hierarchy" section
   - **Added**: Workflow integration examples (greenfield, brownfield, evolution)
   - **Added**: Clear boundaries between tiers (requirements vs decisions vs constraints)
   - **Enhanced**: Documented inheritance patterns (specs inherit from vision, plans inherit from architecture)

5. **`README.md`**
   - **Updated**: Get Started section (added optional Step 2 for product vision)
   - **Updated**: Development Phases table (mentions product vision and architecture establishment)
   - **Added**: Example Workflows section (greenfield with/without vision, brownfield)
   - **Updated**: Detailed process walkthrough (mentions `/product-vision` command)

## Key Concepts

### Strict Separation of Concerns

**Product Vision** (Tier 1):
- Strategic ONLY
- ✅ Problem statement, personas, success metrics
- ❌ NO technology choices, NO architecture, NO APIs

**Feature Specification** (Tier 2):
- Requirements + Constraints
- ✅ Functional requirements, non-functional requirements
- ✅ "Must integrate with existing PostgreSQL" (constraint - what exists)
- ❌ "Use PostgreSQL for storage" (decision - belongs in Tier 3)

**Implementation Plan** (Tier 3):
- Architecture decisions
- ✅ Technology choices, architecture patterns, component design
- ✅ Links decisions to requirements from Tier 2

### Architecture Evolution

**Three Impact Levels**:
1. **Level 1 - Work Within**: Uses existing architecture (no version change)
2. **Level 2 - Extend**: Adds components (minor version bump: v1.2.0 → v1.3.0)
3. **Level 3 - Refactor**: Breaking changes (major version bump: v1.x → v2.0.0)

**Semantic Versioning for Architecture**:
- First feature establishes `docs/system-architecture.md v1.0.0`
- Extensions (new components): minor version bump
- Breaking changes (structural refactor): major version bump
- Evolution history tracked in system-architecture.md

### Inheritance Patterns

**Product Vision → Feature Specs**:
- Specs inherit personas from product vision
- Specs inherit product-wide NFRs from product vision
- Specs add feature-specific requirements

**System Architecture → Feature Plans**:
- Plans inherit technology constraints from system architecture
- Plans inherit integration requirements from existing features
- Plans add feature-specific architecture decisions
- Plans update system architecture with evolution entries

## Migration Guide

### For Existing Projects

**If you have existing specs** (created before this upgrade):
1. No immediate action required - existing specs still work
2. Consider creating `docs/product-vision.md` if building a complex product
3. Consider creating `docs/system-architecture.md` to track architecture evolution
4. New features will inherit from these documents when they exist

**If starting a new project**:
1. **Complex product**: Start with `/product-vision`, then `/specify`, then `/plan`
2. **Simple tool**: Skip `/product-vision`, use `/specify` → `/plan` → `/tasks`
3. First `/plan` will establish `docs/system-architecture.md v1.0.0`

### Workflow Selection

**Use Product Vision when**:
- Building a 0-to-1 product with multiple features
- Need shared personas across features
- Have product-wide non-functional requirements
- Building for multiple user types

**Skip Product Vision when**:
- Building a single-feature tool
- Prototyping or experimenting
- Adding a feature to an existing product with established vision

## Benefits

### Strategic Alignment
- Product vision ensures features align with business goals
- Personas inform feature requirements
- Product-wide NFRs ensure consistency

### Architecture Tracking
- System architecture documents technology decisions over time
- Semantic versioning shows evolution and impact
- Migration planning for breaking changes

### Industry Alignment
- Tier 2 specs now include NFRs (industry standard PRD)
- Clear separation of requirements, constraints, and decisions
- ADRs for architecture decision documentation

### Reduced Duplication
- Product vision defines personas once, features inherit
- System architecture documents tech stack once, features reference
- Product-wide NFRs defined once, features extend

## Backward Compatibility

✅ **Fully backward compatible**:
- Existing `/specify` command works unchanged (new sections optional)
- Existing `/plan` command works unchanged (architecture tracking optional)
- New `/product-vision` command is optional
- No breaking changes to existing workflows

## Questions?

- **Q: Do I need to create product vision for every project?**
  - A: No - it's optional. Use it for complex products with multiple features.

- **Q: What if I already have specs without product vision?**
  - A: They work fine. Add product vision later if needed.

- **Q: Do I need to migrate existing specs?**
  - A: No - existing specs work as-is. New features can optionally inherit from product vision.

- **Q: When is system-architecture.md created?**
  - A: Automatically by the first `/plan` execution (establishes v1.0.0).

## Version

This upgrade is part of spec-kit **v0.2.0**.

---

*For detailed examples and workflows, see [`spec-driven.md`](./spec-driven.md)*
