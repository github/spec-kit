# Quickstart: speckit Python Library

**Feature**: 001-python-litellm-library
**Generated**: 2025-12-19

Get started with spec-kit in under 5 minutes.

## Prerequisites

- Python 3.11 or higher
- At least one LLM provider configured (see [Provider Setup](#provider-setup))

## Installation

```bash
# Install from PyPI
pip install speckit-ai

# Or with MCP server support
pip install speckit-ai[mcp]

# For development
pip install speckit-ai[dev]
```

## Provider Setup

Choose one of the following LLM providers:

### OpenAI (Recommended for beginners)

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### Anthropic Claude

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### Local with Ollama (Free, offline)

```bash
# Install Ollama: https://ollama.ai
ollama pull llama3.1

# No API key needed - runs locally
export SPECKIT_MODEL="ollama/llama3.1"
```

### Google Gemini

```bash
export GEMINI_API_KEY="your-key-here"
export SPECKIT_MODEL="gemini/gemini-1.5-flash"
```

## Basic Usage

### As a Python Library

```python
from speckit import SpecKit

# Initialize with your project
kit = SpecKit(project_path="./my-project")

# Generate a specification from natural language
spec = kit.specify("""
    Add user authentication with:
    - Email/password login
    - Password reset via email
    - Session management with JWT
""")

# View the generated specification
print(spec.to_markdown())

# Save to file
kit.storage.save_specification(spec, feature_id="001-auth")
```

### Using the CLI

```bash
# Initialize a new project
speckit init

# Generate a specification
speckit specify "Add user authentication with email login" \
    --feature-id 001-auth

# Generate technical plan
speckit plan --feature 001-auth

# Generate implementation tasks
speckit tasks --feature 001-auth
```

## Complete Workflow Example

```python
from speckit import SpecKit
from speckit.config import LLMConfig

# 1. Initialize
kit = SpecKit(
    project_path="./my-app",
    llm_config=LLMConfig(model="gpt-4o-mini")  # Or your preferred model
)

# 2. Create project constitution (optional, but recommended)
constitution = kit.constitution(
    project_name="My App",
    principles=[
        "Test-first development",
        "Simple over complex",
        "User experience is paramount"
    ]
)

# 3. Specify a feature
spec = kit.specify("""
    Build a task management system where users can:
    - Create, edit, and delete tasks
    - Organize tasks into projects
    - Set due dates and priorities
    - Mark tasks as complete
""")

# 4. Clarify ambiguities (optional)
spec, questions = kit.clarify(spec)
if questions:
    print("Clarifications needed:")
    for q in questions:
        print(f"  - {q.question}")
    # Answer questions and update spec...

# 5. Generate technical plan
plan = kit.plan(spec)

# 6. Generate implementation tasks
tasks = kit.tasks(plan)

# 7. View ready-to-start tasks
print("Tasks ready to implement:")
for task in tasks.get_next_tasks():
    print(f"  [{task.phase.value}] {task.title}")
    for file in task.file_paths:
        print(f"    - {file}")
```

## Configuration

### Via Environment Variables

```bash
# LLM settings
export SPECKIT_MODEL="gpt-4o"           # Default model
export SPECKIT_TEMPERATURE="0.7"        # Creativity (0.0-2.0)
export SPECKIT_MAX_TOKENS="4096"        # Max response length
export SPECKIT_TIMEOUT="120"            # Timeout in seconds

# Fallback models (comma-separated)
export SPECKIT_FALLBACK_MODELS="gpt-4o-mini,claude-3-haiku-20240307"
```

### Via Configuration File

Create `.speckit/config.yaml` in your project:

```yaml
llm:
  model: gpt-4o-mini
  temperature: 0.7
  max_tokens: 4096
  fallback_models:
    - gpt-4o-mini
    - claude-3-haiku-20240307

storage:
  specs_dir: specs

language: en
verbose: false
```

### Via Code

```python
from speckit import SpecKit
from speckit.config import LLMConfig, SpecKitConfig

config = SpecKitConfig(
    llm=LLMConfig(
        model="ollama/llama3.1",
        temperature=0.5,
        max_tokens=8192
    ),
    project_path="./my-project",
    verbose=True
)

kit = SpecKit(config=config)
```

## Working with Artifacts

### Accessing Generated Content

```python
# Specification
print(spec.feature_name)
print(spec.problem_statement)
for story in spec.user_stories:
    print(f"[{story.priority.value}] {story.i_want}")

# Plan
print(plan.tech_stack.language)
for component in plan.components:
    print(f"{component.name}: {component.file_path}")

# Tasks
print(f"Total tasks: {len(tasks.tasks)}")
print(f"Progress: {tasks.get_progress()}")
```

### Exporting to Markdown

```python
# Individual artifacts
with open("spec.md", "w") as f:
    f.write(spec.to_markdown())

# Using storage
kit.storage.save_specification(spec, "001-feature")
kit.storage.save_plan(plan, "001-feature")
kit.storage.save_tasks(tasks, "001-feature")
```

### Loading Existing Artifacts

```python
spec = kit.storage.load_specification("001-feature")
plan = kit.storage.load_plan("001-feature")
tasks = kit.storage.load_tasks("001-feature")
```

## Using with AI Assistants (MCP)

### Claude Desktop

1. Install with MCP support:
   ```bash
   pip install speckit-ai[mcp]
   ```

2. Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "speckit": {
         "command": "python",
         "args": ["-m", "speckit.mcp"],
         "cwd": "/path/to/your/project"
       }
     }
   }
   ```

3. Restart Claude Desktop. You can now use spec-kit commands directly in chat.

### Cursor

Add to Cursor settings:
```json
{
  "mcp": {
    "speckit": {
      "command": "python -m speckit.mcp"
    }
  }
}
```

## Async Usage

For high-performance applications:

```python
import asyncio
from speckit import SpecKit

async def generate_specs():
    kit = SpecKit(project_path="./my-project")

    # Generate multiple specs concurrently
    specs = await asyncio.gather(
        kit.specify_async("Feature A"),
        kit.specify_async("Feature B"),
        kit.specify_async("Feature C"),
    )

    return specs

specs = asyncio.run(generate_specs())
```

## Error Handling

```python
from speckit.exceptions import (
    LLMError,
    LLMRateLimitError,
    ValidationError,
    ConfigurationError
)

try:
    spec = kit.specify("Feature description")
except LLMRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except LLMError as e:
    print(f"LLM error: {e.message}")
    print(f"Model used: {e.model}")
except ValidationError as e:
    print(f"Invalid output: {e.errors}")
except ConfigurationError as e:
    print(f"Config error: {e}")
```

## Next Steps

- Read the full [API Documentation](contracts/api.md)
- Explore [Examples](../../examples/)
- Learn about [Custom Templates](../../docs/templates.md)
- Join the community on [GitHub Discussions](https://github.com/suportly/spec-kit/discussions)

## Troubleshooting

### "No API key found"

Make sure your provider's API key is set:
```bash
# Check current environment
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Set if missing
export OPENAI_API_KEY="sk-..."
```

### "Model not found"

Verify the model name matches LiteLLM format:
```python
from speckit.llm import LiteLLMProvider
print(LiteLLMProvider.list_models())
```

### "Connection timeout"

For local models (Ollama), ensure the server is running:
```bash
ollama serve  # Start server
ollama list   # Check available models
```

### Slow responses

Try a faster model:
```bash
export SPECKIT_MODEL="gpt-4o-mini"  # Fast cloud model
# or
export SPECKIT_MODEL="ollama/llama3.1:8b"  # Smaller local model
```
