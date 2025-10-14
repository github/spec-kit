# [Context7](https://context7.com/): Live Documentation via MCP

> Make Your AI Coding Agent Smarter with Context7

Your AI coding assistant (like Claude, Cursor, or Copilot) is a student who only has textbooks from last year. They're smart, but they don't know about any new tools or code changes that happened this year. This means they sometimes give you old, incorrect advice.

Context7 is like giving your AI helper an always-updated, online library. When you ask it to code something, Context7 finds the newest, correct instructions and gives them to the AI. This helps your AI write better code and avoid mistakes.

Key properties:
- Delivers live documentation and examples for specific library versions
- Intended for use via MCP in editors/agents (e.g., Cursor)
- Complements your coding assistant by grounding replies in real docs

---

## Why Use Context7 {#why-context7}

Without live docs, assistants can produce outdated or generic answers. Context7 improves reliability by returning:
- Up‑to‑date, version‑specific documentation
- Real, working code examples from official sources
- Concise, high‑signal snippets you can paste into your chat or editor

This results in fewer hallucinations and faster, more accurate implementation. See: 

---

## How to Set It Up?

### 1. Cursor 
Follow these steps to enable the Context7 MCP server in Cursor:
1. Open Cursor Settings → MCP/Servers.
2. Add a new MCP server and select Context7.
3. Save and restart the MCP host if prompted.
4. Verify that Context7 appears in your MCP servers list.

Notes:
- Authentication or API configuration may be prompted by the server UI.

### 2. Qwen
- File: `.qwen/settings.json` (project) or `~/.qwen/settings.json` (global)

  ```json
  {
    "mcpServers": {
      "context7": {
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp", "--api-key", "YOUR_API_KEY"]
      }
    }
  }
  ```

### 3. Qwen

For every coding agent the configuration is same as for qwen. Just look online for relevant files like `.qwen/settings.json` for QWEN and configure it.

---

## Using Context7 in AI Agents

Using it is as simple as adding **"use context7"** to your request.

For example, a popular tool called `openai agents sdk` recently changed its installation command.

*   **Without Context7,** your AI might remember the old, broken command:
    > **You:** `install openai agents sdk`
    > **AI:** `pip install openai-agents-sdk` ❌ (This is wrong now and will fail)

*   **With Context7,** your AI gets the latest information:
    > **You:** `use context7 install openai agents sdk`
    > **AI:** `pip install openai-agents` ✅ (This is the new, correct command)

### How It Works in the Background (The Simple Version)

When you add "use context7" to your prompt:

1.  Your AI knows it needs to get fresh information.
2.  It asks Context7 for the correct documentation for the tool you mentioned (like "Stripe" or "OpenAI").
3.  Context7 finds the latest instructions and code examples.
4.  It hands that information to your AI.
5.  Your AI then uses those perfect, up-to-date instructions to write the code for you.

By using Context7, you're giving your AI a live connection to the latest coding knowledge. This means fewer errors, less frustration, and faster, more accurate coding for you.

-----

Demo resources:
- YouTube reference: [https://www.youtube.com/watch?v=BJX6uJHIz5U](https://www.youtube.com/watch?v=BJX6uJHIz5U)
- YouTube reference: [https://www.youtube.com/watch?v=323l56VqJQw](https://www.youtube.com/watch?v=323l56VqJQw)

- https://context7.com/
 