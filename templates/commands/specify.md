# /spectrena.specify

Create or generate content for a specification.

## Usage

```
# Create new spec with content (one-step)
/spectrena.specify "Brief description" -c COMPONENT

# Generate content for existing spec OR create new interactively
/spectrena.specify
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| description | No | Brief title/description (if creating new) |
| --component, -c | Depends | Component prefix (CORE, API, UI, etc.) |

## Behavior

### Mode 1: With Description (Create New)

1. Validate component (prompt if required but missing)
2. **Create spec using CLI:** `spectrena new -c {component} "{description}"`
   - Creates spec directory with template
   - Creates git branch `spec/{spec-id}`
   - Registers in lineage database
3. If description is brief (< 20 words), ask 2-3 clarifying questions
4. Generate full spec content based on description + clarifications
5. Update spec.md with generated content

### Mode 2: Without Arguments

**If in a spec directory (spec.md exists):**
1. Read existing spec.md
2. Extract description from `## Description` section
3. If description is brief, ask clarifying questions
4. Generate content for empty sections
5. Update spec.md in place

**If NOT in a spec directory:**
1. Ask clarifying questions to understand what to build:
   - What feature/capability?
   - What problem does it solve?
   - Which component?
2. Generate descriptive title from answers
3. **Create spec using CLI:** `spectrena new -c {component} "{generated_title}"`
4. Generate full spec content
5. Save to spec.md

## Clarification Guidelines

**Brief is fine.** If the description lacks detail, ask 2-3 focused questions:

| Input | Questions to Ask |
|-------|------------------|
| `"User auth"` | "OAuth? Username/password? What providers?" |
| `"Monorepo setup"` | "What tools? Melos? Nx? What's being shared?" |
| `"REST API"` | "What resources? Auth required? Rate limiting?" |
| (no input) | "What feature? What problem? Which component?" |

**Max 3 clarification rounds.** Then generate with stated assumptions.

**Always offer to proceed with defaults** - don't block on answers:

```
I can generate with reasonable defaults if you prefer, or answer these quick questions for a more tailored spec.
```

## Content Generation

Fill these sections based on description + clarifications:

| Section | Guidelines |
|---------|------------|
| **Description** | Preserved from input or generated from clarifications |
| **Problem** | What pain point? Who is affected? 2-3 sentences. |
| **Solution** | High-level approach (not implementation). 2-3 sentences. |
| **Dependencies** | Other spec IDs that must complete first. |
| **Open Questions** | Unresolved decisions (from clarification gaps). |

## Examples

### Example 1: Mode 1 with brief input

```
User: /spectrena.specify "Auth system" -c CORE

Claude: I'll create the CORE auth spec. Quick questions:

1. Authentication method? (OAuth, username/password, SSO?)
2. Which OAuth providers if applicable?
3. Need role-based access control?

Or I can generate with OAuth + Google/GitHub defaults.

User: OAuth with Google and GitHub, no RBAC for now

Claude: Creating spec...

$ spectrena new -c CORE "OAuth authentication with Google and GitHub providers"
✓ Created specs/CORE-001-oauth-authentication/
✓ Created branch spec/CORE-001-oauth-authentication

[generates and saves full spec content]

✓ Spec ready: specs/CORE-001-oauth-authentication/spec.md
  Branch: spec/CORE-001-oauth-authentication
```

### Example 2: Mode 1 with detailed input

```
User: /spectrena.specify "OAuth authentication with Google and GitHub providers, JWT sessions, no RBAC initially" -c CORE

Claude: Creating spec...

$ spectrena new -c CORE "OAuth authentication with Google and GitHub providers"
✓ Created specs/CORE-001-oauth-authentication/
✓ Created branch spec/CORE-001-oauth-authentication

[generates full spec directly, no questions needed]

✓ Spec ready: specs/CORE-001-oauth-authentication/spec.md
  Branch: spec/CORE-001-oauth-authentication
```

### Example 3: Mode 2 in existing spec directory

```
User: /spectrena.specify

Claude: Reading specs/CORE-001-monorepo-setup/spec.md...

Description: "Monorepo and Build System"

That's brief. A few questions:
1. Monorepo tool preference? (Melos, Nx, Turborepo?)
2. What packages/apps will share code?
3. CI/CD integration needed?

User: Melos for Flutter, 3 apps sharing a design system, GitHub Actions

Claude: [fills in Problem, Solution, etc. in existing spec.md]

✓ Updated: specs/CORE-001-monorepo-setup/spec.md
```

### Example 4: Mode 2 with no existing spec

```
User: /spectrena.specify

Claude: No spec found in current directory. Let's create one.

1. What feature are you building?
2. What problem does it solve?
3. Which component? (CORE, API, UI, INFRA)

User: Need a notification system for sending push and email alerts. It's infrastructure level.

Claude: Creating spec...

$ spectrena new -c INFRA "Push and email notification system"
✓ Created specs/INFRA-001-push-and-email-notification-system/
✓ Created branch spec/INFRA-001-push-and-email-notification-system

[generates full spec content]

✓ Spec ready: specs/INFRA-001-push-and-email-notification-system/spec.md
  Branch: spec/INFRA-001-push-and-email-notification-system
```
