# Complete Claude Code Tutorial: From Beginner to Hero

This tutorial is mainly written using these resources:

[I should be charging $999 for this Claude Code Tutorial](https://www.youtube.com/watch?v=4nthc76rSl8)

[Claude Code Official Documentation](https://docs.claude.com/en/docs/claude-code/overview)

## Table of Contents
1. [What is Claude Code?](#what-is-claude-code)
2. [Installation & Setup](#installation--setup)
3. [Basic Commands & Interface](#basic-commands--interface)
4. [Working with Files & Folders](#working-with-files--folders)
5. [Context Engineering with CLAUDE.md](#context-engineering)
6. [Common Workflows](#common-workflows)
7. [Subagents](#subagents)
8. [Output Styles](#output-styles)
9. [Custom Commands](#custom-commands)
10. [Hooks System](#hooks-system)
11. [Headless Mode & Automation](#headless-mode)
12. [GitHub Actions & CI/CD](#github-actions)
13. [Model Context Protocol (MCP)](#mcp)
14. [IDE Integrations](#ide-integrations)
15. [Git Workflows](#git-workflows)
16. [Best Practices](#best-practices)
17. [Troubleshooting](#troubleshooting)

---

## What is Claude Code?

Claude Code is an **agentic coding tool** that lives in your terminal and helps you turn ideas into code faster than ever before. Unlike chat interfaces or specialized coding IDEs, Claude Code is:

- **Terminal-native**: Works where developers already work
- **Action-oriented**: Directly edits files, runs commands, creates commits
- **Context-aware**: Maintains awareness of your entire project structure
- **Extensible**: Connects to external tools via MCP (Model Context Protocol)
- **Unix philosophy**: Composable and scriptable

### What Claude Code Does

**Build features from descriptions**: Tell Claude what you want in plain English. It makes a plan, writes code, and ensures it works.

**Debug and fix issues**: Describe a bug or paste an error. Claude analyzes your codebase, identifies the problem, and implements a fix.

**Navigate any codebase**: Ask anything about your team's codebase and get thoughtful answers. Claude Code maintains project structure awareness and can search the web or pull from external data sources.

**Automate tedious tasks**: Fix lint issues, resolve merge conflicts, write release notes. All in a single command from your terminal or automatically in CI.

### Claude Code vs Alternatives

| Feature | Claude Code | Cursor/Copilot | V0/Lovable | Chat (GPT/Claude) |
|---------|-------------|----------------|------------|-------------------|
| **Best for** | Full-stack dev, PM workflows | Heavy coding | Quick prototypes | General queries |
| **File management** | Native, automatic | Manual/context-limited | Template-based | Manual upload |
| **Writing quality** | Excellent | Good | N/A | Excellent |
| **Context engineering** | Superior | Limited | N/A | Manual |
| **Automation** | Built-in (headless, CI/CD) | Limited | None | None |
| **MCP integrations** | Yes | No | No | No |
| **Pricing** | $17-20/month | $20/month | $20/month | $20/month |

**Key Insight**: Claude Code excels at both engineering tasks AND PM workflows (research, writing, analysis) while being fully scriptable for automation.

---

## Installation & Setup

### System Requirements

- **OS**: macOS 10.15+, Ubuntu 20.04+/Debian 10+, Windows 10+ (with WSL 1, WSL 2, or Git for Windows)
- **Node.js**: Version 18 or newer
- **Optional**: ripgrep (usually included, needed for search)

### Installation Methods

#### Method 1: Native Install (Beta - Recommended)

**macOS, Linux, WSL:**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows PowerShell:**
```powershell
irm https://claude.ai/install.ps1 | iex
```

**Install specific version:**
```bash
# macOS/Linux
curl -fsSL https://claude.ai/install.sh | bash -s 1.0.58

# Windows
& ([scriptblock]::Create((irm https://claude.ai/install.ps1))) 1.0.58
```

#### Method 2: npm Install

```bash
npm install -g @anthropic-ai/claude-code
```

**⚠️ Important**: Do NOT use `sudo npm install -g` - this causes permission issues and security risks.

### Authentication

When you first run `claude`, you'll need to authenticate:

**Option 1: Claude Console** (API with pre-paid credits)
- Default option for API users
- Requires active billing at console.anthropic.com
- Auto-creates "Claude Code" workspace for cost tracking

**Option 2: Claude App** (Pro $17 or Max $20 plan)
- Unified subscription for Claude Code + web interface
- Log in with Claude.ai account
- Better value if using both

**Option 3: Enterprise** (AWS Bedrock or Google Vertex AI)
- For enterprise deployments
- Use existing cloud infrastructure
- See [Third-party integrations docs](https://docs.claude.com/en/docs/claude-code/third-party-integrations)

### Verify Installation

```bash
# Check installation health
claude doctor

# Start Claude Code
cd /path/to/your/project
claude
```

### Credential Management

After first login, credentials are stored securely:
- **macOS**: Keychain
- **Linux**: Secret Service API or encrypted file
- **Windows**: Windows Credential Manager

To switch accounts:
```
> /login
```

---

## Basic Commands & Interface

### Starting Claude Code

```bash
# From any directory (not recommended)
claude

# From project directory (recommended)
cd /path/to/your/project
claude

# With specific flags
claude --permission-mode acceptEdits
claude --model opus
claude -p "What does this project do?"  # Print mode (non-interactive)
```

### Essential Slash Commands

| Command | Function |
|---------|----------|
| `/help` | Show all available commands |
| `/clear` | Reset conversation (manage context) |
| `/resume` | Continue a previous conversation |
| `/continue` | Continue most recent conversation |
| `/config` | Configure Claude Code settings |
| `/agents` | Manage subagents |
| `/hooks` | Configure hooks |
| `/mcp` | Manage MCP servers |
| `/output-style` | Change output style |
| `/ide` | Connect to IDE integration |
| `/login` | Switch accounts |
| `/logout` | Sign out |
| `/compact` | Reduce context size |
| `/bug` | Report a bug |
| `/doctor` | Check installation health |

### Interface Elements

When Claude responds, you'll see:

**Status indicators:**
```
⏵⏵ accept edits on    # Auto-accept mode
⏸ plan mode on        # Plan mode (Shift+Tab to toggle)
```

**Progress information:**
- **Time elapsed**: Duration of operation
- **Token count**: Resources used
- **To-do lists**: Claude's self-created plans
- **Agent colors**: When using custom subagents

**Permission modes:**
- **Accept edits**: Claude can edit files after asking
- **Accept all**: Claude can edit without asking (use carefully!)
- **Plan mode**: Claude creates plan before acting

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Shift + Tab` | Toggle Plan Mode |
| `Ctrl + C` | Cancel current operation |
| `Escape` | Exit Claude Code |
| `Ctrl + R` | View detailed agent activity |
| `Cmd/Ctrl + Esc` | Quick launch (in supported IDEs) |

### CLI Flags

```bash
# Permission modes
--permission-mode acceptEdits   # Ask before each edit
--permission-mode acceptAll     # Never ask (dangerous!)
--permission-mode plan          # Start in plan mode

# Model selection
--model sonnet                  # Use Sonnet (default, fast)
--model opus                    # Use Opus (best quality)
--model haiku                   # Use Haiku (fastest, cheapest)

# Non-interactive mode
-p, --print "prompt"           # Print mode, no interaction
--output-format text           # Text output (default)
--output-format json           # JSON output
--output-format stream-json    # Streaming JSON

# Conversation management
--continue                     # Continue most recent conversation
--resume [session-id]          # Resume specific conversation

# Tool restrictions
--allowedTools "Bash,Read"     # Limit available tools
--disallowedTools "Bash"       # Block specific tools

# Context and prompts
--append-system-prompt "text"  # Append to system prompt
--input-format stream-json     # Accept streaming JSON input

# Subagents
--agents '{"name": {...}}'     # Define custom subagents

# Verbose output
--verbose                      # Show detailed logging
```

---

## Working with Files & Folders

### Project Structure Best Practices

```
my-project/
├── CLAUDE.md                   # Project memory (created by `init`)
├── .claude/
│   ├── agents/                 # Custom subagents
│   ├── commands/               # Custom slash commands
│   ├── output-styles/          # Custom output styles
│   ├── hooks/                  # Custom hooks
│   └── settings.local.json     # Local settings
├── .mcp.json                   # MCP server config (team-shared)
├── src/                        # Your code
├── tests/                      # Your tests
└── docs/                       # Documentation
```

### Initializing a Project

```
> init
```

This command:
1. Analyzes your project structure
2. Creates `CLAUDE.md` with project overview
3. Documents core components
4. Provides setup instructions

### Querying Files

**Automatic file discovery:**
```
> what does this project do?
```

Claude analyzes files and provides a summary - no manual context needed.

**Specific questions:**
```
> what files handle authentication?
> explain how the API routing works
> show me where database migrations are defined
```

**File references with @:**
```
> explain @src/auth/login.ts
> compare @src/api/v1.ts and @src/api/v2.ts
> review @src/components/ for best practices
```

### File Operations

**Reading:**
```
> read src/config.ts
> show me the contents of package.json
> what's in the .env.example file?
```

**Editing:**
```
> add input validation to src/forms/registration.ts
> refactor src/utils/formatters.ts to use arrow functions
> update README.md with the new API endpoints
```

**Creating:**
```
> create a new component src/components/UserProfile.tsx
> generate a test file for src/utils/validators.ts
> create a migration for adding user roles
```

**Bulk operations:**
```
> add TypeScript types to all JavaScript files in src/
> fix all lint errors in the project
> update all imports to use the new path structure
```

---

## Context Engineering

### The CLAUDE.md File

`CLAUDE.md` is your **project memory** - always in context, never forgotten.

**Created by:**
```
> init
```

**Example structure:**
```markdown
# My Project

## Overview
This is a Next.js e-commerce platform with Stripe integration.

## Architecture
- Frontend: Next.js 14 with App Router
- Backend: tRPC API
- Database: PostgreSQL with Prisma
- Auth: NextAuth.js
- Payments: Stripe

## Key Files
- src/app: Next.js app router pages
- src/server: tRPC backend
- src/components: React components
- prisma/schema.prisma: Database schema

## Development Rules
- Always write tests for new features
- Never commit directly to main
- Use conventional commits
- Ask before modifying database schema
- Follow the style guide in CONTRIBUTING.md

## Testing
- Unit tests: `npm test`
- E2E tests: `npm run test:e2e`
- Run all tests before creating PR

## Deployment
- Staging: Automatically on PR creation
- Production: Manually trigger via GitHub Actions
```

### Adding to Project Memory

**Quick add:**
```
# Always ask before committing to GitHub
```

Lines starting with `#` are appended to CLAUDE.md.

**What to include:**
- Project overview and architecture
- Tech stack and dependencies
- Coding standards and conventions
- Testing requirements
- Deployment procedures
- Common pitfalls to avoid
- Links to important docs

### Subfolder Memory

Create `CLAUDE.md` in subdirectories for context-specific rules:

```
src/components/CLAUDE.md:
# Component Guidelines
- Use functional components with hooks
- Include PropTypes or TypeScript types
- Write Storybook stories for each component
- Follow atomic design principles
```

---

## Common Workflows

### 1. Understanding an Unfamiliar Codebase

```bash
cd /path/to/new-project
claude
```

```
> what does this project do?
> what's the overall architecture?
> where is the API routing logic?
> how does authentication work?
> what database are we using and where's the schema?
> show me the most recently modified files
```

### 2. Debugging

**Share an error:**
```
> I'm getting this error: [paste error message]
> help me debug this stack trace: [paste trace]
```

**Describe the bug:**
```
> there's a bug where users can submit empty forms - fix it
> the login page shows a blank screen after entering wrong credentials
```

**Claude will:**
- Analyze the error
- Find relevant code
- Identify root cause
- Propose and implement fix
- Run tests if available

### 3. Implementing Features

**Natural language descriptions:**
```
> add input validation to the registration form
> implement dark mode toggle
> add pagination to the products list
> create an export to CSV feature
```

**With specifications:**
```
> implement a rate limiting middleware:
  - 100 requests per 15 minutes per IP
  - Return 429 status when exceeded
  - Store counts in Redis
  - Add configurable limits per route
```

### 4. Refactoring

**Identify legacy code:**
```
> what code in this project needs refactoring?
> show me any callback hell that should use async/await
```

**Request refactoring:**
```
> refactor src/utils/api.ts to use TypeScript
> convert all class components to functional components
> refactor the authentication module for better testability
```

**Claude will:**
- Create a refactoring plan
- Show you what will change
- Preserve functionality
- Run existing tests

### 5. Writing Tests

**Generate test scaffolding:**
```
> write unit tests for src/utils/validators.ts
> create integration tests for the auth API
> add test cases for edge cases in the payment flow
```

**Improve coverage:**
```
> what code is missing tests?
> add tests for the error handling paths
> create E2E tests for the checkout flow
```

### 6. Git Operations

**Conversational Git:**
```
> what files have I changed?
> show me uncommitted changes
> commit my changes with a descriptive message
> create a new branch called feature/user-profiles
> help me resolve this merge conflict
```

**Complex operations:**
```
> create a PR with these changes
> rebase my branch on main
> cherry-pick commit abc123
> amend the last commit with these new changes
```

### 7. Documentation

**Generate docs:**
```
> generate API documentation for src/api/
> write a README for this project
> create JSDoc comments for src/utils/
> document the environment variables needed
```

**Update docs:**
```
> update the README with the new features
> add examples to the API documentation
> create a migration guide for v2
```

### 8. Using Images for Context

```
> [drag screenshot of UI bug]
> analyze this screenshot and suggest fixes

> [paste wireframe]
> implement this design

> [error screenshot]
> debug this error from the screenshot
```

### 9. Working with Multiple Worktrees

```bash
# Create worktree for feature branch
git worktree add ../feature-auth feature/auth

# Start Claude in main worktree
cd /path/to/main
claude

# In another terminal, start Claude in feature worktree
cd ../feature-auth
claude
```

Each instance works independently with its own context.

---

## Subagents

### What Are Subagents?

**Subagents** are specialized AI assistants with:
- Specific expertise
- Limited tool access
- Custom instructions
- Independent context

Think: specialized team members for different tasks.

### When to Use Subagents

✅ **Use subagents for:**
- Task-specific expertise (security review, performance optimization)
- Parallel work (analyzing multiple files simultaneously)
- Context isolation (keep large contexts separate)
- Specialized workflows (API design, documentation)

### Built-in Subagents

View available subagents:
```
> /agents
```

Common built-in agents:
- `code-reviewer`: Code quality and best practices
- `debugger`: Error analysis and fixes
- `api-designer`: API design and documentation
- `performance-optimizer`: Performance improvements
- `security-auditor`: Security vulnerability analysis

### Using Subagents

**Automatic delegation:**
```
> review this PR for security issues
```
Claude automatically uses the security-auditor subagent.

**Explicit request:**
```
> use the code-reviewer agent to analyze src/api/
> have the debugger look at this error
```

**Parallel execution:**
```
> analyze all test files in parallel
```
Claude creates multiple subagent instances.

### Creating Custom Subagents

#### Method 1: Interactive Creation

```
> /agents
> [Select "Create New Agent"]
```

Fill in:
- **Name**: `frontend-reviewer` (lowercase, hyphens)
- **Description**: "Reviews React components for best practices"
- **Tools**: Read, Grep, Glob (comma-separated)
- **Model**: sonnet, opus, haiku, or inherit
- **Custom Instructions**: Your specific guidance

#### Method 2: File Creation

**Project-level** (`.claude/agents/frontend-reviewer.md`):
```markdown
---
name: frontend-reviewer
description: Expert React component reviewer. Use for all component changes.
tools: Read,Grep,Glob
model: sonnet
---

You are a senior React developer specializing in component architecture.

## Focus Areas
- Component composition and reusability
- Performance (memo, useMemo, useCallback)
- Accessibility (ARIA, keyboard navigation)
- TypeScript types and prop validation
- Testing coverage

## Review Format
### ✅ Strengths
- [List strengths]

### ⚠️ Concerns
- [List concerns with severity: Low/Medium/High]

### 📋 Recommendations
1. [Specific, actionable recommendation]
2. [Another recommendation]

## Style
- Be constructive and supportive
- Reference specific line numbers
- Provide code examples
- Prioritize by severity
```

**User-level** (`~/.claude/agents/security-checker.md`):
```markdown
---
name: security-checker
description: Security vulnerability analysis. Use before deploying.
tools: Read,Grep,Bash
model: opus
---

You are a security expert reviewing code for vulnerabilities.

## Check For
- SQL injection vulnerabilities
- XSS attack vectors
- Authentication/authorization issues
- Sensitive data exposure
- Dependency vulnerabilities
- CORS misconfigurations
- Insecure direct object references

## Process
1. Scan for common vulnerability patterns
2. Check authentication/authorization logic
3. Review API endpoints for security
4. Examine data validation
5. Check dependency versions

## Report Format
### 🔴 Critical Issues
[Issues that must be fixed before deployment]

### 🟡 Warnings
[Issues that should be addressed soon]

### 🟢 Recommendations
[Best practice improvements]
```

### Using Custom Subagents

```
> use the frontend-reviewer agent on src/components/UserProfile.tsx
> have security-checker analyze the authentication flow
> use api-designer to create OpenAPI spec for src/api/
```

### Subagent Configuration

**Location priority:**
1. Project agents (`.claude/agents/`) - highest priority
2. User agents (`~/.claude/agents/`) - lower priority

**Model selection:**
- `sonnet`: Fast, good quality (default)
- `opus`: Best quality, slower
- `haiku`: Fastest, good for simple tasks
- `inherit`: Use same model as main conversation

**Tool access:**
- Omit `tools` field = inherits all tools from main thread
- Specify tools = restricted to that list only
- Use `/agents` command to see all available tools including MCP

### Advanced: CLI Subagent Definition

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer. Use after changes.",
    "prompt": "You are a senior developer. Focus on code quality, security, and best practices.",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "model": "sonnet"
  },
  "debugger": {
    "description": "Debugging specialist.",
    "prompt": "You are an expert debugger. Analyze errors, identify root causes, provide fixes.",
    "tools": ["Read", "Bash"],
    "model": "opus"
  }
}'
```

### Best Practices

**DO:**
- ✅ Write clear, specific descriptions (enables auto-delegation)
- ✅ Limit tools to what's needed (security and focus)
- ✅ Use appropriate models (opus for complex, sonnet for most)
- ✅ Share team agents via `.claude/agents/` in git

**DON'T:**
- ❌ Create too many similar agents
- ❌ Give agents unnecessary tool access
- ❌ Write vague descriptions
- ❌ Forget to test agent behavior

---

## Output Styles

### What Are Output Styles?

**Output styles** customize how Claude Code behaves and formats responses for different use cases beyond software engineering.

### Built-in Output Styles

View available styles:
```
> /output-style
```

**Default**: Software engineering focus
- Technical explanations
- Code-first solutions
- Implementation details

**Explanatory**: Educational focus
- Detailed explanations
- Step-by-step reasoning
- Learning-oriented

**Concise**: Minimal output
- Brief responses
- Get to the point
- Less context needed

**Descriptive**: Planning focus
- `TODO(human)` markers for manual work
- High-level descriptions
- Less actual code generation

### Switching Output Styles

**Interactive menu:**
```
> /output-style
[Select from menu]
```

**Direct switch:**
```
> /output-style explanatory
> /output-style concise
> /output-style descriptive
```

### Creating Custom Output Styles

**Interactive creation:**
```
> /output-style:new I want an output style that focuses on security and includes threat modeling for every change
```

Claude creates a custom style saved to `~/.claude/output-styles/`.

**Manual creation** (`~/.claude/output-styles/security-focused.md`):
```markdown
---
name: security-focused
description: Security-first development with threat modeling
---

When working on code:

1. **Always consider security implications first**
2. **Include threat modeling** for each change
3. **Document security assumptions**
4. **Highlight potential vulnerabilities**
5. **Suggest security tests**

## Response Format

### Security Analysis
- Threat model for the change
- Attack vectors to consider
- Mitigations implemented

### Implementation
[Code with security best practices]

### Security Tests
[Suggested security test cases]

### Additional Considerations
- Authentication/authorization impacts
- Data exposure risks
- Dependency security
```

**Use your custom style:**
```
> /output-style security-focused
```

### Output Style Scope

**User-level** (`~/.claude/output-styles/`)
- Available across all projects
- Personal preferences

**Project-level** (`.claude/output-styles/`)
- Shared with team via git
- Project-specific requirements

### vs CLAUDE.md vs --append-system-prompt

| Method | Purpose | Scope | Priority |
|--------|---------|-------|----------|
| **CLAUDE.md** | Project context, rules, architecture | User message | High |
| **Output Styles** | Response formatting, behavior | System prompt | Medium |
| **--append-system-prompt** | CLI-specific instructions | System prompt | Highest |

**CLAUDE.md**: "This is my project, here are the rules"
**Output Style**: "This is how you should behave/respond"
**--append-system-prompt**: "For this specific run, do X"

---

## Custom Commands

### What Are Custom Commands?

Custom commands are **saved prompts** you can trigger with `/command-name`.

Think: keyboard shortcuts for complex prompts.

### Creating Commands

#### Project Commands

**Create directory:**
```bash
mkdir -p .claude/commands
```

**Create command file** (`.claude/commands/optimize.md`):
```markdown
---
description: Optimize code for performance
---

Analyze the given code and optimize it for performance:

1. Identify performance bottlenecks
2. Suggest specific optimizations
3. Implement the top 3 improvements
4. Explain the performance impact of each
5. Add performance tests if applicable

Focus on:
- Algorithm efficiency (O(n) complexity)
- Memory usage
- Database query optimization
- Caching opportunities
- Async/await patterns
```

**Use the command:**
```
> /optimize src/utils/dataProcessor.ts
```

#### User Commands

**Create directory:**
```bash
mkdir -p ~/.claude/commands
```

**Create personal command** (`~/.claude/commands/pr-ready.md`):
```markdown
---
description: Prepare code for PR submission
---

Prepare this code for pull request:

1. Run all tests and fix failures
2. Fix all lint errors
3. Update or add documentation
4. Check for console.log or debugging code
5. Verify no sensitive data (API keys, passwords)
6. Run prettier/formatter
7. Update CHANGELOG if it exists
8. Generate PR description summarizing changes

After completing all steps, provide:
- Summary of changes made
- Test results
- Any remaining manual steps needed
```

**Use the command:**
```
> /pr-ready
```

### Commands with Arguments

**Create parameterized command** (`.claude/commands/github-issue.md`):
```markdown
---
description: Analyze GitHub issue and create implementation plan
---

Fetch and analyze GitHub issue #$ARGUMENTS:

1. Read the issue details from GitHub
2. Extract requirements and acceptance criteria
3. Identify affected files and components
4. Create implementation plan with steps
5. Estimate complexity (Small/Medium/Large)
6. List potential risks or unknowns

Provide a structured plan ready for implementation.
```

**Use with argument:**
```
> /github-issue 123
```

`$ARGUMENTS` is replaced with `123`.

### Nested Commands

Organize commands in subdirectories:

```
.claude/commands/
├── frontend/
│   ├── component.md
│   └── optimize-bundle.md
├── backend/
│   ├── api-endpoint.md
│   └── database-migration.md
└── testing/
    ├── unit-test.md
    └── e2e-test.md
```

Commands show scope in description:
```
/component (project:frontend)
/api-endpoint (project:backend)
```

### Command Examples for Developers

**Code review command:**
```markdown
---
description: Comprehensive code review
---

Review the provided code for:

## Correctness
- Logic errors
- Edge cases
- Error handling

## Performance
- Algorithm efficiency
- Unnecessary loops
- Database queries

## Security
- Input validation
- Authentication/authorization
- Data exposure

## Maintainability
- Code clarity
- Documentation
- Test coverage

## Best Practices
- Design patterns
- SOLID principles
- Language idioms

Provide specific, actionable feedback with line numbers.
```

**Test generation command:**
```markdown
---
description: Generate comprehensive test suite
---

Generate tests for the given code:

1. Unit tests for all public functions
2. Edge case tests
3. Error handling tests
4. Integration tests if applicable
5. Mock external dependencies
6. Aim for 80%+ code coverage

Use the project's testing framework and conventions from CLAUDE.md.
```

**Refactoring command:**
```markdown
---
description: Safe refactoring with tests
---

Refactor the given code:

1. Identify refactoring opportunities
2. Create/run existing tests to verify behavior
3. Apply refactoring incrementally
4. Run tests after each change
5. Verify no functionality changed
6. Update documentation

Refactoring types to consider:
- Extract method/function
- Rename for clarity
- Remove duplication
- Simplify conditionals
- Improve naming
```

### Best Practices

**DO:**
- ✅ Create commands for repeated workflows
- ✅ Include clear instructions and structure
- ✅ Reference CLAUDE.md for project context
- ✅ Share team commands via git
- ✅ Test commands before relying on them

**DON'T:**
- ❌ Create too many similar commands
- ❌ Make commands too general (lose focus)
- ❌ Forget to document what commands do
- ❌ Hardcode project-specific paths

---

## Hooks System

### What Are Hooks?

**Hooks** are user-defined shell commands that execute at specific points in Claude Code's lifecycle.

Think: Git hooks, but for AI operations.

### Why Use Hooks?

**Deterministic control**: Certain actions *always* happen (not relying on LLM)

**Use cases:**
- **Notifications**: Alert when Claude needs input
- **Automatic formatting**: Run prettier after file edits
- **Logging**: Track all executed commands
- **Feedback**: Enforce code standards automatically
- **Custom permissions**: Block sensitive file modifications

### Hook Events

| Event | When It Fires | Can Block? |
|-------|---------------|------------|
| `PreToolUse` | Before tool execution | ✅ Yes |
| `PostToolUse` | After tool completes | ❌ No |
| `BeforeMessage` | Before sending to LLM | ❌ No |
| `AfterMessage` | After LLM responds | ❌ No |
| `SessionEnd` | When Claude session ends | ❌ No |

### Quick Start: Logging Bash Commands

**1. Install jq:**
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq
```

**2. Create hook:**
```
> /hooks
[Select PreToolUse]
[Select "+ Add new matcher..."]
[Type "Bash"]
[Select "+ Add new hook..."]
```

**3. Enter command:**
```bash
jq -r '"\(.tool_input.command) - \(.tool_input.description // "No description")"' >> ~/.claude/bash-command-log.txt
```

**4. Choose storage:**
```
[Select "User settings" for all projects]
```

Now all Bash commands Claude runs are logged to `~/.claude/bash-command-log.txt`.

### Hook Structure

**Input**: JSON via stdin
**Output**: Can modify behavior or provide feedback

**PreToolUse hook input:**
```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test",
    "description": "Running test suite"
  }
}
```

**PostToolUse hook input:**
```json
{
  "tool_name": "Write",
  "tool_input": {
    "path": "src/app.ts",
    "content": "..."
  },
  "tool_output": {
    "success": true
  }
}
```

### Creating Hooks

#### Interactive Creation

```
> /hooks
[Select event type]
[Add matchers (tool filters)]
[Add hook commands]
[Choose scope: User or Project]
```

#### Manual Creation

**User hooks** (`~/.claude/hooks/config.json`):
```json
{
  "PreToolUse": [
    {
      "matchers": ["Bash"],
      "hooks": [
        {
          "command": "jq -r '.tool_input.command' >> ~/.claude/bash-log.txt"
        }
      ]
    }
  ]
}
```

**Project hooks** (`.claude/hooks/config.json`):
```json
{
  "PreToolUse": [
    {
      "matchers": ["Write"],
      "hooks": [
        {
          "command": "jq -r '.tool_input.path' | grep -q 'src/production/' && echo 'Cannot modify production files' && exit 1"
        }
      ]
    }
  ],
  "PostToolUse": [
    {
      "matchers": ["Write"],
      "hooks": [
        {
          "command": "prettier --write $(jq -r '.tool_input.path')"
        }
      ]
    }
  ]
}
```

### Hook Examples

#### 1. Automatic Code Formatting

**PostToolUse hook for TypeScript files:**
```bash
# Hook command
jq -r '.tool_input.path' | grep -E '\.(ts|tsx) && prettier --write $(jq -r '.tool_input.path') || true
```

#### 2. Block Sensitive File Modifications

**PreToolUse hook:**
```bash
# Block production config changes
jq -r '.tool_input.path' | grep -q 'config/production.yml' && echo '❌ Cannot modify production config without approval' && exit 1
```

When hook exits with code 1, Claude:
- Receives the error message
- Tool use is blocked
- Claude can try a different approach

#### 3. Slack Notifications

**PreToolUse hook for deployments:**
```bash
#!/bin/bash
command=$(jq -r '.tool_input.command')
if echo "$command" | grep -q 'deploy'; then
  curl -X POST $SLACK_WEBHOOK_URL \
    -H 'Content-Type: application/json' \
    -d "{\"text\": \"🚀 Claude is attempting to deploy: $command\"}"
fi
```

#### 4. Lint Enforcement

**PostToolUse hook:**
```bash
#!/bin/bash
file=$(jq -r '.tool_input.path')
if [[ $file == *.js ]] || [[ $file == *.ts ]]; then
  eslint "$file" --fix
fi
```

#### 5. Test Before Commit

**PreToolUse hook for git commits:**
```bash
#!/bin/bash
command=$(jq -r '.tool_input.command')
if echo "$command" | grep -q 'git commit'; then
  echo "Running tests before commit..."
  npm test || (echo "❌ Tests failed. Cannot commit." && exit 1)
fi
```

#### 6. Security Scanning

**PreToolUse hook:**
```bash
#!/bin/bash
command=$(jq -r '.tool_input.command')
# Block npm install without package-lock
if echo "$command" | grep -q 'npm install' && ! echo "$command" | grep -q 'package-lock.json'; then
  echo "⚠️  Use 'npm ci' instead of 'npm install' to respect package-lock.json"
  exit 1
fi
```

#### 7. Logging All Tool Use

**PostToolUse hook:**
```bash
#!/bin/bash
jq -c '{
  timestamp: now | strftime("%Y-%m-%d %H:%M:%S"),
  tool: .tool_name,
  input: .tool_input
}' >> ~/.claude/tool-log.jsonl
```

### Hook Best Practices

**DO:**
- ✅ Use hooks for deterministic checks
- ✅ Keep hook commands fast (< 1 second)
- ✅ Provide clear error messages
- ✅ Log to files for auditing
- ✅ Test hooks before deploying

**DON'T:**
- ❌ Use hooks for complex logic (use subagents instead)
- ❌ Block tools unnecessarily (frustrates workflow)
- ❌ Create hooks that fail intermittently
- ❌ Forget to handle errors gracefully

---

## Headless Mode & Automation

### What is Headless Mode?

**Headless mode** (non-interactive) allows Claude Code to run programmatically from scripts, cron jobs, and CI/CD pipelines.

### Basic Usage

**Print mode** (`-p` or `--print`):
```bash
# Single command
claude -p "What does this project do?"

# With file context
cd /path/to/project
claude -p "Explain the authentication flow"

# Output to file
claude -p "Generate API documentation" > docs/api.md
```

### Output Formats

#### Text (Default)

```bash
claude -p "Summarize changes in git diff"
# Output: Plain text response
```

#### JSON

```bash
claude -p "Analyze this code" --output-format json
```

**Output structure:**
```json
{
  "result": "The code implements...",
  "usage": {
    "input_tokens": 1250,
    "output_tokens": 450
  },
  "cost_usd": 0.0125,
  "conversation_id": "550e8400-...",
  "session_id": "550e8400-..."
}
```

**Parse with jq:**
```bash
result=$(claude -p "Generate code" --output-format json)
code=$(echo "$result" | jq -r '.result')
cost=$(echo "$result" | jq -r '.cost_usd')
echo "Cost: $cost"
```

#### Streaming JSON

```bash
claude -p "Explain this file" --output-format stream-json
```

Each line is a complete JSON object (JSONL format).

### Automation Flags

```bash
# Permission modes
claude -p "Fix bugs" --permission-mode acceptAll  # Auto-accept all edits
claude -p "Review code" --permission-mode plan     # Plan-only mode

# Tool restrictions
claude -p "Analyze" --allowedTools "Read,Grep"     # Limit tools
claude -p "Review" --disallowedTools "Bash"        # Block specific tools

# Model selection
claude -p "Complex task" --model opus
claude -p "Simple task" --model haiku

# Continue conversations
claude --continue "Now add tests"                   # Continue last
claude --resume <session-id> "Update docs"         # Resume specific
claude -p --continue "Refactor for performance"    # Non-interactive continue
```

### Multi-turn Conversations

**Resume previous session:**
```bash
# Interactive: shows conversation picker
claude --resume

# Non-interactive: continue most recent
claude -p --continue "Add error handling"

# Resume specific session
SESSION_ID="550e8400-e29b-41d4-a716-446655440000"
claude -p --resume $SESSION_ID "Update tests"
```

### Streaming JSON Input

For complex multi-turn automation:

```bash
echo '{"type":"user","message":{"role":"user","content":[{"type":"text","text":"Explain this code"}]}}' | \
  claude -p --output-format stream-json --input-format stream-json
```

**Use case**: Building custom AI agents that need multi-turn conversations.

### Scripting Examples

#### 1. Automated Code Review

```bash
#!/bin/bash
# review.sh - Review all changed files

# Get changed files
files=$(git diff --name-only main)

for file in $files; do
  echo "Reviewing $file..."
  
  result=$(claude -p "Review @$file for code quality, security, and best practices. Provide specific feedback." \
    --output-format json \
    --permission-mode plan)
  
  feedback=$(echo "$result" | jq -r '.result')
  
  # Save to review file
  echo "# Review: $file" >> review-report.md
  echo "$feedback" >> review-report.md
  echo "" >> review-report.md
done

echo "Review complete! See review-report.md"
```

#### 2. Automated Testing

```bash
#!/bin/bash
# auto-test.sh - Generate and run tests

claude -p "Generate unit tests for all files in src/utils/ that don't have tests" \
  --permission-mode acceptAll

# Run tests
npm test

# If tests fail, ask Claude to fix
if [ $? -ne 0 ]; then
  claude -p "Tests are failing. Fix the issues." \
    --permission-mode acceptAll
fi
```

#### 3. Daily Dependency Update

```bash
#!/bin/bash
# update-deps.sh - Check and update dependencies

# Check for updates
claude -p "Check for outdated npm dependencies and suggest updates" \
  --output-format json > deps-check.json

updates=$(cat deps-check.json | jq -r '.result')

if [ -n "$updates" ]; then
  # Send Slack notification
  curl -X POST $SLACK_WEBHOOK \
    -d "{\"text\": \"📦 Dependency updates available:\n$updates\"}"
fi
```

#### 4. Incident Response Agent

```bash
#!/bin/bash
# incident-response.sh

investigate_incident() {
  local incident="$1"
  local severity="${2:-medium}"
  
  claude -p "Incident: $incident (Severity: $severity)" \
    --append-system-prompt "You are an SRE expert. Analyze logs, identify root cause, suggest fixes." \
    --allowedTools "Read,Bash,Grep" \
    --output-format json
}

# Usage
investigate_incident "API latency spike in /users endpoint" "high"
```

#### 5. Documentation Generator

```bash
#!/bin/bash
# generate-docs.sh

claude -p "Generate comprehensive documentation for this project:
1. README.md with setup instructions
2. API.md with all endpoints
3. CONTRIBUTING.md with development guidelines
4. CHANGELOG.md from git history" \
  --permission-mode acceptAll \
  --model opus

echo "Documentation generated!"
```

#### 6. PR Summary Generator

```bash
#!/bin/bash
# pr-summary.sh

# Get PR number from argument
PR_NUM=$1

# Get diff
git diff main > /tmp/pr-diff.txt

# Generate summary
claude -p "Summarize this PR diff in markdown:
- Overview of changes
- Files modified
- Key improvements
- Breaking changes
- Testing notes

$(cat /tmp/pr-diff.txt)" \
  --output-format text > pr-summary.md

echo "PR summary saved to pr-summary.md"
```

### Error Handling

```bash
#!/bin/bash

set -e  # Exit on error

# Capture both stdout and exit code
if output=$(claude -p "Fix the bug" 2>&1); then
  echo "Success: $output"
else
  exit_code=$?
  echo "Error: Claude failed with exit code $exit_code"
  echo "Output: $output"
  
  # Alert team
  curl -X POST $SLACK_WEBHOOK \
    -d "{\"text\": \"❌ Claude automation failed: $output\"}"
  
  exit $exit_code
fi
```

### Cron Job Example

```bash
# crontab -e
# Run security scan daily at 2 AM
0 2 * * * cd /path/to/project && /usr/local/bin/claude -p "Run security audit on all code. Report any vulnerabilities." --output-format json > /var/log/claude-security-$(date +\%Y\%m\%d).json
```

### Best Practices for Automation

**DO:**
- ✅ Use `--permission-mode acceptAll` for fully automated tasks
- ✅ Restrict tools with `--allowedTools` for security
- ✅ Use `--output-format json` for parsing results
- ✅ Handle errors and exit codes properly
- ✅ Log all automation runs
- ✅ Set timeouts for long-running tasks

**DON'T:**
- ❌ Run automation without testing manually first
- ❌ Give automation full Bash access without restrictions
- ❌ Ignore error handling
- ❌ Run in production without review
- ❌ Forget to monitor costs

---

## GitHub Actions & CI/CD

### GitHub Actions Integration

Claude Code can automate workflows directly in your GitHub repository via pull requests and issues.

### Quick Setup

**Option 1: Interactive Setup (Easiest)**

```bash
cd /path/to/your/repo
claude

> /install-github-app
[Follow prompts to install app and configure secrets]
```

**Requirements:**
- Repository admin access
- Direct Claude API user (not Bedrock/Vertex)

**Option 2: Manual Setup**

1. **Install GitHub App**: https://github.com/apps/claude
2. **Add Secret**: Add `ANTHROPIC_API_KEY` to repository secrets
3. **Add Workflow**: Copy workflow file to `.github/workflows/claude.yml`

### Example Workflow File

`.github/workflows/claude.yml`:
```yaml
name: Claude Code

on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened]

jobs:
  claude:
    runs-on: ubuntu-latest
    if: contains(github.event.comment.body, '@claude') || github.event_name == 'issues'
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for better context
      
      - name: Run Claude Code
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Usage in GitHub

**In Pull Requests:**
```
@claude review this PR for security issues
@claude add tests for the new authentication logic
@claude fix the failing CI checks
@claude update documentation for these API changes
```

**In Issues:**
```
@claude implement this feature request
@claude investigate this bug and create a fix PR
@claude refactor the database module for better performance
```

Claude will:
1. Analyze the issue/PR
2. Create a new branch
3. Make necessary changes
4. Create a pull request with implementation
5. Comment on the original issue/PR with status

### Advanced Configuration

**Custom workflow with AWS Bedrock:**

```yaml
name: Claude Code (Bedrock)

on:
  issue_comment:
    types: [created]

jobs:
  claude:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # For OIDC
      contents: write
      pull-requests: write
      issues: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1
      
      - name: Run Claude Code
        env:
          AWS_REGION: us-east-1
          AWS_BEDROCK_MODEL: anthropic.claude-3-5-sonnet-20241022
        run: |
          npm install -g @anthropic-ai/claude-code
          claude -p "${{ github.event.comment.body }}" \
            --permission-mode acceptAll
```

**Custom workflow with Google Vertex AI:**

```yaml
name: Claude Code (Vertex)

on:
  issue_comment:
    types: [created]

jobs:
  claude:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: write
      pull-requests: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: 'projects/123/locations/global/workloadIdentityPools/github/providers/github'
          service_account: 'github-actions@project.iam.gserviceaccount.com'
      
      - name: Run Claude Code
        env:
          GOOGLE_CLOUD_PROJECT: my-project
          GOOGLE_CLOUD_REGION: us-central1
        run: |
          npm install -g @anthropic-ai/claude-code
          claude -p "${{ github.event.comment.body }}" \
            --permission-mode acceptAll
```

### GitLab CI/CD

`.gitlab-ci.yml`:
```yaml
claude-review:
  stage: review
  image: node:18
  script:
    - npm install -g @anthropic-ai/claude-code
    - |
      claude -p "Review the changes in this MR:
      - Code quality
      - Security issues
      - Best practices
      - Test coverage
      
      Provide specific, actionable feedback." \
        --output-format json > review.json
    - cat review.json | jq -r '.result' > review-report.md
  artifacts:
    paths:
      - review-report.md
    expire_in: 1 week
  only:
    - merge_requests

claude-test:
  stage: test
  image: node:18
  script:
    - npm install -g @anthropic-ai/claude-code
    - |
      claude -p "Generate and run tests for code changes:
      1. Identify untested code
      2. Generate comprehensive test suite
      3. Run tests and fix failures
      4. Report coverage" \
        --permission-mode acceptAll
  only:
    - merge_requests
```

### CI/CD Best Practices

**DO:**
- ✅ Use `--permission-mode acceptAll` for automated changes
- ✅ Restrict tool access with `--allowedTools`
- ✅ Set appropriate timeouts
- ✅ Use secrets for API keys
- ✅ Review generated PRs before merging
- ✅ Monitor costs (token usage)

**DON'T:**
- ❌ Auto-merge Claude's PRs without review
- ❌ Give unrestricted Bash access
- ❌ Deploy directly to production
- ❌ Ignore error handling
- ❌ Run on every commit (cost!)

### Example Use Cases

**1. Automated Code Review:**
```
@claude review this PR focusing on:
- Security vulnerabilities
- Performance issues
- Code duplication
- Test coverage gaps
```

**2. Bug Fix Automation:**
```
@claude investigate this bug and create a PR with:
- Root cause analysis
- Fix implementation
- Test cases to prevent regression
- Documentation updates
```

**3. Feature Implementation:**
```
@claude implement this feature:
- Add user profile page
- Include avatar upload
- Add edit functionality
- Write tests
- Update API documentation
```

**4. Refactoring:**
```
@claude refactor the authentication module:
- Convert to TypeScript
- Add proper error handling
- Improve test coverage
- Update documentation
```

---

## Model Context Protocol (MCP)

### What is MCP?

**Model Context Protocol** is a standard for connecting AI models to external data sources and tools. MCP servers expose:

- **Resources**: Data to read (files, API responses, database records)
- **Tools**: Actions to perform (create ticket, send message, update database)
- **Prompts**: Reusable prompt templates

### Why Use MCP?

Extend Claude Code with:
- **Google Drive**: Read strategy docs, PRDs
- **Slack**: Search conversations, post updates
- **Jira/Linear**: Read tickets, update status
- **Figma**: Reference designs
- **Notion**: Access documentation
- **PostgreSQL**: Query databases
- **GitHub**: Review PRs, issues

### Installing MCP Servers

#### Quick Add Commands

**Pre-configured servers:**
```bash
# Development tools
claude mcp add sentry --transport http https://mcp.sentry.dev/mcp
claude mcp add github --transport http https://mcp.github.com/mcp

# Project management
claude mcp add linear --transport sse https://mcp.linear.app/sse
claude mcp add jira --transport sse https://mcp.atlassian.com/v1/sse
claude mcp add asana --transport sse https://mcp.asana.com/sse

# Design & collaboration
claude mcp add figma --transport http http://127.0.0.1:3845/mcp
claude mcp add notion --transport http https://mcp.notion.com/mcp
claude mcp add slack --transport http https://mcp.slack.com/mcp

# Business tools
claude mcp add hubspot --transport http https://mcp.hubspot.com/anthropic
claude mcp add stripe --transport http https://mcp.stripe.com
claude mcp add intercom --transport http https://mcp.intercom.com/mcp
```

**With environment variables:**
```bash
claude mcp add clickup \
  --env CLICKUP_API_KEY=your_key \
  --env CLICKUP_TEAM_ID=your_id \
  -- npx -y @hauptsache.net/clickup-mcp
```

#### MCP Scopes

```bash
# Local (you, this project) - default
claude mcp add myserver -- npx server

# Project (shared via .mcp.json in git)
claude mcp add --scope project myserver -- npx server

# User (you, all projects)
claude mcp add --scope user myserver -- npx server
```

### Understanding `--` (Double Dash)

Everything **before** `--` is for Claude's config:
```bash
claude mcp add myserver --env KEY=value --scope project
```

Everything **after** `--` is the command to run the MCP server:
```bash
-- npx @myorg/mcp-server --port 8080
```

**Complete example:**
```bash
claude mcp add myserver --env API_KEY=abc123 --scope project -- python server.py --port 8080
```

**Windows users**: Must use `cmd /c` wrapper:
```cmd
claude mcp add myserver -- cmd /c npx @myorg/mcp-server
```

### Project-Level MCP Configuration

When using `--scope project`, Claude creates `.mcp.json`:

```json
{
  "mcpServers": {
    "linear": {
      "command": "npx",
      "args": ["-y", "@linear/mcp-server"],
      "env": {
        "LINEAR_API_KEY": "${LINEAR_API_KEY}"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_URL": "${POSTGRES_URL}"
      }
    }
  }
}
```

**Environment variable expansion:**
- `${VAR}` - Expands to value of VAR
- `${VAR:-default}` - Use VAR if set, otherwise "default"

**Add .mcp.json to git** so team shares the same tools!

**Keep secrets out of git** - use environment variables:
```bash
# .env.local (git-ignored)
LINEAR_API_KEY=lin_api_...
POSTGRES_URL=postgresql://...
```

### Using MCP Resources

**View available resources:**
```
> @[press Tab]
```

Resources appear in autocomplete:
```
@linear:project://PROJ-123
@gdrive:file://1A2B3C4D5E6F
@notion:page://abc123
```

**Reference in prompts:**
```
> summarize @linear:project://ENG-2025-Q1
> compare @gdrive:file://strategy-doc with our current roadmap
> review @github:pr://123 for security issues
```

**Multiple resources:**
```
> compare @linear:issue://ENG-456 with @jira:issue://PROJ-789 and identify differences in approach
```

### Using MCP Prompts

**View available prompts:**
```
> /[press Tab]
```

MCP prompts appear as `/mcp__servername__promptname`.

**Execute prompt:**
```
> /mcp__linear__create_issue
[Follow interactive prompts]
```

**With arguments:**
```
> /mcp__github__review_pr 123
```

### Using MCP Tools

MCP tools are automatically available to Claude. Just ask:

```
> create a Linear issue for this bug
> search Slack for conversations about the Q4 roadmap
> query the database for user signup trends
> update the Jira ticket with these findings
> send a message to #engineering channel
```

Claude automatically uses the appropriate MCP tool.

### OAuth Authentication

Some MCP servers require OAuth. Use the interactive menu:

```
> /mcp
[Select server requiring auth]
[Complete OAuth flow in browser]
```

**Reset authentication:**
```bash
claude mcp reset-project-choices
```

### Managing MCP Servers

**List installed servers:**
```bash
claude mcp list
```

**Remove server:**
```bash
claude mcp remove server-name
```

**Import from Claude Desktop:**
```bash
claude mcp import-from-claude-desktop
[Select which servers to import]
[Choose scope: user or project]
```

### Troubleshooting MCP

**Connection issues:**
```bash
# Set timeout (default: 5000ms)
MCP_TIMEOUT=10000 claude
```

**Large outputs:**
```bash
# Increase token limit (default: 10000)
MAX_MCP_OUTPUT_TOKENS=50000 claude
```

**Debug connection:**
```bash
claude --verbose
```

### Example MCP Workflows

#### Workflow 1: Ticket-Driven Development

```
> /mcp
[Authenticate with Linear]

> show me all my assigned tickets
> explain the requirements for LINEAR-123
> implement the feature described in LINEAR-123
> update LINEAR-123 with implementation notes
> create a PR linked to LINEAR-123
```

#### Workflow 2: Design Implementation

```
> /mcp
[Authenticate with Figma]

> show me the designs for the user profile page
> implement the design from @figma:frame://abc123
> compare my implementation to @figma:frame://abc123
```

#### Workflow 3: Data-Driven Decisions

```
> /mcp
[Connect to PostgreSQL]

> query the database for user retention by cohort
> analyze the results and suggest product improvements
> create a Linear issue for the top recommendation
> draft a Slack message to #product with findings
```

---

## IDE Integrations

### Supported IDEs

Claude Code integrates with:
- **VS Code** (including Cursor, Windsurf, VSCodium)
- **JetBrains IDEs** (IntelliJ, PyCharm, WebStorm, PhpStorm, GoLand, Android Studio)

### Features

All IDE integrations provide:
- **Quick launch**: `Cmd/Ctrl + Esc` to open Claude
- **Diff viewing**: See changes in IDE's diff viewer
- **Selection context**: Current file/selection auto-shared
- **File references**: Easy `@file` insertion

### VS Code Setup

**1. Install extension:**
- Open VS Code
- Search "Claude Code" in marketplace
- Install official extension

**2. Launch Claude:**
```
Cmd + Esc (Mac)
Ctrl + Esc (Windows/Linux)
```

Or click Claude Code icon in sidebar.

**3. Configure:**
```
> /config
```

Set diff tool to `auto` for IDE detection.

### JetBrains Setup

**1. Install plugin:**
- Open IDE
- Settings → Plugins
- Search "Claude Code"
- Install and restart

**2. Connect terminal:**
```
> /ide
```

**3. Configure (optional):**

Settings → Tools → Claude Code:
- **Claude command**: Path to claude binary
- **Suppress notifications**: Skip "command not found" alerts
- **Option+Enter for newlines**: macOS multi-line support
- **Auto-updates**: Keep plugin current

### IDE-Specific Features

**VS Code:**
- Sidebar integration
- Native diff viewer
- Extension ecosystem
- Remote development support

**JetBrains:**
- Built-in diff viewer
- Diagnostic sharing (lint/syntax errors)
- Powerful refactoring tools
- Database tools integration

### Working with IDEs

**Selection context:**
```
[Select code in IDE]
> explain this code
> refactor this for better performance
> add error handling here
```

Claude automatically has your selection as context.

**File shortcuts:**
```
Cmd/Ctrl + Option/Alt + K
```
Inserts `@file` reference at cursor.

**Diff viewing:**

When Claude modifies files:
1. Changes appear in IDE diff viewer
2. Review side-by-side
3. Accept or reject changes
4. Edit inline before accepting

### Remote Development

**VS Code Remote:**
Works automatically with:
- WSL
- SSH
- Dev Containers
- GitHub Codespaces

**JetBrains Remote:**
- Install plugin on **remote host**, not local
- Use `/ide` command to connect
- Configure Claude command path

### Troubleshooting IDEs

**ESC key not working (JetBrains):**

Settings → Advanced Settings → Terminal:
```
☑ Override IDE shortcuts in terminal
```

**Claude command not found:**

1. Verify installation:
```bash
which claude
```

2. Add to PATH or configure full path in IDE settings:
```
/usr/local/bin/claude
```

**IDE not detected:**

1. Ensure IDE CLI is installed:
```bash
# VS Code
code --version

# JetBrains
idea --version
```

2. Run from project root
3. Use `/ide` command manually

**WSL issues:**

Configure Claude command as:
```
wsl -d Ubuntu -- bash -lic "claude"
```

---

## Git Workflows

### Conversational Git

```
> what files have I changed?
> show me my uncommitted changes
> what's the current branch?
> show me recent commits
> what branches exist?
```

### Making Commits

**Simple commit:**
```
> commit my changes with a descriptive message
```

Claude analyzes changes and writes conventional commits.

**Staged commits