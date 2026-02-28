# Wireframe Generation

## Overview

The wireframe commands generate SVG wireframes from your feature specification, providing visual validation before technical implementation begins. This creates a stakeholder review checkpoint in the SDD workflow.

## Commands

| Command | Description |
|---------|-------------|
| `/speckit.wireframe` | Generate dark-theme SVG wireframes |
| `/speckit.wireframe-light` | Generate light-theme SVG wireframes |

## When to Use

**Use wireframes when:**
- Your feature has user-facing UI components
- You need stakeholder sign-off before implementation
- Complex user flows need visual clarification
- You want to validate the spec interpretation visually

**Skip wireframes when:**
- Backend-only features (APIs, services)
- Infrastructure or DevOps work
- Pure data processing features

## Workflow Integration

```
/speckit.specify → /speckit.clarify → /speckit.wireframe → [REVIEW] → /speckit.plan
```

Wireframes provide a "hard stop" for stakeholder approval before investing in technical planning and implementation.

## Output Location

Wireframes are saved to a `wireframes/` subdirectory within the feature's spec directory:

```
specs/[###-feature-name]/wireframes/
```

For example:
```
specs/001-user-profile/
├── spec.md
├── wireframes/
│   ├── profile-view.svg
│   └── profile-edit.svg
└── plan.md (after /speckit.plan)
```

## Canvas Sizes

| Canvas | Dimensions | Use Case |
|--------|------------|----------|
| Standard | 1400×800 | Default for most screens |
| Wide | 1600×800 | Extra annotation space (100px margins) |
| Tall | 1400×1000 | Complex vertical layouts |
| Extended | 1600×1000 | Full annotation mode |

## Layout Structure

Each wireframe shows **side-by-side Desktop and Mobile** views:

| Section | Position | Size |
|---------|----------|------|
| Desktop area | x=40, y=60 | 900×680 (3-column layout) |
| Mobile area | x=980, y=60 | 360×700 (phone frame) |

**Desktop 3-column layout:**
- Sidebar: 200px
- Main content: 440px
- Detail panel: 240px
- 10px gaps between columns

## Dark vs Light Theme

Both themes use the same layout structure with different color palettes:

### Dark Theme (`/speckit.wireframe`)
- Background: `#0f172a` → `#1e293b` gradient
- Primary accent: `#8b5cf6` (violet)
- Best for: Developer presentations, dark mode applications

### Light Theme (`/speckit.wireframe-light`)
- Background: `#ffffff` → `#f0f4f8` gradient
- Primary accent: `#8b5cf6` (violet)
- Best for: Client presentations, light mode applications

## Multi-Page Wireframes

For complex features, the command generates multiple SVG files:

| Scenario | Naming Pattern | Example |
|----------|----------------|---------|
| Sequential flow | `NN-step-name.svg` | `01-login.svg`, `02-register.svg` |
| State variations | `screen-state.svg` | `dashboard-empty.svg`, `dashboard-error.svg` |
| Role variations | `screen-role.svg` | `settings-admin.svg`, `settings-member.svg` |

## Annotations

Wireframes include annotation callouts that explain UI interactions:
- Annotation boxes in margin areas
- Dashed leader lines connecting to UI elements
- Color-coded by interaction type

## Example Usage

```
/speckit.wireframe
```

The command will:
1. Identify the feature's spec file
2. Analyze UI requirements from the spec
3. Recommend a wireframe strategy
4. Generate SVG files in the wireframes directory
5. Confirm files are ready for browser review

After generation, open the SVG files in any browser to review with stakeholders.
