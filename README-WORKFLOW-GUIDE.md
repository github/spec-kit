# Spec Kit Workflow Guide 🏗️
*Building Software Like a Master Architect*

## What is This Thing?

Imagine you want to build a skyscraper. You wouldn't just grab some steel beams and start welding, right? You'd hire a visionary architect to create detailed blueprints, a structural engineer to ensure everything is sound, and skilled construction crews to follow the plans precisely.

**The Enhanced Spec Kit Framework works exactly the same way for building software.**

Instead of jumping straight into coding and hoping it works, you use a systematic three-phase process with specialized "AI construction specialists" who follow detailed specifications to build your software features correctly the first time.

---

## The Construction Crew Analogy 🏢

Think of the Spec Kit commands as different specialists in a world-class construction company:

### **🎯 The Visionary Architect** (`/specify`)
- **What they do:** Take your rough idea ("I need user authentication") and create comprehensive blueprints with detailed requirements, user scenarios, and implementation context
- **Enhancement:** Now includes deep research phase that analyzes existing patterns and gathers external best practices
- **When to use:** Starting any new feature or major change
- **Example:** "User login with social media integration" → Complete feature specification with context engineering

### **📐 The Master Planner** (`/plan`)
- **What they do:** Transform specifications into detailed technical implementation plans with validation gates and quality checkpoints
- **Enhancement:** Includes Implementation Blueprint with validation gates to prevent failures
- **When to use:** After specifications are complete and approved
- **Example:** Takes auth specification → Technical architecture with data models, APIs, and quality gates

### **📋 The Project Manager** (`/tasks`)
- **What they do:** Break down implementation plans into specific, actionable tasks with clear success criteria
- **When to use:** After planning phase is complete and validated
- **Example:** Takes implementation plan → Numbered task list ready for execution

### **🗺️ The Site Surveyor** (`/prime-core`)
- **What they do:** Survey the entire codebase "construction site" to understand existing structures, patterns, and constraints
- **When to use:** Start of every session or when switching contexts
- **Example:** Analyzes project structure, identifies patterns, loads constitutional principles

### **🔍 The Building Inspector** (`/review`)
- **What they do:** Thoroughly inspect all work for quality, safety, and compliance with building codes (Spec Kit constitution)
- **When to use:** Before committing code, during pull requests, or periodic quality audits
- **Example:** Reviews code changes for constitutional compliance, security, and performance

### **✅ The Quality Control Manager** (`/validate`)
- **What they do:** Run comprehensive validation gates to ensure each phase meets quality standards before proceeding
- **When to use:** At the end of each phase or when quality assurance is needed
- **Example:** Validates specifications are complete, plans meet constitutional requirements

### **🔧 The Problem Solver** (`/debug`)
- **What they do:** Systematically diagnose and resolve complex issues using root cause analysis
- **When to use:** When facing mysterious bugs, performance issues, or system failures
- **Example:** "Users can't login after password reset" → Systematic debugging with solution

### **📝 The Documentation Clerk** (`/smart-commit`)
- **What they do:** Analyze changes and create intelligent git commits that tell the story of development
- **When to use:** Before committing any code changes
- **Example:** Analyzes staged changes → Properly formatted conventional commit with context

---

## The Magic: The Three-Phase Process 🔗

**This is the KEY part that makes everything work!**

Unlike traditional development that jumps straight to coding, Spec Kit follows a proven three-phase construction process:

```
🎯 Phase 1: SPECIFICATION (The Blueprint)
   ↓ (Specification gets passed to...)
📐 Phase 2: PLANNING (The Construction Plan)
   ↓ (Plan gets passed to...)
📋 Phase 3: EXECUTION (The Building Process)
```

**CRITICAL:** Each phase validates and builds upon the previous phase - they're not isolated steps!

---

## The Enhanced Three-Phase Workflow 📋

### **Phase 1: Specification - Creating the Blueprint**

**The Enhanced Research-Driven Process:**

```bash
# Step 1: Load project context (always start here)
/prime-core

# Step 2: Create comprehensive specification with research
/specify "user authentication system with social media integration and role-based permissions"
```

**What happens behind the scenes:**
- **Research Phase:** AI agents search the codebase for similar patterns
- **External Research:** Best practices and gotchas are researched and documented
- **Context Engineering:** All necessary implementation context is gathered
- **Requirements Definition:** Clear, testable requirements are created
- **Validation:** Context Completeness Check ensures implementability

**Output:** `specs/PROJ-123.user-auth/spec.md` with comprehensive specification

---

### **Phase 2: Planning - Creating the Construction Plan**

```bash
# Step 3: Create detailed implementation plan with validation gates
/plan
```

**What happens behind the scenes:**
- **Technical Context:** Technology stack and dependencies defined
- **Implementation Blueprint:** Context integration and known patterns documented
- **Constitutional Check:** Ensures library-first, CLI interface, test-first principles
- **Validation Gates:** Quality checkpoints defined for implementation
- **Design Documents:** Data models, API contracts, and test scenarios created

**Output:** Complete implementation plan with validation gates in `specs/PROJ-123.user-auth/`

---

### **Phase 3: Execution - Building the Feature**

```bash
# Step 4: Break down into actionable tasks
/tasks

# Step 5: Validate before implementation
/validate plan specs/PROJ-123.user-auth/plan.md

# Step 6: Implement following constitutional principles
# (Manual implementation or with AI assistance)

# Step 7: Review and commit
/review
/smart-commit "implement user authentication system"
```

**What happens behind the scenes:**
- **Task Generation:** Implementation plan becomes ordered, actionable tasks
- **Quality Gates:** Each task includes validation criteria
- **Constitutional Compliance:** Library-first, CLI interface, test-first enforced
- **Systematic Review:** Code quality, security, and performance validation
- **Intelligent Commits:** Changes documented with proper commit messages

---

## Complete Real Example: Building User Authentication 🔐

Let's build a complete user authentication system from scratch, step by step:

### **Step 1: The Site Survey** 🗺️
```bash
/prime-core
```

**What happens:**
- Analyzes project structure and existing patterns
- Loads constitutional principles and coding standards
- Identifies similar authentication patterns in codebase
- Prepares context for effective specification

**Result:** AI understands your project and is ready for effective development

---

### **Step 2: The Visionary Architect Creates the Blueprint** 🎯
```bash
/specify "user authentication system with email/password login, Google OAuth integration, role-based permissions (user/admin), password reset functionality, and session management"
```

**What happens behind the scenes:**
- **Codebase Research:** Searches for existing auth patterns, user models, security utilities
- **External Research:** Researches OAuth2 best practices, session security, RBAC patterns
- **Context Engineering:** Documents required libraries, gotchas, and implementation patterns
- **Requirements Definition:** Creates testable functional requirements
- **User Scenarios:** Defines complete user journeys with acceptance criteria

**Result:** `specs/PROJ-123.user-auth/spec.md` with comprehensive blueprint including:
- Complete user scenarios (login, logout, registration, password reset)
- Functional requirements (FR-001: System MUST validate email format)
- Context engineering with library gotchas and similar patterns
- Research findings on security best practices

---

### **Step 3: The Master Planner Creates Construction Plans** 📐
```bash
/plan
```

**What happens behind the scenes:**
- **Technical Context:** Defines Node.js/Express, PostgreSQL, JWT tokens, bcrypt
- **Implementation Blueprint:** References existing user models, auth middleware patterns
- **Constitutional Check:** Ensures auth is library-first with CLI interface
- **Validation Gates:** Defines Context Completeness, Design Validation, Implementation Readiness
- **Design Documents:** Creates data models, API contracts, test scenarios

**Result:** Complete implementation plan in `specs/PROJ-123.user-auth/` including:
- `plan.md` - Detailed technical implementation plan
- `data-model.md` - User and role data structures
- `contracts/auth-api.json` - API endpoint specifications
- `research.md` - Technology decisions and alternatives
- `quickstart.md` - Key validation scenarios

---

### **Step 4: The Project Manager Creates Work Orders** 📋
```bash
/tasks
```

**What happens:**
- Analyzes implementation plan and design documents
- Creates ordered, dependency-aware task list
- Each task includes validation criteria and success definitions
- Tasks follow constitutional principles (tests before implementation)

**Result:** `specs/PROJ-123.user-auth/tasks.md` with numbered, actionable tasks:
```
1. CREATE database migration for users and roles tables
2. CREATE contract tests for authentication endpoints
3. IMPLEMENT User model with validation
4. IMPLEMENT authentication middleware library
5. ADD CLI interface to auth library
...
```

---

### **Step 5: Quality Validation Before Building** ✅
```bash
/validate plan specs/PROJ-123.user-auth/plan.md
```

**What happens:**
- Runs Context Completeness Gate (all references accessible)
- Checks Constitutional Compliance Gate (library-first, CLI, test-first)
- Validates Implementation Readiness Gate (dependencies available)
- Verifies all validation gates are achievable

**Result:** Validation report confirming readiness to proceed or identifying blockers

---

### **Step 6: Implementation (Following Constitutional Principles)**

Now you implement following the tasks, with constitutional principles enforced:

**Library-First Principle:**
- Create `src/auth/` library with clear purpose
- Expose all functionality through library interface
- No direct app code in auth logic

**CLI Interface Principle:**
- Add `src/auth/cli.js` with commands:
  - `auth create-user --email user@example.com`
  - `auth verify-token --token <jwt>`
  - `auth reset-password --email user@example.com`

**Test-First Principle (NON-NEGOTIABLE):**
- Write contract tests first (must fail initially)
- Then integration tests
- Then unit tests
- Only then implement to make tests pass

---

### **Step 7: The Building Inspector Reviews Everything** 🔍
```bash
/review src/auth/
```

**What happens:**
- **Constitutional Compliance:** Verifies library-first, CLI interface, test-first
- **Code Quality:** Checks type safety, error handling, documentation
- **Security Review:** Validates input validation, password hashing, token security
- **Performance:** Ensures no N+1 queries or inefficient operations

**Result:** Detailed review report with categorized findings (critical/important/suggestions)

---

### **Step 8: The Documentation Clerk Records the Work** 📝
```bash
/smart-commit "implement user authentication system with OAuth2 and RBAC"
```

**What happens:**
- Analyzes all staged changes
- Verifies constitutional compliance (tests committed before implementation)
- Creates conventional commit message with proper categorization
- Suggests logical grouping if changes should be split

**Result:** Properly formatted commit:
```
feat(auth): implement user authentication system

- User registration with email validation
- JWT-based session management with refresh tokens
- Google OAuth2 integration with profile sync
- Role-based access control (user/admin roles)
- Password reset with secure token generation
- CLI interface with user management commands

Implements FR-001 through FR-012 from specification.
All contract, integration, and unit tests pass.

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## The Enhanced Quality Control System 🔍

Every feature goes through multiple validation gates, just like building inspections:

### **Specification Phase Gates**
- **Context Completeness Gate:** "No Prior Knowledge" test passes
- **Requirements Clarity Gate:** No [NEEDS CLARIFICATION] markers remain
- **Research Quality Gate:** External best practices documented

### **Planning Phase Gates**
- **Constitutional Compliance Gate:** Library-first, CLI, test-first principles
- **Design Validation Gate:** All requirements addressed in technical design
- **Implementation Readiness Gate:** All dependencies available and documented

### **Implementation Phase Gates**
- **Code Quality Gate:** Type safety, error handling, documentation complete
- **Test Coverage Gate:** Contract → Integration → Unit tests all pass
- **Performance Gate:** No obvious bottlenecks or inefficiencies

### **Constitutional Principles (The Building Code)**

**Library-First Principle:**
- Every feature is a reusable library
- Libraries have clear, documented purposes
- No direct application code mixed with business logic

**CLI Interface Principle:**
- Every library exposes CLI commands
- Commands support --help, --version, --format
- Text-based input/output for debuggability

**Test-First Principle (NON-NEGOTIABLE):**
- Tests are written and failing before implementation
- RED-GREEN-Refactor cycle strictly followed
- Contract → Integration → Unit test progression

---

## When to Use Each Command 🤔

### **Use `/prime-core` when:**
- Starting any development session
- Switching between different features or contexts
- Onboarding to a new project
- After major architectural changes

### **Use `/specify` when:**
- Starting a new feature or major change
- You have rough requirements that need to be detailed
- You need comprehensive research and context gathering
- Requirements need to be validated for completeness

### **Use `/plan` when:**
- You have a complete, approved specification
- You need technical implementation details
- You want validation gates defined
- You're ready to create architectural design

### **Use `/tasks` when:**
- You have a complete implementation plan
- You need actionable, ordered work items
- You want to track implementation progress
- You're ready to begin coding

### **Use `/review` when:**
- Before committing any code
- During pull request reviews
- For periodic code quality audits
- When constitutional compliance needs verification

### **Use `/validate` when:**
- At the end of each phase before proceeding
- When quality assurance is needed
- Before major implementation efforts
- When constitutional compliance is questioned

### **Use `/debug` when:**
- Facing complex, mysterious bugs
- System behavior is unexpected
- Root cause analysis is needed
- Systematic debugging approach required

### **Use `/smart-commit` when:**
- Before committing any changes
- You want proper conventional commit format
- Changes need to be documented with context
- Git history quality is important

---

## Common Workflows 🔄

### **New Feature from Scratch**
```bash
/prime-core
/specify "feature description"
/plan
/tasks
# Implement following tasks
/review
/smart-commit
```

### **Modifying Existing Code**
```bash
/prime-core
/specify "modification requirements"
# Focus on impact analysis and migration strategy
/plan
# Implementation with careful change management
/review
/smart-commit
```

### **Debugging Complex Issues**
```bash
/prime-core
/debug "problem description"
# Follow systematic debugging process
# Implement fix following constitutional principles
/review
/smart-commit "fix: resolve [issue description]"
```

### **Code Review Process**
```bash
/review [file or directory]
# Address findings systematically
/validate implementation
# Ensure constitutional compliance
```

---

## Pro Tips for Success 🚀

### **🎯 Always Start with Context**
Begin every session with `/prime-core` to load project understanding. This prevents misunderstandings and ensures quality.

### **🔗 Follow the Three-Phase Process**
Don't skip phases. Each phase builds on the previous and catches different types of issues:
- Specification catches requirement issues
- Planning catches architectural issues
- Tasks catch implementation issues

### **📚 Research Before Specifying**
The enhanced `/specify` command includes research. Let it analyze existing patterns and external best practices before creating specifications.

### **🔍 Use Validation Gates**
Run `/validate` at the end of each phase. It's much cheaper to catch issues early than during implementation.

### **⚖️ Constitutional Compliance is Non-Negotiable**
The constitution isn't suggestions - it's the foundation that makes everything work:
- Library-first prevents tight coupling
- CLI interfaces enable automation and testing
- Test-first prevents regressions and enables confidence

### **🧪 Trust the Test-First Process**
Writing tests first feels slower initially but:
- Forces clear thinking about requirements
- Prevents scope creep and feature bloat
- Enables confident refactoring
- Provides immediate feedback on implementation

---

## Quick Start Guide - Your First Feature (10 minutes) 🚀

Let's build a simple "user profile display" feature to experience the workflow:

### **1. Survey the Site**
```bash
/prime-core
```
*Understanding your project structure and patterns*

### **2. Create the Blueprint**
```bash
/specify "user profile display page showing avatar, name, email, and join date with edit profile button"
```
*Creates comprehensive specification with research*

### **3. Create Construction Plans**
```bash
/plan
```
*Creates technical implementation plan with validation gates*

### **4. Create Work Orders**
```bash
/tasks
```
*Breaks down into specific, actionable tasks*

### **5. Validate Before Building**
```bash
/validate plan specs/proj-123.user-profile/plan.md
```
*Ensures everything is ready for implementation*

### **6. Implement (Following the Tasks)**
- Follow tasks in order
- Write tests first (constitutional requirement)
- Implement to make tests pass
- Create library with CLI interface

### **7. Quality Inspection**
```bash
/review src/profile/
```
*Comprehensive quality review*

### **8. Document the Work**
```bash
/smart-commit "implement user profile display page"
```
*Creates professional commit message*

### **Celebrate!** 🎉
You just used the enhanced Spec Kit framework to build a feature with:
- Comprehensive planning and research
- Constitutional compliance
- Quality validation gates
- Professional documentation

---

## The Enhanced Advantage: Why This Works 💡

### **Context Engineering Prevents Failures**
- Specifications include all necessary implementation context
- Similar patterns are identified and referenced
- Library gotchas are documented upfront
- External best practices are integrated

### **Validation Gates Catch Issues Early**
- Context Completeness prevents "missing information" failures
- Constitutional Compliance ensures architectural consistency
- Implementation Readiness validates all dependencies

### **Research-Driven Development**
- External best practices integrated from the start
- Existing codebase patterns leveraged effectively
- Common pitfalls avoided through upfront research

### **Systematic Quality Process**
- Multiple validation points throughout development
- Constitutional principles provide consistent standards
- Quality reviews built into the workflow

---

## Common Mistakes to Avoid ❌

### **❌ Skipping the Prime Phase**
```bash
# WRONG - jumping in without context
/specify "some feature"
```

```bash
# RIGHT - understand the project first
/prime-core
/specify "some feature"
```

### **❌ Rushing Through Validation**
```bash
# WRONG - skipping validation gates
/specify → /plan → /tasks → implement
```

```bash
# RIGHT - validate at each phase
/specify → /validate spec → /plan → /validate plan → /tasks
```

### **❌ Ignoring Constitutional Principles**
```bash
# WRONG - implementing directly in app code
src/app/auth-logic.js
```

```bash
# RIGHT - library-first with CLI interface
src/auth/
├── lib/auth-service.js
├── cli/auth-commands.js
└── tests/auth.test.js
```

### **❌ Skipping Research**
- The enhanced `/specify` includes research for a reason
- Context engineering prevents implementation failures
- Don't rush to implementation without understanding existing patterns

---

## Remember: You're the Visionary, Spec Kit is Your Construction Company 🏗️

- **You decide WHAT to build** (vision, requirements, business goals)
- **Spec Kit figures out HOW to build it** (systematic process, quality gates, implementation)
- **The enhanced framework ensures success** (research, context, validation, constitutional compliance)

This isn't about replacing human creativity - it's about amplifying your vision with systematic, high-quality implementation that follows proven principles.

---

## Quick Command Reference 📋

| Phase | Command | Purpose | Output |
|-------|---------|---------|--------|
| **Context** | `/prime-core` | Load project understanding | Project context analysis |
| **Specify** | `/specify` | Research-driven specification | Complete feature blueprint |
| **Plan** | `/plan` | Technical implementation plan | Architecture with validation gates |
| **Execute** | `/tasks` | Actionable task breakdown | Ordered implementation tasks |
| **Quality** | `/review` | Code quality inspection | Comprehensive review report |
| **Quality** | `/validate` | Phase validation gates | Gate pass/fail assessment |
| **Support** | `/debug` | Root cause analysis | Systematic problem resolution |
| **Support** | `/smart-commit` | Intelligent git commits | Professional commit messages |

---

**Ready to build something amazing with enhanced quality and systematic process?**

**Start with `/prime-core`, then `/specify "your amazing idea"` and watch your vision become reality through systematic, research-driven development!** ✨

*The enhanced Spec Kit framework: Where vision meets systematic execution.*