# Domain Analysis Tool

**Intelligent domain analysis and template population for specification-driven development**

Transform raw data files into comprehensive domain models with automated entity extraction, business rule inference, and interactive setup wizards.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Cross-Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com/your-username/domain-analysis-tool)

---

## What is Domain Analysis?

Domain Analysis Tool automatically extracts business entities, rules, and integration patterns from your data files to populate specification templates with real, data-driven content. Instead of manually writing template placeholders, let the tool analyze your JSON/CSV files and generate comprehensive domain models.

## Key Features

### Automated Domain Discovery
- **Entity Extraction**: Automatically identify business entities from file schemas
- **Business Rule Inference**: Generate testable business rules from data patterns
- **Integration Mapping**: Identify external systems and data flow patterns
- **Schema Analysis**: Deep inspection of JSON/CSV structures and relationships


## Quick Start

### Prerequisites
- Python 3.11 or higher
- Git (for repository integration)
- bash shell (Linux/macOS) or PowerShell (Windows)

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/your-username/domain-analysis-tool.git
cd domain-analysis-tool
```

2. **Install Python dependencies**:
```bash
pip install pyyaml
```

```bash
chmod +x scripts/bash/analyze-domain.sh
```


**Automatic Analysis**:
```bash
```

## Core Functionality

```

**After** (Populated):
```markdown
### Key Entities
- **Invoice**: Financial document representing amount due (confidence: 95%)
- **Payment**: Financial transaction for invoice settlement (confidence: 92%)
- **Supplier**: External entity providing goods/services (confidence: 88%)


### Interactive Configuration
```bash
```

### Integration with Specification Frameworks
- Compatible with spec-kit methodology
- Template population for specification documents
- Git branch integration for feature development
- Structured output for further processing

## Architecture


### Shell Scripts
- `scripts/bash/analyze-domain.sh` - Unix/Linux/macOS entry point
- `scripts/bash/common.sh` - Shared utilities and functions
- `scripts/powershell/analyze-domain.ps1` - Windows PowerShell entry point
- `scripts/powershell/common.ps1` - PowerShell utilities


**Tested with**:
- 39 JSON files, 3 CSV files (SageRecon dataset)
- 1000+ records per file
- Analysis completion: <30 seconds
- Memory usage: <100MB for typical datasets


We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: Report bugs and request features through GitHub Issues
- **Documentation**: See [USAGE.md](USAGE.md) for comprehensive examples
- **Community**: Discussions and questions welcome

## Acknowledgments

