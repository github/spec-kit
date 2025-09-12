# [PROJECT NAME] - OpenAI Codex CLI Integration

Auto-generated from all feature plans. Last updated: [DATE]

## Overview

This project uses **Specification-Driven Development (SDD)** with OpenAI Codex CLI. Codex CLI is a lightweight coding agent that runs locally and can read, modify, and run code on your local machine to help build features faster, squash bugs, and understand unfamiliar code.

## Active Technologies
[EXTRACTED FROM ALL PLAN.MD FILES]

## Project Structure
```
[ACTUAL STRUCTURE FROM PLANS]
```

## SDD Workflow with Codex CLI

### 1. Specification Phase
```bash
codex "/specify [feature description]"
```
Creates a detailed specification from natural language description. The specification includes user stories, functional requirements, and acceptance criteria.

### 2. Planning Phase  
```bash
codex "/plan [technical details and constraints]"
```
Generates technical implementation plan based on the specification. Includes architecture decisions, technology choices, and constitutional compliance checks.

### 3. Task Generation
```bash
codex "/tasks"
```
Breaks down the plan into executable tasks following Test-Driven Development principles.

## Commands for Active Technologies
[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]

## Code Style Guidelines
[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]

## Codex CLI Configuration

### Basic Usage
- **Interactive TUI**: Run `codex` for interactive mode
- **Direct prompts**: Use `codex "your prompt here"`
- **Non-interactive**: Use `codex exec "your prompt"`

### Key Flags
- `--model/-m`: Select AI model
- `--ask-for-approval/-a`: Enable approval prompts
- `--full-auto`: Enable full automation mode

### Authentication
Codex CLI supports:
- **ChatGPT plan** (recommended): Sign in with your ChatGPT Plus/Pro/Team/Enterprise account
- **API key**: Alternative setup for usage-based billing

### Configuration File
Edit `~/.codex/config.toml` for persistent settings:
```toml
# Model selection
default_model = "gpt-4"

# Approval settings
ask_for_approval = true

# MCP server support
[mcp_servers]
# Add your MCP servers here
```

## Recent Changes
[LAST 3 FEATURES AND WHAT THEY ADDED]

## Constitutional Principles

This project follows strict constitutional principles:
- **Library-First**: Every feature starts as a standalone library
- **Test-First**: TDD is non-negotiable (RED-GREEN-REFACTOR cycle)
- **CLI Interface**: Every library exposes functionality via CLI
- **Integration Testing**: Use real dependencies, not mocks

See `memory/constitution.md` for complete details.

## Tips for Codex CLI

### Effective Prompts
- Be specific about what you want to build and why
- Include context about your tech stack and constraints
- Reference existing code patterns when applicable

### SDD Best Practices
- Always start with `/specify` to create clear specifications
- Use `/plan` to make technical decisions explicit
- Break work into small, testable tasks with `/tasks`
- Follow the constitutional principles for code quality

### Error Handling
- If Codex gets stuck, provide more specific context
- Use `codex --ask-for-approval` for safer execution
- Check `~/.codex/config.toml` for configuration issues

<!-- MANUAL ADDITIONS START -->
<!-- Add your custom instructions, project-specific prompts, or team conventions here -->
<!-- MANUAL ADDITIONS END -->