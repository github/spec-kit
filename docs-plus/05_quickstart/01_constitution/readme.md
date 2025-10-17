# 01 - Constitution Setup

## Overview

The constitution is your project's rule book. It sets up your coding standards and technical choices that apply to ALL features you'll build. You only do this **once** at the start of your project.

**What you'll accomplish:**

- Set up project-wide coding rules and standards
- Choose your technical tools and preferences
- Establish principles that apply to ALL features (not just one app)
- Create the foundation for learning Spec-Driven Development

## Prerequisites

- Complete the [main quickstart setup](../readme.md)
- Have SpecKit installed in your project
- Be ready to work with your chosen AI agent

## Step-by-Step Instructions

### Step 1: Navigate to Your Project and understand structure

**Your Prompt:**

```
show me the current project structure.
```

**Agent Does:**

- Shows the created directory structure
- Confirms SpecKit installation and setup

### Step 2: Run Constitution Command

**Your Prompt:**

```
/sp.constitution

Project principles and standards:
- Write tests first (TDD approach)
- Use Python 3.12+ with type hints everywhere
- Keep code clean and easy to read
- Document important decisions with ADRs
- Follow essential OOP principles: SOLID, DRY, KISS

Technical stack:
- Python 3.12+ with UV package manager
- pytest for testing
- Keep all project files in git

Quality requirements:
- All tests must pass
- At least 80% code coverage
- Use dataclasses for data structures
```

**Agent Does:**

- Creates comprehensive constitution file
- Sets up project standards and OOP principles
- Defines coding principles and best practices
- Establishes technical preferences and quality gates

### Step 3: Review Generated Constitution and Commit to GitHub

**Your Prompt:**

```
Show me the generated constitution file and explain what it contains.
```

**Agent Does:**

- Displays the constitution content
- Explains each section:
  - **Project Principles** - Core development philosophy and OOP principles
  - **Technical Standards** - Code quality, structure, and best practices
  - **Testing Requirements** - TDD and coverage standards
  - **Architecture Decisions** - When to create ADRs and design patterns
  - **Quality Gates** - CI/CD requirements and code quality checks

**Your Prompt**

```
Use the agent to commit and open a PR for the constitution: /sp.git.commit_pr Commit and push the constitution along with current work.
```

**Agent Does:**

- Create a conventional commit for the constitution and push to a new feature branch
- Create a draft PR (or share the compare URL if `gh` auth is missing)

### Step 4: Customize Constitution (Optional)

**Your Prompt:**

```
Review the constitution and suggest any modifications based on my preferences:
- I want comprehensive type hints everywhere
- I want detailed docstrings for all public functions
- I want error handling to be explicit, not silent
- I want to use dataclasses for data structures
- I want to follow SOLID principles
- Focus on learning and teaching value
```

**Agent Does:**

- Analyzes current constitution
- Suggests specific modifications
- Updates constitution file if requested
- Explains the impact of each change

### Step 5: Verify Constitution Setup (Optional)

**Your Prompt:**

```
Verify that the constitution is properly set up by:
1. Showing the final constitution file
2. Confirming it's in the correct location (.speckit/memory/constitution.md)
3. Explaining how this will guide future development
```

**Agent Does:**

- Shows final constitution content
- Confirms file location
- Explains how constitution guides future spec loops
- Shows how it integrates with SpecKit workflow

## Expected Output

### Constitution File Structure

```
.speckit/memory/constitution.md
```

## What's Next

The constitution is now established and will guide all future development. The next step is to begin the first spec loop with the [Basic Operations](02_basic_operations/readme.md) feature.

**Key Points:**

- Constitution is a living document - update as needed
- All future spec loops will reference this constitution
- This establishes HOW to build (principles), not WHAT to build (specific apps)
- These rules apply to ALL features you'll create in this project

---

**Next:** [02 - Basic Operations](02_basic_operations/readme.md)
