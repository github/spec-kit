---
description: Generate specialized agent files tailored to the current repository's tech stack and practices
---

# Generate SpecKit Agents

You will create specialized agent files in the `.claude/agents/speckit/` directory, each tailored to the current repository's technology stack, architecture patterns, and best practices.

## Agent Types to Create

1. **backend-coder** - Backend implementation specialist
2. **frontend-coder** - Frontend implementation specialist
3. **researcher** - Codebase exploration and pattern analysis specialist
4. **planner** - Task decomposition and workflow specialist

## Discovery Process

**IMPORTANT**: Do NOT assume any file or directory structure. Discover the project organization first.

### Step 1: Search for Documentation

Try multiple strategies to find project documentation:

```bash
# Look for documentation files (may not exist)
glob "**/*README.md"
glob "**/*CLAUDE.md"
glob "**/docs/**/*.md"
glob "**/.claude/**/*.md"
glob "**/CONTRIBUTING.md"
glob "**/ARCHITECTURE.md"

# Look for coding guidelines
glob "**/STYLE_GUIDE.md"
glob "**/.editorconfig"
glob "**/.prettierrc*"
glob "**/.eslintrc*"
```

**If documentation found**: Extract tech stack, patterns, and best practices from it.

**If no documentation found**: Proceed to code analysis (Step 2).

### Step 2: Discover Project Structure

Analyze the actual codebase structure:

```bash
# Find project root indicators
glob "**/package.json"      # Node.js
glob "**/pom.xml"           # Java/Maven
glob "**/build.gradle*"     # Java/Gradle
glob "**/Cargo.toml"        # Rust
glob "**/go.mod"            # Go
glob "**/requirements.txt"  # Python
glob "**/Gemfile"           # Ruby
glob "**/build.sbt"         # Scala
glob "**/composer.json"     # PHP

# Identify source directories
glob "**/src/**"
glob "**/lib/**"
glob "**/app/**"
glob "**/backend/**"
glob "**/frontend/**"
glob "**/server/**"
glob "**/client/**"

# Find test directories
glob "**/*test*/**"
glob "**/*spec*/**"
```

### Step 3: Identify Technologies

Extract from build/config files:

```bash
# Read package manager files (if found)
# Look for dependencies, frameworks, language versions
read package.json          # if Node.js
read build.sbt             # if Scala
read requirements.txt      # if Python
read go.mod               # if Go
read Cargo.toml           # if Rust

# Check configuration files
read tsconfig.json        # TypeScript config
read .babelrc             # Babel config
read vite.config.*        # Vite config
read webpack.config.*     # Webpack config
```

### Step 4: Analyze Code Patterns

If documentation is sparse, analyze code directly:

```bash
# Backend patterns
grep -r "class\|interface\|type\|struct" --include="*.ts" --include="*.js" --include="*.go" --include="*.rs" --include="*.scala" | head -50

# Frontend patterns
grep -r "export.*function\|export.*const.*=\|export default" --include="*.tsx" --include="*.jsx" | head -50

# Database patterns
grep -r "SELECT\|INSERT\|CREATE TABLE" --include="*.sql" | head -20
grep -r "Repository\|Model\|Schema" | head -30

# API patterns
grep -r "GET\|POST\|PUT\|DELETE.*api\|router\|route" | head -30
```

### Step 5: Check for Existing Agents (Optional)

```bash
# See if there are already agent examples to follow
glob ".claude/agents/**/*.md"
```

## Agent File Structure

Each agent MUST follow this template structure:

```markdown
---
name: [agent-name]
type: [developer|analyst|coordinator]
color: "[hex-color]"
description: [One-line description]
capabilities:
  - [capability_1]
  - [capability_2]
  - [capability_3]
priority: high
hooks:
  pre: |
    echo "[emoji] [Agent name] starting: $TASK"
  post: |
    echo "✨ [Action] complete"
---

# [Agent Name] Agent

You are a [role] specialized in [tech stack found in project].

## Core Responsibilities

1. **[Responsibility]**: [Description]
2. **[Responsibility]**: [Description]
...

## Tech Stack

[List technologies discovered from project]

## Implementation Guidelines

### 1. [Topic]

[Guidelines extracted from docs or inferred from code patterns]

```[language]
// ✅ Good practice (from project)
[example from codebase or docs]

// ❌ Anti-pattern
[example of what to avoid]
```

## Best Practices

- ✅ [Practice from project docs/code]
- ✅ [Another practice]
- ❌ [Anti-pattern to avoid]

## Collaboration

- **With [Agent]**: [How they work together]
- **Use TodoWrite**: Track task progress

Remember: [Key principle for this agent]
```

## Agent Templates

### Template 1: Backend Coder

**Discover**:
- Backend language (Scala, Java, Go, Python, Node.js, Rust, etc.)
- Web framework (Express, FastAPI, Spring, Actix, etc.)
- Database approach (ORM, query builder, raw SQL)
- API style (REST, GraphQL, gRPC)
- Testing framework
- Build/packaging tool

**Core Sections**:
1. Language-specific coding standards
2. Framework usage patterns
3. Database access patterns
4. API implementation
5. Error handling
6. Testing approach
7. Build/deployment

**Capabilities Examples**:
- `api_implementation`
- `database_access`
- `error_handling`
- Framework-specific skills

### Template 2: Frontend Coder

**Discover**:
- Frontend framework (React, Vue, Angular, Svelte, etc.)
- Language/Type system (TypeScript, JavaScript, Flow)
- State management (Redux, Zustand, Pinia, Context, etc.)
- Data fetching (TanStack Query, SWR, Apollo, etc.)
- Styling approach (CSS Modules, Tailwind, Styled Components, etc.)
- Build tool (Vite, Webpack, Parcel, etc.)

**Core Sections**:
1. Component patterns
2. Type safety practices
3. State management
4. Data fetching
5. Styling conventions
6. Performance optimization
7. Testing

**Capabilities Examples**:
- `component_development`
- `state_management`
- `styling`
- Framework-specific skills

### Template 3: Researcher

**TECHNOLOGY AGNOSTIC** - Same for all projects.

**Core Sections**:
1. Research methodology (broad-to-narrow search)
2. Search strategies by domain
3. Pattern analysis techniques
4. Cross-reference analysis
5. Tools: Read, Glob, Grep, Bash (git)
6. Output format templates
7. Common research tasks

**Capabilities**: `code_analysis`, `pattern_recognition`, `dependency_tracking`, `knowledge_synthesis`

**CRITICAL**:
- NO MCP tools
- Works purely with Read, Glob, Grep, Bash
- Not tied to any specific technology

### Template 4: Planner

**MOSTLY AGNOSTIC** - Adapts to project workflow.

**Discover**:
- Workflow commands (glob ".claude/commands/*.md" or similar)
- Task tracking approach (if documented)
- Project principles/constitution (if exists)
- Architecture patterns (affects task breakdown)

**Core Sections**:
1. Workflow process (SpecKit or project-specific)
2. Task decomposition principles
3. Dependency analysis
4. Priority assignment
5. Phase organization
6. Project principles (if found)
7. Planning templates

**Capabilities**: `task_decomposition`, `dependency_analysis`, `workflow_orchestration`, `risk_assessment`

**CRITICAL**:
- NO MCP tools
- Use TodoWrite for task tracking

## Implementation Instructions

### Phase 1: Discovery

```bash
# Try documentation first
glob "**/*README.md"
glob "**/*CLAUDE.md"
glob "**/docs/**"

# If found, read and extract patterns
# If not found, analyze code structure

# Find build files
glob "**/package.json"
glob "**/build.*"
glob "**/pom.xml"
glob "**/Cargo.toml"
# ... (check all common ones)

# Identify source structure
glob "**/src/**"
glob "**/backend/**"
glob "**/frontend/**"

# Read build files to extract dependencies
```

### Phase 2: Extract Information

From documentation (if exists):
- Tech stack and versions
- Architecture patterns
- Best practices (Do's and Don'ts)
- Code examples
- Performance targets
- Design principles

From code analysis (if no docs):
- File organization patterns
- Naming conventions
- Common imports/dependencies
- Architectural layers
- Error handling patterns
- Testing approaches

### Phase 3: Generate Agents

For each agent:

1. **Set metadata** (frontmatter):
   - Unique name
   - Appropriate type
   - Distinct color
   - Clear description
   - Relevant capabilities

2. **Write responsibilities** based on role and project needs

3. **Document tech stack** (backend/frontend only):
   - Use actual technologies found
   - Include versions if known

4. **Create guidelines**:
   - Extract from documentation if available
   - Infer from code patterns if not
   - Include real code examples

5. **Define best practices**:
   - Use ✅ for recommended approaches
   - Use ❌ for anti-patterns
   - Be specific to project

6. **Specify collaboration**:
   - How agents work together
   - Always include TodoWrite usage

### Phase 4: Validate

Check each agent:
- ✅ Complete frontmatter
- ✅ Reflects actual project technologies
- ✅ NO MCP tools referenced
- ✅ Real examples (not generic)
- ✅ TodoWrite mentioned
- ✅ Collaboration specified

## Suggested Colors

- Backend: `#E74C3C` (red/orange)
- Frontend: `#3498DB` (blue)
- Researcher: `#9B59B6` (purple)
- Planner: `#4ECDC4` (teal)

## Suggested Emojis

- Backend: 🔧 (tool/building)
- Frontend: ⚛️ (React) or 🎨 (design)
- Researcher: 🔍 (search)
- Planner: 🎯 (goal/target)

## Success Criteria

✅ All 4 agents created in `.claude/agents/speckit/`
✅ Each has complete frontmatter
✅ NO MCP tools in any agent
✅ Technologies match actual project
✅ Examples from actual codebase/docs
✅ All specify TodoWrite usage
✅ All specify collaboration patterns

## Important Principles

- **Discover, don't assume**: Use glob/grep to find what exists
- **Adapt, don't template**: Create agents based on what you find
- **Extract, don't invent**: Pull patterns from actual code/docs
- **Be specific**: Reference actual files, patterns, technologies
- **Stay agnostic**: Don't hardcode paths or assume structure

## Example Discovery Flow

```bash
# 1. Look for docs
glob "**/*CLAUDE.md"
# → Found: CLAUDE.md, backend/CLAUDE.md, frontend/CLAUDE.md
# → Action: Read these for patterns

# 2. Check build files
glob "**/package.json"
# → Found: frontend/package.json
# → Action: Read to extract frontend stack

glob "**/build.sbt"
# → Found: backend/build.sbt
# → Action: Read to extract backend stack

# 3. Analyze structure
glob "backend/**/*.scala"
# → Found: Many .scala files in backend/src/main/scala/
# → Action: Note Scala backend

glob "frontend/**/*.tsx"
# → Found: React components in frontend/src/
# → Action: Note React + TypeScript frontend

# 4. Search for patterns
grep -r "case class" backend/ --include="*.scala"
# → Action: Extract common patterns for backend agent

grep -r "export function" frontend/ --include="*.tsx"
# → Action: Extract component patterns for frontend agent

# 5. Generate agents using discovered information
```

Remember: These agents embody the **actual** repository's practices. Every detail should come from discovery, not assumption.
