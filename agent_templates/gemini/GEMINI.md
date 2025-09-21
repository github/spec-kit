# [PROJECT NAME] Development Guidelines for Gemini CLI

Auto-generated from all feature plans. Last updated: [DATE]

## Active Technologies
[EXTRACTED FROM ALL PLAN.MD FILES]

## Project Structure
```
[ACTUAL STRUCTURE FROM PLANS]
```

## Commands
[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]

## Code Style
[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]

## Recent Changes
[LAST 3 FEATURES AND WHAT THEY ADDED]

## Gemini CLI Specifics

<!--
NOTE: The Gemini and Qwen agent templates contain identical command specifications (TOML format, {{args}} placeholders, similar directory structure).
This duplication is intentional to ensure consistency across agents and facilitate compatibility. Any changes to command formats should be reflected in both templates.
If future refactoring is possible, consider extracting a shared base template. For now, this documentation serves to clarify the reason for duplication and avoid maintenance confusion.
-->

- Use TOML command format with {{args}} placeholders
- Commands are stored in `.gemini/commands/` directory
- Use `gemini` CLI tool for execution

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->