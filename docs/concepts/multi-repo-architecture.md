# Multi-Repository Architecture

Managing specifications across multiple codebases.

> **Practical Guide**: See [Guides: Multi-Repo Workspaces](../guides/multi-repo-workspaces.md) for workflow and examples.

## Workspace as a Version-Controlled Entity

### Core Principle

In multi-repo architecture, the **workspace itself must be a git repository**. This is not optional—it's fundamental to treating specifications as first-class citizens in your development process.

### Why Workspace Version Control Matters

**Specifications are not ephemeral documentation**. They are:
- **Living requirements** that evolve with your product
- **Decision records** explaining why features were built a certain way
- **Contracts** between frontend, backend, and other system components
- **Historical artifacts** showing how your system architecture evolved

Without version control:
- ❌ No history of requirement changes
- ❌ No code review for specs (specs should be reviewed like code!)
- ❌ No traceability from code back to requirements
- ❌ Team members have different versions of specs
- ❌ CI/CD cannot access specifications
- ❌ Impossible to correlate spec changes with implementation changes

### Philosophical Foundation

This approach aligns with **Spec-Driven Development's core philosophy**: specifications are executable artifacts that directly generate implementations. If specs drive code, they deserve the same rigor:

| Artifact | Version Control | Code Review | CI/CD | Team Collaboration |
|----------|----------------|-------------|-------|-------------------|
| **Code** | ✅ Always | ✅ Always | ✅ Always | ✅ Always |
| **Specs** | ✅ Must have | ✅ Must have | ✅ Must have | ✅ Must have |

**Specs = Code**. Therefore: **Specs need git**.

## Workspace Structure

```
workspace-root/           # ← This is a git repository
├─ .git/                 # Version control for workspace
├─ .specify/
│  └─ workspace.yml      # Workspace configuration
├─ specs/                # Centralized specifications (tracked by workspace git)
│  ├─ feature-1/
│  └─ feature-2/
├─ backend-repo/         # Separate git repository
│  └─ .git/             # Independent version control
├─ frontend-repo/        # Separate git repository
│  └─ .git/             # Independent version control
└─ cli-repo/            # Separate git repository
   └─ .git/             # Independent version control
```

**Critical distinction:** The workspace directory is a git repository that tracks **specifications**. Sub-directories (backend-repo/, frontend-repo/) are separate git repositories that track **code**. They are independent unless you use git submodules.

## Key Concepts

- **One specification** spans multiple repos
- **Convention-based routing** determines which repos are affected
- **Per-repo requirements** can differ (Jira keys, architectures)
- **Centralized tracking** through specifications
- **Version-controlled workspace** ensures specs are treated like code

## Convention-Based Routing

Specs automatically route to target repos based on naming:
- `backend-*` → backend repo
- `frontend-*` → frontend repo
- `fullstack-*` → all repos

Customizable in `workspace.yml`.

## Per-Repo Requirements

Different repos in same workspace can have:
- Different Jira key requirements (enterprise vs public GitHub)
- Different architectural patterns
- Different tech stacks
- Different coding standards

## Industry Patterns and Precedents

The workspace-as-repository pattern is not unique to spec-kit. It's a well-established practice in large-scale software development:

### Pattern Examples

**Kubernetes Enhancement Proposals (KEPs)**
- Repo: `kubernetes/enhancements`
- Purpose: Cross-cutting proposals spanning 100+ component repos
- Pattern: Central RFC repo + individual component repos

**Rust Language RFCs**
- Repo: `rust-lang/rfcs`
- Purpose: Language and stdlib evolution proposals
- Pattern: RFC repo separate from compiler, stdlib, tools

**Android Open Source Project (AOSP)**
- Tool: repo manifest system
- Purpose: Coordinate 400+ repositories
- Pattern: Manifest repo + component repos

**Enterprise Architectures**
- Pattern: "Platform docs" or "Architecture" repo
- Common at: Netflix, Uber, Amazon (microservices)
- Purpose: Cross-service contracts and specifications

### Why This Pattern Works

1. **Clear separation**: Specs (requirements) vs code (implementation)
2. **Independent lifecycle**: Specs can evolve before/after code
3. **Single source of truth**: One place for all cross-cutting concerns
4. **Access control**: Different teams can have different permissions
5. **Discoverability**: Central repo is obvious entry point for new team members

## Alternative Organizational Patterns

While workspace-as-repository is the default, teams may choose alternatives:

### When to Use Each Pattern

| Pattern | Best For | Drawbacks |
|---------|----------|-----------|
| **Workspace repo** (default) | Multi-repo systems with cross-cutting features | Extra repo to manage |
| **Separate specs repo** | Large orgs, RFC-style processes | Need to maintain cross-references |
| **Specs in dominant repo** | Small teams, single primary repo | Feels unbalanced for equal repos |
| **Specs per repo** | Fully independent services | Hard to manage cross-cutting specs |

See [Multi-Repo Workspaces Guide](../guides/multi-repo-workspaces.md#alternative-patterns) for detailed comparison.

## Capabilities in Multi-Repo

For large multi-repo features:
1. Create full specification (tracked in workspace)
2. Decompose into capabilities
3. Each capability targets specific repo(s)
4. Parallel implementation across repos
5. All capability specs tracked in workspace

**Traceability chain:**
```
Workspace git (specs)
  ↓ References
Code repos (implementation)
  ↓ Links back to
Workspace git (specs)
```

## Conceptual Model

Think of the workspace as the **"product brain"**:
- **Workspace repo** = Product vision, requirements, specifications
- **Code repos** = Implementation details, execution

The workspace answers "what and why", code repos answer "how".

This separation enables:
- ✅ Spec review before implementation starts
- ✅ Implementation changes without spec churn
- ✅ Multiple implementations of same spec (experimentation)
- ✅ Spec reuse across different systems

## Next Steps

- [Guides: Multi-Repo Workspaces](../guides/multi-repo-workspaces.md) - Detailed setup and workflows
- [Getting Started](../getting-started/) - Installation and first steps
- [Workspace Config Reference](../reference/workspace-config.md) - Technical configuration details
