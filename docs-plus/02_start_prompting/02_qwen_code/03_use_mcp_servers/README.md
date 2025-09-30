# Use MCP Servers to 10x Productivity (Simple, Practical)

MCP servers give Qwen superpowers: browse the web, run Playwright, talk to GitHub, recall memory, and search fast. Add a few, and you’ll plan, code, test, and research without leaving Qwen.

Setup (once)
- Work inside `01_hello_qwen`, then run `qwen`.
- Keep secrets in your shell (export env vars), not in files.

## Configuration basics (settings.json)
- `qwen mcp list` → confirm servers
- `/mcp` → see tools and auth status
- Before configuring a new server: run `qwen mcp list` and `/mcp` to see baseline

- File: `.qwen/settings.json` (project) or `~/.qwen/settings.json` (global)

## Recommended starters (what + how to add)

1. [Playwright MCP](https://github.com/microsoft/playwright-mcp) (headless browser, capture, test flows)
  - Value: script user journeys; verify pages after changes.
  - Add .qwen/settings.json:
  ```json
  {
    "mcpServers": {
      "playwright": {
        "command": "npx",
        "args": [
          "@playwright/mcp@latest"
        ]
      }
    }
  }
  ```
- Configure Playwright as above, then run `qwen mcp list` and `/mcp` again to confirm
- Ask (Playwright workflow prompt):
   - "now setup a simple page that shows galaxy. Take the screenshot to ensure it's all perfect and review it. Continue iterating after reviewing to get perfect galaxy view"

2. [Tavily Browser Search](https://github.com/tavily-ai/tavily-mcp) (web search + fetch)
  - Value: quick research, compare docs, gather refs.
  ```json
  {
    "mcpServers": {
      "tavily-remote": {
        "command": "npx",
        "args": [
          "-y",
          "mcp-remote",
          "https://mcp.tavily.com/mcp/?tavilyApiKey=<your-api-key>"
        ]
      }
    }
  }
  ```
  - Ask (search prompt): Check and research if gemini 3.0 and sonnet 4.5 are released.

3. [Context7MCP](https://github.com/mcp/upstash/context7) - Up-to-date Code Docs For Any Prompt
  - Value: focused answers + sources for decisions.
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

4. [OpenMemory](openmemory.dev) (save facts across sessions)
  ```json
      "openmemory": {
        "command": "npx",
        "args": [
          "-y",
          "openmemory"
        ],
        "env": {
          "OPENMEMORY_API_KEY": "YOUR_API_KEY"
        }
      }
  ```
  - Ask (mem prompt): Use add-memory tool and save that we prefer to use OpenAI Agents SDK, MCP, A2A, Kubernetes for Agentic AI.

Daily flow (2 minutes)
1) `qwen mcp list` → confirm servers
2) `/mcp` → see tools and auth status
3) Before configuring a new server: run `qwen mcp list` and `/mcp` to see baseline
4) Configure Playwright as above, then run `qwen mcp list` and `/mcp` again to confirm
5) Ask (Playwright workflow prompt):
   - "now setup a simple page that shows galaxy. Take the screenshot to ensure it's all perfect and review it. Continue iterating after reviewing to get perfect galaxy view"
6) Save a team fact: `SaveMemory("We release on Fridays 3pm UTC.")`

Trust, safety, and approvals
- Start with defaults (confirmation on tools). Toggle with `/approval-mode` when confident.
- In `.qwen/settings.json`, you can whitelist/blacklist tools (e.g., allow `Shell(git status)`, block `rm`).

## How to choose servers (think like a technical business manager)
Outcome first: What decision or workflow does this unblock (e.g., “verify login flow daily”, “gather competitive notes in 5 minutes”)?
- ROI quick check: Setup < 15 min, saves > 30 min/week, reduces context switching.
- Security posture: Auth via env vars; no broad shell; whitelist tools; avoid storing tokens in repo.
- Maintenance: Active repo, clear docs, simple add/remove commands, minimal deps.
- Integration fit: Complements your stack (browser, search, memory); avoids overlap.
- Proof-of-value: 1‑day pilot with a concrete metric (e.g., flaky login caught, 3 curated sources with quotes, meeting brief auto‑generated).


