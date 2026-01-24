# Semantic Anchors Reference

> **Purpose**: This file defines the semantic anchors used across spec-kit commands.
> These anchors are well-established terms that activate rich contextual understanding in LLMs.

## How to Use

Include relevant anchors in command headers to prime the LLM with the right mental models.
Format: `Semantic Anchors: [anchor1], [anchor2], [anchor3]`

---

## Requirements Engineering

| Anchor | Core Concepts | When to Use |
|--------|---------------|-------------|
| **EARS Syntax** | Easy Approach to Requirements Syntax. Patterns: Ubiquitous, Event-driven, State-driven, Optional, Complex. Eliminates ambiguity. | Writing functional requirements |
| **INVEST Criteria** | Independent, Negotiable, Valuable, Estimable, Small, Testable. Quality criteria for user stories. | Validating user story quality |
| **Specification by Example** | Concrete examples as specs. Living documentation. Collaborative discovery. Gojko Adzic. | Creating acceptance criteria |
| **Jobs-to-Be-Done** | Outcome-focused. "When [situation], I want to [motivation], so I can [outcome]". Clayton Christensen. | Understanding user needs |

## Testing & Validation

| Anchor | Core Concepts | When to Use |
|--------|---------------|-------------|
| **BDD Gherkin** | Given-When-Then syntax. Feature files. Scenarios. Dan North. Cucumber. | Writing acceptance scenarios |
| **ATDD** | Acceptance Test-Driven Development. Tests before code. Executable specs. | Validation workflow |
| **TDD London School** | Outside-in. Mock collaborators. Test behavior not state. Steve Freeman, Nat Pryce. | Unit testing approach |
| **TDD Chicago School** | Inside-out. State verification. Classic TDD. Kent Beck. | Alternative testing approach |
| **Property-Based Testing** | Generators. Invariants. Shrinking. QuickCheck, Hypothesis, fast-check. | Edge case discovery |

## Architecture & Design

| Anchor | Core Concepts | When to Use |
|--------|---------------|-------------|
| **Hexagonal Architecture** | Ports and Adapters. Domain isolation. Alistair Cockburn. | Code structure decisions |
| **Clean Architecture** | Dependency rule. Use cases. Entities. Robert C. Martin. | Layer organization |
| **C4 Model** | Context, Containers, Components, Code. Simon Brown. Hierarchical diagrams. | Architecture documentation |
| **ADR** | Architecture Decision Records. Context, Decision, Consequences. Michael Nygard. | Recording tech decisions |
| **arc42** | Template for architecture documentation. 12 sections. Stakeholder-focused. | Architecture docs structure |

## Design Principles

| Anchor | Core Concepts | When to Use |
|--------|---------------|-------------|
| **SOLID Principles** | Single Responsibility, Open-Closed, Liskov Substitution, Interface Segregation, Dependency Inversion. | Code quality |
| **Convention over Configuration** | Sensible defaults. Minimal config. Ruby on Rails principle. | Default behavior decisions |
| **Principle of Least Astonishment** | Behavior matches expectations. Predictable interfaces. | UX and API design |
| **DRY** | Don't Repeat Yourself. Single source of truth. Pragmatic Programmer. | Code organization |
| **YAGNI** | You Aren't Gonna Need It. No speculative features. XP principle. | Scope decisions |

## Problem Solving & Debugging

| Anchor | Core Concepts | When to Use |
|--------|---------------|-------------|
| **5 Whys** | Root cause analysis. Iterative questioning. Toyota Production System. | Bug diagnosis |
| **Ishikawa Diagram** | Fishbone diagram. Cause categories: People, Process, Equipment, Materials, Environment, Management. | Complex problem analysis |
| **Rubber Duck Debugging** | Explain problem aloud. Articulate assumptions. Force clarity. | Stuck on bugs |
| **Scientific Method** | Hypothesis, Experiment, Observation, Conclusion. Systematic debugging. | Performance issues |

## Process & Workflow

| Anchor | Core Concepts | When to Use |
|--------|---------------|-------------|
| **Double Diamond** | Discover, Define, Develop, Deliver. Divergent and convergent thinking. Design Council. | Feature exploration |
| **Cynefin Framework** | Simple, Complicated, Complex, Chaotic, Disorder. Dave Snowden. Context-appropriate responses. | Decision making |
| **Wardley Mapping** | Value chain. Evolution stages. Strategic planning. Simon Wardley. | Tech strategy |
| **Kanban** | Visualize work. Limit WIP. Manage flow. Pull system. | Task management |

## Documentation

| Anchor | Core Concepts | When to Use |
|--------|---------------|-------------|
| **Diataxis Framework** | Tutorials, How-to guides, Reference, Explanation. Four documentation types. Daniele Procida. | Documentation structure |
| **Docs-as-Code** | Version controlled. Reviewed. Automated. Same tools as code. | Doc workflow |

---

## Anchor Combinations (Triangulation)

Combine anchors to create precise context:

| Combination | Activated Context |
|-------------|-------------------|
| `ATDD + BDD Gherkin + Specification by Example` | Full acceptance testing mindset with concrete examples |
| `Hexagonal Architecture + SOLID + Clean Architecture` | Layered, testable, maintainable code structure |
| `5 Whys + Ishikawa + Scientific Method` | Rigorous systematic debugging approach |
| `INVEST + EARS + Jobs-to-Be-Done` | Complete requirements engineering toolkit |
| `arc42 + C4 Model + ADR` | Comprehensive architecture documentation |

---

## Integration in Commands

### Example Header Block

```markdown
---
description: Create feature specification
semantic_anchors:
  - EARS Syntax
  - INVEST Criteria
  - Specification by Example
  - Jobs-to-Be-Done
---

# Specify Feature

**Activated Frameworks**: EARS for requirements, INVEST for story quality, Specification by Example for acceptance criteria.

You are a **Requirements Engineer** applying EARS syntax and INVEST criteria...
```

### Token Efficiency

Instead of:
> "Write requirements that are testable, unambiguous, and focused on user value with clear acceptance criteria that can be verified"

Use:
> "Apply EARS Syntax for requirements. Validate with INVEST criteria. Define acceptance via Specification by Example."

This compresses ~25 words to ~15 words while activating richer LLM knowledge.
