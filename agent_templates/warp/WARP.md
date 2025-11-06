# Warp Project Rules - Spec-Driven Development

This project uses **Spec-Driven Development (SDD)** methodology with the [GitHub Spec Kit](https://github.com/github/spec-kit).

## Project Context

This is a spec-kit project that follows a structured development workflow:
1. Define specifications before implementation
2. Create technical implementation plans
3. Break down into actionable tasks
4. Execute implementation according to the plan

## Available Spec-Kit Workflows

When working on this project, you can guide the user through these structured workflows:

### `/speckit.constitution` - Create Project Principles
Create or update project governing principles and development guidelines that will guide all subsequent development.

**Usage:** User should describe principles focused on code quality, testing standards, user experience consistency, and performance requirements.

**Script:** `scripts/bash/setup-plan.sh constitution`

---

### `/speckit.specify` - Define Requirements
Define what needs to be built with focus on the **what** and **why**, not the tech stack.

**Usage:** User should describe the feature or application they want to build, focusing on user needs and functionality.

**Script:** `scripts/bash/setup-plan.sh specify`

---

### `/speckit.plan` - Create Technical Plan
Create technical implementation plans with the chosen tech stack and architecture.

**Usage:** User should specify their technology choices, frameworks, databases, and architectural decisions.

**Script:** `scripts/bash/setup-plan.sh plan`

---

### `/speckit.tasks` - Generate Task List
Generate actionable task lists for implementation based on the plan.

**Usage:** Run this after creating a plan to break it down into specific implementation tasks.

**Script:** `scripts/bash/create-new-feature.sh tasks`

---

### `/speckit.implement` - Execute Implementation
Execute all tasks to build the feature according to the plan.

**Usage:** Run this to implement all the tasks that were generated.

**Script:** `scripts/bash/create-new-feature.sh implement`

---

## Optional Quality Commands

### `/speckit.clarify` - Clarify Underspecified Areas
Clarify underspecified areas in the specification. Recommended before creating a technical plan.

**Script:** `scripts/bash/setup-plan.sh clarify`

---

### `/speckit.analyze` - Consistency Analysis
Cross-artifact consistency & coverage analysis. Run after creating tasks, before implementation.

**Script:** `scripts/bash/create-new-feature.sh analyze`

---

### `/speckit.checklist` - Quality Checklists
Generate custom quality checklists that validate requirements completeness, clarity, and consistency.

**Script:** `scripts/bash/create-new-feature.sh checklist`

---

## How to Use These Workflows

1. **Start a new feature**: Begin with `/speckit.constitution` to establish project principles
2. **Define the feature**: Use `/speckit.specify` to describe what you want to build
3. **Plan the implementation**: Use `/speckit.plan` to define your technical approach
4. **Break it down**: Use `/speckit.tasks` to create actionable tasks
5. **Build it**: Use `/speckit.implement` to execute the plan

## Project Structure

- `.specify/` - Spec-kit configuration and templates
  - `memory/` - Project memory and principles
  - `scripts/` - Automation scripts for workflows
  - `templates/` - Document templates

## Environment Variables

- `SPECIFY_FEATURE` - Override feature detection for non-Git repositories

## Support

For more information, see the [Spec Kit documentation](https://github.com/github/spec-kit).
