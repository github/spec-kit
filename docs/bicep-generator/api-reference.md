# Bicep Generator - API Reference

## Overview

This document provides detailed API reference for the Bicep Generator module. The Bicep Generator is designed to analyze projects and automatically generate Azure Bicep infrastructure templates.

## Module Structure

```
src/specify_cli/bicep/
├── __init__.py              # Main module initialization
├── analyzer.py              # Project analysis engine
├── generator.py             # Template generation engine
├── validator.py             # Template validation
├── deployer.py              # Azure deployment
├── mcp_client.py            # Azure MCP Server integration
├── bicep_utils.py           # Utility functions
├── cost_estimator.py        # Cost estimation
├── security_analyzer.py     # Security analysis
├── template_editor.py       # Template editing
├── explanation_engine.py    # Template explanations
├── error_handler.py         # Error handling
├── performance.py           # Performance optimization
├── security.py              # Security hardening
├── type_checker.py          # Code quality analysis
└── models/
    ├── analysis_models.py   # Analysis data models
    ├── template_models.py   # Template data models
    └── deployment_models.py # Deployment data models
```

## Core Classes

### ProjectAnalyzer

Analyzes project structure and detects Azure service dependencies.

**Location:** `src/specify_cli/bicep/analyzer.py`

#### Class Definition

```python
class ProjectAnalyzer:
    """
    Analyze project for Azure resource requirements.
    
    Attributes:
        project_path: Path to project directory
        config: Analysis configuration
        console: Rich console for output
        cache: Optional cache for performance
    """
    
    def __init__(
        self,
        project_path: Path,
        config: Optional[AnalysisConfig] = None,
        console: Optional[Console] = None,
        enable_cache: bool = True
    ):
        """Initialize project analyzer."""
```

#### Methods

##### `analyze() -> ProjectAnalysis`

Perform comprehensive project analysis.

**Returns:** `ProjectAnalysis` object containing detected resources

**Raises:**
- `AnalysisError`: If analysis fails
- `PermissionError`: If files cannot be accessed

**Example:**

```python
from specify_cli.bicep import ProjectAnalyzer
from pathlib import Path

analyzer = ProjectAnalyzer(
    project_path=Path("./my-project"),
    enable_cache=True
)

analysis = analyzer.analyze()
print(f"Detected {len(analysis.resources)} resources")
```

##### `detect_dependencies() -> List[ServiceDependency]`

Detect Azure service dependencies from configuration files.

**Returns:** List of `ServiceDependency` objects

**Example:**

```python
dependencies = analyzer.detect_dependencies()
for dep in dependencies:
    print(f"{dep.service_type}: {dep.confidence}")
```

##### `analyze_configuration() -> Dict[str, Any]`

Extract configuration settings from project files.

**Returns:** Dictionary of configuration values

##### `detect_secrets() -> List[SecretReference]`

Scan for hardcoded secrets and credentials.

**Returns:** List of `SecretReference` objects

**Security Note:** Detected secrets should be migrated to Azure Key Vault.

---

### BicepGenerator

Generates Bicep templates from project analysis.

**Location:** `src/specify_cli/bicep/generator.py`

#### Class Definition

```python
class BicepGenerator:
    """
    Generate Azure Bicep templates from analysis.
    
    Attributes:
        analysis: Project analysis results
        config: Generator configuration
        mcp_client: Azure MCP Server client
        console: Rich console for output
    """
    
    def __init__(
        self,
        analysis: ProjectAnalysis,
        config: Optional[GeneratorConfig] = None,
        console: Optional[Console] = None
    ):
        """Initialize Bicep generator."""
```

#### Methods

##### `generate() -> GenerationResult`

Generate complete Bicep template set.

**Returns:** `GenerationResult` with paths to generated files

**Raises:**
- `GenerationError`: If generation fails
- `SchemaError`: If schema retrieval fails

**Example:**

```python
from specify_cli.bicep import BicepGenerator

generator = BicepGenerator(
    analysis=analysis,
    config=GeneratorConfig(
        output_dir=Path("./bicep-templates"),
        region="eastus",
        environment="production"
    )
)

result = generator.generate()
print(f"Generated {len(result.files)} templates")
```

##### `generate_resource(resource_spec: ResourceSpec) -> str`

Generate Bicep code for a single resource.

**Parameters:**
- `resource_spec`: Resource specification

**Returns:** Bicep template string

**Example:**

```python
bicep_code = generator.generate_resource(
    ResourceSpec(
        resource_type="Microsoft.Storage/storageAccounts",
        name="mystorageaccount",
        api_version="2023-01-01"
    )
)
```

##### `generate_parameters() -> Dict[str, Parameter]`

Generate parameter definitions for templates.

**Returns:** Dictionary of parameter objects

##### `validate_generation() -> ValidationResult`

Validate generated templates.

**Returns:** `ValidationResult` with any errors/warnings

---

### MCPClient

Interface to Azure MCP Server for schema and resource information.

**Location:** `src/specify_cli/bicep/mcp_client.py`

#### Class Definition

```python
class MCPClient:
    """
    Client for Azure MCP Server integration.
    
    Attributes:
        session: MCP client session
        transport: StdioServerParameters for MCP
        console: Rich console for output
    """
    
    def __init__(
        self,
        console: Optional[Console] = None,
        enable_cache: bool = True
    ):
        """Initialize MCP client."""
```

#### Methods

##### `get_bicep_schema(resource_type: str, api_version: str) -> Dict[str, Any]`

Retrieve Bicep schema for a resource type.

**Parameters:**
- `resource_type`: Azure resource type (e.g., "Microsoft.Storage/storageAccounts")
- `api_version`: API version (e.g., "2023-01-01")

**Returns:** JSON schema dictionary

**Caching:** Results are cached with 1-hour TTL

**Example:**

```python
from specify_cli.bicep import MCPClient

async with MCPClient() as client:
    schema = await client.get_bicep_schema(
        "Microsoft.Storage/storageAccounts",
        "2023-01-01"
    )
    print(f"Schema properties: {schema['properties'].keys()}")
```

##### `get_best_practices(resource_type: str) -> List[str]`

Get best practices for a resource type.

**Parameters:**
- `resource_type`: Azure resource type

**Returns:** List of best practice recommendations

##### `get_resource_providers() -> List[str]`

List available Azure resource providers.

**Returns:** List of provider namespaces

---

### TemplateValidator

Validates generated Bicep templates.

**Location:** `src/specify_cli/bicep/validator.py`

#### Class Definition

```python
class TemplateValidator:
    """
    Validate Bicep templates.
    
    Attributes:
        template_dir: Directory containing templates
        subscription_id: Azure subscription ID
        console: Rich console for output
    """
    
    def __init__(
        self,
        template_dir: Path,
        subscription_id: Optional[str] = None,
        console: Optional[Console] = None
    ):
        """Initialize template validator."""
```

#### Methods

##### `validate() -> ValidationResult`

Perform comprehensive template validation.

**Returns:** `ValidationResult` with errors and warnings

**Validation Checks:**
1. Bicep syntax validation
2. Schema validation
3. Best practices compliance
4. Security checks
5. Azure deployment validation (if subscription_id provided)

**Example:**

```python
from specify_cli.bicep import TemplateValidator

validator = TemplateValidator(
    template_dir=Path("./bicep-templates"),
    subscription_id="xxx-xxx-xxx"
)

result = validator.validate()
if result.is_valid:
    print("✓ All templates valid")
else:
    for error in result.errors:
        print(f"✗ {error.message}")
```

##### `validate_syntax() -> List[ValidationError]`

Validate Bicep syntax using Bicep CLI.

**Returns:** List of syntax errors

##### `validate_schema() -> List[ValidationError]`

Validate against Azure resource schemas.

**Returns:** List of schema validation errors

##### `validate_security() -> List[SecurityIssue]`

Check for security issues.

**Returns:** List of security issues

---

### BicepDeployer

Deploys Bicep templates to Azure.

**Location:** `src/specify_cli/bicep/deployer.py`

#### Class Definition

```python
class BicepDeployer:
    """
    Deploy Bicep templates to Azure.
    
    Attributes:
        template_dir: Directory containing templates
        resource_group: Target resource group
        subscription_id: Azure subscription ID
        console: Rich console for output
    """
    
    def __init__(
        self,
        template_dir: Path,
        resource_group: str,
        subscription_id: str,
        console: Optional[Console] = None
    ):
        """Initialize Bicep deployer."""
```

#### Methods

##### `deploy(dry_run: bool = False) -> DeploymentResult`

Deploy templates to Azure.

**Parameters:**
- `dry_run`: If True, validate without deploying

**Returns:** `DeploymentResult` with deployment status

**Raises:**
- `DeploymentError`: If deployment fails
- `AuthenticationError`: If Azure authentication fails

**Example:**

```python
from specify_cli.bicep import BicepDeployer

deployer = BicepDeployer(
    template_dir=Path("./bicep-templates"),
    resource_group="my-rg",
    subscription_id="xxx-xxx-xxx"
)

# Dry run first
result = deployer.deploy(dry_run=True)
if result.would_succeed:
    # Actual deployment
    result = deployer.deploy()
    print(f"Deployed {len(result.resources)} resources")
```

##### `validate_deployment() -> ValidationResult`

Validate deployment without executing.

**Returns:** `ValidationResult`

##### `get_deployment_status() -> DeploymentStatus`

Check status of ongoing deployment.

**Returns:** `DeploymentStatus` object

---

## Data Models

### ProjectAnalysis

Project analysis results.

**Location:** `src/specify_cli/bicep/models/analysis_models.py`

```python
@dataclass
class ProjectAnalysis:
    """Results of project analysis."""
    
    project_name: str
    project_path: Path
    language: str
    framework: Optional[str]
    resources: List[ResourceSpec]
    dependencies: List[ServiceDependency]
    configuration: Dict[str, Any]
    secrets: List[SecretReference]
    analysis_date: datetime
    version: str
```

**Fields:**

- `project_name`: Name of the project
- `project_path`: Path to project directory
- `language`: Primary programming language
- `framework`: Framework (if detected)
- `resources`: List of required Azure resources
- `dependencies`: Service dependencies
- `configuration`: Extracted configuration
- `secrets`: Detected secret references
- `analysis_date`: When analysis was performed
- `version`: Analysis schema version

---

### ResourceSpec

Specification for an Azure resource.

```python
@dataclass
class ResourceSpec:
    """Specification for an Azure resource."""
    
    resource_type: str
    name: str
    api_version: str
    properties: Dict[str, Any]
    sku: Optional[SkuSpec]
    location: Optional[str]
    tags: Dict[str, str]
    dependencies: List[str]
```

**Fields:**

- `resource_type`: Azure resource type (e.g., "Microsoft.Storage/storageAccounts")
- `name`: Resource name
- `api_version`: API version to use
- `properties`: Resource properties
- `sku`: SKU specification
- `location`: Azure region
- `tags`: Resource tags
- `dependencies`: Names of dependent resources

---

### GenerationResult

Template generation results.

**Location:** `src/specify_cli/bicep/models/template_models.py`

```python
@dataclass
class GenerationResult:
    """Results of template generation."""
    
    success: bool
    files: List[Path]
    errors: List[GenerationError]
    warnings: List[str]
    generation_time: float
    resource_count: int
```

**Fields:**

- `success`: Whether generation succeeded
- `files`: Paths to generated template files
- `errors`: Any errors encountered
- `warnings`: Warning messages
- `generation_time`: Time taken (seconds)
- `resource_count`: Number of resources generated

---

### ValidationResult

Template validation results.

```python
@dataclass
class ValidationResult:
    """Results of template validation."""
    
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationWarning]
    info: List[str]
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
```

---

### DeploymentResult

Deployment results.

**Location:** `src/specify_cli/bicep/models/deployment_models.py`

```python
@dataclass
class DeploymentResult:
    """Results of Azure deployment."""
    
    success: bool
    deployment_id: str
    resources: List[str]
    outputs: Dict[str, Any]
    duration: float
    errors: List[DeploymentError]
```

---

## Utility Functions

### bicep_utils.py

#### `format_resource_name(name: str, resource_type: str) -> str`

Format resource name according to Azure naming conventions.

**Parameters:**
- `name`: Proposed resource name
- `resource_type`: Azure resource type

**Returns:** Formatted name compliant with Azure rules

**Example:**

```python
from specify_cli.bicep.bicep_utils import format_resource_name

name = format_resource_name("my-storage", "Microsoft.Storage/storageAccounts")
# Returns: "mystorageaccount" (lowercase, no hyphens)
```

#### `get_default_location() -> str`

Get default Azure region from configuration or environment.

**Returns:** Azure region name

#### `validate_resource_name(name: str, resource_type: str) -> bool`

Validate resource name against Azure naming rules.

**Parameters:**
- `name`: Resource name to validate
- `resource_type`: Azure resource type

**Returns:** True if valid, False otherwise

#### `generate_unique_name(base: str, resource_type: str) -> str`

Generate unique resource name with random suffix.

**Parameters:**
- `base`: Base name
- `resource_type`: Azure resource type

**Returns:** Unique resource name

---

## Error Handling

### Error Categories

The Bicep Generator defines error categories in `error_handler.py`:

```python
class ErrorCategory(str, Enum):
    """Error categories."""
    
    ANALYSIS = "analysis"
    GENERATION = "generation"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    SCHEMA = "schema"
    CONFIGURATION = "configuration"
    PERMISSION = "permission"
    RESOURCE = "resource"
    TIMEOUT = "timeout"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"
```

### Exception Hierarchy

```
BicepError (base)
├── AnalysisError
│   ├── DependencyDetectionError
│   └── ConfigurationError
├── GenerationError
│   ├── TemplateGenerationError
│   └── SchemaError
├── ValidationError
│   ├── SyntaxError
│   ├── SchemaValidationError
│   └── SecurityValidationError
├── DeploymentError
│   ├── AuthenticationError
│   ├── PermissionError
│   └── ResourceConflictError
└── MCPError
    ├── ConnectionError
    └── SchemaRetrievalError
```

### Error Handler

```python
from specify_cli.bicep.error_handler import ErrorHandler, ErrorRecovery

handler = ErrorHandler()

try:
    result = generator.generate()
except GenerationError as e:
    recovery = handler.handle_error(e)
    if recovery.can_retry:
        result = generator.generate()  # Retry
    else:
        console.print(f"[red]Error:[/red] {recovery.user_message}")
```

---

## Performance & Caching

### Cache Configuration

The performance module provides LRU caching with TTL:

```python
from specify_cli.bicep.performance import (
    schema_cache,      # 1-hour TTL, 500 entries, 50MB
    analysis_cache,    # 30-min TTL, 100 entries, 30MB
    validation_cache   # 15-min TTL, 200 entries, 20MB
)

# Clear cache
schema_cache.clear()

# Get statistics
stats = schema_cache.get_stats()
print(f"Hit rate: {stats.hit_rate:.1%}")
```

### Performance Monitoring

```python
from specify_cli.bicep.performance import PerformanceTimer, PerformanceMonitor

# Time operation
async with PerformanceTimer("generate_template", items_processed=10):
    result = generator.generate()

# Get metrics
monitor = PerformanceMonitor()
metrics = monitor.get_metrics("generate_template")
print(f"Average: {metrics.avg_duration:.2f}s")
```

---

## Security

### Input Validation

```python
from specify_cli.bicep.security import InputValidator, ValidationRule

validator = InputValidator()

# Validate resource name
if validator.validate(
    "my-storage-account",
    ValidationRule.AZURE_RESOURCE_NAME
):
    print("✓ Valid resource name")

# Validate file path
if validator.is_safe_path(Path("./templates/main.bicep")):
    print("✓ Safe path (no directory traversal)")
```

### Credential Management

```python
from specify_cli.bicep.security import credential_manager

# Store credential
credential_manager.set_credential("azure_token", "secret-value")

# Retrieve credential
token = credential_manager.get_credential("azure_token")

# Rotate credential
credential_manager.rotate_credential("azure_token", "new-value")
```

### Rate Limiting

```python
from specify_cli.bicep.security import rate_limited

@rate_limited(max_calls=100, time_window=60)
async def call_azure_api():
    # API call implementation
    pass
```

---

## Configuration

### GeneratorConfig

```python
@dataclass
class GeneratorConfig:
    """Configuration for Bicep generator."""
    
    output_dir: Path
    region: str = "eastus"
    environment: str = "dev"
    template_style: str = "modular"
    include_monitoring: bool = True
    include_networking: bool = False
    naming_prefix: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    security_level: str = "standard"
```

### AnalysisConfig

```python
@dataclass
class AnalysisConfig:
    """Configuration for project analysis."""
    
    project_path: Path
    exclude_patterns: List[str] = field(default_factory=list)
    detect_containers: bool = True
    detect_databases: bool = True
    detect_messaging: bool = True
    scan_for_secrets: bool = True
    cache_enabled: bool = True
```

---

## CLI Integration

The Bicep Generator is integrated into the Specify CLI:

```bash
# Access commands
specify bicep analyze [OPTIONS]
specify bicep generate [OPTIONS]
specify bicep validate [OPTIONS]
specify bicep deploy [OPTIONS]
```

See [User Guide](./user-guide.md) for complete CLI documentation.

---

## Examples

### Complete Workflow Example

```python
from pathlib import Path
from specify_cli.bicep import (
    ProjectAnalyzer,
    BicepGenerator,
    TemplateValidator,
    BicepDeployer,
    GeneratorConfig
)

async def generate_and_deploy():
    # 1. Analyze project
    analyzer = ProjectAnalyzer(project_path=Path("./my-app"))
    analysis = analyzer.analyze()
    
    # 2. Generate templates
    generator = BicepGenerator(
        analysis=analysis,
        config=GeneratorConfig(
            output_dir=Path("./bicep-templates"),
            region="eastus",
            environment="production"
        )
    )
    result = generator.generate()
    
    # 3. Validate templates
    validator = TemplateValidator(
        template_dir=Path("./bicep-templates"),
        subscription_id="xxx-xxx-xxx"
    )
    validation = validator.validate()
    
    if not validation.is_valid:
        print("Validation failed!")
        return
    
    # 4. Deploy to Azure
    deployer = BicepDeployer(
        template_dir=Path("./bicep-templates"),
        resource_group="my-rg",
        subscription_id="xxx-xxx-xxx"
    )
    deployment = deployer.deploy()
    
    print(f"✓ Deployed {len(deployment.resources)} resources")

# Run
import asyncio
asyncio.run(generate_and_deploy())
```

---

## Version History

- **0.1.0**: Initial release with core functionality
- **0.2.0**: Added cost estimation and security analysis
- **0.3.0**: Added template editing and explanation engine
- **0.4.0**: Added performance optimization and caching
- **0.5.0**: Added security hardening and code quality tools

---

## Additional Resources

- [User Guide](./user-guide.md)
- [Troubleshooting Guide](./troubleshooting.md)
- [Architecture Guide](./architecture.md)
- [Contributing Guide](../CONTRIBUTING.md)
