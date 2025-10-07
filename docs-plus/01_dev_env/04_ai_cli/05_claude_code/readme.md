# [Claude Code](https://www.claude.com/product/claude-code) (Premium)

Claude Code empowers anyone who can describe a problem to start building a solution. You don't have to be a senior developer to tackle complex problems. If you can clearly articulate a goal—whether it's building a new feature, analyzing a dataset, or creating a script to automate a task—you can use Claude to help you achieve it.

Think of this tool not just as a code writer, but as your personal AI pair programmer, debugger, and mentor, living right inside your terminal.

**Prerequisites:**

*   **Claude Pro or Max Subscription:** The Claude Code CLI is a premium tool and requires a paid subscription.
*   **Node.js & npm:** You must have Node.js (version 18 or higher) installed. **Important:** This is only to run the Claude Code tool itself. You can use it to work on projects in any programming language, like Python, Go, or Rust.

---

## **1. Setup: Your First Two Minutes**

Getting started is incredibly simple.

**Step 1: Install the CLI**
Open your terminal and run the following command. This installs the `claude` command globally on your machine.

```bash
npm install -g @anthropic-ai/claude-code
```

**Step 2: Authenticate**
Navigate to the root directory of any project you want to work on (or even an empty folder) and launch the agent:

```bash
claude
```

The first time you run this, a browser window will open, prompting you to log in to your Claude account. This one-time authentication links the CLI to your paid subscription, and you're ready to go.

---

## **2. The Command Palette: Your Basic Toolkit**

You interact with the agent using natural language and special "slash commands." To see all available commands at any time, simply type `/help`.

Here are the most essential commands you'll use every day:

| Command | Description |
| :--- | :--- |
| `/add` or `/add-dir` | Adds specific files or entire directories to Claude's working context. This is crucial for focusing its attention. |
| `/clear` | Clears the current conversation, giving you a fresh start. |
| `/model` | Allows you to switch between different Claude models (e.g., Sonnet for speed, Opus for power) depending on your task. |
| `/init` | Creates a `CLAUDE.md` file in your project. This file acts as the agent's long-term memory for your project. |
| `/memory` | Opens the `CLAUDE.md` file for editing directly from the CLI. |
| `/search` | Performs a web search and adds the results to the context. Perfect for fetching documentation on a new library. |
| `/review` | Asks Claude to perform a code review on your recent changes (it uses `git diff`). |
| `/run` | Allows Claude to execute shell commands (like `git commit` or `npm install`). It will always ask for your approval first. |

---

## **3. Quickstart: Building a Python CLI Calculator**

Let's build a simple command-line calculator from scratch. This will demonstrate the core workflow of creating, modifying, and testing code with the agent.

**Step 1: Create and Enter Project Directory**
In your regular terminal (not the Claude prompt), create a new folder for our project.

```bash
mkdir python-calculator
cd python-calculator
```

**Step 2: Launch Claude and Give Instructions**
Now, launch the agent from within your new project directory.

```bash
claude
```

Once you see the Claude prompt, type the following request:

> **Create a simple command-line calculator in Python. The main file should be named `calculator.py`. It should use the `sys` module to take three arguments: a number, an operator (+, -, \*, /), and another number, then print the result.**

Claude will analyze your request and propose creating a new file, `calculator.py`, with the necessary code. It will show you a "diff" of the changes.

**Step 3: Approve the Changes**
Press `y` and `Enter` to approve the file creation. You now have a working calculator!

**Step 4: Add Error Handling**
Let's make it more robust. In the same Claude session, ask it to improve the code:

> **Now, add error handling to `calculator.py`. It should check if the correct number of arguments are provided and also handle invalid operators. Print a user-friendly message for each error.**

Again, Claude will propose changes to the existing `calculator.py` file. Review the diff and approve it by pressing `y`.

**Step 5: Test Your Application**
Exit the Claude session by pressing `Ctrl+C`. You are now back in your regular terminal. You can test your new calculator:

```bash
# Run a valid calculation
python calculator.py 10 "*" 5
# Expected output: 50.0

# Test the error handling
python calculator.py 10
# Expected output: Usage: python calculator.py <num1> <operator> <num2>
```

Congratulations, you've just built and improved a project with an AI agent!

---

## **4. Thinking Like an Agent: Core Concepts & Techniques**

To unlock Claude's full potential, you need to understand *how* to work with it.

**A. Plan Mode: Safe Code Analysis**
For complex or sensitive tasks, you can instruct Claude to create a detailed plan *before* making any changes. In "Plan Mode," the agent will only perform read-only operations. This is perfect for planning a large refactor or exploring a new codebase without fear of accidental changes.

*   **How to Activate:**
    *   Start a session in Plan Mode: `claude --permission-mode plan`
    *   Toggle it during a session: Press `Shift+Tab` until you see the `plan mode on` indicator.

**B. Using Tools and Referencing Files**
Claude can integrate with your existing tools and quickly reference files.

*   **File and Directory References (`@`):** To instantly add the content of a file or the structure of a directory to the conversation, use the `@` symbol. This is much faster than waiting for Claude to find files on its own.
    *   `> Explain the logic in @src/utils/auth.py`
    *   `> What is the structure of the @src/components directory?`
*   **Tool Use (`/run`):** Claude can run shell commands, including your favorite tools like `git` or the GitHub CLI (`gh`). For example, you can ask Claude to summarize your changes and then create a pull request:
    *   `> summarize my changes and then use git to create a new branch named "feature/user-export" and commit the changes with the summary as the message`

**C. Extended Thinking for Complex Problems**
For difficult architectural problems or deep bugs, tell Claude to "think harder." This enables a special mode where Claude takes more time to reason about the problem, consider alternatives, and provide a more thorough answer.

*   **How to Activate:** Press `Tab` in your terminal or simply include phrases like "think deeply" or "take your time and think step-by-step" in your prompt.

---
## **5. Extend Claude Code with MCP servers

Claude Code supports Model Context Protocol servers to add capabilities like browser automation, search, and memory.

### Setup principles

- Work inside your project folder so `.claude/` or `CLAUDE.md` settings apply.
- Store API keys in environment variables (`export KEY=value`) rather than committing them.
- Verify server registration with `/mcp` inside a Claude session.

### Configure MCP servers (example)

Create or extend a config file (the exact location depends on the Claude CLI version; consult the official docs). A typical JSON snippet might look like:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp", "--api-key", "YOUR_API_KEY"]
    }
  }
}
```

Restart the CLI and type `/mcp` to confirm both servers loaded. You can then prompt: "Use Playwright to open example.com and take a screenshot" or "Context7, search for the latest Claude API docs."


## **6. Practical Workflows for Everyday Development**

Claude excels at more than just writing new code. It's a partner for the entire development lifecycle.

**A. Debugging: Your AI Pair Programmer**
Stuck on a bug?
1.  **Provide Context:** Paste the full error message and stack trace directly into the prompt.
2.  **Describe the Problem:** Explain what you were doing. For example: `> I'm seeing this error when I run my Flask app. It happens when I try to access the /profile page.`
3.  **Let Claude Investigate:** Claude will analyze the error, read the relevant files in your codebase, and propose a fix.

**B. Refactoring and Modernizing a Codebase**
Safely update legacy code with Claude's help.
1.  **Identify Targets:** Ask Claude to find areas for improvement. `> find any Python 2 syntax in this project and suggest how to update it to Python 3` or `> suggest how to refactor user_service.py to be more modular`.
2.  **Verify the Changes:** After approving the code changes, immediately ask Claude to use your testing tools. `> run the tests using pytest to confirm the refactor was successful`.

**C. Learning a New Codebase**
When joining a new project, use Claude as your personal onboarding guide.
1.  **Get an Overview:** Start broad. `> give me a high-level overview of this Django project`.
2.  **Ask Specific Questions:** Drill down. `> explain the purpose of the models in the 'orders' app` or `> how is user authentication handled?`
3.  **Trace the Flow:** Understand connections. `> trace the "create new order" process from the API view to the database`.

**D. Configuration via `CLAUDE.md` and workspace files**

Claude Code uses a few locations to store context and settings:

1. **`CLAUDE.md`** (project root) — The agent's persistent memory. Create it with `/init` and edit with `/memory`. Add project-specific instructions, custom commands, and coding standards here.
2. **`.claude/` directory** (optional) — Some teams store reusable slash commands or custom workflows in this folder.
3. **User-level config** — Claude stores your auth tokens and global preferences in a system directory (exact path varies by OS).


## **7. Sub-Agents and Other Essential Concepts

**Sub-Agents**
Sub-agents are spawned to handle specific sub-tasks. The key takeaway is that you can (and should) give the agent large, complex goals. The agent is designed to decompose the problem, assign work to sub-agents, and synthesize the results.

## 8. Best Practices from Anthropic's Own Teams

The teams at Anthropic use Claude Code daily. Here's how they get the most value out of it.

**A. Treat it as a Thought Partner, Not Just a Code Generator**
The most effective users don't just ask Claude to write code; they use it to explore ideas, map out logic flows, and identify edge cases _before_ development even begins. A product designer might ask Claude to map out all possible error states for a new feature to improve the initial design.

**B. Automate Repetitive Tasks**
Many teams automate tedious but critical parts of their workflow:

- **Test Generation:** Use Claude to write comprehensive unit tests for new features.
- **Code Reviews:** Set up GitHub Actions that ask Claude to comment on pull requests, flagging formatting issues or suggesting refactors.
- **Documentation:** Have Claude ingest multiple source files to create condensed markdown runbooks and troubleshooting guides.

**C. Combine Technical and Non-Technical Work**
Claude Code blurs the line between technical and non-technical roles. For example:

- **Marketers** at Anthropic use agents to process CSVs of ad copy, identify underperformers, and generate hundreds of new variations in minutes.
- The **Legal team** built a prototype "phone tree" system to help employees find the right lawyer, all without needing dedicated engineering resources.

This demonstrates that anyone who can clearly describe a problem can use Claude Code to start building a solution.

- https://docs.claude.com/en/docs/claude-code/overview
- [workflows](https://docs.claude.com/en/docs/claude-code/sub-agents)
- https://www-cdn.anthropic.com/58284b19e702b49db9302d5b6f135ad8871e7658.pdf
