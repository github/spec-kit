# /spectrena.specify

Create or generate content for a specification.

## Usage

```
# Create new spec with content (one-step)
/spectrena.specify "Brief description" -c COMPONENT

# Generate content for existing spec (after spectrena new)
/spectrena.specify
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| description | No | Brief title/description (if creating new) |
| --component, -c | Depends | Component prefix (CORE, API, UI, etc.) |

## Input Expectations

**Brief is fine.** If the description lacks detail, ask 2-3 clarifying questions before generating.

| Input | Action |
|-------|--------|
| `"User auth"` | Ask: "OAuth? Username/password? What providers?" |
| `"Monorepo setup"` | Ask: "What tools? Melos? Nx? What's being shared?" |
| `"REST API"` | Ask: "What resources? Auth required? Rate limiting?" |
| Detailed paragraph | Generate directly, confirm understanding |

**Max 3 clarification rounds.** Then generate with stated assumptions.

## Clarification Guidelines

Ask focused questions:

```
I'll create the spec for "Monorepo setup". A few quick questions:

1. What monorepo tool? (Melos, Nx, Turborepo, or undecided?)
2. What will be shared across packages? (code, assets, configs?)
3. Any CI/CD requirements?

Or if you want, I can generate with reasonable defaults and you can refine.
```

**Always offer to proceed with defaults** - don't block on answers.

## Behavior

### Mode 1: With Description (Create New)

1. Validate component (prompt if required but missing)
2. If description is brief (< 20 words), ask 2-3 clarifying questions
3. Generate spec ID using project config
4. Create spec directory and branch
5. Generate full spec content
6. Save to spec.md

### Mode 2: Without Arguments (Fill Existing)

1. Read existing spec.md
2. Extract description from `## Description` section
3. If description is brief, ask clarifying questions
4. Generate content for empty sections
5. Update spec.md in place

## Content Generation

Fill these sections based on the description (and clarifications):

| Section | Guidelines |
|---------|------------|
| **Problem** | What pain point? Who is affected? 2-3 sentences. |
| **Solution** | High-level approach (not implementation). 2-3 sentences. |
| **Dependencies** | Other spec IDs that must complete first. |
| **Open Questions** | Unresolved decisions (from clarification gaps). |

## Examples

### Brief Input → Clarification

```
User: /spectrena.specify "Auth system" -c CORE

Claude: I'll create the CORE auth spec. Quick questions:

1. Authentication method? (OAuth, username/password, SSO, magic links?)
2. Which OAuth providers if applicable? (Google, GitHub, etc.)
3. Need role-based access control (RBAC)?

Or I can generate with OAuth + Google/GitHub defaults.

User: OAuth with Google and GitHub, no RBAC for now

Claude: Got it. Creating CORE-001-auth-system...
[generates full spec]
```

### Detailed Input → Direct Generation

```
User: /spectrena.specify "OAuth authentication with Google and GitHub providers, session management with JWT, no RBAC initially but design for future extension" -c CORE

Claude: Creating CORE-001-oauth-authentication...
[generates full spec directly, no questions needed]
```

### Fill Existing Spec

```
User: /spectrena.specify

Claude: Reading specs/CORE-001-monorepo-setup/spec.md...
Description: "Monorepo and Build System"

That's brief. A few questions:
1. Monorepo tool preference?
2. What packages/apps will share code?
3. CI/CD integration needed?

User: Melos for Flutter, 3 apps sharing a design system and API client, GitHub Actions

Claude: [fills in Problem, Solution, Dependencies, etc.]
```
