# Spec Kit Plus: How to Build Production-Ready Apps with AI Agents

This tutorial is based on this video:

[Spec Kit: How to Build Production-Ready Apps with AI Agents](https://www.youtube.com/watch?v=8jtIXRyGMQU)

## SpecKitPlus: Building Production-Ready Apps with AI Coding Agents

## Introduction

AI coding agents are powerful tools, but without proper structure, they often produce buggy, incomplete applications with poor UX. SpecKitPlus solves this problem by introducing spec-driven development to your AI agent workflow, giving your agent the same context and structure that professional development teams use.

## What is SpecKitPlus?

SpecKit is a structured workflow from Panaversity SpeckitPlus GitHub Fork that executes scripts and fine-tuned prompts to produce high-quality context for your coding agent. It brings traditional spec-driven development practices to AI-assisted coding, ensuring your agent knows exactly what to build before writing a single line of code.

**Key Benefits:**
- Structured planning and implementation
- Better code quality and fewer bugs
- Git-based version control workflow
- Test-driven development
- Works with any coding agent (Claude Code, Cursor, Windsurf, Codeium, etc.)

## Understanding Spec-Driven Development

Spec-driven development has been the foundation of professional software development for decades. The process involves:

1. **Analysis** - Understanding requirements
2. **Planning** - Breaking down the work into tasks
3. **Implementation** - Building the features
4. **Testing** - Verifying everything works

SpecKit automates this proven methodology for AI coding agents, documenting everything upfront so the agent can pick up exactly where it left off, even in new conversations.

## Core Workflow Components

### 1. Constitution (One-Time Setup)
Sets project principles, standards, and tech stack preferences at the start of your project.

### 2. Feature Lifecycle
The main workflow for planning and implementing features:

- **Specify** - Define business requirements (non-technical)
- **Clarify** (Optional) - Agent asks follow-up questions
- **Plan** - Create technical implementation plan, data models, and service interfaces
- **Tasks** - Break plan into individual actionable tasks
- **Analyze** (Optional) - Verify documentation completeness
- **Implement** - Agent builds the features
- **Test & Merge** - Validate changes and merge to main branch

## Getting Started

### Installing SpecKit

1. Navigate to your project directory
2. Run the installation command:

```bash
uvx speckitplus init <PROJECt_NAME>
```

3. Select your AI agent (Claude, Cursor, Codeium, etc.)
4. Choose your script type (PowerShell, Bash, etc.)

You can install SpecKit for multiple agents simultaneously by running the command multiple times with different agent selections.

## Project Structure

After installation, SpecKit creates:

```
your-project/
├── .speckit/
│   ├── memory/
│   │   └── constitution.md
│   ├── scripts/
│   └── templates/
├── .cursor/
│   └── commands/
├── .codeium/
│   └── prompts/
└── .claude/
    └── commands/
```

**Key Files:**
- **constitution.md** - Project principles and standards
- **scripts/** - Helper scripts for branch creation and workflow automation
- **templates/** - Templates for specs, plans, and tasks
- **commands/prompts** - Detailed instructions for each workflow step

## Step-by-Step Workflow

### Step 1: Constitution

Set up your project standards (run once at project start):

```bash
/constitution
```

**Example prompt:**
```
Write clean and modular code and use Next.js 15 best practices
```

The agent will generate a comprehensive constitution file including:
- Framework best practices
- Component organization
- Code standards
- Architecture decisions

**Pro Tip:** This is a human-in-the-loop process. Review and modify the generated constitution to match your preferences.

### Step 2: Specify

Define what you want to build (business requirements only):

```bash
/specify
```

**Example prompt:**
```
I would like to build a basic expense tracking app.
- Add, view, and delete expenses
- Track personal expenses with amount, date, categories, and description
- Simple dashboard showing recent expenses and basic totals
- Do not implement user auth as this is just a personal tracker
```

SpecKit automatically:
- Creates a new feature branch
- Generates a spec file with user scenarios, edge cases, and acceptance criteria

### Step 3: Clarify (Optional)

Let the agent ask clarifying questions:

```bash
/clarify
```

The agent will analyze your spec and ask targeted questions to fill gaps:
- UI behavior preferences
- Edge case handling
- Data validation rules
- Feature scope clarifications

**Example questions:**
- "Should the system allow negative amounts to represent refunds?"
- "What does 'recent expenses' mean? Last 10? Last 30 days?"
- "Are descriptions and categories required or optional?"

### Step 4: Plan

Create a technical implementation plan:

```bash
/plan
```

**Provide technical details:**
```
Use Next.js with app router, route handlers, and server actions.
Add backend/server-side logic to a server folder in the src folder.
Use local storage to persist data.
Do not implement auth.
```

SpecKit generates:
- **quick-start.md** - Feature overview and testing scenarios
- **plan.md** - Complete technical plan with data models, contracts, and architecture
- **research.md** - Technical research and decisions
- Agent files updated with project context

### Step 5: Tasks

Break the plan into actionable implementation steps:

```bash
/tasks
```

The agent creates phases with numbered tasks (T001, T002, etc.):
- Phase 3.1: Setup and foundation
- Phase 3.2: Storage and utilities  
- Phase 3.3: Contract tests (TDD)
- Phase 3.4: Server actions
- Phase 3.5: Components
- And so on...

### Step 6: Implement

Build the features in manageable chunks:

```bash
/implement
```

**Implementation strategies:**

**Option 1 - Full implementation:**
```bash
/implement
```

**Option 2 - Specific tasks:**
```bash
/implement T001 to T005
```

**Option 3 - By phase:**
```bash
/implement phase 3.1
```

**Best Practice:** Implement in small chunks to maintain context window efficiency. Clear chat between phases to prevent context degradation.

The agent will:
1. Run tests (which fail initially - expected behavior)
2. Implement the functionality
3. Re-run tests (which now pass)
4. Mark completed tasks with an X in the tasks file

### Step 7: Test

Follow the quick-start.md guide to manually test your application:
- Verify all user scenarios
- Test edge cases
- Confirm acceptance criteria

### Step 8: Merge

Create a pull request and merge to main:

1. Commit your changes
2. Publish the feature branch
3. Create a pull request on GitHub
4. Review and merge
5. Delete the feature branch
6. Switch back to main and sync

```bash
git checkout main
git pull origin main
```

## Test-Driven Development (TDD)

SpecKit follows TDD principles:

1. **Write tests first** - Tests are created before implementation
2. **Watch tests fail** - Initial test run shows expected failures
3. **Implement features** - Build functionality to pass tests
4. **Tests pass** - Confirms feature completion
5. **Refactor** - Add polish and optimizations

You'll see a `tests/` folder in your project with comprehensive test suites for each feature.

## Using SpecKit with Different Agents

### Claude Code / Cursor
Use slash commands directly:
```bash
/constitution
/specify
/plan
```

### Codeium (or agents without slash commands)
Drag and drop the prompt files into chat:
1. Navigate to `.codeium/prompts/`
2. Drag the desired prompt file (e.g., `constitution.md`) into the chat
3. Add your requirements

**This approach works with ANY coding agent**, making SpecKit universally compatible.

## Adding New Features

To add additional features after completing your first one:

1. Start fresh - no need to run `/constitution` again
2. Run `/specify` with your new feature requirements
3. SpecKit automatically creates a new feature branch
4. Follow the complete workflow (clarify → plan → tasks → implement)
5. Each feature gets its own isolated spec folder
6. Merge when complete

**Example:**
```bash
/specify

Please add a budget tracking feature to this app.
```

## Pro Tips and Best Practices

### Context Management
- Clear chat between major steps to maintain clean context
- Implement features in phases rather than all at once
- The agent can always pick up from where it left off using the task files

### Human-in-the-Loop
- Review and modify generated files (constitution, specs, plans)
- Don't blindly accept everything - you're in control
- Provide feedback and corrections as needed

### Git Workflow
- SpecKit automatically creates feature branches
- Keep main branch clean and stable
- Only merge tested, working features

### Monitoring Usage
For Claude Code users, check usage limits at:
- claude.ai → Settings → Usage

### Testing
- Always follow the quick-start guide test scenarios
- Verify all edge cases
- Test in a real browser, not just in the agent

## Troubleshooting

### Scripts Not Executing
Ensure you have the correct permissions and have installed UV properly.

### Agent Not Finding Commands
- For slash command agents: Check that SpecKit is installed for that agent
- For other agents: Manually drag prompt files from the agent's folder

### Context Window Issues
- Implement in smaller chunks
- Clear chat more frequently
- Use specific task ranges instead of implementing everything at once

## Real-World Example: Expense Tracker

Here's a complete example flow:

**1. Constitution:**
```
Write clean and modular code using Next.js 15 best practices
```

**2. Specify:**
```
Build an expense tracking app with add/view/delete functionality.
Track amount, date, category, and description.
Show dashboard with recent expenses and totals.
No authentication needed.
```

**3. Clarify responses:**
- Use flexible amounts (allow decimals, no negatives)
- Categories required, descriptions optional
- Recent = last 30 days
- Standard categories: Food, Transportation, Entertainment, etc.

**4. Plan:**
```
Use Next.js with app router and server actions.
Store backend logic in src/server folder.
Use localStorage for persistence.
No authentication.
```

**5. Implementation:**
- Implement phase by phase
- Tests created first (TDD)
- Components built incrementally
- Final testing via quick-start scenarios

**Result:** A fully functional, tested expense tracker with clean code organization and proper Git history.

## Conclusion

SpecKit transforms AI coding agents from unpredictable tools into structured development partners. By following professional development practices and maintaining clear documentation, you'll consistently build production-ready applications that match your vision.

**Key Takeaways:**
- Structure matters - proper planning prevents poor apps
- Test-driven development ensures quality
- Git workflows keep your codebase clean
- Human oversight improves AI outputs
- The workflow is repeatable for every feature

**Next Steps:**
1. Star the SpecKit repository on GitHub
2. Try it with your preferred coding agent
3. Start with a small project to learn the workflow
4. Scale up to more complex applications

Happy building!
```