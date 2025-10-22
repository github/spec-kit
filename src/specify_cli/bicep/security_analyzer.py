"""
Security analysis and compliance validation for Azure Bicep templates.

This module provides comprehensive security scanning, compliance checking,
and security best practices validation for Azure infrastructure deployments.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import json
import re
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SeverityLevel(str, Enum):
    """Security finding severity levels."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks."""
    
    CIS_AZURE = "cis_azure"
    NIST_CSF = "nist_csf"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    GDPR = "gdpr"


class SecurityCategory(str, Enum):
    """Security finding categories."""
    
    IDENTITY_ACCESS = "identity_access"
    DATA_PROTECTION = "data_protection"
    NETWORK_SECURITY = "network_security"
    LOGGING_MONITORING = "logging_monitoring"
    CONFIGURATION = "configuration"
    ENCRYPTION = "encryption"
    BACKUP_RECOVERY = "backup_recovery"
    COMPLIANCE = "compliance"


@dataclass
class SecurityFinding:
    """A security finding from analysis."""
    
    id: str
    title: str
    description: str
    severity: SeverityLevel
    category: SecurityCategory
    
    # Location information
    resource_name: str
    resource_type: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    
    # Compliance mappings
    compliance_frameworks: List[ComplianceFramework] = field(default_factory=list)
    control_ids: List[str] = field(default_factory=list)
    
    # Remediation
    remediation_steps: List[str] = field(default_factory=list)
    remediation_difficulty: str = "medium"  # low, medium, high
    
    # Evidence
    current_configuration: Dict[str, Any] = field(default_factory=dict)
    recommended_configuration: Dict[str, Any] = field(default_factory=dict)
    
    # Risk assessment
    risk_score: int = 0  # 0-100
    impact_description: str = ""
    
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ComplianceReport:
    """Compliance assessment report."""
    
    framework: ComplianceFramework
    overall_score: float  # 0-100
    
    # Control status
    passed_controls: int = 0
    failed_controls: int = 0
    not_applicable_controls: int = 0
    
    # Findings by control
    control_findings: Dict[str, List[SecurityFinding]] = field(default_factory=dict)
    
    # Summary
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    
    def calculate_scores(self):
        """Calculate compliance scores."""
        total_controls = self.passed_controls + self.failed_controls
        if total_controls > 0:
            self.overall_score = (self.passed_controls / total_controls) * 100
        else:
            self.overall_score = 0


@dataclass
class SecurityAssessment:
    """Complete security assessment results."""
    
    deployment_name: str
    timestamp: datetime
    
    # Findings
    findings: List[SecurityFinding] = field(default_factory=list)
    
    # Compliance reports
    compliance_reports: Dict[ComplianceFramework, ComplianceReport] = field(default_factory=dict)
    
    # Summary statistics
    total_resources_scanned: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    info_findings: int = 0
    
    # Risk metrics
    overall_risk_score: float = 0.0  # 0-100
    security_posture: str = "unknown"  # excellent, good, fair, poor, critical
    
    def calculate_summary(self):
        """Calculate summary statistics."""
        severity_counts = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 0,
            SeverityLevel.MEDIUM: 0,
            SeverityLevel.LOW: 0,
            SeverityLevel.INFO: 0
        }
        
        total_risk_score = 0
        for finding in self.findings:
            severity_counts[finding.severity] += 1
            total_risk_score += finding.risk_score
        
        self.critical_findings = severity_counts[SeverityLevel.CRITICAL]
        self.high_findings = severity_counts[SeverityLevel.HIGH]
        self.medium_findings = severity_counts[SeverityLevel.MEDIUM]
        self.low_findings = severity_counts[SeverityLevel.LOW]
        self.info_findings = severity_counts[SeverityLevel.INFO]
        
        # Calculate overall risk score
        if self.findings:
            self.overall_risk_score = total_risk_score / len(self.findings)
        
        # Determine security posture
        if self.critical_findings > 0:
            self.security_posture = "critical"
        elif self.high_findings > 5 or self.overall_risk_score > 80:
            self.security_posture = "poor"
        elif self.high_findings > 2 or self.overall_risk_score > 60:
            self.security_posture = "fair"
        elif self.medium_findings > 10 or self.overall_risk_score > 30:
            self.security_posture = "good"
        else:
            self.security_posture = "excellent"
    
    def get_findings_by_severity(self, severity: SeverityLevel) -> List[SecurityFinding]:
        """Get findings by severity level."""
        return [f for f in self.findings if f.severity == severity]
    
    def get_findings_by_category(self, category: SecurityCategory) -> List[SecurityFinding]:
        """Get findings by security category."""
        return [f for f in self.findings if f.category == category]


class SecurityAnalyzer:
    """
    Azure security analysis and compliance validation engine.
    
    Provides comprehensive security scanning, compliance checking, and
    security best practices validation for Azure infrastructure deployments.
    """
    
    def __init__(self):
        # Initialize security rules database
        self.security_rules = self._initialize_security_rules()
        
        # Initialize compliance frameworks
        self.compliance_frameworks = self._initialize_compliance_frameworks()
        
        # Initialize resource scanners
        self.resource_scanners = self._initialize_resource_scanners()
    
    async def analyze_deployment_security(
        self,
        resources: List[Dict[str, Any]],
        deployment_name: str = "deployment",
        compliance_frameworks: Optional[List[ComplianceFramework]] = None
    ) -> SecurityAssessment:
        """
        Perform comprehensive security analysis of a deployment.
        
        Args:
            resources: List of Azure resource definitions
            deployment_name: Name of the deployment
            compliance_frameworks: Compliance frameworks to check against
            
        Returns:
            Complete security assessment
        """
        logger.info(f"Starting security analysis for deployment '{deployment_name}'")
        
        assessment = SecurityAssessment(
            deployment_name=deployment_name,
            timestamp=datetime.utcnow()
        )
        
        assessment.total_resources_scanned = len(resources)
        
        # Analyze each resource
        for resource in resources:
            resource_findings = await self._analyze_resource_security(resource)
            assessment.findings.extend(resource_findings)
        
        # Run compliance checks if frameworks specified
        if compliance_frameworks:
            for framework in compliance_frameworks:
                compliance_report = await self._generate_compliance_report(
                    assessment.findings, framework
                )
                assessment.compliance_reports[framework] = compliance_report
        
        # Calculate summary statistics
        assessment.calculate_summary()
        
        logger.info(
            f"Security analysis completed: {len(assessment.findings)} findings "
            f"({assessment.critical_findings} critical, {assessment.high_findings} high)"
        )
        
        return assessment
    
    async def _analyze_resource_security(
        self, 
        resource: Dict[str, Any]
    ) -> List[SecurityFinding]:
        """Analyze security of a single resource."""
        resource_type = resource.get('type', 'unknown')
        resource_name = resource.get('name', 'unnamed')
        properties = resource.get('properties', {})
        
        findings = []
        
        # Get applicable security rules for this resource type
        rules = self.security_rules.get(resource_type, [])
        
        for rule in rules:
            try:
                if self._evaluate_security_rule(rule, resource):
                    finding = self._create_finding_from_rule(rule, resource)
                    findings.append(finding)
            except Exception as e:
                logger.warning(f"Error evaluating rule {rule.get('id')} for {resource_name}: {e}")
        
        # Run resource-specific scanners
        scanner = self.resource_scanners.get(resource_type)
        if scanner:
            try:
                scanner_findings = await scanner(resource)
                findings.extend(scanner_findings)
            except Exception as e:
                logger.warning(f"Error running scanner for {resource_type}: {e}")
        
        return findings
    
    def _evaluate_security_rule(
        self, 
        rule: Dict[str, Any], 
        resource: Dict[str, Any]
    ) -> bool:
        """Evaluate if a security rule applies to a resource."""
        conditions = rule.get('conditions', [])
        
        for condition in conditions:
            if not self._evaluate_condition(condition, resource):
                return False
        
        return True
    
    def _evaluate_condition(
        self, 
        condition: Dict[str, Any], 
        resource: Dict[str, Any]
    ) -> bool:
        """Evaluate a single condition."""
        condition_type = condition.get('type')
        path = condition.get('path', '')
        expected_value = condition.get('value')
        operator = condition.get('operator', 'equals')
        
        # Get actual value from resource
        actual_value = self._get_nested_value(resource, path)
        
        # Evaluate based on operator
        if operator == 'equals':
            return actual_value == expected_value
        elif operator == 'not_equals':
            return actual_value != expected_value
        elif operator == 'exists':
            return actual_value is not None
        elif operator == 'not_exists':
            return actual_value is None
        elif operator == 'contains':
            return expected_value in str(actual_value) if actual_value else False
        elif operator == 'not_contains':
            return expected_value not in str(actual_value) if actual_value else True
        elif operator == 'in':
            return actual_value in expected_value if isinstance(expected_value, list) else False
        elif operator == 'not_in':
            return actual_value not in expected_value if isinstance(expected_value, list) else True
        
        return False
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from dictionary using dot notation path."""
        if not path:
            return data
        
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _create_finding_from_rule(
        self, 
        rule: Dict[str, Any], 
        resource: Dict[str, Any]
    ) -> SecurityFinding:
        """Create security finding from rule and resource."""
        
        resource_name = resource.get('name', 'unnamed')
        resource_type = resource.get('type', 'unknown')
        
        # Calculate risk score
        severity = SeverityLevel(rule.get('severity', SeverityLevel.MEDIUM))
        base_score = {
            SeverityLevel.CRITICAL: 90,
            SeverityLevel.HIGH: 70,
            SeverityLevel.MEDIUM: 50,
            SeverityLevel.LOW: 30,
            SeverityLevel.INFO: 10
        }[severity]
        
        return SecurityFinding(
            id=f"{resource_name}_{rule['id']}",
            title=rule['title'].format(resource_name=resource_name),
            description=rule['description'],
            severity=severity,
            category=SecurityCategory(rule.get('category', SecurityCategory.CONFIGURATION)),
            resource_name=resource_name,
            resource_type=resource_type,
            compliance_frameworks=rule.get('compliance_frameworks', []),
            control_ids=rule.get('control_ids', []),
            remediation_steps=rule.get('remediation_steps', []),
            remediation_difficulty=rule.get('remediation_difficulty', 'medium'),
            current_configuration=resource.get('properties', {}),
            recommended_configuration=rule.get('recommended_configuration', {}),
            risk_score=base_score,
            impact_description=rule.get('impact_description', ''),
        )
    
    async def _generate_compliance_report(
        self,
        findings: List[SecurityFinding],
        framework: ComplianceFramework
    ) -> ComplianceReport:
        """Generate compliance report for specific framework."""
        
        report = ComplianceReport(framework=framework)
        
        # Get framework controls
        framework_controls = self.compliance_frameworks.get(framework, {})
        
        # Group findings by control
        for finding in findings:
            if framework in finding.compliance_frameworks:
                for control_id in finding.control_ids:
                    if control_id not in report.control_findings:
                        report.control_findings[control_id] = []
                    report.control_findings[control_id].append(finding)
        
        # Calculate control status
        for control_id in framework_controls.keys():
            if control_id in report.control_findings:
                report.failed_controls += 1
            else:
                report.passed_controls += 1
        
        # Count findings by severity
        for finding in findings:
            if framework in finding.compliance_frameworks:
                if finding.severity == SeverityLevel.CRITICAL:
                    report.critical_findings += 1
                elif finding.severity == SeverityLevel.HIGH:
                    report.high_findings += 1
                elif finding.severity == SeverityLevel.MEDIUM:
                    report.medium_findings += 1
                elif finding.severity == SeverityLevel.LOW:
                    report.low_findings += 1
        
        # Calculate overall score
        report.calculate_scores()
        
        return report
    
    def _initialize_security_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize security rules database."""
        return {
            'Microsoft.Web/sites': [
                {
                    'id': 'https_only',
                    'title': 'HTTPS Only not enforced for {resource_name}',
                    'description': 'Web app should enforce HTTPS only to ensure secure communications',
                    'severity': SeverityLevel.HIGH,
                    'category': SecurityCategory.NETWORK_SECURITY,
                    'compliance_frameworks': [ComplianceFramework.CIS_AZURE, ComplianceFramework.SOC2],
                    'control_ids': ['CIS-9.1', 'SOC2-CC6.1'],
                    'conditions': [
                        {
                            'type': 'property_check',
                            'path': 'properties.httpsOnly',
                            'operator': 'not_equals',
                            'value': True
                        }
                    ],
                    'remediation_steps': [
                        'Navigate to App Service configuration',
                        'Enable "HTTPS Only" setting',
                        'Update application URLs to use HTTPS',
                        'Test application functionality'
                    ],
                    'recommended_configuration': {
                        'httpsOnly': True
                    },
                    'impact_description': 'Traffic may be intercepted or modified in transit'
                },
                {
                    'id': 'min_tls_version',
                    'title': 'Minimum TLS version not configured for {resource_name}',
                    'description': 'Web app should enforce minimum TLS version 1.2',
                    'severity': SeverityLevel.MEDIUM,
                    'category': SecurityCategory.ENCRYPTION,
                    'compliance_frameworks': [ComplianceFramework.PCI_DSS, ComplianceFramework.HIPAA],
                    'control_ids': ['PCI-4.1', 'HIPAA-164.312'],
                    'conditions': [
                        {
                            'type': 'property_check',
                            'path': 'properties.siteConfig.minTlsVersion',
                            'operator': 'not_in',
                            'value': ['1.2', '1.3']
                        }
                    ],
                    'remediation_steps': [
                        'Navigate to TLS/SSL settings',
                        'Set minimum TLS version to 1.2 or higher',
                        'Test client compatibility'
                    ],
                    'recommended_configuration': {
                        'siteConfig': {'minTlsVersion': '1.2'}
                    }
                }
            ],
            'Microsoft.Storage/storageAccounts': [
                {
                    'id': 'secure_transfer',
                    'title': 'Secure transfer not required for {resource_name}',
                    'description': 'Storage account should require secure transfer (HTTPS/SMB 3.0)',
                    'severity': SeverityLevel.HIGH,
                    'category': SecurityCategory.DATA_PROTECTION,
                    'compliance_frameworks': [ComplianceFramework.CIS_AZURE, ComplianceFramework.SOC2],
                    'control_ids': ['CIS-3.1', 'SOC2-CC6.1'],
                    'conditions': [
                        {
                            'type': 'property_check',
                            'path': 'properties.supportsHttpsTrafficOnly',
                            'operator': 'not_equals',
                            'value': True
                        }
                    ],
                    'remediation_steps': [
                        'Enable "Secure transfer required" setting',
                        'Update client applications to use HTTPS',
                        'Test data access functionality'
                    ],
                    'recommended_configuration': {
                        'supportsHttpsTrafficOnly': True
                    }
                },
                {
                    'id': 'blob_public_access',
                    'title': 'Public blob access allowed for {resource_name}',
                    'description': 'Storage account should not allow public blob access',
                    'severity': SeverityLevel.CRITICAL,
                    'category': SecurityCategory.DATA_PROTECTION,
                    'compliance_frameworks': [ComplianceFramework.CIS_AZURE, ComplianceFramework.GDPR],
                    'control_ids': ['CIS-3.7', 'GDPR-32'],
                    'conditions': [
                        {
                            'type': 'property_check',
                            'path': 'properties.allowBlobPublicAccess',
                            'operator': 'equals',
                            'value': True
                        }
                    ],
                    'remediation_steps': [
                        'Disable "Allow Blob public access"',
                        'Review existing public containers',
                        'Implement proper access controls',
                        'Update application access patterns'
                    ],
                    'recommended_configuration': {
                        'allowBlobPublicAccess': False
                    },
                    'impact_description': 'Sensitive data may be publicly accessible'
                }
            ],
            'Microsoft.KeyVault/vaults': [
                {
                    'id': 'soft_delete',
                    'title': 'Soft delete not enabled for {resource_name}',
                    'description': 'Key Vault should have soft delete enabled for data protection',
                    'severity': SeverityLevel.MEDIUM,
                    'category': SecurityCategory.DATA_PROTECTION,
                    'compliance_frameworks': [ComplianceFramework.CIS_AZURE],
                    'control_ids': ['CIS-8.1'],
                    'conditions': [
                        {
                            'type': 'property_check',
                            'path': 'properties.enableSoftDelete',
                            'operator': 'not_equals',
                            'value': True
                        }
                    ],
                    'remediation_steps': [
                        'Enable soft delete on Key Vault',
                        'Configure retention period',
                        'Update backup procedures'
                    ],
                    'recommended_configuration': {
                        'enableSoftDelete': True,
                        'softDeleteRetentionInDays': 90
                    }
                },
                {
                    'id': 'network_access',
                    'title': 'Network access not restricted for {resource_name}',
                    'description': 'Key Vault should restrict network access',
                    'severity': SeverityLevel.HIGH,
                    'category': SecurityCategory.NETWORK_SECURITY,
                    'compliance_frameworks': [ComplianceFramework.CIS_AZURE, ComplianceFramework.NIST_CSF],
                    'control_ids': ['CIS-8.2', 'NIST-AC-3'],
                    'conditions': [
                        {
                            'type': 'property_check',
                            'path': 'properties.publicNetworkAccess',
                            'operator': 'equals',
                            'value': 'Enabled'
                        }
                    ],
                    'remediation_steps': [
                        'Configure network access restrictions',
                        'Set up private endpoints if needed',
                        'Configure IP access rules',
                        'Test application connectivity'
                    ],
                    'recommended_configuration': {
                        'publicNetworkAccess': 'Disabled'
                    }
                }
            ],
            'Microsoft.Sql/servers': [
                {
                    'id': 'azure_ad_admin',
                    'title': 'Azure AD administrator not configured for {resource_name}',
                    'description': 'SQL Server should have Azure AD administrator configured',
                    'severity': SeverityLevel.HIGH,
                    'category': SecurityCategory.IDENTITY_ACCESS,
                    'compliance_frameworks': [ComplianceFramework.CIS_AZURE, ComplianceFramework.SOC2],
                    'control_ids': ['CIS-4.1', 'SOC2-CC6.1'],
                    'conditions': [
                        {
                            'type': 'property_check',
                            'path': 'properties.administrators',
                            'operator': 'not_exists'
                        }
                    ],
                    'remediation_steps': [
                        'Configure Azure AD administrator',
                        'Assign appropriate permissions',
                        'Update connection strings if needed',
                        'Test authentication'
                    ]
                },
                {
                    'id': 'firewall_rules',
                    'title': 'Overly permissive firewall rules for {resource_name}',
                    'description': 'SQL Server firewall should not allow access from 0.0.0.0',
                    'severity': SeverityLevel.CRITICAL,
                    'category': SecurityCategory.NETWORK_SECURITY,
                    'compliance_frameworks': [ComplianceFramework.CIS_AZURE, ComplianceFramework.PCI_DSS],
                    'control_ids': ['CIS-4.2', 'PCI-1.3'],
                    'conditions': [
                        {
                            'type': 'property_check',
                            'path': 'properties.firewallRules',
                            'operator': 'contains',
                            'value': '0.0.0.0'
                        }
                    ],
                    'remediation_steps': [
                        'Remove overly permissive firewall rules',
                        'Configure specific IP ranges',
                        'Use virtual network rules if possible',
                        'Test connectivity from allowed sources'
                    ],
                    'impact_description': 'Database may be accessible from any internet location'
                }
            ]
        }
    
    def _initialize_compliance_frameworks(self) -> Dict[ComplianceFramework, Dict[str, Any]]:
        """Initialize compliance framework definitions."""
        return {
            ComplianceFramework.CIS_AZURE: {
                'CIS-3.1': {
                    'title': 'Ensure that "Secure transfer required" is set to "Enabled"',
                    'description': 'Enable secure transfer for Azure Storage'
                },
                'CIS-3.7': {
                    'title': 'Ensure that "Allow Blob public access" is set to "Disabled"',
                    'description': 'Disable public blob access for storage accounts'
                },
                'CIS-4.1': {
                    'title': 'Ensure that Azure Active Directory Admin is Configured',
                    'description': 'Configure Azure AD admin for SQL servers'
                },
                'CIS-4.2': {
                    'title': 'Ensure that "Allow access to Azure services" is disabled',
                    'description': 'Restrict SQL server firewall access'
                },
                'CIS-8.1': {
                    'title': 'Ensure that the expiration date is set on all Secrets',
                    'description': 'Set expiration dates for Key Vault secrets'
                },
                'CIS-8.2': {
                    'title': 'Ensure that the Key Vault is recoverable',
                    'description': 'Enable Key Vault soft delete and purge protection'
                },
                'CIS-9.1': {
                    'title': 'Ensure that HTTPS is enabled for App Services',
                    'description': 'Enforce HTTPS for web applications'
                }
            },
            ComplianceFramework.SOC2: {
                'SOC2-CC6.1': {
                    'title': 'Logical and Physical Access Controls',
                    'description': 'Implement appropriate access controls'
                }
            },
            ComplianceFramework.PCI_DSS: {
                'PCI-1.3': {
                    'title': 'Prohibit direct public access between the Internet and any system component',
                    'description': 'Restrict network access to cardholder data environment'
                },
                'PCI-4.1': {
                    'title': 'Use strong cryptography and security protocols',
                    'description': 'Implement strong encryption for data transmission'
                }
            },
            ComplianceFramework.HIPAA: {
                'HIPAA-164.312': {
                    'title': 'Transmission Security',
                    'description': 'Implement technical safeguards for ePHI transmission'
                }
            },
            ComplianceFramework.GDPR: {
                'GDPR-32': {
                    'title': 'Security of Processing',
                    'description': 'Implement appropriate technical and organizational measures'
                }
            },
            ComplianceFramework.NIST_CSF: {
                'NIST-AC-3': {
                    'title': 'Access Enforcement',
                    'description': 'Enforce approved authorizations for logical access'
                }
            }
        }
    
    def _initialize_resource_scanners(self) -> Dict[str, Any]:
        """Initialize resource-specific security scanners."""
        return {
            'Microsoft.Web/sites': self._scan_web_app,
            'Microsoft.Storage/storageAccounts': self._scan_storage_account,
            'Microsoft.KeyVault/vaults': self._scan_key_vault,
            'Microsoft.Sql/servers': self._scan_sql_server
        }
    
    async def _scan_web_app(self, resource: Dict[str, Any]) -> List[SecurityFinding]:
        """Specialized scanner for web apps."""
        findings = []
        resource_name = resource.get('name', 'unnamed')
        properties = resource.get('properties', {})
        
        # Check for custom domains without SSL
        host_names = properties.get('hostNames', [])
        for hostname in host_names:
            if not hostname.endswith('.azurewebsites.net'):
                # Custom domain should have SSL certificate
                findings.append(SecurityFinding(
                    id=f"{resource_name}_custom_domain_ssl",
                    title=f"Custom domain {hostname} may not have SSL certificate",
                    description="Custom domains should have valid SSL certificates configured",
                    severity=SeverityLevel.MEDIUM,
                    category=SecurityCategory.ENCRYPTION,
                    resource_name=resource_name,
                    resource_type=resource['type'],
                    remediation_steps=[
                        "Purchase or import SSL certificate",
                        "Bind certificate to custom domain",
                        "Test HTTPS access"
                    ],
                    risk_score=60
                ))
        
        return findings
    
    async def _scan_storage_account(self, resource: Dict[str, Any]) -> List[SecurityFinding]:
        """Specialized scanner for storage accounts."""
        findings = []
        resource_name = resource.get('name', 'unnamed')
        properties = resource.get('properties', {})
        
        # Check encryption settings
        encryption = properties.get('encryption', {})
        if not encryption.get('services', {}).get('blob', {}).get('enabled', False):
            findings.append(SecurityFinding(
                id=f"{resource_name}_blob_encryption",
                title=f"Blob encryption not enabled for {resource_name}",
                description="Storage account should have blob encryption enabled",
                severity=SeverityLevel.HIGH,
                category=SecurityCategory.ENCRYPTION,
                resource_name=resource_name,
                resource_type=resource['type'],
                remediation_steps=[
                    "Enable blob service encryption",
                    "Verify encryption is working",
                    "Update compliance documentation"
                ],
                risk_score=75
            ))
        
        return findings
    
    async def _scan_key_vault(self, resource: Dict[str, Any]) -> List[SecurityFinding]:
        """Specialized scanner for Key Vault."""
        findings = []
        resource_name = resource.get('name', 'unnamed')
        properties = resource.get('properties', {})
        
        # Check access policies
        access_policies = properties.get('accessPolicies', [])
        for i, policy in enumerate(access_policies):
            permissions = policy.get('permissions', {})
            
            # Check for overly broad permissions
            key_permissions = permissions.get('keys', [])
            if '*' in key_permissions or 'all' in key_permissions:
                findings.append(SecurityFinding(
                    id=f"{resource_name}_broad_key_permissions_{i}",
                    title=f"Overly broad key permissions in {resource_name}",
                    description="Access policy grants excessive key permissions",
                    severity=SeverityLevel.MEDIUM,
                    category=SecurityCategory.IDENTITY_ACCESS,
                    resource_name=resource_name,
                    resource_type=resource['type'],
                    remediation_steps=[
                        "Review access policy permissions",
                        "Apply principle of least privilege",
                        "Update access policies with specific permissions"
                    ],
                    risk_score=65
                ))
        
        return findings
    
    async def _scan_sql_server(self, resource: Dict[str, Any]) -> List[SecurityFinding]:
        """Specialized scanner for SQL servers."""
        findings = []
        resource_name = resource.get('name', 'unnamed')
        properties = resource.get('properties', {})
        
        # Check for SQL authentication
        if properties.get('administratorLogin'):
            findings.append(SecurityFinding(
                id=f"{resource_name}_sql_auth",
                title=f"SQL authentication enabled for {resource_name}",
                description="Consider using only Azure AD authentication for enhanced security",
                severity=SeverityLevel.LOW,
                category=SecurityCategory.IDENTITY_ACCESS,
                resource_name=resource_name,
                resource_type=resource['type'],
                remediation_steps=[
                    "Evaluate if SQL authentication is necessary",
                    "Configure Azure AD-only authentication if possible",
                    "Implement strong password policies if SQL auth required"
                ],
                risk_score=40
            ))
        
        return findings