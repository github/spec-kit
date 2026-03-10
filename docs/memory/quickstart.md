# SpecKit Memory Quickstart

Get started with SpecKit Memory in 5 minutes.

## Installation (2 minutes)

### Windows
```bash
python scripts/memory/install_all.py
```

### Linux/Mac
```bash
bash scripts/memory/install_all.sh
```

This creates:
- `~/.claude/memory/` - Memory storage
- `~/.claude/spec-kit/` - SpecKit link
- Configuration files

## Initialize Project (1 minute)

```bash
cd your-project
python ~/.claude/spec-kit/scripts/memory/init_memory.py
```

This creates:
- `.spec-kit/project.json` - Project config
- Memory files (lessons.md, patterns.md, etc.)

## Basic Usage (2 minutes)

### Python API

```python
from specify_cli.memory.orchestrator import MemoryOrchestrator

# Initialize
memory = MemoryOrchestrator()

# Save what you learned
memory.add_lesson(
    title="JWT token expires too quickly",
    problem="Access tokens expired after 1 hour, disrupting users",
    solution="Increased to 24 hours and added refresh token rotation"
)

# Find relevant past solutions
results = memory.search("authentication timeout")
for result in results:
    print(f"{result['title']}: {result['summary']}")
```

### CLI Commands

```bash
# Search memory
cd ~/.claude/spec-kit
python -m specify_cli.memory.orchestrator search "authentication"

# Add entry
python -m specify_cli.memory.orchestrator add lesson \
  --title "JWT fix" \
  --content "Use refresh tokens"

# List patterns
python -m specify_cli.memory.orchestrator list patterns
```

## Memory Files

### lessons.md
Learnings from mistakes and fixes.

```markdown
## JWT Token Expiration

**Problem**: Tokens expired after 1 hour
**Solution**: Use refresh tokens, increase access token to 24h
```

### patterns.md
Reusable solutions.

```markdown
## Refresh Token Pattern

**When**: Authentication requires long sessions
**How**: Short access token + long-lived refresh token
**Code**: [implementation]
```

### architecture.md
Technical decisions.

```markdown
## JWT vs Session-Based Auth

**Decision**: JWT with refresh tokens
**Why**: Stateless, scalable, mobile-friendly
**Trade-off**: More complex token revocation
```

## Integration with SpecKit

Memory automatically integrates with SpecKit commands:

```bash
# /speckit.specify - Reads relevant memory before creating spec
# /speckit.plan - Gets architecture context for planning
# /speckit.tasks - Suggests patterns from memory
```

## Next Steps

1. [Full Documentation](README.md)
2. [Performance Tuning](performance_tuning.md)
3. [Configuration Guide](../INSTALL_MEMORY.md)
4. [API Reference](README.md#api-reference)

## Common Tasks

### Search for past solutions
```python
results = memory.search("database connection error")
```

### Save a pattern
```python
memory.add_pattern(
    title="Database Retry Pattern",
    description="Exponential backoff for transient DB errors",
    code="""
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
def query_db():
    ...
"""
)
```

### Record architecture decision
```python
memory.add_architecture(
    title="PostgreSQL vs MongoDB",
    context="Need structured data with relations",
    decision="PostgreSQL",
    rationale="ACID compliance, relational model, mature ecosystem"
)
```

### Cross-project search
```python
# Search across all your projects
results = memory.search("authentication", scope="global")
```

## Troubleshooting

**Installation failed?**
```bash
python scripts/memory/verify_install.py
```

**Can't import?**
```bash
export PYTHONPATH="$PYTHONPATH:$(pwd)/src"
```

**Memory not saving?**
Check `~/.claude/spec-kit/config/memory.json` - ensure `enabled: true`

## Tips

1. **Be specific**: "JWT token expires in 1 hour" > "Auth issue"
2. **Include context**: What were you trying to do?
3. **Link related entries**: Reference patterns in lessons
4. **Review regularly**: Clean up outdated entries monthly
5. **Use categories**: Helps with filtering and search

## Example Workflow

```python
# Before starting task
relevant = memory.search("user authentication")

# While working
try:
    # ... your code ...
except Exception as e:
    # Save what you learned
    memory.add_lesson(
        title=str(e),
        problem="Error while implementing auth",
        solution="How I fixed it..."
    )

# After discovering pattern
memory.add_pattern(
    title="Auth Error Handling Pattern",
    description="How to handle auth errors gracefully",
    code="..."
)

# Before making architectural decision
past_decisions = memory.get_architecture()
# Review past decisions...
```

Happy coding!
