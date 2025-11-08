# Corporate Guidelines

Corporate/organizational guidelines for AI agents implementing Spec-Driven Development.

## Hierarchy

Priority order when making decisions:

1. **Constitution** (`/memory/constitution.md`) - HIGHEST
2. **Corporate Guidelines** (this directory) - MEDIUM
3. **Spec Kit Defaults** - LOWEST

Constitution always wins. If constitution says "MUST use PostgreSQL" but guidelines suggest MySQL, use PostgreSQL.

## File Structure

```text
.guidelines/
├── README.md                    # This file
├── branch-config.json           # Branch naming configuration
├── stack-mapping.json           # Multi-stack path mapping
├── reactjs-guidelines.md        # React/frontend standards
├── java-guidelines.md           # Java/Spring Boot standards
├── dotnet-guidelines.md         # .NET/C# standards
├── nodejs-guidelines.md         # Node.js/Express standards
└── python-guidelines.md         # Python/Django/Flask standards
```

## Version Management

Configuration files include version metadata:

```json
{
  "version": "1.0",
  "last_updated": "2025-01-15"
}
```

Guideline markdown files (optional):

```markdown
---
version: 1.2.0
last_updated: 2025-01-15
---
```

## Auto-Detection

Tech stack detected from project files:

- **ReactJS**: `package.json` with `"react"` dependency
- **Java**: `pom.xml` or `build.gradle`
- **.NET**: `*.csproj` or `*.sln`
- **Node.js**: `package.json` with `"express"` or backend dependencies
- **Python**: `requirements.txt`, `pyproject.toml`, or `setup.py`

## Multi-Stack Support

`stack-mapping.json` defines how guidelines map to paths:

```json
{
  "stacks": [
    {
      "name": "reactjs",
      "guideline": "reactjs-guidelines.md",
      "paths": ["frontend/**", "client/**"],
      "extensions": [".tsx", ".jsx"],
      "priority": 10
    },
    {
      "name": "java",
      "guideline": "java-guidelines.md",
      "paths": ["backend/**", "server/**"],
      "extensions": [".java"],
      "priority": 10
    }
  ]
}
```

Precedence (highest to lowest):

1. Explicit path mapping (`stack-mapping.json`)
2. File extension (`*.tsx` → React, `*.java` → Java)
3. Directory convention (`frontend/` → React, `backend/` → Java)
4. Auto-detection (project markers)

## Branch Configuration

**Note**: Branch naming strategy is handled by `branch-config.json` (machine-readable configuration) and scripts (`scripts/bash/create-new-feature.sh`), not by markdown guidelines. AI agents should use the JSON configuration for deterministic branch creation.

See `docs/branching-strategy.md` for user documentation on the branching system.

## Customization

Replace `@YOUR_ORG` placeholders with actual corporate package names in all `*-guidelines.md` files.

## Constitution vs Guidelines

- **Constitution** (`/memory/constitution.md`): Project principles, highest priority, requires team vote
- **Guidelines** (`/.guidelines/*.md`): Corporate infrastructure, medium priority, updated as standards change

## Non-Compliance

When guideline violations detected:

1. Warning message about non-compliance
2. Create `.guidelines-todo.md` in feature directory
3. Continue work (guidelines are recommendations, not blockers)

## Usage

Load guidelines automatically based on detected tech stack. Apply in priority order: Constitution > Guidelines > Defaults.

## Guideline Structure

Each `*-guidelines.md` file contains:

1. **Scaffolding**: Corporate commands for creating projects
2. **Package Registry**: Internal registry configuration
3. **Mandatory Libraries**: Required corporate packages
4. **Banned Libraries**: Packages that must not be used
5. **Architecture**: Preferred patterns
6. **Security**: Authentication, authorization, data handling
7. **Coding Standards**: Style guides, naming conventions
