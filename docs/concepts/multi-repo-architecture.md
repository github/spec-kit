# Multi-Repository Architecture

Managing specifications across multiple codebases.

> **Practical Guide**: See [Guides: Multi-Repo Workspaces](../guides/multi-repo-workspaces.md) for workflow and examples.

## Workspace Structure

```
workspace-root/
├─ .specify/
│  └─ workspace.yml    # Workspace configuration
├─ specs/              # Centralized specifications
│  ├─ feature-1/
│  └─ feature-2/
├─ backend-repo/       # Git repository
├─ frontend-repo/      # Git repository
└─ cli-repo/          # Git repository
```

## Key Concepts

- **One specification** spans multiple repos
- **Convention-based routing** determines which repos are affected
- **Per-repo requirements** can differ (Jira keys, architectures)
- **Centralized tracking** through specifications

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

## Capabilities in Multi-Repo

For large multi-repo features:
1. Create full specification
2. Decompose into capabilities
3. Each capability targets specific repo(s)
4. Parallel implementation across repos

## Next Steps

- [Guides: Multi-Repo Workspaces](../guides/multi-repo-workspaces.md) - Detailed setup and workflows
- [Getting Started](../getting-started/) - Installation and first steps
