---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load context**: Read FEATURE_SPEC and `/memory/constitution.md`. Load IMPL_PLAN template (already copied).

3. **Execute plan workflow**: Follow the structure in IMPL_PLAN template to:
   - Fill Technical Context (mark unknowns as "NEEDS CLARIFICATION")
   - Fill Constitution Check section from constitution
   - Evaluate gates (ERROR if violations unjustified)
   - Phase 0: Generate research.md (resolve all NEEDS CLARIFICATION)
   - Phase 1: Generate data-model.md, contracts/, quickstart.md
   - Phase 1: Update agent context by running the agent script
   - Re-evaluate Constitution Check post-design

4. **Stop and report**: Command ends after Phase 2 planning. Report branch, IMPL_PLAN path, and generated artifacts.

## Phases

### Phase 0: Outline & Research

1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task
   - For async communication patterns → protocol/technology evaluation task

2. **Generate and dispatch research agents**:

   ```text
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   For async communication patterns:
     Task: "Evaluate {WebSocket vs SSE vs Webhooks vs Message Queues} for {feature requirements}"
     Task: "Research AsyncAPI specification best practices for {identified pattern}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

### Phase 1: Design & Contracts

**Prerequisites:** `research.md` complete

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Detect communication patterns** from functional requirements and feature spec:
   - Scan for **async indicators**: "real-time", "live", "streaming", "push", "event", "notification", "bidirectional", "chat", "feed", "updates", "subscribe", "publish", "webhook", "message"
   - Scan for **sync indicators**: "request", "query", "fetch", "get", "create", "update", "delete", "CRUD"
   - **If async indicators found**: Mark as async or hybrid
   - **If ambiguous**: Add to Technical Context as "NEEDS CLARIFICATION: Does [feature] require synchronous (request-response) or asynchronous (real-time/event-driven) communication?"
   - Document decision in Technical Context → Communication Patterns field

3. **Generate API contracts** based on detected communication patterns:

   **For Synchronous Operations** (REST/GraphQL):
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Generate OpenAPI specification → `/contracts/openapi.yaml` or `/contracts/rest-api.yaml`
   - Generate GraphQL schema → `/contracts/graphql.schema` (if GraphQL detected)

   **For Asynchronous Operations** (Events/WebSocket/Messaging):
   - For each real-time feature → channel/event type
   - Identify: channel names, message payloads, event types
   - Define: publish/subscribe patterns, message schemas
   - Generate AsyncAPI specification → `/contracts/asyncapi.yaml` or `/contracts/events-api.yaml`
   - Document: WebSocket endpoints, event types, message formats

   **For Hybrid APIs** (Both sync and async):
   - Generate both OpenAPI and AsyncAPI specifications
   - Document integration points between sync and async operations
   - Clarify which operations use which pattern and why

   **Contract File Naming**:
   - `openapi.yaml` or `rest-api.yaml` - REST API specifications
   - `asyncapi.yaml` or `events-api.yaml` - Event/WebSocket specifications
   - `graphql.schema` - GraphQL schema definitions
   - Multiple contracts allowed in `/contracts/` directory

4. **Agent context update**:
   - Run `{AGENT_SCRIPT}`
   - These scripts detect which AI agent is in use
   - Update the appropriate agent-specific context file
   - Add only new technology from current plan
   - Preserve manual additions between markers

**Output**: data-model.md, /contracts/*, quickstart.md, agent-specific file

## Key rules

- Use absolute paths
- ERROR on gate failures or unresolved clarifications
