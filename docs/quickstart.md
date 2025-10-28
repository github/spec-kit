# Quick Start Guide

This guide will help you get started with Spec-Driven Development using Spec Kit.

> **Important**: There are two ways to interact with Specify; pick the right one for your workflow:
>
> - CLI: run the `specify` command (no leading slash) in your terminal.
> - Slash commands (AI assistant): use `/speckit.specify`, `/speckit.plan`, etc., inside an AI assistant or editor that supports slash commands (for example, GitHub Copilot Chat). Do not remove the leading slash — these commands rely on the slash prefix to trigger the assistant correctly.
>
> See the [VS Code Usage Guide](vscode-usage.md) for details on where to run each type of command.

| Command Type | Where to Run | Example | Notes |
|-------------|--------------|---------|--------|
| CLI Commands | Terminal (Bash, PowerShell) | `specify init <PROJECT_NAME>` | No leading slash |
| Slash Commands | AI Assistant (e.g., GitHub Copilot Chat) | `/speckit.specify ...` | Requires leading slash |

> NEW: All automation scripts now provide both Bash (`.sh`) and PowerShell (`.ps1`) variants. The `specify` CLI auto-selects based on OS unless you pass `--script sh|ps`.

## The 4-Step Process

### 1. Install Specify

Initialize your project using the CLI:

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>
```

Pick script type explicitly (optional):

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME> --script ps  # Force PowerShell
uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME> --script sh  # Force POSIX shell
```

### 2. Create the Spec

Use the `/speckit.specify` slash command (in an AI assistant or editor that supports slash commands) to describe what you want to build. Focus on the **what** and **why**, not the tech stack. The slash command is intended to be consumed by an AI assistant and is different from the CLI `specify` command (no slash) which you run in a terminal.

If you use a coding agent, some agents may try to rewrite or "improve" your prompt. Make the difference from step 1 explicit in your slash prompt. For example, include an explicit instruction such as:

```
Do NOT change or implement this spec; only return the specification text focusing on requirements and acceptance criteria.
```

Keeping the `/speckit` prefix is important — removing it will break slash command behavior.

Example (slash command used in the assistant/chat):

```text
/speckit.specify Build an application that can help me organize my photos in separate photo albums. Albums are grouped by date and can be re-organized by dragging and dropping on the main page. Albums are never in other nested albums. Within each album, photos are previewed in a tile-like interface.

Note: Do NOT change or implement this spec; only return the spec text focusing on requirements and acceptance criteria.
```

If you prefer the terminal, you can still run the CLI version (no leading slash):

```bash
specify "Build an application that can help me organize my photos in separate photo albums..."
```

### 3. Create a Technical Implementation Plan

Use the plan command to provide your tech stack and architecture choices.

```text
/speckit.plan The application uses Vite with minimal number of libraries. Use vanilla HTML, CSS, and JavaScript as much as possible. Images are not uploaded anywhere and metadata is stored in a local SQLite database.
```

### 4. Break Down and Implement

In **Copilot Chat**, run:

```text
/speckit.tasks
```
Then:

```text
/speckit.implement
```

Let the AI generate tasks, write code, run tests, and fix bugs — all from your specs!

## Running Commands and Troubleshooting

> **Note**: Always run CLI commands in your terminal and slash commands in your AI assistant. See our [VS Code Usage Guide](vscode-usage.md) for setup instructions.

### Common Issues and Solutions

- **Command not found**: Ensure `uvx` is installed (`pip install uvx`)
- **Wrong script type**: Use `--script ps` (PowerShell) or `--script sh` (Bash) to override auto-selection
- **Slash commands not working**: Verify your AI assistant supports slash commands and the `/speckit` prefix is included
- **Environment errors**: Check Python/Node.js installation and PATH settings
- **Git access issues**: Verify your Git credentials and repository access

## Detailed Example: Building Taskify

Here's a complete example of building a team productivity platform:

### Step 1: Define Requirements with `/speckit.specify`

```text
/speckit.specify Develop Taskify, a team productivity platform. Predefine 5 users: 1 product manager, 4 engineers. Create 3 sample projects with Kanban columns: To Do, In Progress, In Review, Done. No login. Drag-and-drop tasks. Highlight user-assigned tasks. Allow editing/deleting own comments only.

Note: Do NOT implement — only return the spec.
```

For more detailed requirements:

```text
/speckit.specify Build a team productivity platform with these core features:

1. Users and Authentication:
   - 5 predefined users (1 PM, 4 engineers)
   - No login system (simplified first version)
   - User selection from list on startup

2. Project Structure:
   - 3 sample projects
   - Kanban board per project
   - Columns: To Do, In Progress, In Review, Done
   - 5-15 tasks per project
   - At least one task per column

3. Task Management:
   - Drag-and-drop between columns
   - Assign users to tasks
   - Highlight tasks assigned to current user
   - Unlimited comments per task
   - Users can edit/delete their own comments only

Note: Do NOT implement — only return the spec.
```

### Step 2: Refine the Specification

After the initial specification is created, clarify any missing requirements:

```text
For each sample project or project that you create there should be a variable number of tasks between 5 and 15
tasks for each one randomly distributed into different states of completion. Make sure that there's at least
one task in each stage of completion.
```

Also validate the specification checklist:

```text
Read the review and acceptance checklist, and check off each item in the checklist if the feature spec meets the criteria. Leave it empty if it does not.
```

### Step 3: Generate Technical Plan with `/speckit.plan`

Be specific about your tech stack and technical requirements:

```text
/speckit.plan Generate a plan using:
- Backend: .NET Aspire with Postgres database
- Frontend: Blazor server with drag-and-drop task boards
- APIs: REST endpoints for projects, tasks, and notifications
- Features: Real-time updates, drag-and-drop UI
```

### Step 4: Validate and Implement

Have your AI agent audit the implementation plan:

```text
Now I want you to go and audit the implementation plan and the implementation detail files.
Read through it with an eye on determining whether or not there is a sequence of tasks that you need
to be doing that are obvious from reading this. Because I don't know if there's enough here.
```

Generate the implementation:

```text
/speckit.implement specs/002-create-taskify/plan.md
```

## Key Principles

- **Be explicit** about what you're building and why
- **Don't focus on tech stack** during specification phase
- **Iterate and refine** your specifications before implementation
- **Validate** the plan before coding begins
- **Let the AI agent handle** the implementation details

## Next Steps

- Read the complete methodology in our 
[documentation](docs/methodology.md)
- Try the examples in the
 [samples repository](docs/samples.md)
- Join our 
[community](CONTRIBUTING.md)
for tips and support
