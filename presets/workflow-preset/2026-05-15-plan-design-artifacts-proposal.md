# Plan Design Artifacts Proposal

> Superseded in the current preset contract: `test-plan.md` is no longer a standalone artifact. Test strategy is derived by `/speckit.tasks` from behavior contracts, interface contracts, `research.md`, and `quickstart.md`; object design and service sequencing remain optional planning artifacts.

## Purpose

This proposal refines the expected output boundary of `/speckit.plan`.
The current planning workflow produces `plan.md`, `research.md`,
`data-model.md`, `contracts/`, and `quickstart.md`. That covers the
technical approach, domain model, interface contracts, and a key validation
path, but it leaves three design concerns without stable homes:

1. Internal object structure: design patterns, inheritance, composition,
   dependencies, and references between implementation objects.
2. Service-call behavior: the order of calls across APIs, services, external
   systems, asynchronous events, and failure branches.
3. Test design: the testing scope, testing levels, scenario matrix, data
   strategy, and traceability from requirements to validation.

The goal is to add explicit planning artifacts for these concerns without
turning `plan.md` into a large mixed-purpose document. `plan.md` should remain
the technical decision summary and navigation point. Detailed design should
live in dedicated files that can be consumed by `/speckit.tasks`,
`/speckit.implement`, and reviewers.

## Recommended File Layout

Use independent planning artifacts under the feature directory:

```text
specs/<feature>/
├── plan.md
├── research.md
├── data-model.md
├── contracts/
│   ├── <interface-contracts>
│   └── sequences.md
├── class-diagram.md
├── test-plan.md
└── quickstart.md
```

The three proposed additions are:

- `class-diagram.md`: internal implementation object design.
- `contracts/sequences.md`: service-call and interface-flow sequencing.
- `test-plan.md`: testing strategy and test scenario design.

## Planning Granularity

`/speckit.plan` operates at technical design granularity. It should provide
enough structure for `/speckit.tasks` to create executable tasks and for
`/speckit.implement` to preserve the intended architecture, but it should not
expand into task numbering, source code, test functions, or method-level
implementation details.

```text
spec.md
  product behavior, user stories, acceptance criteria

plan.md
  technical approach, decisions, constraints, artifact navigation

research.md
  unresolved technical questions, decisions, rationale, alternatives

data-model.md
  domain entities, business fields, relationships, validation, states

contracts/
  external interface contracts and observable service interaction behavior

class-diagram.md
  internal object structure, patterns, inheritance, composition, references

test-plan.md
  testing strategy, coverage intent, scenario matrix, validation levels

quickstart.md
  minimal executable validation path

tasks.md
  concrete tasks, files, ordering, parallelization
```

## Artifact Contracts

### `class-diagram.md`

**Responsibility**

`class-diagram.md` captures internal implementation design. It explains how
the code should be organized around core classes, interfaces, abstract types,
design patterns, inheritance, composition, aggregation, dependencies, and
references.

It is the right place for diagrams involving objects such as services,
repositories, adapters, strategies, factories, controllers, coordinators,
interfaces, and abstract base classes.

**Upstream inputs**

- `spec.md`: user stories, feature behavior, and domain language.
- `plan.md`: selected architecture, project structure, platform, and
  implementation constraints.
- `research.md`: decisions about design patterns, framework constraints,
  extensibility, or dependency direction.
- `data-model.md`: domain entities that need representation in the
  implementation object model.
- `contracts/`: external boundaries that internal objects must satisfy.

**Downstream consumers**

- `/speckit.tasks`: derives implementation tasks for services, adapters,
  repositories, strategies, factories, interfaces, and other core objects.
- `/speckit.implement`: preserves object boundaries, dependency direction,
  inheritance, and composition choices.
- Code review: checks whether implementation drifted from the intended design
  pattern or object responsibilities.

**Boundary**

`class-diagram.md` does not define API request or response fields. Those belong
in `contracts/`.

It does not replace `data-model.md`. Domain entity fields, business validation,
relationships, and state transitions remain in `data-model.md`. A class diagram
may reference a domain entity only when needed to explain object collaboration.

It does not define test strategy or test cases. Those belong in `test-plan.md`.

It does not define task IDs, file-by-file implementation steps, or execution
order. Those belong in `tasks.md`.

**Granularity**

The artifact should describe core implementation types and their relationships:

- Key classes, interfaces, and abstract types.
- Responsibilities of each core type.
- Inheritance, composition, aggregation, dependency, and reference
  relationships.
- Design pattern participants and extension points.
- Lifecycle or ownership rules when they affect implementation structure.

It should not list every helper, DTO, private utility, or method. It may include
important methods only when they are necessary to explain a design pattern or
object contract.

**Decision rule**

If the question is "how are internal implementation objects organized?", use
`class-diagram.md`.

If the question is "what business fields does the entity have?", use
`data-model.md`.

If the question is "what does the external interface accept or return?", use
`contracts/`.

### `contracts/sequences.md`

**Responsibility**

`contracts/sequences.md` captures service-call-level sequencing. It explains
how an API request, command, event, or external interaction flows across
components, services, infrastructure, and third-party systems.

It is the right place for sequence diagrams covering synchronous calls,
asynchronous events, callbacks, retries, compensation, rollback, and observable
failure behavior.

**Upstream inputs**

- `spec.md`: user workflows, acceptance scenarios, and externally observable
  behavior.
- `plan.md`: service boundaries, architecture, deployment assumptions, and
  external dependencies.
- `research.md`: integration decisions, failure-handling decisions, and
  framework constraints.
- `contracts/`: endpoint, command, event, or message contracts.
- `data-model.md`: state changes or persistence boundaries affected by the
  service flow.

**Downstream consumers**

- `/speckit.tasks`: derives tasks for integrations, service orchestration,
  transaction boundaries, async event handling, retries, and failure paths.
- `/speckit.implement`: implements the intended call order, service boundaries,
  compensation behavior, and error propagation.
- `test-plan.md`: derives integration, contract, and end-to-end scenarios from
  the documented flows.

**Boundary**

`contracts/sequences.md` does not define request and response field schemas.
Those belong in the interface contract files under `contracts/`.

It does not describe internal inheritance, composition, or class relationships.
Those belong in `class-diagram.md`.

It does not define the testing matrix. That belongs in `test-plan.md`.

It does not provide user-facing run instructions. Those belong in
`quickstart.md`.

**Granularity**

The artifact should describe participants, message order, service boundaries,
and critical branches:

- Calling actor or system.
- API, service, worker, database, queue, or external system participants.
- Main success path.
- Important alternate paths.
- Failure handling, retries, compensation, rollback, and idempotency behavior.
- Async event publication and consumption when applicable.

It should not expand into individual private function calls unless a function
represents a meaningful service or integration boundary.

**Decision rule**

If the question is "how does a request, command, or event flow across
components or services?", use `contracts/sequences.md`.

If the question is "what fields are in the interface?", use the relevant
contract schema under `contracts/`.

If the question is "which classes collaborate internally?", use
`class-diagram.md`.

### `test-plan.md`

**Responsibility**

`test-plan.md` captures test design. It defines how the feature should be
validated across test levels, what is in scope, what is out of scope, which
data is needed, and how requirements trace to validation scenarios.

It should include a test case matrix as one section, not reduce the whole
artifact to a matrix. The plan should explain the strategy behind the matrix.

**Upstream inputs**

- `spec.md`: user stories, acceptance criteria, edge cases, and priorities.
- `plan.md`: testing framework, technical stack, project structure, and
  constraints.
- `research.md`: test tooling decisions and tradeoffs.
- `data-model.md`: validation rules, state transitions, and data combinations.
- `contracts/`: interface contracts that need contract tests.
- `contracts/sequences.md`: integration flows, async flows, and failure paths.
- `quickstart.md`: minimal executable validation path.

**Downstream consumers**

- `/speckit.tasks`: derives test tasks, including unit, contract, integration,
  and end-to-end validation tasks.
- `/speckit.implement`: executes validation according to the planned testing
  levels and coverage intent.
- CI and review: check whether delivered tests match the planned coverage.
- `quickstart.md`: remains the minimal manual or scripted validation path and
  can be referenced by the test plan.

**Boundary**

`test-plan.md` does not implement test code. Test files, test functions,
fixtures, and assertions are created during implementation.

It does not replace `quickstart.md`. `quickstart.md` is the shortest executable
validation path; `test-plan.md` is the broader test design.

It does not redefine product requirements. Requirements remain in `spec.md`.

It does not redefine interface schemas. Schemas remain in `contracts/`.

It does not assign task IDs or execution order. Those belong in `tasks.md`.

**Granularity**

The artifact should describe validation intent at scenario and test-level
granularity:

- Test objectives.
- In-scope and out-of-scope areas.
- Unit, contract, integration, and end-to-end testing strategy.
- Test data, fixture, and mock strategy.
- Requirement-to-test traceability.
- Test case matrix with scenario, preconditions, inputs, expected result, test
  level, and source requirement.
- Non-functional validation when required by the feature, such as performance,
  security, compatibility, or accessibility.

It should not include exact test function bodies, assertion code, or complete
fixture file contents.

**Decision rule**

If the question is "what should be tested and at what level?", use
`test-plan.md`.

If the question is "how can a user or reviewer quickly verify the feature
works?", use `quickstart.md`.

If the question is "which test file should be created first?", use `tasks.md`.

## `plan.md` Boundary

`plan.md` should remain the decision summary and navigation file. It should
reference the detailed artifacts rather than embedding their full contents.

Recommended `plan.md` section:

```markdown
## Design Artifacts

- Internal object design: ./class-diagram.md
- Service sequences: ./contracts/sequences.md
- Test plan: ./test-plan.md
- Data model: ./data-model.md
- Interface contracts: ./contracts/
- Validation path: ./quickstart.md
```

`plan.md` owns:

- Technical approach.
- Technology choices.
- Project structure.
- Constitution and architecture checks.
- Complexity justification.
- Links to detailed design artifacts.

`plan.md` does not own:

- Complete class diagrams.
- Complete sequence diagrams.
- Complete test matrices.
- Task IDs or file-level implementation steps.
- Source code or test code.

## Reasoning Flow

The proposed artifacts form a dependency chain that preserves the current
spec-driven workflow while making design responsibilities explicit:

```text
                 ┌──────────────┐
                 │   spec.md    │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │   plan.md    │
                 └──────┬───────┘
                        ↓
        ┌───────────────┼────────────────┐
        ↓               ↓                ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ data-model.md│ │  contracts/  │ │ research.md  │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       ↓                ↓                ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│class-diagram │ │ sequences.md │ │ test-plan.md │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       └───────────────┬┴───────────────┘
                       ↓
                 ┌──────────────┐
                 │   tasks.md   │
                 └──────────────┘
```

The dependency direction is intentional:

- `spec.md` defines the product behavior.
- `plan.md` chooses the technical approach and points to design artifacts.
- `research.md` resolves unknowns that influence design decisions.
- `data-model.md` defines domain state and business data.
- `contracts/` defines externally visible interfaces.
- `class-diagram.md` translates domain and architecture decisions into internal
  object structure.
- `contracts/sequences.md` translates interface boundaries into observable
  service flows.
- `test-plan.md` derives validation strategy from requirements, data,
  contracts, and service flows.
- `tasks.md` converts the design artifacts into ordered executable work.

## Expected Downstream Behavior

If this proposal is accepted, `/speckit.tasks` should treat these files as
optional but first-class planning inputs:

- Read `class-diagram.md` when present and generate implementation tasks that
  preserve the documented object model.
- Read `contracts/sequences.md` when present and generate integration,
  orchestration, async-flow, and failure-path tasks.
- Read `test-plan.md` when present and generate test tasks that reflect the
  planned test levels and scenario matrix.

`/speckit.implement` should also read these files when present:

- Use `class-diagram.md` to keep implementation object boundaries aligned.
- Use `contracts/sequences.md` to implement service flows and failure behavior.
- Use `test-plan.md` to validate the delivered feature against the planned
  coverage.

## Non-Goals

This proposal does not require all features to produce large diagrams or a
large test plan. Simple features may produce concise files or mark sections as
not applicable with a concrete reason.

This proposal does not move product requirements out of `spec.md`.

This proposal does not replace `data-model.md`, `contracts/`, or
`quickstart.md`.

This proposal does not require source code changes by itself. It defines a
reviewable target design for possible future changes to the Spec Kit templates
and command instructions.

## Review Questions

1. Should `class-diagram.md`, `contracts/sequences.md`, and `test-plan.md` be
   required for every `/speckit.plan` run, or optional artifacts generated only
   when relevant?
2. Should `/speckit.tasks` generate test tasks automatically whenever
   `test-plan.md` exists, even if the user did not explicitly request TDD?
3. Should sequence diagrams be stored only in `contracts/sequences.md`, or
   should projects with no external contracts place them at
   `specs/<feature>/sequences.md`?
4. Should `class-diagram.md` use Mermaid class diagrams as the default format,
   or remain format-neutral so teams can use PlantUML or text tables?
