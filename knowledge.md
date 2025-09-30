# Spec Kit Project Knowledge

## Project Overview
Spec Kit is a specification-driven development workflow tool that helps teams create, manage, and implement feature specifications systematically.

## Project Structure
- `templates/`: Template files for specs, plans, tasks, and commands
- `scripts/`: Bash and PowerShell scripts for workflow automation
- `specs/`: Feature specifications organized by numbered branches (e.g., `001-feature-name/`)
- `src/specify_cli/`: Python CLI implementation
- `docs/`: Documentation files

## Key Workflows

### Feature Development Flow
1. Create feature branch using `scripts/bash/create-new-feature.sh "Feature description"`
2. Write specification in `specs/###-feature-name/spec.md`
3. Create implementation plan in `specs/###-feature-name/plan.md`
4. Generate tasks in `specs/###-feature-name/tasks.md`
5. Implement according to tasks

### Branch Naming Convention
Feature branches follow the pattern: `###-short-description` where `###` is a zero-padded three-digit number (e.g., `001-add-auth`, `002-user-profile`)

## Commands Available
The project includes template commands in `templates/commands/`:
- `specify.md`: Main specification creation
- `plan.md`: Implementation planning
- `tasks.md`: Task breakdown
- `clarify.md`: Clarification requests
- `analyze.md`: Code analysis
- `implement.md`: Implementation guidance
- `constitution.md`: Project constitution

## Development Guidelines
- Specifications should focus on WHAT and WHY, not HOW
- Use `[NEEDS CLARIFICATION: question]` markers for ambiguous requirements
- All functional requirements must be testable
- Specs are written for business stakeholders, not just developers

## Scripts
- Scripts may need execute permissions: `chmod +x scripts/bash/*.sh`
- Common script utilities are in `scripts/bash/common.sh`
- Scripts support both git and non-git repositories
