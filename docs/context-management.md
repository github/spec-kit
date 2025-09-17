# Context Management with APM

## NPM for Agent Context

Just like npm revolutionized JavaScript by enabling package reuse, APM creates an ecosystem for sharing agent context.

## Package Composition & Reuse

```yaml
# Your project inherits team knowledge via apm.yml file in the root
dependencies:
  apm:
    - company/design-system     # UI patterns, brand guidelines
    - company/security-standards # Auth patterns, data handling
    - community/best-practices  # Industry standards
```

**Result**: Your project gets all the instructions of above packages applied via dynamically generated Agents.md files using `specify apm compile`. These files are optimally generated to minimize contextual load for Agents compatible with the Agents.md standard.

**Enterprise Scenario**: Design team creates accessibility guidelines once → entire organization uses them → agents work consistently across all projects.

## Mathematical Context Optimization

**The Technical Foundation**: APM uses mathematical optimization to solve the context efficiency problem.

```
Context_Efficiency = Relevant_Instructions / Total_Instructions_Loaded
```

**Why This Matters**: When agents work in `/styles/` directory, they shouldn't load Python compliance rules. APM's Context Optimization Engine ensures agents get minimal, highly relevant context.

**The Algorithm**: Constraint satisfaction optimization that finds placement minimizing context pollution while maximizing relevance. Each instruction gets mathematically optimal placement across the project hierarchy.

## Quick Start

```bash
specify init my-project --use-apm --ai copilot
specify apm install company/design-system  
specify apm compile  # Mathematical optimization generates distributed AGENTS.md files
```

## Universal Agent Compatibility

APM generates distributed `AGENTS.md` files compatible with the [agents.md standard](https://agents.md), working with any coding agent (GitHub Copilot, Cursor, Claude, Codex, Aider, etc.).

## Authentication Setup (Optional)

```bash
export GITHUB_APM_PAT=your_fine_grained_token_here
```

Only needed for private packages. Public community packages work without authentication.

## The Complete Value

1. **Package Ecosystem** - Share and compose agent intelligence like code dependencies
2. **Mathematical Optimization** - Context Optimization Engine ensures relevance without pollution  
3. **Universal Standards** - Works with any agent via industry-standard agents.md format
4. **Enterprise Ready** - Team knowledge scales across entire organizations