"""Enhanced ARM template validation with Azure best practices.

This module extends the basic ARM validator with additional checks for
Azure Well-Architected Framework compliance and best practices.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import re

from .arm_validator import ARMValidator, ValidationResult
from .models.bicep_template import BicepTemplate
from .models.resource_requirement import ResourceType

logger = logging.getLogger(__name__)


@dataclass
class BestPracticeCheck:
    """Represents a best practice validation check."""
    rule_id: str
    title: str
    description: str
    category: str
    severity: str  # "error", "warning", "info"
    resource_types: List[str] = field(default_factory=list)
    
    def applies_to_resource(self, resource_type: str) -> bool:
        """Check if this rule applies to a resource type."""
        return not self.resource_types or resource_type in self.resource_types


@dataclass
class BestPracticeViolation:
    """Represents a violation of a best practice."""
    rule_id: str
    resource_name: str
    resource_type: str
    message: str
    severity: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class WellArchitectedAssessment:
    """Assessment against Azure Well-Architected Framework pillars."""
    reliability_score: float = 0.0
    security_score: float = 0.0
    cost_optimization_score: float = 0.0
    operational_excellence_score: float = 0.0
    performance_efficiency_score: float = 0.0
    
    violations: List[BestPracticeViolation] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    @property
    def overall_score(self) -> float:
        """Calculate overall Well-Architected score."""
        scores = [
            self.reliability_score,
            self.security_score, 
            self.cost_optimization_score,
            self.operational_excellence_score,
            self.performance_efficiency_score
        ]
        return sum(scores) / len(scores) if scores else 0.0


class BestPracticesValidator:
    """Validates Bicep templates against Azure best practices and Well-Architected Framework."""
    
    def __init__(self, arm_validator: Optional[ARMValidator] = None):
        """Initialize the validator."""
        self.arm_validator = arm_validator or ARMValidator()
        self.best_practices = self._initialize_best_practices()
    
    def _initialize_best_practices(self) -> List[BestPracticeCheck]:
        """Initialize the list of best practice checks."""
        checks = []
        
        # Security best practices
        checks.extend([
            BestPracticeCheck(
                rule_id="SEC001",
                title="HTTPS Only Enforcement", 
                description="Web applications should enforce HTTPS-only traffic",
                category="Security",
                severity="error",
                resource_types=["Microsoft.Web/sites"]
            ),
            BestPracticeCheck(
                rule_id="SEC002",
                title="Minimum TLS Version",
                description="Services should use minimum TLS version 1.2",
                category="Security", 
                severity="warning",
                resource_types=["Microsoft.Web/sites", "Microsoft.Storage/storageAccounts", "Microsoft.KeyVault/vaults"]
            ),
            BestPracticeCheck(
                rule_id="SEC003",
                title="Managed Identity Usage",
                description="Resources should use managed identities instead of connection strings",
                category="Security",
                severity="warning",
                resource_types=["Microsoft.Web/sites", "Microsoft.Web/sites/functions"]
            ),
            BestPracticeCheck(
                rule_id="SEC004",
                title="Key Vault Integration",
                description="Secrets should be stored in Azure Key Vault",
                category="Security",
                severity="error",
                resource_types=[]
            ),
            BestPracticeCheck(
                rule_id="SEC005",
                title="Network Security",
                description="Resources should have appropriate network access restrictions",
                category="Security", 
                severity="warning",
                resource_types=["Microsoft.Storage/storageAccounts", "Microsoft.Sql/servers"]
            )
        ])
        
        # Reliability best practices
        checks.extend([
            BestPracticeCheck(
                rule_id="REL001",
                title="High Availability Configuration",
                description="Critical resources should be configured for high availability",
                category="Reliability",
                severity="warning",
                resource_types=["Microsoft.Sql/servers", "Microsoft.Web/serverfarms"]
            ),
            BestPracticeCheck(
                rule_id="REL002", 
                title="Backup Configuration",
                description="Data resources should have backup enabled",
                category="Reliability",
                severity="warning",
                resource_types=["Microsoft.Sql/servers/databases", "Microsoft.Storage/storageAccounts"]
            ),
            BestPracticeCheck(
                rule_id="REL003",
                title="Auto-scaling Configuration",
                description="Compute resources should support auto-scaling",
                category="Reliability", 
                severity="info",
                resource_types=["Microsoft.Web/serverfarms"]
            ),
            BestPracticeCheck(
                rule_id="REL004",
                title="Health Check Configuration",
                description="Applications should have health checks configured",
                category="Reliability",
                severity="warning",
                resource_types=["Microsoft.Web/sites"]
            )
        ])
        
        # Performance best practices
        checks.extend([
            BestPracticeCheck(
                rule_id="PERF001",
                title="CDN Usage",
                description="Static content should use CDN for better performance",
                category="Performance",
                severity="info",
                resource_types=["Microsoft.Web/staticSites", "Microsoft.Storage/storageAccounts"]
            ),
            BestPracticeCheck(
                rule_id="PERF002",
                title="Caching Configuration",
                description="Applications should implement caching for better performance",
                category="Performance",
                severity="info",
                resource_types=["Microsoft.Web/sites"]
            ),
            BestPracticeCheck(
                rule_id="PERF003",
                title="Appropriate SKU Selection",
                description="Resources should use appropriate SKUs for workload requirements",
                category="Performance",
                severity="warning",
                resource_types=["Microsoft.Web/serverfarms", "Microsoft.Sql/servers"]
            )
        ])
        
        # Cost optimization best practices
        checks.extend([
            BestPracticeCheck(
                rule_id="COST001",
                title="Right-sized Resources",
                description="Resources should be right-sized for actual usage",
                category="Cost",
                severity="info",
                resource_types=["Microsoft.Web/serverfarms", "Microsoft.Sql/servers"]
            ),
            BestPracticeCheck(
                rule_id="COST002",
                title="Storage Tier Optimization", 
                description="Storage accounts should use appropriate access tiers",
                category="Cost",
                severity="info",
                resource_types=["Microsoft.Storage/storageAccounts"]
            ),
            BestPracticeCheck(
                rule_id="COST003",
                title="Reserved Capacity Usage",
                description="Consider reserved capacity for predictable workloads",
                category="Cost", 
                severity="info",
                resource_types=["Microsoft.Sql/servers", "Microsoft.Web/serverfarms"]
            )
        ])
        
        # Operational excellence best practices
        checks.extend([
            BestPracticeCheck(
                rule_id="OPS001",
                title="Resource Tagging",
                description="All resources should have consistent tagging strategy",
                category="Operations",
                severity="warning",
                resource_types=[]
            ),
            BestPracticeCheck(
                rule_id="OPS002",
                title="Monitoring Configuration",
                description="Resources should have monitoring and alerting configured",
                category="Operations",
                severity="warning", 
                resource_types=["Microsoft.Web/sites", "Microsoft.Sql/servers"]
            ),
            BestPracticeCheck(
                rule_id="OPS003",
                title="Diagnostic Settings",
                description="Resources should have diagnostic settings enabled",
                category="Operations",
                severity="info",
                resource_types=["Microsoft.Web/sites", "Microsoft.KeyVault/vaults", "Microsoft.Storage/storageAccounts"]
            )
        ])
        
        return checks
    
    async def validate_template_best_practices(self, 
                                             bicep_template: BicepTemplate,
                                             template_content: str) -> WellArchitectedAssessment:
        """Validate a Bicep template against best practices."""
        logger.info(f"Validating template '{bicep_template.name}' against best practices")
        
        assessment = WellArchitectedAssessment()
        
        try:
            # Convert to ARM for detailed analysis
            arm_template = bicep_template.to_arm_template()
            
            # Run basic ARM validation first
            basic_validation = await self.arm_validator.validate_template(arm_template)
            
            if not basic_validation.is_valid:
                # Add ARM validation errors as violations
                for error in basic_validation.errors:
                    assessment.violations.append(BestPracticeViolation(
                        rule_id="ARM001",
                        resource_name="template",
                        resource_type="template",
                        message=error,
                        severity="error"
                    ))
            
            # Analyze resources for best practices
            if "resources" in arm_template:
                for resource in arm_template["resources"]:
                    await self._validate_resource_best_practices(resource, assessment, template_content)
            
            # Calculate pillar scores
            self._calculate_pillar_scores(assessment)
            
            # Generate recommendations
            self._generate_recommendations(assessment)
            
            logger.info(f"Best practices validation completed. Overall score: {assessment.overall_score:.2f}")
            
        except Exception as e:
            logger.error(f"Error during best practices validation: {e}")
            assessment.violations.append(BestPracticeViolation(
                rule_id="VAL001",
                resource_name="template",
                resource_type="template", 
                message=f"Validation error: {e}",
                severity="error"
            ))
        
        return assessment
    
    async def _validate_resource_best_practices(self,
                                              resource: Dict[str, Any], 
                                              assessment: WellArchitectedAssessment,
                                              template_content: str) -> None:
        """Validate a single resource against best practices."""
        resource_type = resource.get("type", "")
        resource_name = resource.get("name", "unknown")
        properties = resource.get("properties", {})
        
        # Check each best practice rule
        for check in self.best_practices:
            if check.applies_to_resource(resource_type):
                violation = await self._check_best_practice_rule(
                    check, resource, resource_name, resource_type, properties, template_content
                )
                if violation:
                    assessment.violations.append(violation)
    
    async def _check_best_practice_rule(self,
                                      check: BestPracticeCheck,
                                      resource: Dict[str, Any],
                                      resource_name: str, 
                                      resource_type: str,
                                      properties: Dict[str, Any],
                                      template_content: str) -> Optional[BestPracticeViolation]:
        """Check a specific best practice rule against a resource."""
        
        # Security checks
        if check.rule_id == "SEC001":  # HTTPS Only
            if resource_type == "Microsoft.Web/sites":
                https_only = properties.get("httpsOnly", False)
                if not https_only:
                    return BestPracticeViolation(
                        rule_id=check.rule_id,
                        resource_name=resource_name,
                        resource_type=resource_type,
                        message="Web app should enforce HTTPS-only traffic",
                        severity=check.severity,
                        suggestion="Set httpsOnly property to true"
                    )
        
        elif check.rule_id == "SEC002":  # Minimum TLS Version
            if resource_type == "Microsoft.Web/sites":
                site_config = properties.get("siteConfig", {})
                min_tls = site_config.get("minTlsVersion", "1.0")
                if min_tls < "1.2":
                    return BestPracticeViolation(
                        rule_id=check.rule_id,
                        resource_name=resource_name, 
                        resource_type=resource_type,
                        message=f"Minimum TLS version is {min_tls}, should be 1.2 or higher",
                        severity=check.severity,
                        suggestion="Set siteConfig.minTlsVersion to '1.2'"
                    )
            
            elif resource_type == "Microsoft.Storage/storageAccounts":
                min_tls = properties.get("minimumTlsVersion", "TLS1_0")
                if min_tls < "TLS1_2":
                    return BestPracticeViolation(
                        rule_id=check.rule_id,
                        resource_name=resource_name,
                        resource_type=resource_type,
                        message=f"Minimum TLS version is {min_tls}, should be TLS1_2",
                        severity=check.severity,
                        suggestion="Set minimumTlsVersion to 'TLS1_2'"
                    )
        
        elif check.rule_id == "SEC003":  # Managed Identity
            if resource_type in ["Microsoft.Web/sites", "Microsoft.Web/sites/functions"]:
                identity = resource.get("identity")
                if not identity or identity.get("type") != "SystemAssigned":
                    return BestPracticeViolation(
                        rule_id=check.rule_id,
                        resource_name=resource_name,
                        resource_type=resource_type,
                        message="Resource should use system-assigned managed identity",
                        severity=check.severity,
                        suggestion="Add identity with type 'SystemAssigned'"
                    )
        
        elif check.rule_id == "SEC004":  # Key Vault Integration
            # Check if template has Key Vault and uses it properly
            has_keyvault = "Microsoft.KeyVault/vaults" in template_content
            has_hardcoded_secrets = self._check_hardcoded_secrets(template_content)
            
            if has_hardcoded_secrets and not has_keyvault:
                return BestPracticeViolation(
                    rule_id=check.rule_id,
                    resource_name="template",
                    resource_type="template",
                    message="Template contains potential hardcoded secrets but no Key Vault",
                    severity=check.severity,
                    suggestion="Add Key Vault and use Key Vault references for secrets"
                )
        
        # Reliability checks
        elif check.rule_id == "REL001":  # High Availability
            if resource_type == "Microsoft.Sql/servers":
                # Check for geo-replication or availability zones
                backup_policy = properties.get("backupPolicy", {})
                geo_redundant = backup_policy.get("geoRedundantBackup", "Disabled")
                if geo_redundant == "Disabled":
                    return BestPracticeViolation(
                        rule_id=check.rule_id,
                        resource_name=resource_name,
                        resource_type=resource_type,
                        message="SQL Server should have geo-redundant backup enabled for high availability",
                        severity=check.severity,
                        suggestion="Enable geo-redundant backup"
                    )
        
        elif check.rule_id == "REL004":  # Health Checks
            if resource_type == "Microsoft.Web/sites":
                site_config = properties.get("siteConfig", {})
                health_check = site_config.get("healthCheckPath")
                if not health_check:
                    return BestPracticeViolation(
                        rule_id=check.rule_id,
                        resource_name=resource_name,
                        resource_type=resource_type,
                        message="Web app should have health check configured",
                        severity=check.severity,
                        suggestion="Configure siteConfig.healthCheckPath"
                    )
        
        # Performance checks
        elif check.rule_id == "PERF003":  # Appropriate SKU
            if resource_type == "Microsoft.Web/serverfarms":
                sku = resource.get("sku", {})
                sku_name = sku.get("name", "")
                if sku_name.startswith("F"):  # Free tier
                    return BestPracticeViolation(
                        rule_id=check.rule_id,
                        resource_name=resource_name,
                        resource_type=resource_type,
                        message="Free tier SKU may not be suitable for production workloads",
                        severity=check.severity,
                        suggestion="Consider using Basic (B1) or higher SKU for production"
                    )
        
        # Operations checks
        elif check.rule_id == "OPS001":  # Resource Tagging
            tags = resource.get("tags", {})
            required_tags = ["Environment", "Owner", "CostCenter"]
            missing_tags = [tag for tag in required_tags if tag not in tags]
            
            if missing_tags:
                return BestPracticeViolation(
                    rule_id=check.rule_id,
                    resource_name=resource_name,
                    resource_type=resource_type,
                    message=f"Resource is missing required tags: {', '.join(missing_tags)}",
                    severity=check.severity,
                    suggestion=f"Add tags: {', '.join(missing_tags)}"
                )
        
        elif check.rule_id == "OPS002":  # Monitoring
            if resource_type in ["Microsoft.Web/sites", "Microsoft.Sql/servers"]:
                # Check if Application Insights is referenced
                app_settings = properties.get("siteConfig", {}).get("appSettings", [])
                has_app_insights = any(
                    "APPLICATIONINSIGHTS" in setting.get("name", "") 
                    for setting in app_settings
                )
                
                if not has_app_insights and "Microsoft.Insights/components" not in template_content:
                    return BestPracticeViolation(
                        rule_id=check.rule_id,
                        resource_name=resource_name,
                        resource_type=resource_type,
                        message="Resource should have Application Insights monitoring configured",
                        severity=check.severity,
                        suggestion="Add Application Insights and configure connection"
                    )
        
        return None
    
    def _check_hardcoded_secrets(self, template_content: str) -> bool:
        """Check for potential hardcoded secrets in template."""
        secret_patterns = [
            r'password\s*[=:]\s*["\'][^"\']+["\']',
            r'secret\s*[=:]\s*["\'][^"\']+["\']',
            r'key\s*[=:]\s*["\'][^"\']+["\']',
            r'connectionString\s*[=:]\s*["\'][^"\']+["\']'
        ]
        
        for pattern in secret_patterns:
            if re.search(pattern, template_content, re.IGNORECASE):
                return True
        
        return False
    
    def _calculate_pillar_scores(self, assessment: WellArchitectedAssessment) -> None:
        """Calculate Well-Architected Framework pillar scores."""
        
        # Group violations by category
        violations_by_category = {}
        for violation in assessment.violations:
            rule = next((r for r in self.best_practices if r.rule_id == violation.rule_id), None)
            if rule:
                category = rule.category
                if category not in violations_by_category:
                    violations_by_category[category] = []
                violations_by_category[category].append(violation)
        
        # Calculate scores (1.0 = perfect, 0.0 = many issues)
        total_checks_by_category = {}
        for check in self.best_practices:
            category = check.category
            total_checks_by_category[category] = total_checks_by_category.get(category, 0) + 1
        
        # Security score
        security_violations = len(violations_by_category.get("Security", []))
        security_total = total_checks_by_category.get("Security", 1)
        assessment.security_score = max(0.0, 1.0 - (security_violations / security_total))
        
        # Reliability score
        reliability_violations = len(violations_by_category.get("Reliability", []))
        reliability_total = total_checks_by_category.get("Reliability", 1) 
        assessment.reliability_score = max(0.0, 1.0 - (reliability_violations / reliability_total))
        
        # Cost optimization score
        cost_violations = len(violations_by_category.get("Cost", []))
        cost_total = total_checks_by_category.get("Cost", 1)
        assessment.cost_optimization_score = max(0.0, 1.0 - (cost_violations / cost_total))
        
        # Performance efficiency score
        perf_violations = len(violations_by_category.get("Performance", []))
        perf_total = total_checks_by_category.get("Performance", 1)
        assessment.performance_efficiency_score = max(0.0, 1.0 - (perf_violations / perf_total))
        
        # Operational excellence score
        ops_violations = len(violations_by_category.get("Operations", []))
        ops_total = total_checks_by_category.get("Operations", 1)
        assessment.operational_excellence_score = max(0.0, 1.0 - (ops_violations / ops_total))
    
    def _generate_recommendations(self, assessment: WellArchitectedAssessment) -> None:
        """Generate recommendations based on violations."""
        
        # Count violations by severity
        errors = [v for v in assessment.violations if v.severity == "error"]
        warnings = [v for v in assessment.violations if v.severity == "warning"]
        
        if errors:
            assessment.recommendations.append(
                f"🚨 Address {len(errors)} critical security and compliance issues immediately"
            )
        
        if warnings:
            assessment.recommendations.append(
                f"⚠️ Review and fix {len(warnings)} important best practice violations"
            )
        
        # Specific recommendations based on score
        if assessment.security_score < 0.8:
            assessment.recommendations.append(
                "🔒 Improve security posture by enabling HTTPS, using managed identities, and implementing proper secrets management"
            )
        
        if assessment.reliability_score < 0.8:
            assessment.recommendations.append(
                "🛡️ Enhance reliability with backup configuration, health checks, and high availability setup"
            )
        
        if assessment.operational_excellence_score < 0.8:
            assessment.recommendations.append(
                "📊 Improve operations with consistent tagging, monitoring setup, and diagnostic configuration"
            )
        
        if assessment.cost_optimization_score < 0.8:
            assessment.recommendations.append(
                "💰 Optimize costs by right-sizing resources and considering reserved capacity"
            )
        
        if assessment.performance_efficiency_score < 0.8:
            assessment.recommendations.append(
                "⚡ Enhance performance with caching, CDN usage, and appropriate SKU selection"
            )
    
    def generate_assessment_report(self, assessment: WellArchitectedAssessment) -> str:
        """Generate a detailed assessment report."""
        
        lines = []
        
        # Header
        lines.append("# Azure Well-Architected Framework Assessment")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().isoformat()}")
        lines.append(f"**Overall Score:** {assessment.overall_score:.2f}/1.00")
        lines.append("")
        
        # Pillar scores
        lines.append("## Pillar Scores")
        lines.append("")
        lines.append(f"- **Reliability:** {assessment.reliability_score:.2f}/1.00")
        lines.append(f"- **Security:** {assessment.security_score:.2f}/1.00") 
        lines.append(f"- **Cost Optimization:** {assessment.cost_optimization_score:.2f}/1.00")
        lines.append(f"- **Operational Excellence:** {assessment.operational_excellence_score:.2f}/1.00")
        lines.append(f"- **Performance Efficiency:** {assessment.performance_efficiency_score:.2f}/1.00")
        lines.append("")
        
        # Violations
        if assessment.violations:
            lines.append("## Issues Found")
            lines.append("")
            
            # Group by severity
            errors = [v for v in assessment.violations if v.severity == "error"]
            warnings = [v for v in assessment.violations if v.severity == "warning"]
            infos = [v for v in assessment.violations if v.severity == "info"]
            
            if errors:
                lines.append("### 🚨 Critical Issues")
                lines.append("")
                for violation in errors:
                    lines.append(f"- **{violation.resource_name}** ({violation.resource_type}): {violation.message}")
                    if violation.suggestion:
                        lines.append(f"  - *Suggestion:* {violation.suggestion}")
                lines.append("")
            
            if warnings:
                lines.append("### ⚠️ Warnings")
                lines.append("")
                for violation in warnings:
                    lines.append(f"- **{violation.resource_name}** ({violation.resource_type}): {violation.message}")
                    if violation.suggestion:
                        lines.append(f"  - *Suggestion:* {violation.suggestion}")
                lines.append("")
            
            if infos:
                lines.append("### ℹ️ Recommendations")
                lines.append("")
                for violation in infos:
                    lines.append(f"- **{violation.resource_name}** ({violation.resource_type}): {violation.message}")
                    if violation.suggestion:
                        lines.append(f"  - *Suggestion:* {violation.suggestion}")
                lines.append("")
        
        # Recommendations
        if assessment.recommendations:
            lines.append("## Key Recommendations")
            lines.append("")
            for rec in assessment.recommendations:
                lines.append(f"- {rec}")
            lines.append("")
        
        return "\n".join(lines)


# Export main classes
__all__ = ["BestPracticesValidator", "WellArchitectedAssessment", "BestPracticeViolation"]