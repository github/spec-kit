#!/usr/bin/env bash
# agent-config.sh
# Centralized configuration for all supported AI agents
# This file should be sourced by other scripts that need the agent list

# All supported AI agents
# Add new agents here to automatically include them in releases
ALL_AGENTS=(
  claude
  gemini
  copilot
  cursor-agent
  qwen
  opencode
  windsurf
  codex
  kilocode
  auggie
  roo
  codebuddy
  q
)

# Agent-specific configuration
# Format: agent_name:directory:file_extension:arg_format:extra_files
declare -A AGENT_CONFIG=(
  # Markdown-based agents with $ARGUMENTS
  ["claude"]=".claude/commands:md:\$ARGUMENTS:"
  ["copilot"]=".github/prompts:prompt.md:\$ARGUMENTS:vscode-settings"
  ["cursor-agent"]=".cursor/commands:md:\$ARGUMENTS:"
  ["opencode"]=".opencode/command:md:\$ARGUMENTS:"
  ["windsurf"]=".windsurf/workflows:md:\$ARGUMENTS:"
  ["codex"]=".codex/prompts:md:\$ARGUMENTS:"
  ["kilocode"]=".kilocode/workflows:md:\$ARGUMENTS:"
  ["auggie"]=".augment/commands:md:\$ARGUMENTS:"
  ["roo"]=".roo/commands:md:\$ARGUMENTS:"
  ["codebuddy"]=".codebuddy/commands:md:\$ARGUMENTS:"
  ["q"]=".amazonq/prompts:md:\$ARGUMENTS:"

  # TOML-based agents with {{args}}
  ["gemini"]=".gemini/commands:toml:{{args}}:gemini-readme"
  ["qwen"]=".qwen/commands:toml:{{args}}:qwen-readme"
)

# Function to get agent configuration values
get_agent_dir() { echo "${AGENT_CONFIG[$1]}" | cut -d: -f1; }
get_agent_ext() { echo "${AGENT_CONFIG[$1]}" | cut -d: -f2; }
get_agent_args() { echo "${AGENT_CONFIG[$1]}" | cut -d: -f3; }
get_agent_extras() { echo "${AGENT_CONFIG[$1]}" | cut -d: -f4; }

# Export for use in sourcing scripts
export ALL_AGENTS
export AGENT_CONFIG
