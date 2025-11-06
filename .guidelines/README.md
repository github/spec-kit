# Corporate Guidelines

This directory contains corporate/organizational guidelines that customize Spec Kit behavior for your specific development environment.

## Purpose

These guidelines allow you to specify:

- **Corporate infrastructure** - Internal scaffolding commands, package registries, SDKs
- **Mandatory libraries** - Required corporate packages for authentication, UI components, APIs
- **Security & compliance** - Corporate security policies, data handling requirements
- **Coding standards** - Tech stack-specific best practices and patterns
- **Branch naming** - Corporate branch naming conventions

## Hierarchy

When making decisions, prompts follow this priority order:

1. **Constitution** (`/memory/constitution.md`) - Project-specific principles (HIGHEST)
2. **Corporate Guidelines** (this directory) - Organizational standards (MEDIUM)
3. **Spec Kit Defaults** - Built-in best practices (LOWEST)

**Example**: If constitution says "MUST use PostgreSQL" but guidelines suggest MySQL, constitution wins.

## File Structure

```text
.guidelines/
├── README.md                    # This file
├── branching-guidelines.md      # Branch naming conventions
├── reactjs-guidelines.md        # React/frontend standards
├── java-guidelines.md           # Java/Spring Boot standards
├── dotnet-guidelines.md         # .NET/C# standards
├── nodejs-guidelines.md         # Node.js/Express standards
└── python-guidelines.md         # Python/Django/Flask standards
```

## How It Works

### Auto-Detection

Prompts automatically detect your tech stack from project files:

- **ReactJS**: `package.json` with `"react"` dependency
- **Java**: `pom.xml` or `build.gradle`
- **.NET**: `*.csproj` or `*.sln`
- **Node.js**: `package.json` with `"express"` or backend-focused dependencies
- **Python**: `requirements.txt`, `pyproject.toml`, or `setup.py`

### Multi-Stack Support

If multiple tech stacks detected (e.g., React frontend + Java backend), prompts load and apply both guidelines contextually.

**Example**:

- Frontend code → Apply `reactjs-guidelines.md`
- Backend code → Apply `java-guidelines.md`

## Customization

### Step 1: Copy This Directory to Your Project

When initializing a new project with Specify:

```bash
specify init --ai claude
```

Copy `.guidelines/` from the Spec Kit release package to your project root.

### Step 2: Customize Guidelines

Edit each `*-guidelines.md` file to match your organization:

**Before** (generic placeholder):

```markdown
## Scaffolding

Use corporate React scaffolding:

```bash
npx @YOUR_ORG/create-react-app my-app
```

**After** (customized):

```markdown
## Scaffolding

Use corporate React scaffolding:

```bash
npx @acmecorp/create-react-app my-app --template typescript
```

### Step 3: Commit Guidelines to Your Repo

Guidelines are **project-specific** and should be versioned:

```bash
git add .guidelines/
git commit -m "chore: add corporate development guidelines"
```

### Step 4: Update as Standards Evolve

When corporate standards change:

1. Update relevant `*-guidelines.md` files
2. Commit changes
3. Spec Kit prompts automatically use updated guidelines

## Guidelines vs Constitution

| Aspect | Constitution | Guidelines |
|--------|--------------|------------|
| **Scope** | Project principles | Corporate infrastructure |
| **Priority** | Highest | Medium |
| **Location** | `/memory/constitution.md` | `/.guidelines/*.md` |
| **Changes** | Requires team vote | Updated as standards change |
| **Example** | "MUST write tests first" | "Use @acme/ui-components" |

## Non-Compliance Handling

When prompts detect guideline violations:

1. **Warning**: Explicit message about non-compliance
2. **TODO file**: Creates `.guidelines-todo.md` in feature directory listing violations
3. **Continue**: Allows work to proceed (guidelines are recommendations, not blockers)

**Example TODO file**:

```markdown
# Guideline Compliance TODOs

## ⚠️ Violations Detected

- [ ] Replace public npm packages with @acme/ui-components
- [ ] Configure Artifactory registry in package.json
- [ ] Update authentication to use @acme/idm-client

## Corporate Standards

See: `.guidelines/reactjs-guidelines.md`
```

## Usage in Prompts

Guidelines are read by these prompts:

- **`/specify plan`** - Architecture decisions (CRITICAL)
- **`/specify implement`** - Code generation (CRITICAL)
- **`/specify analyze`** - Compliance validation (IMPORTANT)
- **`/specify tasks`** - Task generation (IMPORTANT)

**Example usage** (automatic, no user action needed):

```text
User: /specify plan

Agent:
1. Reading constitution.md...
2. Detecting tech stack... found React + Java
3. Loading reactjs-guidelines.md and java-guidelines.md...
4. Creating architecture plan following:
   - Constitution principles (highest priority)
   - Corporate guidelines (medium priority)
   - Spec Kit defaults (lowest priority)
```

## Tech Stack Templates

Each `*-guidelines.md` file contains:

### 1. Scaffolding

Corporate commands for creating new projects/modules.

### 2. Package Registry

Internal registry configuration (Artifactory, Nexus, etc.).

### 3. Mandatory Libraries

Required corporate packages with usage examples.

### 4. Banned Libraries

Public packages that must not be used (security/licensing).

### 5. Architecture Patterns

Preferred patterns (microservices, monolith, layering).

### 6. Security & Compliance

Authentication, authorization, data handling, logging.

### 7. Coding Standards

Style guides, naming conventions, file structure.

## Examples

### Example 1: React with Corporate UI Library

**`.guidelines/reactjs-guidelines.md`**:

```markdown
## Mandatory Libraries

### UI Components

**MUST** use corporate component library:

```bash
npm install @acmecorp/ui-components@latest
```

**Usage**:

```javascript
import { Button, Modal, DataTable } from '@acmecorp/ui-components';
```

**Result**: When running `/specify implement`, agent generates code using `@acmecorp/ui-components` instead of public libraries like Material-UI.

### Example 2: Java with Corporate SDK

**`.guidelines/java-guidelines.md`**:

```markdown
## Mandatory Libraries

### API Client

**MUST** use corporate API SDK:

```xml
<dependency>
    <groupId>com.acmecorp</groupId>
    <artifactId>acme-api-client</artifactId>
    <version>2.4.1</version>
</dependency>
```

**Result**: When running `/specify plan`, agent includes corporate SDK in architecture instead of building custom HTTP clients.

### Example 3: Multi-Stack Project

**Project structure**:

```text
my-app/
├── frontend/     # React app
├── backend/      # Java Spring Boot
├── .guidelines/
│   ├── reactjs-guidelines.md
│   └── java-guidelines.md
```

**Result**: Prompts load both guidelines and apply contextually based on which part of the codebase is being worked on.

## Troubleshooting

### Guidelines Not Applied

**Symptom**: Agent ignores corporate libraries, uses public packages.

**Solutions**:

1. Check file location: Must be `/.guidelines/*.md` at project root
2. Check file names: Must match exactly (e.g., `reactjs-guidelines.md`)
3. Check formatting: Must follow template structure with proper headings
4. Check tech stack detection: Run `/specify analyze` to verify detected stack

### Multiple Tech Stacks Not Detected

**Symptom**: Only one guideline file loaded in multi-stack project.

**Solution**: Ensure project structure clearly indicates both stacks:

- Frontend: `package.json` in frontend directory
- Backend: `pom.xml` or `*.csproj` in backend directory

### Constitution Conflicts with Guidelines

**Symptom**: Unclear which rule to follow.

**Solution**: Constitution always wins. Update constitution or guidelines to align:

**Option 1** (Update constitution):

```markdown
Database: SHOULD use PostgreSQL unless corporate guidelines specify otherwise
```

**Option 2** (Update guidelines):

```markdown
NOTE: Project constitution mandates PostgreSQL. This guideline defers to constitution.
```

## Best Practices

### 1. Keep Guidelines Updated

Review and update quarterly or when corporate standards change.

### 2. Be Specific

**Bad** (vague):

```markdown
Use corporate libraries
```

**Good** (specific):

```markdown
## Authentication

MUST use @acmecorp/idm-client v3.x:

```bash
npm install @acmecorp/idm-client@^3.0.0
```

Example:

```javascript
import { Auth } from '@acmecorp/idm-client';
const user = await Auth.login(credentials);
```

### 3. Provide Examples

Every guideline should include code examples showing correct usage.

### 4. Document Rationale

Explain **why** a guideline exists:

**Example**:

```markdown
## Banned Libraries

**DO NOT USE** public authentication libraries (passport, auth0, etc.)

**Rationale**: Corporate security policy requires all authentication to use
@acmecorp/idm-client for centralized audit logging and compliance.
```

### 5. Version Dependencies

Always specify version ranges or exact versions:

```markdown
MUST use @acmecorp/ui-components v2.x (v1.x is deprecated, v3.x not yet approved)
```

## Support

For questions about:

- **Guidelines content**: Contact your tech lead or architecture team
- **Spec Kit usage**: See main README.md or open GitHub issue
- **Corporate standards**: Consult internal developer portal

## See Also

- `/memory/constitution.md` - Project-specific principles
- `AGENTS.md` - AI agent development practices
- Main `README.md` - Spec Kit documentation
