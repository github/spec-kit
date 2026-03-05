# Spec-Kit MCP Server

Comprehensive MCP (Model Context Protocol) server that provides spec-driven development tools, covering all the functionality of the Specify CLI with enhanced AI integration.

## Features

### 🔧 **Project Management**
- `specify_init` - Initialize projects with templates and configuration
- `specify_check` - Check available tools and development environment

### 📋 **Specification Creation**
- `speckit_constitution` - Establish project constitution with principles and standards
- `speckit_specify` - Create baseline specifications from natural language
- `speckit_clarify` - Generate structured clarification questions
- `speckit_analyze_domain` - Perform domain analysis and context gathering

### 📅 **Planning & Task Management**
- `speckit_plan` - Create detailed implementation plans from specifications
- `speckit_tasks` - Generate actionable tasks with role assignments
- `speckit_checklist` - Create quality checklists for validation

### 🔍 **Analysis & Quality**
- `speckit_analyze` - Cross-artifact consistency and alignment analysis
- Quality assurance and validation tools

### 🚀 **Implementation**
- `speckit_implement` - Execute implementation with guided or automated modes

### 💾 **Knowledge Management**
- `speckit_memory_store` - Store project knowledge and decisions
- `speckit_memory_retrieve` - Retrieve stored information

## Installation

### Option 1: Install from source
```bash
# Clone or download the MCP server files
cd spec-kit-mcp-server
pip install -e .
```

### Option 2: Install using uv (recommended)
```bash
uv tool install --from spec-kit-mcp-server
```

### Option 3: Development installation
```bash
git clone <repository-url>
cd spec-kit-mcp-server
pip install -e ".[dev]"
```

## Configuration

### Add to Claude Desktop

Add the following to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "spec-kit-mcp-server": {
      "command": "python3",
      "args": ["/path/to/spec-kit-mcp-server.py"],
      "env": {
        "SPEC_KIT_HOME": "/path/to/your/project"
      }
    }
  }
}
```

### Environment Variables

- `SPEC_KIT_HOME`: Override the default working directory
- `SPEC_KIT_LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)

## Usage

### Basic Workflow

1. **Initialize Project**
   ```
   Tool: specify_init
   Parameters:
     - project_name: "my-project"
     - project_type: "web" (web, api, cli, mobile, library)
     - ai_assistant: "claude"
   ```

2. **Establish Constitution**
   ```
   Tool: speckit_constitution
   Parameters:
     - project_values: ["Quality-first", "User-centric"]
     - quality_standards: ["100% test coverage"]
     - development_principles: ["TDD", "Continuous improvement"]
   ```

3. **Create Specification**
   ```
   Tool: speckit_specify
   Parameters:
     - feature_description: "User authentication system"
     - requirements: ["Login with email/password", "Password reset"]
     - acceptance_criteria: ["Users can log in successfully"]
   ```

4. **Generate Implementation Plan**
   ```
   Tool: speckit_plan
   Parameters:
     - specification_id: "spec_1"
     - implementation_approach: "incremental"
     - timeline_estimate: "2 weeks"
   ```

5. **Create Tasks**
   ```
   Tool: speckit_tasks
   Parameters:
     - plan_id: "plan_1"
     - task_granularity: "story"
     - assign_roles: true
   ```

6. **Generate Checklist**
   ```
   Tool: speckit_checklist
   Parameters:
     - checklist_type: "implementation"
     - specification_id: "spec_1"
     - quality_level: "comprehensive"
   ```

### Advanced Features

#### Domain Analysis
```
Tool: speckit_analyze_domain
Parameters:
  - domain_description: "E-commerce platform"
  - project_context: "User authentication and order management"
  - analysis_depth: "comprehensive"
```

#### Cross-Artifact Analysis
```
Tool: speckit_analyze
Parameters:
  - artifacts: ["spec_1", "plan_1", "tasks_1"]
  - analysis_type: "consistency"
  - report_format: "detailed"
```

#### Memory Management
```
# Store decision
Tool: speckit_memory_store
Parameters:
  - key: "architecture_decision_001"
  - content: "Decision to use microservices architecture"
  - category: "decision"

# Retrieve decision
Tool: speckit_memory_retrieve
Parameters:
  - key: "architecture_decision_001"
  - category: "decision"
```

## Directory Structure

The MCP server creates and maintains the following directory structure in your project:

```
project-root/
├── .specify/
│   ├── templates/          # Template files
│   ├── memory/            # Stored knowledge and decisions
│   └── scripts/           # Automation scripts
├── .claude/               # Claude-specific files
└── constitution.yaml      # Project constitution
```

## Integration with Existing Tools

### Specify CLI Compatibility
The MCP server provides tools that cover 100% of Specify CLI functionality:
- ✅ `specify init` → `specify_init`
- ✅ `specify check` → `specify_check`
- ✅ `/speckit.constitution` → `speckit_constitution`
- ✅ `/speckit.specify` → `speckit_specify`
- ✅ `/speckit.clarify` → `speckit_clarify`
- ✅ `/speckit.analyze-domain` → `speckit_analyze_domain`
- ✅ `/speckit.plan` → `speckit_plan`
- ✅ `/speckit.tasks` → `speckit_tasks`
- ✅ `/speckit.checklist` → `speckit_checklist`
- ✅ `/speckit.analyze` → `speckit_analyze`
- ✅ `/speckit.implement` → `speckit_implement`

### Enhanced Features
Beyond CLI compatibility, the MCP server provides:
- **Persistent memory** for project knowledge
- **Cross-session state** management
- **AI-enhanced analysis** and recommendations
- **Integration with other MCP tools**

## Development

### Running Tests
```bash
pytest
pytest --cov=spec_kit_mcp_server
```

### Code Formatting
```bash
black spec_kit_mcp_server.py
flake8 spec_kit_mcp_server.py
mypy spec_kit_mcp_server.py
```

### Adding New Tools

1. Add tool definition to `handle_list_tools()`
2. Implement tool handler function
3. Update documentation
4. Add tests

Example new tool:
```python
@server.call_tool()
async def handle_my_new_tool(arguments: Dict[str, Any]) -> CallToolResult:
    # Implementation here
    return CallToolResult(content=[TextContent(type="text", text="Success")])
```

## Security

The MCP server follows security best practices:
- No external network access by default
- Sandboxed file operations
- Input validation and sanitization
- Secure defaults for all configurations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- 📖 Documentation: https://docs.spec-kit.dev
- 🐛 Issues: https://github.com/spec-kit/spec-kit-mcp-server/issues
- 💬 Discussions: https://github.com/spec-kit/spec-kit-mcp-server/discussions

## Changelog

### v1.0.0
- Initial release with full Specify CLI compatibility
- Project management tools
- Specification creation and management
- Planning and task generation
- Quality checklists and analysis
- Implementation execution modes
- Persistent memory system
- Security and validation features