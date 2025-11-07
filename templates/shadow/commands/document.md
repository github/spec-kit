---
description: Generate documentation from code and specifications
---

# Generate Documentation

Generate documentation from code, specifications, and project artifacts.

## Usage

```bash
{SHADOW_PATH}/scripts/bash/setup-ai-doc{SCRIPT_EXT}
```

## What This Generates

### API Documentation
- Endpoint descriptions
- Request/response formats
- Authentication requirements
- Error codes

### Code Documentation
- Module purposes
- Function signatures
- Class hierarchies
- Important algorithms

### User Documentation
- Feature overviews
- Usage examples
- Configuration guides
- Troubleshooting

### Developer Documentation
- Setup instructions
- Build process
- Testing guidelines
- Contribution guidelines

## Documentation Types

### Quick Reference
Ultra-compact reference (<200 tokens) for AI agents

### AI Documentation
Detailed context for AI coding assistants

### README Updates
Keep README current with features

### API Specs
OpenAPI/Swagger specifications

## Output Locations

```
docs/api/          # API documentation
docs/guides/       # User guides
docs/development/  # Developer docs
.ai/quick-ref.md   # Quick reference
.ai/ai-doc.md      # AI documentation
```

## Best Practices

- Generate docs after implementation
- Keep docs in sync with code
- Include examples
- Update on breaking changes
- Review for clarity

## Documentation Standards

- Use clear, concise language
- Include code examples
- Add diagrams where helpful
- Link related topics
- Keep up to date
