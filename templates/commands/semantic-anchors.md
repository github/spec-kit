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

## Requirements Elicitation

| Anchor | Core Concepts | When to Use |
|--------|---------------|-------------|
| **Socratic Method** | Guided questioning to uncover assumptions. Reveal gaps through dialogue. | Clarification sessions |
| **Requirements Elicitation** | Structured discovery techniques. Stakeholder interviews. Observation. Workshops. | Gathering requirements |
| **Active Listening** | Capture intent, not just words. Paraphrase. Clarify understanding. | User interviews |

## Project Management

| Anchor | Core Concepts | When to Use |
|--------|---------------|-------------|
| **Work Breakdown Structure** | Hierarchical decomposition. Deliverable-oriented. WBS Dictionary. | Task decomposition |
| **User Story Mapping** | Backbone (activities) → Skeleton (tasks) → Ribs (stories). Jeff Patton. | Feature organization |
| **Dependency Graph** | DAG for task ordering. Critical path identification. Blocking analysis. | Task sequencing |
| **Critical Path Method** | Longest sequence of dependent tasks. Float calculation. Schedule optimization. | Project scheduling |
| **Progressive Elaboration** | Refine details as knowledge increases. Rolling wave planning. | Iterative planning |
| **Spike** | Timeboxed research/exploration. Reduce uncertainty. XP practice. | Research tasks |

## Quality Assurance

| Anchor | Core Concepts | When to Use |
|--------|---------------|-------------|
| **Definition of Ready** | Criteria for starting work. Scrum artifact. Prerequisites checklist. | Pre-work validation |
| **Definition of Done** | Completion criteria. Quality gates. Acceptance checklist. | Work completion |
| **Quality Gates** | Stage-gate process. Checkpoints. Go/no-go decisions. | Phase transitions |
| **Acceptance Criteria** | Testable conditions. Pass/fail requirements. Gherkin scenarios. | Story validation |
| **Exploratory Testing** | Session-based. Charter-driven. Observe beyond scripts. Discovery focus. | Finding edge cases |
| **Regression Testing** | Verify unchanged functionality. Detect unintended changes. | Post-change validation |

## Code Quality

| Anchor | Core Concepts | When to Use |
|--------|---------------|-------------|
| **Code Smell Catalog** | Martin Fowler's refactoring patterns. Long method. God class. Feature envy. | Code review |
| **OWASP Top 10** | Security vulnerability classification. Injection. Broken auth. XSS. | Security review |
| **Technical Debt Quadrant** | Martin Fowler: Reckless/Prudent × Deliberate/Inadvertent. | Debt classification |
| **Cyclomatic Complexity** | McCabe metric. Decision points. Branch counting. Testability indicator. | Complexity analysis |
| **Boy Scout Rule** | Leave code better than you found it. Incremental improvement. | Continuous improvement |

## Pattern Discovery

| Anchor | Core Concepts | When to Use |
|--------|---------------|-------------|
| **Pattern Mining** | Extract recurring solutions. Identify conventions. Document idioms. | Codebase analysis |
| **Code Archaeology** | Understanding existing systems. Historical analysis. Evolution tracking. | Legacy code |
| **Conway's Law** | System structure mirrors organization. Communication patterns. | Architecture analysis |

## Agent & System Design

| Anchor | Core Concepts | When to Use |
|--------|---------------|-------------|
| **Single Responsibility** | One reason to change. Focused purpose. SOLID SRP. | Agent design |
| **Separation of Concerns** | Independent aspects. Loose coupling. High cohesion. | System decomposition |
| **Domain-Driven Design** | Bounded contexts. Ubiquitous language. Aggregates. Eric Evans. | Domain modeling |
| **Microservices Pattern** | Independent deployment. Specialized components. API boundaries. | Service architecture |
| **Capability Mapping** | Skills to roles. Competency alignment. Resource allocation. | Agent assignment |

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
| `Socratic Method + Requirements Elicitation + Active Listening` | Effective clarification and discovery sessions |
| `Code Smell Catalog + OWASP Top 10 + Technical Debt Quadrant` | Comprehensive code review covering quality, security, and debt |
| `User Story Mapping + Work Breakdown Structure + Dependency Graph` | Complete task organization and sequencing |
| `Definition of Ready + Definition of Done + Quality Gates` | Full quality lifecycle management |
| `Pattern Mining + ADR + Code Archaeology` | Systematic pattern extraction and documentation |
| `Single Responsibility + Separation of Concerns + DDD` | Well-designed agent and component architecture |

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
