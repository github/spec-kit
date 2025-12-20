---
description: Complete project setup - runs setup-hooks, agents, and constitution in sequence
scripts:
  sh: echo "Setup orchestrator - no script needed"
  ps: echo "Setup orchestrator - no script needed"
---

# SpecKit Project Setup

You are the **Setup Orchestrator**. Your job is to run the complete initial setup for a SpecKit project by executing the following commands in sequence.

## Setup Sequence

Execute these commands in order, waiting for each to complete before proceeding:

### Step 1: Setup Hooks and Skills

Run the `/speckit.setup-hooks` command to:
- Detect project frameworks and technologies
- Create Claude Code skills for detected frameworks
- Configure hooks for the project

**Action**: Execute `/speckit.setup-hooks` now.

After completion, proceed to Step 2.

---

### Step 2: Configure Project Agents

Run the `/speckit.agents` command to:
- Set up specialized agents for the project
- Configure agent skills and tools
- Create agent workflow structure

**Action**: Execute `/speckit.agents` now.

After completion, proceed to Step 3.

---

### Step 3: Establish Constitution

Run the `/speckit.constitution` command to:
- Define project principles and values
- Establish coding standards
- Create the project constitution document

**Action**: Execute `/speckit.constitution` now.

---

## Completion

After all three steps are complete, summarize what was set up:

1. **Skills & Hooks**: List the frameworks detected and skills created
2. **Agents**: List the agents configured
3. **Constitution**: Confirm the constitution was established

Then inform the user that setup is complete and they can now use:
- `/speckit.specify` to create a feature specification
- `/speckit.plan` to create an implementation plan
