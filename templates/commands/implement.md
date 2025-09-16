---
description: Complete the implementation phase of Spec-Driven Development (SDD) by coordinating with developer agents, enforcing the project CONSTITUTION and feature design guidelines, or generating code during a single session.
scripts:
  sh: scripts/bash/check-implement-prerequisites.sh --json
---

Given the context provided as an argument, do this:

1. Run {SCRIPT} from repo root and parse: FEATURE_DIR and AVAILABLE_SPECS (files). All paths must be absolute.
2. Load and analyze available specification artifacts:
   - Always read tasks.md for detailed implementation plan
   - Always read CONSTITUTION for governance rules
   - IF EXISTS: Read data-model.md for entities
   - IF EXISTS: Read contracts/ for API endpoints
   - IF EXISTS: Read research.md for technical decisions
   - IF EXISTS: Read quickstart.md for test scenarios

   Note: Not all projects have all documents. For example:
   - CLI tools might not have contracts/
   - Simple libraries might not need data-model.md

3. Start implementing each phase of the feature as outlined in the tasks.md document, step by step.
   - Skip completed tasks (marked ✅)
   - Resume from last in_progress task (marked 🔄)
   - Start with first pending task if fresh start
   - IF AGENTS/TOOLS ARE AVAILABLE: Prefer delegation to available agents/tools with explicit commands and inputs
   - IF AGENTS/TOOLS ARE AVAILABLE: Task marked with [P] within same developing phase can be called simultaneously
   - IF AGENTS/TOOLS ARE AVAILABLE: Provide them with the minimal required context from the available design documents
   - Resolve tasks only when requirements is clear
   - Handle edge cases by seeking clarification when specs are ambiguous, documenting assumptions and yielding back to user when unable to resolve
   - Commit each completed step in avaiable version control system

4. After each step:
   - Update tasks.md entries with 🔄 (in progress) or ✅ (completed) or ❌ (blocked)
   - Run verification (tests/build)

Context for implementation: {ARGS}

Default CONSTITUTION path: memory/constitution.md
Never violate CONSTITUTION.
