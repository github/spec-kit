---
description: "Use sandboxed runs and discuss safe shell execution"
---

Objective: Understand sandboxing and safe command execution policies.

Steps
1. Non-interactive, sandboxed example:
   - `qwen -s -p "run shell command: env | grep SANDBOX"`
2. Discuss allow/block policies (concept):
   - Allow list: `{ "coreTools": ["run_shell_command(git)"] }`
   - Block list: `{ "excludeTools": ["run_shell_command(rm)"] }`
3. Ask: "Explain when to enable sandbox and how mounts are isolated."

Acceptance
- You can articulate when sandbox is appropriate and how to avoid destructive ops.



