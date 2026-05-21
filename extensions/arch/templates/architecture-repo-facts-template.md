# Architecture Repo Facts: [PROJECT]

**Purpose**: Record observable repository facts that support reverse generation of the project-level 4+1 architecture artifacts.

**Note**: This evidence file is filled in by the `__SPECKIT_COMMAND_ARCH_REVERSE__` command before the architecture views are updated. It is a fact source for architecture reasoning, not an implementation audit report.

## Repository Identity

| Fact | Evidence Source | Confidence | Architecture Relevance |
|------|-----------------|------------|--------------------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## Entry Points

| Entry Point | Type | Evidence Source | Observed Responsibility | Supported Scenario |
|-------------|------|-----------------|--------------------------|--------------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## User-Visible Behaviors

| Behavior | Evidence Source | Actor / Trigger | Observable Outcome | Supported Use Case |
|----------|-----------------|-----------------|--------------------|--------------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## System Boundaries

| Boundary | Evidence Source | Inbound Interaction | Outbound Interaction | Not Proven |
|----------|-----------------|---------------------|----------------------|------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## Data and State Clues

| Fact / Entity | Evidence Source | Observed Lifecycle Clue | Fact Source | Not Proven |
|---------------|-----------------|-------------------------|-------------|------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## Runtime and Process Clues

| Runtime Fact | Evidence Source | Trigger / Handoff | Failure or Retry Clue | Not Proven |
|--------------|-----------------|-------------------|-----------------------|------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## Development Structure Clues

| Module / Package Area | Evidence Source | Observed Responsibility | Dependency Clue | Boundary Risk |
|-----------------------|-----------------|--------------------------|-----------------|---------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## Repository-First Projection

Record repository-first evidence only when `.specify/memory/repository-first/` exists. Leave explicit gaps when the directory or expected artifacts are absent.

### Build Manifest Detection

| Ecosystem | Manifest Evidence | Detection Status | Runtime Surface Notes |
|-----------|-------------------|------------------|-----------------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

### First-Party Module Edges

| From Module | To Module | Evidence Source | Observed Direction | Architecture Boundary Meaning |
|-------------|-----------|-----------------|--------------------|-------------------------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

### Module Invocation Governance

| Rule Source | Allowed Direction | Forbidden Direction | Architecture Constraint | Risk If Violated |
|-------------|-------------------|---------------------|-------------------------|------------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

### Dependency Governance Signals

| Signal Source | Dependency / Concern | Signal Type | Affected Boundary | Architecture Review Trigger |
|---------------|----------------------|-------------|-------------------|-----------------------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## Physical / Deployment Clues

| Deployment Fact | Evidence Source | Environment / External System | Operational Constraint | Not Proven |
|-----------------|-----------------|-------------------------------|------------------------|------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## Git History Signals

| Signal | Evidence Source | Architecture Meaning | Confidence | Review Trigger |
|--------|-----------------|----------------------|------------|----------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## Evidence Gaps

| Gap | Affected View | Why It Blocks Architecture Conclusion |
|-----|---------------|----------------------------------------|
| NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE | NEEDS REPO FACTS UPDATE |

## Evidence Rules

- Every non-placeholder fact must name an evidence source such as a file, directory, configuration, test, script, manifest, command output, or commit signal.
- Confidence values are `High`, `Medium`, or `Low`.
- `High` means multiple independent sources agree, or docs/tests and code entry points agree.
- `Medium` means one strong source is present, such as clear configuration, entry point, route declaration, or behavior test.
- `Low` means naming, directory structure, isolated code, or Git history suggests a fact but lacks behavior evidence.
- Git history is an auxiliary signal for change axes and boundary risks. It cannot independently prove architecture conclusions.
- Repository-first dependency matrices are fact inputs. Do not copy full dependency inventories into architecture views; summarize only architecture constraints, governance signals, gaps, or review triggers.
- Repository-first module invocation specs may support development-view dependency rules when each rule maps to a concrete module edge or dependency signal.
- Concrete classes, functions, fields, endpoints, database tables, and implementation data structures may appear only as evidence sources, not architecture conclusions.
