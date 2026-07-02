# Brainstorm: Extension Capability System

**Date:** 2026-07-02
**Status:** active

## Problem Framing

Spec-kit's extension system lets third-party extensions provide commands that work across all supported agent harnesses. The `CommandRegistrar` handles format conversion (Markdown, TOML, YAML, SKILL.md) and path routing (`.claude/skills/`, `.opencode/commands/`, `.forge/commands/`, etc.). This works well for the structural layer.

However, extensions that need to reference agent-specific capabilities in their command content have no mechanism to do so portably. When a command needs to say "ask the user an interactive question" or "spawn a parallel subagent," it must hardcode a specific agent's tool name (e.g., `AskUserQuestion` for Claude Code, `question` for OpenCode). The result: extensions either target a single agent or maintain per-agent conditional blocks manually.

This is not a hypothetical problem. The spex extension bundle (cc-spex) has 46 Claude Code-specific references across its commands. 41 of those are CORE dependencies (the command breaks without them). The main patterns:

- **Script discovery**: `find ~/.claude -name 'script.sh'` (14 instances) assumes Claude Code's plugin directory
- **Tool name references**: `AskUserQuestion`, `Agent` tool, `EnterWorktree` hardcoded in instructions
- **Capability-dependent sections**: subagent dispatch, worktree isolation, context clearing are only available on some harnesses

The spex extension can't work on OpenCode, Codex, Cursor, or any other harness without maintaining separate command variants or messy conditional blocks.

## Why This Is a General Problem

This isn't specific to spex. Any extension that goes beyond simple "run a script and report results" workflows will hit the same wall:

### Use Case 1: Interactive decision points

An extension command that needs user input mid-workflow (e.g., "which approach do you prefer?") must know the agent's interactive prompt mechanism. Claude Code has `AskUserQuestion` with structured multi-select. OpenCode has the `question` tool. Codex has no interactive input at all. A portable command needs to express "ask the user" generically and have it resolve per agent.

### Use Case 2: Parallel work distribution

An extension that distributes work across subagents (code review across multiple dimensions, parallel test execution, research from multiple angles) must know whether the agent supports subagent spawning and what tool to use. Claude Code has the `Agent` tool with background execution. OpenCode has the `Task` tool. Many agents have nothing. A portable command needs conditional sections: "if subagents are available, fan out; otherwise, execute sequentially."

### Use Case 3: Process enforcement

Extensions that enforce workflow discipline (e.g., "don't implement before the spec is reviewed") rely on hook systems that vary dramatically. Claude Code has `PreToolUse` hooks that can mechanically block tool calls. OpenCode has `tool.execute.before` plugin events. Most agents have nothing. An extension needs to know what enforcement level is possible and adapt its instructions accordingly.

### Use Case 4: Plugin script discovery

Extensions bundle shell/Python scripts that commands invoke at runtime. The install location varies by agent (`~/.claude/plugins/`, `~/.opencode/plugins/`, etc.). Today there's no portable way for a command to reference "my extension's script directory." Each command must hardcode a search path.

### Use Case 5: Context management

Some workflows benefit from clearing conversation context between phases (e.g., generate code, then review it with fresh eyes). Claude Code has `/clear`. Most agents have no equivalent. Commands need to conditionally suggest context management or skip it.

## What Exists Today

Spec-kit has partial infrastructure that could be extended:

1. **`post_process_skill_content()`** on `SkillsIntegration` (base.py) is an existing hook where integrations can transform command content after template processing. Claude's integration uses it to inject frontmatter flags. But it only covers skills-format agents (Claude, Codex, Cursor, Kimi, Agy, Trae). MarkdownIntegration, TomlIntegration, and YamlIntegration agents (OpenCode, Forge, Gemini, Goose, etc.) have no equivalent.

2. **`_feature_capabilities()`** (CLI-level) returns a dict of boolean flags for what the spec-kit CLI can do. The same pattern at the integration level would let each agent declare its capabilities.

3. **`_invocation_style.py`** already categorizes agents into behavioral groups. This is a proto-capability taxonomy by syntax, not by functional capabilities.

4. **Workflow expressions engine** (`expressions.py`) implements a safe Jinja2 subset with conditional evaluation. It's currently walled off from command template processing, only used by the workflow YAML engine.

5. **`process_template()`** does placeholder substitution (`{SCRIPT}`, `__AGENT__`, `__CONTEXT_FILE__`), but has no conditional logic.

## Proposed Enhancement

Three additions to spec-kit, each building on existing patterns:

### 1. Capability declarations on integrations

Each `IntegrationBase` subclass declares a `capabilities` dict describing what the agent supports:

```python
class ClaudeIntegration(SkillsIntegration):
    capabilities = {
        "interactive_prompts": {
            "tool": "AskUserQuestion",
            "structured": True,
            "multi_select": True
        },
        "subagents": {
            "tool": "Agent",
            "background": True,
            "worktree_isolation": True
        },
        "process_enforcement": {
            "hooks": True,
            "pre_tool_gate": True
        },
        "context_clearing": {
            "command": "/clear"
        },
    }

class OpenCodeIntegration(MarkdownIntegration):
    capabilities = {
        "interactive_prompts": {
            "tool": "question",
            "structured": True,
            "multi_select": False
        },
        "subagents": {
            "tool": "Task",
            "background": False,
            "worktree_isolation": False
        },
        "process_enforcement": {
            "hooks": False,
            "pre_tool_gate": True  # via tool.execute.before plugin
        },
    }
    # No context_clearing = capability absent
```

This follows the `_feature_capabilities()` pattern, replicated at integration level. The `IntegrationBase` declares an empty default; subclasses override.

### 2. Conditional content processing in template pipeline

A mechanism to include/exclude command content sections based on capability flags and substitute generic tool references with agent-specific names. Extension commands use explicit conditional syntax:

```markdown
## Interactive Review

{{#if interactive_prompts}}
Present the review findings using {{tool:interactive_prompts}}:
- Option A: "Fix all issues"
- Option B: "Let me pick which to fix"  
- Option C: "Skip fixes"
{{else}}
List the review findings and proceed with fixing all issues.
{{/if}}
```

The implementation approach (reuse workflow expressions engine, extend process_template, or add a purpose-built system) is a design decision for the spec phase. The requirement is: explicit, readable conditional blocks that are processed at install time (not at runtime).

### 3. Generalize post-processing to all format types

Extend the `post_process_skill_content()` pattern to all integration base classes. Add a `post_process_command_content()` method to `IntegrationBase` that is called from `register_commands()` in `agents.py` for all format types (markdown, TOML, YAML, skills). This gives every integration the opportunity to transform content.

### 4. Plugin root variable

Add a `__PLUGIN_ROOT__` substitution variable to `process_template()` and `register_commands()`. Each integration resolves it to the actual plugin install path. Extension commands replace `find ~/.claude -name 'script.sh'` with `"$__PLUGIN_ROOT__/scripts/script.sh"`.

## Approaches Considered

### A: Capability metadata + template conditionals in spec-kit (chosen)

As described above. Spec-kit gains a generic capability system that any extension can use.

- Pros: Clean separation. Each integration declares its truth. Explicit conditional syntax is readable and testable. Any extension benefits, not just spex. Follows existing patterns.
- Cons: Introduces conditional syntax into command markdown. Extensions must learn the vocabulary. Needs careful design of capability schema.

### B: Extensions handle it themselves

Each extension maintains per-agent command variants or conditional blocks using its own conventions. Spec-kit stays unchanged.

- Pros: Zero spec-kit changes. Extensions have full control.
- Cons: Every extension reinvents the wheel. No standard for capability detection. Conditional blocks are ad-hoc and inconsistent across extensions. Scale problem: 28 agents x N extensions = M variants.

### C: Per-agent command file overrides

Extensions provide a default command file plus optional `commands/agent-overrides/{agent}.md` files. Spec-kit picks the override if it exists, falls back to default.

- Pros: Simple to implement. Full control over agent-specific content.
- Cons: Massive duplication. An extension with 13 commands targeting 5 agents = 65 files to maintain. Drift between variants. Doesn't scale.

## Decision

**Approach A: Capability metadata + template conditionals in spec-kit.**

This is the only approach that scales. The capability system is generic infrastructure that makes ALL extensions portable, not just one. It follows spec-kit's existing patterns and adds a small, well-defined surface area.

## Key Requirements

1. Capability declarations as a dict on `IntegrationBase` subclasses
2. Conditional content blocks processed at install time (when `register_commands()` or `_register_extension_skills()` writes output files)
3. Tool name substitution via capability references
4. `post_process_command_content()` generalized to all format types
5. Plugin root variable for portable script discovery
6. Extension manifest support for declaring required capabilities (with warning/error when targeting an unsupported agent)

## Open Questions

- What is the canonical capability vocabulary? Need to survey all 28 integrations to identify the full set of varying capabilities
- Should the capability dict be on the class or in `registrar_config`?
- Should capability values be structured dicts (with tool names and sub-properties) or flat booleans with a separate tool-mapping table?
- How should the conditional syntax interact with format conversion? (Conditionals must be processed before TOML/YAML conversion)
- Should the workflow expressions engine be reused, or is a simpler system better for command templates?
- How should extensions declare minimum capability requirements in `extension.yml`?
- Should `specify extension install` warn or error when the target agent lacks required capabilities?
