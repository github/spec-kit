"""
Functional specification generator for legacy systems.

Generates functional-spec.md that documents WHAT the legacy system does
(features, workflows, configurations) to feed into modernization workflow.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

# Handle both relative and absolute imports
try:
    from .analysis_context import AnalysisContext
except ImportError:
    from analysis_context import AnalysisContext


class FunctionalSpecGenerator:
    """
    Generate functional specification from legacy system analysis.

    Creates a comprehensive document of what the system does, stratified by
    criticality (CRITICAL/STANDARD/LEGACY QUIRKS).
    """

    def __init__(self, context: AnalysisContext):
        """
        Initialize functional spec generator.

        Args:
            context: Shared analysis context
        """
        self.context = context

    def generate_functional_spec(self, output_path: Path) -> Path:
        """
        Generate functional-spec.md file.

        Args:
            output_path: Path where the file should be written

        Returns:
            Path to the generated file
        """
        sections = []

        # Header
        sections.append(self._build_header())

        # Overview
        sections.append(self._build_overview())

        # Features Inventory
        sections.append(self._build_features_inventory())

        # User Workflows
        sections.append(self._build_user_workflows())

        # Configuration Mapping
        sections.append(self._build_configuration_mapping())

        # Data Models
        sections.append(self._build_data_models())

        # Known Quirks
        sections.append(self._build_known_quirks())

        # How to Use
        sections.append(self._build_usage_guide())

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(sections))

        return output_path

    def _build_header(self) -> str:
        """Build header section."""
        return f"""# Functional Specification (Legacy System)

**Project**: {self.context.project_name}
**Analysis Date**: {self.context.analysis_date}
**Purpose**: Document WHAT the legacy system does for modernization

---

## Document Purpose

This document captures the functional capabilities of the legacy system.
It answers "WHAT does the system do?" not "HOW does it do it?"

Use this document to:
- Ensure all features are captured in modernization spec
- Identify critical behaviors that must be preserved
- Understand configuration requirements
- Plan feature migration priority

---"""

    def _build_overview(self) -> str:
        """Build overview section."""
        return f"""## System Overview

### Technology Profile

- **Primary Language**: {self.context.scan_result.tech_stack.primary_language.title()}
- **Frameworks**: {", ".join(self.context.scan_result.tech_stack.frameworks) if self.context.scan_result.tech_stack.frameworks else "None detected"}
- **Build Tools**: {", ".join(self.context.scan_result.tech_stack.build_tools) if self.context.scan_result.tech_stack.build_tools else "Standard"}
- **Package Manager**: {self.context.scan_result.tech_stack.package_manager or "Not detected"}

### Size & Complexity

- **Lines of Code**: {self.context.metrics.lines_of_code:,}
- **File Count**: {self.context.scan_result.metrics.file_count}
- **Languages**: {", ".join(self.context.scan_result.tech_stack.languages)}
- **Dependencies**: {self.context.metrics.total_dependencies} packages

### Structure

- **Source Directories**: {", ".join(self.context.scan_result.structure.source_dirs) if self.context.scan_result.structure.source_dirs else "Standard layout"}
- **Test Coverage**: {self.context.metrics.test_coverage:.0f}%
- **Has CI/CD**: {"Yes" if self.context.scan_result.structure.has_ci_cd else "No"}
- **Has Documentation**: {"Yes" if self.context.scan_result.structure.has_documentation else "Limited"}

---"""

    def _build_features_inventory(self) -> str:
        """Build features inventory section."""
        critical_features = self._identify_critical_features()
        standard_features = self._identify_standard_features()
        quirks = self._identify_legacy_quirks()

        return f"""## Features Inventory

### CRITICAL Features (Preserve Exactly)

These features involve security, payments, data integrity, or compliance.
They MUST be migrated with exact behavior preservation.

{critical_features}

### STANDARD Features (Can Modernize)

These features can be reimplemented with modern patterns while preserving
core functionality.

{standard_features}

### LEGACY QUIRKS (Decide: Preserve or Fix)

These are implementation peculiarities that may be bugs or intentional.
Decision needed on whether to preserve for compatibility or fix.

{quirks}

---"""

    def _identify_critical_features(self) -> str:
        """Identify critical features from analysis."""
        features = []

        # Check for authentication/security
        has_auth = any("auth" in str(d).lower() or "security" in str(d).lower()
                      for d in self.context.scan_result.structure.config_files + self.context.scan_result.structure.source_dirs)

        if has_auth:
            features.append(self._format_feature(
                "User Authentication & Authorization",
                "Security-critical feature managing user access",
                self._find_auth_location(),
                "CRITICAL",
                ["Session management", "Password handling", "Access control"],
                "Examine auth implementation - timeouts, token handling, MFA if present"
            ))

        # Check for data persistence
        has_db = any("db" in str(f).lower() or "database" in str(f).lower() or "model" in str(f).lower()
                    for f in self.context.scan_result.structure.config_files + self.context.scan_result.structure.source_dirs)

        if has_db:
            features.append(self._format_feature(
                "Data Persistence & Integrity",
                "Database operations and data validation",
                self._find_data_location(),
                "CRITICAL",
                ["CRUD operations", "Validation rules", "Data integrity constraints"],
                "Examine data models, validation logic, and constraints - ALL must be preserved"
            ))

        # Check for API endpoints
        if self.context.scan_result.tech_stack.frameworks:
            features.append(self._format_feature(
                "API Endpoints",
                f"REST/GraphQL API using {', '.join(self.context.scan_result.tech_stack.frameworks)}",
                self._find_api_location(),
                "CRITICAL",
                ["Request/response formats", "Error handling", "Validation"],
                "Document all endpoints, their contracts, and error responses"
            ))

        if not features:
            features.append("**AI should examine codebase** to identify critical features:\n"
                          "- Authentication/authorization\n"
                          "- Payment processing\n"
                          "- Data validation and integrity\n"
                          "- Audit logging\n"
                          "- Any compliance-related features")

        return "\n\n".join(features)

    def _identify_standard_features(self) -> str:
        """Identify standard features from analysis."""
        features = []

        # Logging
        features.append(self._format_feature(
            "Logging & Monitoring",
            "Application logging and error tracking",
            "Throughout application",
            "STANDARD",
            ["Error logging", "Audit trails", "Performance monitoring"],
            "Can modernize to structured logging (JSON) and centralized logging"
        ))

        # Configuration
        if self.context.scan_result.structure.config_files:
            features.append(self._format_feature(
                "Configuration Management",
                "Application settings and environment config",
                ", ".join(self.context.scan_result.structure.config_files[:3]),
                "STANDARD",
                ["Environment variables", "App settings", "Feature flags"],
                "Migrate to env vars and modern config management"
            ))

        # Testing
        if self.context.scan_result.structure.has_tests:
            features.append(self._format_feature(
                "Test Infrastructure",
                f"Automated testing ({self.context.metrics.test_coverage:.0f}% coverage)",
                ", ".join(self.context.scan_result.structure.test_dirs),
                "STANDARD",
                ["Unit tests", "Integration tests", "Test utilities"],
                "Maintain test coverage, upgrade test framework to modern version"
            ))

        # CI/CD
        if self.context.scan_result.structure.has_ci_cd:
            features.append(self._format_feature(
                "CI/CD Pipeline",
                "Automated build and deployment",
                "CI/CD configuration files detected",
                "STANDARD",
                ["Build automation", "Test automation", "Deployment automation"],
                "Enhance pipeline with modern practices (Docker, secrets management)"
            ))

        return "\n\n".join(features)

    def _identify_legacy_quirks(self) -> str:
        """Identify legacy quirks and decisions needed."""
        quirks = []

        # Outdated dependencies
        outdated = self.context.metrics.outdated_dependencies
        if outdated > 10:
            quirks.append(self._format_quirk(
                "Many Outdated Dependencies",
                f"{outdated} packages behind latest versions",
                self._find_dependency_file(),
                "Update all to latest compatible versions",
                "Some APIs may have changed - check breaking changes",
                "MODERATE"
            ))

        # Low test coverage
        if self.context.metrics.test_coverage < 60:
            quirks.append(self._format_quirk(
                "Low Test Coverage",
                f"Only {self.context.metrics.test_coverage:.0f}% of code is tested",
                "Entire codebase",
                "Add comprehensive test suite (target: 80%+)",
                "Risk of breaking untested code during migration",
                "HIGH"
            ))

        # High technical debt
        if self.context.metrics.technical_debt_percentage > 40:
            quirks.append(self._format_quirk(
                "High Technical Debt",
                f"{self.context.metrics.technical_debt_percentage:.0f}% of code is technical debt",
                "Throughout codebase",
                "Refactor during migration",
                "May indicate code smells, duplication, or poor patterns",
                "HIGH"
            ))

        # Vulnerable dependencies
        vulnerable = sum(r.vulnerable_count for r in self.context.dependency_reports)
        if vulnerable > 0:
            quirks.append(self._format_quirk(
                "Security Vulnerabilities",
                f"{vulnerable} known vulnerabilities in dependencies",
                self._find_dependency_file(),
                "Update vulnerable packages immediately",
                "Security risk - prioritize fixes",
                "CRITICAL"
            ))

        if not quirks:
            quirks.append("None identified in automated analysis.\n\n"
                         "**AI should examine code for**:\n"
                         "- Hardcoded values that should be configurable\n"
                         "- Non-standard ID formats or naming conventions\n"
                         "- Unusual error handling patterns\n"
                         "- Business logic in unexpected places")

        return "\n\n".join(quirks)

    def _build_user_workflows(self) -> str:
        """Build user workflows section."""
        return f"""## User Workflows

**Note**: This section requires AI examination of the codebase to extract
actual user journeys and interaction patterns.

### Workflow Discovery Process

To document user workflows, AI should:

1. **Examine Routes/Controllers**: In {self._find_api_location()}
2. **Identify Entry Points**: User-facing endpoints or UI entry points
3. **Trace Data Flow**: Follow user actions through the system
4. **Document State Changes**: What happens at each step

### Common Workflow Patterns to Look For

#### Pattern 1: User Registration/Login
- Account creation
- Email verification (if present)
- Login process
- Password reset workflow

#### Pattern 2: Core Business Operations
- Main user tasks (based on {", ".join(self.context.scan_result.tech_stack.frameworks) if self.context.scan_result.tech_stack.frameworks else "application type"})
- Data entry/modification
- Report generation
- Export/import operations

#### Pattern 3: Administrative Operations
- User management
- Configuration changes
- System monitoring
- Backup/restore operations

### AI Action Required

**Examine**: {", ".join(self.context.scan_result.structure.source_dirs[:3]) if self.context.scan_result.structure.source_dirs else "Source code"}

**Document for each workflow**:
1. **Entry Point**: How does user initiate?
2. **Steps**: What happens in sequence?
3. **Data**: What data is required/modified?
4. **Validations**: What checks are performed?
5. **Success State**: What is the final outcome?
6. **Error Cases**: What can go wrong?

---"""

    def _build_configuration_mapping(self) -> str:
        """Build configuration mapping section."""
        configs = self.context.scan_result.structure.config_files

        if not configs:
            config_list = "**No configuration files detected in automated scan**\n\nAI should search for: .env, config.*, settings.*, *.ini, *.yaml, *.toml files"
        else:
            config_items = []
            for config_file in configs[:10]:  # Limit to first 10
                purpose = self._infer_config_purpose(config_file)
                strategy = self._suggest_migration_strategy(config_file)
                config_items.append(f"| `{config_file}` | {purpose} | {strategy} |")

            config_list = "| Config File | Purpose | Migration Strategy |\n"
            config_list += "|-------------|---------|--------------------|\n"
            config_list += "\n".join(config_items)

        return f"""## Configuration Mapping

### Detected Configuration Files

{config_list}

### Configuration Categories

#### Environment-Specific
- Development, staging, production settings
- **Migration**: Use environment variables or cloud config services

#### Application Settings
- Feature flags, timeouts, limits
- **Migration**: Centralized config management

#### Secrets & Credentials
- API keys, database passwords, tokens
- **Migration**: Secret management service (AWS Secrets Manager, HashiCorp Vault)

#### Build Configuration
- Compiler settings, optimization flags
- **Migration**: Update for modern build tools

### AI Action Required

For each configuration file:
1. **Read the file** and understand what it configures
2. **Categorize** settings (environment, secrets, app settings, build)
3. **Identify** which settings are environment-specific vs. static
4. **Document** any hardcoded values that should be configurable
5. **Suggest** modern equivalents (env vars, cloud config, etc.)

---"""

    def _build_data_models(self) -> str:
        """Build data models section."""
        has_db = any("db" in str(f).lower() or "model" in str(f).lower()
                    for f in self.context.scan_result.structure.source_dirs)

        return f"""## Data Models

### Schema Documentation

**Status**: Requires AI examination of codebase

**Likely Location**: {self._find_data_location()}

### What to Document

#### Entities
- User
- [Other domain entities - AI should identify]

#### Relationships
- One-to-many
- Many-to-many
- Foreign keys and constraints

#### Validation Rules
- Required fields
- Format constraints (email, phone, etc.)
- Min/max values
- Custom business rules

#### Indices & Performance
- Primary keys
- Indexed columns
- Query patterns

### AI Action Required

1. **Find Schema Definitions**: In {self._find_data_location()}
2. **Document Each Entity**:
   - Fields and types
   - Constraints and validations
   - Relationships
   - Indexes
3. **Extract Business Rules**: From validation logic
4. **Identify Critical Fields**: That must not be null or have specific formats
5. **Map to Modern Schema**: Suggest equivalent in target database

### Example Format

```markdown
#### Entity: User

**Table/Collection**: users

Fields:
- id: Integer, Primary Key, Auto-increment
- email: String, Unique, Not Null, Format: email
- password_hash: String, Not Null
- created_at: Timestamp, Default: now()
- last_login: Timestamp, Nullable

Relationships:
- Has many: orders (user_id → orders.user_id)

Validation Rules:
- Email must be unique
- Password must be hashed with bcrypt
- Created_at cannot be modified after creation
```

---"""

    def _build_known_quirks(self) -> str:
        """Build known quirks section."""
        return f"""## Known Limitations & Quirks

### From Automated Analysis

{self._list_known_issues()}

### Common Quirk Categories

#### Hardcoded Values
**AI should search for**: Magic numbers, hardcoded URLs, fixed timeouts

**Example**: Session timeout hardcoded to 30 minutes
**Decision**: Make configurable via environment variable?

#### Non-Standard Formats
**AI should search for**: Custom ID formats, unusual date formats, proprietary data structures

**Example**: Order ID format `ORD-{{timestamp}}-{{random}}`
**Decision**: Keep for compatibility or switch to standard UUID?

#### Business Logic in Unexpected Places
**AI should search for**: Calculations in views/templates, validation in UI, business rules in database

**Example**: Price calculation in frontend JavaScript
**Decision**: Move to backend API

#### Performance Issues
**AI should search for**: N+1 queries, missing indexes, unoptimized loops

**Example**: Loading all users then filtering in code
**Decision**: Add database query filter

#### Error Handling Inconsistencies
**AI should search for**: Silent failures, inconsistent error formats, unclear error messages

**Example**: Some endpoints return {{error: "message"}}, others return {{message: "error"}}
**Decision**: Standardize error response format

### AI Action Required

Examine codebase for:
1. Hardcoded configuration values
2. Magic numbers and strings
3. Inconsistent patterns across modules
4. Performance bottlenecks
5. Unclear error handling

For each quirk found:
- **Document**: What is the quirk?
- **Location**: Where is it in the code?
- **Impact**: Does it affect functionality or just code quality?
- **Decision**: Preserve (for compatibility) or Fix (improvement)?

---"""

    def _build_usage_guide(self) -> str:
        """Build usage guide section."""
        return """## How to Use This Document

### During Modernization Planning

1. **Feature Completeness Check**:
   - Review CRITICAL features - ALL must be in modernization spec
   - Review STANDARD features - Most should be in spec
   - Review LEGACY QUIRKS - Decide preserve vs. fix

2. **Priority Setting**:
   - CRITICAL features → Highest priority (Phase 1)
   - STANDARD features → Medium priority (Phase 2-3)
   - Improvements → Lower priority (Phase 3-4)

3. **Risk Assessment**:
   - High risk: CRITICAL features with low test coverage
   - Medium risk: STANDARD features with complex logic
   - Low risk: Well-tested, simple features

### During Implementation

1. **Reference for Each Feature**:
   - Check this document for feature description
   - Examine legacy code location for implementation details
   - Preserve behavior for CRITICAL features
   - Modernize implementation for STANDARD features

2. **Testing Strategy**:
   - CRITICAL features: Test against legacy behavior exactly
   - STANDARD features: Test functional equivalence
   - Improvements: Test new behavior thoroughly

### For AI Agents

**Deep Examination Required**: This document provides structure, but AI must
examine the actual code to extract:

- Specific API endpoints and contracts
- Exact validation rules and constraints
- Detailed workflow steps and state transitions
- Configuration options and their effects
- Data model schemas and relationships

**Process**:
1. Read this document for overview
2. Examine legacy code in locations referenced
3. Extract detailed specifications
4. Document findings in spec.md for modernization

---

**Status**: Automated analysis complete. AI deep-dive needed for details.
**Next Step**: Use this as guide for comprehensive code examination."""

    # Helper methods

    def _format_feature(self, name: str, description: str, location: str,
                       criticality: str, components: List[str], notes: str) -> str:
        """Format a feature description."""
        components_list = "\n".join([f"  - {c}" for c in components])

        return f"""#### {name}

**Description**: {description}
**Location**: {location}
**Criticality**: {criticality}

**Components**:
{components_list}

**Migration Notes**: {notes}"""

    def _format_quirk(self, name: str, description: str, location: str,
                     recommendation: str, notes: str, priority: str) -> str:
        """Format a legacy quirk."""
        return f"""#### {name}

**Description**: {description}
**Location**: {location}
**Priority**: {priority}

**Recommendation**: {recommendation}

**Notes**: {notes}"""

    def _find_auth_location(self) -> str:
        """Find likely location of auth code."""
        for dir_name in self.context.scan_result.structure.source_dirs:
            if any(keyword in dir_name.lower() for keyword in ["auth", "security", "user"]):
                return dir_name

        return "Examine source code for auth, security, or user modules"

    def _find_data_location(self) -> str:
        """Find likely location of data models."""
        for dir_name in self.context.scan_result.structure.source_dirs:
            if any(keyword in dir_name.lower() for keyword in ["model", "entity", "db", "database", "schema"]):
                return dir_name

        return "Examine source code for models, entities, or schema definitions"

    def _find_api_location(self) -> str:
        """Find likely location of API code."""
        for dir_name in self.context.scan_result.structure.source_dirs:
            if any(keyword in dir_name.lower() for keyword in ["api", "route", "controller", "endpoint"]):
                return dir_name

        if self.context.scan_result.structure.source_dirs:
            return f"{self.context.scan_result.structure.source_dirs[0]} (likely contains routes/controllers)"

        return "Examine source code for API routes or controllers"

    def _find_dependency_file(self) -> str:
        """Find dependency file."""
        pkg_mgr = self.context.scan_result.tech_stack.package_manager

        if not pkg_mgr:
            return "package.json, requirements.txt, pom.xml, or similar"

        if "npm" in pkg_mgr.lower():
            return "package.json"
        elif "pip" in pkg_mgr.lower():
            return "requirements.txt or setup.py"
        elif "maven" in pkg_mgr.lower():
            return "pom.xml"
        elif "gradle" in pkg_mgr.lower():
            return "build.gradle"
        else:
            return f"{pkg_mgr} configuration file"

    def _infer_config_purpose(self, config_file: str) -> str:
        """Infer purpose of config file."""
        lower = config_file.lower()

        if "env" in lower:
            return "Environment variables"
        elif "database" in lower or "db" in lower:
            return "Database connection"
        elif "test" in lower:
            return "Test configuration"
        elif "ci" in lower or "cd" in lower:
            return "CI/CD pipeline"
        elif "lint" in lower:
            return "Code linting rules"
        elif "build" in lower or "webpack" in lower or "rollup" in lower:
            return "Build configuration"
        else:
            return "Application settings"

    def _suggest_migration_strategy(self, config_file: str) -> str:
        """Suggest migration strategy for config."""
        lower = config_file.lower()

        if "env" in lower:
            return "Keep, update keys"
        elif "secret" in lower or "credential" in lower:
            return "Move to secret manager"
        elif "test" in lower:
            return "Update for new test framework"
        elif "build" in lower:
            return "Replace with modern build tool config"
        else:
            return "Review and migrate"

    def _list_known_issues(self) -> str:
        """List known issues from analysis."""
        issues = []

        if not self.context.scan_result.structure.has_tests:
            issues.append("- No automated test infrastructure")

        if self.context.metrics.test_coverage < 60:
            issues.append(f"- Low test coverage ({self.context.metrics.test_coverage:.0f}%)")

        vulnerable = sum(r.vulnerable_count for r in self.context.dependency_reports)
        if vulnerable > 0:
            issues.append(f"- {vulnerable} vulnerable dependencies")

        if self.context.metrics.outdated_dependencies > 10:
            issues.append(f"- {self.context.metrics.outdated_dependencies} outdated packages")

        if self.context.metrics.technical_debt_percentage > 40:
            issues.append(f"- High technical debt ({self.context.metrics.technical_debt_percentage:.0f}%)")

        if not issues:
            issues.append("- None identified in automated scan (AI examination may find more)")

        return "\n".join(issues)


def main():
    """Example usage of FunctionalSpecGenerator."""
    print("FunctionalSpecGenerator module loaded successfully")
    print("This module is called by ReportGenerator during analysis")


if __name__ == "__main__":
    main()
