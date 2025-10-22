"""
Interactive architecture review system for Bicep templates.

This module provides comprehensive architecture analysis, compliance scoring,
optimization recommendations, cost analysis, and performance metrics.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
import re
from dataclasses import dataclass, field
from enum import Enum

from .models.project_analysis import ProjectAnalysisResult
from .models.template_update import TemplateUpdateManifest
from .best_practices_validator import BestPracticesValidator, ValidationResult

logger = logging.getLogger(__name__)


class ReviewScope(str, Enum):
    """Architecture review scopes."""
    
    COMPLIANCE = "compliance"
    COST = "cost" 
    PERFORMANCE = "performance"
    SECURITY = "security"
    RELIABILITY = "reliability"
    ALL = "all"


class OptimizationPriority(str, Enum):
    """Priority levels for optimization recommendations."""
    
    CRITICAL = "critical"    # Security issues, compliance violations
    HIGH = "high"           # Cost savings, performance improvements
    MEDIUM = "medium"       # Best practices, maintainability
    LOW = "low"            # Nice-to-have improvements


@dataclass
class CostAnalysis:
    """Cost analysis results for Azure resources."""
    
    estimated_monthly_cost: float
    cost_breakdown: Dict[str, float]
    cost_optimization_opportunities: List[Dict[str, Any]]
    cost_alerts: List[str]
    savings_potential: float
    
    def get_total_savings(self) -> float:
        """Calculate total potential savings."""
        return sum(opp.get('potential_savings', 0) for opp in self.cost_optimization_opportunities)


@dataclass
class PerformanceMetrics:
    """Performance analysis for Azure resources."""
    
    bottlenecks: List[Dict[str, Any]]
    scaling_recommendations: List[Dict[str, Any]]
    performance_score: float  # 0-100
    latency_analysis: Dict[str, Any]
    throughput_analysis: Dict[str, Any]
    resource_utilization: Dict[str, float]
    
    def get_critical_bottlenecks(self) -> List[Dict[str, Any]]:
        """Get bottlenecks marked as critical."""
        return [b for b in self.bottlenecks if b.get('severity') == 'critical']


@dataclass
class OptimizationRecommendation:
    """Single optimization recommendation."""
    
    id: str
    title: str
    description: str
    category: str  # cost, performance, security, compliance
    priority: OptimizationPriority
    impact: str  # high, medium, low
    effort: str  # high, medium, low
    
    # Implementation details
    resources_affected: List[str]
    implementation_steps: List[str]
    estimated_savings: Optional[float] = None
    performance_improvement: Optional[str] = None
    compliance_benefit: Optional[str] = None
    
    # Risk assessment
    risk_level: str = "low"  # high, medium, low
    rollback_plan: Optional[str] = None
    
    def get_roi_score(self) -> float:
        """Calculate ROI score based on impact vs effort."""
        impact_scores = {'high': 3, 'medium': 2, 'low': 1}
        effort_scores = {'high': 1, 'medium': 2, 'low': 3}
        
        impact = impact_scores.get(self.impact, 1)
        effort = effort_scores.get(self.effort, 1)
        
        return (impact * effort) / 3.0  # Normalize to 0-3 scale


@dataclass
class ArchitectureReviewResult:
    """Complete architecture review results."""
    
    # Basic information
    project_path: Path
    review_scope: ReviewScope
    timestamp: datetime
    
    # Scoring
    overall_score: float  # 0-100
    compliance_score: float
    cost_efficiency_score: float
    performance_score: float
    security_score: float
    reliability_score: float
    
    # Analysis results
    cost_analysis: Optional[CostAnalysis] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    validation_results: List[ValidationResult] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[OptimizationRecommendation] = field(default_factory=list)
    
    # Issues and alerts
    critical_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def get_prioritized_recommendations(self) -> List[OptimizationRecommendation]:
        """Get recommendations sorted by ROI and priority."""
        return sorted(
            self.recommendations,
            key=lambda r: (r.priority.value, -r.get_roi_score()),
            reverse=False
        )
    
    def get_total_potential_savings(self) -> float:
        """Calculate total potential cost savings."""
        return sum(r.estimated_savings or 0 for r in self.recommendations)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of review results."""
        return {
            'overall_score': self.overall_score,
            'total_recommendations': len(self.recommendations),
            'critical_issues': len(self.critical_issues),
            'potential_savings': self.get_total_potential_savings(),
            'review_scope': self.review_scope.value,
            'timestamp': self.timestamp.isoformat()
        }


class ArchitectureReviewer:
    """
    Interactive architecture review system for Bicep templates.
    
    Provides comprehensive analysis including compliance scoring, cost optimization,
    performance recommendations, and security assessment.
    """
    
    def __init__(self, best_practices_validator: BestPracticesValidator):
        self.validator = best_practices_validator
        
        # Cost optimization rules
        self.cost_rules = self._initialize_cost_rules()
        
        # Performance rules
        self.performance_rules = self._initialize_performance_rules()
        
        # Resource pricing (simplified for demo - would use Azure Pricing API)
        self.resource_pricing = self._initialize_resource_pricing()
    
    async def conduct_review(
        self,
        project_path: Path,
        templates: Dict[str, str],
        parameters: Dict[str, Any],
        scope: ReviewScope = ReviewScope.ALL
    ) -> ArchitectureReviewResult:
        """
        Conduct comprehensive architecture review.
        
        Args:
            project_path: Path to project root
            templates: Dictionary of template names to content
            parameters: Template parameters
            scope: Review scope (compliance, cost, performance, all)
            
        Returns:
            Complete review results with recommendations
        """
        logger.info(f"Starting architecture review with scope: {scope}")
        
        result = ArchitectureReviewResult(
            project_path=project_path,
            review_scope=scope,
            timestamp=datetime.utcnow(),
            overall_score=0.0,
            compliance_score=0.0,
            cost_efficiency_score=0.0,
            performance_score=0.0,
            security_score=0.0,
            reliability_score=0.0
        )
        
        # Validate templates with best practices
        await self._validate_templates(templates, parameters, result)
        
        # Conduct scope-specific analysis
        if scope in [ReviewScope.COST, ReviewScope.ALL]:
            await self._analyze_costs(templates, parameters, result)
        
        if scope in [ReviewScope.PERFORMANCE, ReviewScope.ALL]:
            await self._analyze_performance(templates, parameters, result)
        
        if scope in [ReviewScope.COMPLIANCE, ReviewScope.ALL]:
            await self._analyze_compliance(templates, parameters, result)
        
        if scope in [ReviewScope.SECURITY, ReviewScope.ALL]:
            await self._analyze_security(templates, parameters, result)
        
        if scope in [ReviewScope.RELIABILITY, ReviewScope.ALL]:
            await self._analyze_reliability(templates, parameters, result)
        
        # Generate recommendations
        await self._generate_recommendations(templates, parameters, result)
        
        # Calculate overall score
        result.overall_score = self._calculate_overall_score(result)
        
        logger.info(f"Architecture review completed with overall score: {result.overall_score:.1f}/100")
        
        return result
    
    async def _validate_templates(
        self,
        templates: Dict[str, str],
        parameters: Dict[str, Any],
        result: ArchitectureReviewResult
    ):
        """Validate templates using best practices validator."""
        for template_name, template_content in templates.items():
            validation_result = await self.validator.validate_template(
                template_content, parameters
            )
            result.validation_results.append(validation_result)
            
            # Extract critical issues
            result.critical_issues.extend(validation_result.get_critical_issues())
            result.warnings.extend(validation_result.get_warnings())
    
    async def _analyze_costs(
        self,
        templates: Dict[str, str],
        parameters: Dict[str, Any],
        result: ArchitectureReviewResult
    ):
        """Analyze cost implications and optimization opportunities."""
        logger.info("Analyzing cost implications...")
        
        total_cost = 0.0
        cost_breakdown = {}
        optimization_opportunities = []
        cost_alerts = []
        
        for template_name, template_content in templates.items():
            # Extract resources and estimate costs
            resources = self._extract_resources_from_template(template_content)
            
            for resource in resources:
                resource_type = resource.get('type', '')
                resource_name = resource.get('name', 'unnamed')
                properties = resource.get('properties', {})
                
                # Estimate monthly cost
                monthly_cost = self._estimate_resource_cost(resource_type, properties)
                total_cost += monthly_cost
                cost_breakdown[f"{resource_name} ({resource_type})"] = monthly_cost
                
                # Check for cost optimization opportunities
                optimizations = self._identify_cost_optimizations(resource_type, properties, resource_name)
                optimization_opportunities.extend(optimizations)
                
                # Generate cost alerts
                alerts = self._generate_cost_alerts(resource_type, properties, monthly_cost, resource_name)
                cost_alerts.extend(alerts)
        
        # Calculate potential savings
        savings_potential = sum(opp.get('potential_savings', 0) for opp in optimization_opportunities)
        
        result.cost_analysis = CostAnalysis(
            estimated_monthly_cost=total_cost,
            cost_breakdown=cost_breakdown,
            cost_optimization_opportunities=optimization_opportunities,
            cost_alerts=cost_alerts,
            savings_potential=savings_potential
        )
        
        # Calculate cost efficiency score
        result.cost_efficiency_score = min(100, max(0, 100 - (len(optimization_opportunities) * 10)))
    
    async def _analyze_performance(
        self,
        templates: Dict[str, str],
        parameters: Dict[str, Any],
        result: ArchitectureReviewResult
    ):
        """Analyze performance characteristics and bottlenecks."""
        logger.info("Analyzing performance characteristics...")
        
        bottlenecks = []
        scaling_recommendations = []
        performance_score = 100.0
        
        for template_name, template_content in templates.items():
            resources = self._extract_resources_from_template(template_content)
            
            for resource in resources:
                resource_type = resource.get('type', '')
                resource_name = resource.get('name', 'unnamed')
                properties = resource.get('properties', {})
                
                # Identify performance bottlenecks
                resource_bottlenecks = self._identify_performance_bottlenecks(
                    resource_type, properties, resource_name
                )
                bottlenecks.extend(resource_bottlenecks)
                
                # Generate scaling recommendations
                scaling_recs = self._generate_scaling_recommendations(
                    resource_type, properties, resource_name
                )
                scaling_recommendations.extend(scaling_recs)
        
        # Calculate performance score
        performance_score -= len(bottlenecks) * 15
        performance_score = max(0, performance_score)
        
        result.performance_metrics = PerformanceMetrics(
            bottlenecks=bottlenecks,
            scaling_recommendations=scaling_recommendations,
            performance_score=performance_score,
            latency_analysis={},
            throughput_analysis={},
            resource_utilization={}
        )
        
        result.performance_score = performance_score
    
    async def _analyze_compliance(
        self,
        templates: Dict[str, str],
        parameters: Dict[str, Any],
        result: ArchitectureReviewResult
    ):
        """Analyze compliance with Azure Well-Architected Framework."""
        logger.info("Analyzing compliance...")
        
        compliance_score = 0.0
        total_checks = 0
        
        for validation_result in result.validation_results:
            compliance_score += validation_result.overall_score
            total_checks += 1
        
        if total_checks > 0:
            result.compliance_score = (compliance_score / total_checks) * 100
        else:
            result.compliance_score = 100.0
    
    async def _analyze_security(
        self,
        templates: Dict[str, str],
        parameters: Dict[str, Any],
        result: ArchitectureReviewResult
    ):
        """Analyze security posture and vulnerabilities."""
        logger.info("Analyzing security posture...")
        
        security_score = 100.0
        security_issues = []
        
        for template_name, template_content in templates.items():
            resources = self._extract_resources_from_template(template_content)
            
            for resource in resources:
                resource_type = resource.get('type', '')
                resource_name = resource.get('name', 'unnamed')
                properties = resource.get('properties', {})
                
                # Check security configurations
                issues = self._check_security_configurations(resource_type, properties, resource_name)
                security_issues.extend(issues)
        
        # Deduct points for security issues
        security_score -= len(security_issues) * 10
        result.security_score = max(0, security_score)
        
        # Add to critical issues if severe
        for issue in security_issues:
            if issue.get('severity') == 'critical':
                result.critical_issues.append(f"Security: {issue['description']}")
    
    async def _analyze_reliability(
        self,
        templates: Dict[str, str],
        parameters: Dict[str, Any],
        result: ArchitectureReviewResult
    ):
        """Analyze reliability and resilience patterns."""
        logger.info("Analyzing reliability...")
        
        reliability_score = 100.0
        reliability_issues = []
        
        for template_name, template_content in templates.items():
            resources = self._extract_resources_from_template(template_content)
            
            for resource in resources:
                resource_type = resource.get('type', '')
                resource_name = resource.get('name', 'unnamed')
                properties = resource.get('properties', {})
                
                # Check reliability patterns
                issues = self._check_reliability_patterns(resource_type, properties, resource_name)
                reliability_issues.extend(issues)
        
        reliability_score -= len(reliability_issues) * 12
        result.reliability_score = max(0, reliability_score)
    
    async def _generate_recommendations(
        self,
        templates: Dict[str, str],
        parameters: Dict[str, Any],
        result: ArchitectureReviewResult
    ):
        """Generate optimization recommendations based on analysis."""
        logger.info("Generating optimization recommendations...")
        
        recommendations = []
        
        # Cost optimization recommendations
        if result.cost_analysis:
            for opp in result.cost_analysis.cost_optimization_opportunities:
                rec = OptimizationRecommendation(
                    id=f"cost-{len(recommendations)}",
                    title=opp['title'],
                    description=opp['description'],
                    category='cost',
                    priority=OptimizationPriority(opp.get('priority', 'medium')),
                    impact=opp.get('impact', 'medium'),
                    effort=opp.get('effort', 'medium'),
                    resources_affected=opp.get('resources', []),
                    implementation_steps=opp.get('steps', []),
                    estimated_savings=opp.get('potential_savings', 0)
                )
                recommendations.append(rec)
        
        # Performance recommendations
        if result.performance_metrics:
            for rec_data in result.performance_metrics.scaling_recommendations:
                rec = OptimizationRecommendation(
                    id=f"perf-{len(recommendations)}",
                    title=rec_data['title'],
                    description=rec_data['description'],
                    category='performance',
                    priority=OptimizationPriority(rec_data.get('priority', 'medium')),
                    impact=rec_data.get('impact', 'medium'),
                    effort=rec_data.get('effort', 'medium'),
                    resources_affected=rec_data.get('resources', []),
                    implementation_steps=rec_data.get('steps', []),
                    performance_improvement=rec_data.get('improvement', 'Unknown')
                )
                recommendations.append(rec)
        
        # Compliance recommendations
        for validation_result in result.validation_results:
            for issue in validation_result.get_critical_issues():
                rec = OptimizationRecommendation(
                    id=f"compliance-{len(recommendations)}",
                    title=f"Address compliance issue: {issue}",
                    description=f"Resolve compliance violation: {issue}",
                    category='compliance',
                    priority=OptimizationPriority.CRITICAL,
                    impact='high',
                    effort='medium',
                    resources_affected=[],
                    implementation_steps=[f"Review and fix: {issue}"],
                    compliance_benefit='Improved compliance score'
                )
                recommendations.append(rec)
        
        result.recommendations = recommendations
    
    def _calculate_overall_score(self, result: ArchitectureReviewResult) -> float:
        """Calculate overall architecture score."""
        scores = []
        weights = []
        
        if result.review_scope in [ReviewScope.COMPLIANCE, ReviewScope.ALL]:
            scores.append(result.compliance_score)
            weights.append(0.25)
        
        if result.review_scope in [ReviewScope.COST, ReviewScope.ALL]:
            scores.append(result.cost_efficiency_score)
            weights.append(0.20)
        
        if result.review_scope in [ReviewScope.PERFORMANCE, ReviewScope.ALL]:
            scores.append(result.performance_score)
            weights.append(0.20)
        
        if result.review_scope in [ReviewScope.SECURITY, ReviewScope.ALL]:
            scores.append(result.security_score)
            weights.append(0.20)
        
        if result.review_scope in [ReviewScope.RELIABILITY, ReviewScope.ALL]:
            scores.append(result.reliability_score)
            weights.append(0.15)
        
        if not scores:
            return 0.0
        
        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        
        # Calculate weighted average
        weighted_score = sum(s * w for s, w in zip(scores, normalized_weights))
        
        # Apply penalty for critical issues
        penalty = min(50, len(result.critical_issues) * 10)
        
        return max(0, weighted_score - penalty)
    
    def _extract_resources_from_template(self, template_content: str) -> List[Dict[str, Any]]:
        """Extract resource definitions from Bicep template."""
        resources = []
        
        # Simple regex-based extraction for demo (real implementation would use proper Bicep parser)
        resource_pattern = r'resource\s+(\w+)\s+\'([^\']+)\'\s*=\s*\{([^}]+)\}'
        matches = re.finditer(resource_pattern, template_content, re.DOTALL)
        
        for match in matches:
            resource_name = match.group(1)
            resource_type = match.group(2)
            
            resources.append({
                'name': resource_name,
                'type': resource_type,
                'properties': {}  # Simplified for demo
            })
        
        return resources
    
    def _estimate_resource_cost(self, resource_type: str, properties: Dict[str, Any]) -> float:
        """Estimate monthly cost for a resource."""
        base_costs = self.resource_pricing.get(resource_type, 100.0)  # Default $100/month
        
        # Apply multipliers based on properties (simplified)
        multiplier = 1.0
        
        # Size-based multipliers
        if 'sku' in properties:
            sku = properties['sku']
            if 'Premium' in str(sku):
                multiplier *= 3.0
            elif 'Standard' in str(sku):
                multiplier *= 2.0
        
        return base_costs * multiplier
    
    def _identify_cost_optimizations(
        self, 
        resource_type: str, 
        properties: Dict[str, Any], 
        resource_name: str
    ) -> List[Dict[str, Any]]:
        """Identify cost optimization opportunities for a resource."""
        optimizations = []
        
        rules = self.cost_rules.get(resource_type, [])
        
        for rule in rules:
            if self._evaluate_cost_rule(rule, properties):
                optimizations.append({
                    'title': rule['title'].format(resource_name=resource_name),
                    'description': rule['description'],
                    'potential_savings': rule.get('savings', 0),
                    'priority': rule.get('priority', 'medium'),
                    'impact': rule.get('impact', 'medium'),
                    'effort': rule.get('effort', 'medium'),
                    'resources': [resource_name],
                    'steps': rule.get('steps', [])
                })
        
        return optimizations
    
    def _generate_cost_alerts(
        self, 
        resource_type: str, 
        properties: Dict[str, Any], 
        monthly_cost: float, 
        resource_name: str
    ) -> List[str]:
        """Generate cost alerts for expensive resources."""
        alerts = []
        
        # Alert for high-cost resources
        if monthly_cost > 1000:
            alerts.append(f"High cost resource: {resource_name} (${monthly_cost:.2f}/month)")
        
        # Resource-specific alerts
        if resource_type == 'Microsoft.Compute/virtualMachines':
            if monthly_cost > 500:
                alerts.append(f"Consider resizing VM {resource_name} to reduce costs")
        
        return alerts
    
    def _identify_performance_bottlenecks(
        self, 
        resource_type: str, 
        properties: Dict[str, Any], 
        resource_name: str
    ) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks for a resource."""
        bottlenecks = []
        
        rules = self.performance_rules.get(resource_type, [])
        
        for rule in rules:
            if self._evaluate_performance_rule(rule, properties):
                bottlenecks.append({
                    'resource': resource_name,
                    'type': rule['type'],
                    'description': rule['description'],
                    'severity': rule.get('severity', 'medium'),
                    'recommendation': rule.get('recommendation', '')
                })
        
        return bottlenecks
    
    def _generate_scaling_recommendations(
        self, 
        resource_type: str, 
        properties: Dict[str, Any], 
        resource_name: str
    ) -> List[Dict[str, Any]]:
        """Generate scaling recommendations for a resource."""
        recommendations = []
        
        # Basic scaling recommendations
        if resource_type == 'Microsoft.Web/serverfarms':
            recommendations.append({
                'title': f'Configure auto-scaling for {resource_name}',
                'description': 'Enable automatic scaling based on CPU and memory metrics',
                'priority': 'medium',
                'impact': 'high',
                'effort': 'low',
                'resources': [resource_name],
                'steps': ['Configure scale-out rules', 'Set performance counters', 'Test scaling behavior'],
                'improvement': '50% better load handling'
            })
        
        return recommendations
    
    def _check_security_configurations(
        self, 
        resource_type: str, 
        properties: Dict[str, Any], 
        resource_name: str
    ) -> List[Dict[str, Any]]:
        """Check security configurations for a resource."""
        issues = []
        
        # Basic security checks
        if resource_type == 'Microsoft.Storage/storageAccounts':
            issues.append({
                'resource': resource_name,
                'description': 'Storage account should use HTTPS only',
                'severity': 'high'
            })
        
        return issues
    
    def _check_reliability_patterns(
        self, 
        resource_type: str, 
        properties: Dict[str, Any], 
        resource_name: str
    ) -> List[Dict[str, Any]]:
        """Check reliability patterns for a resource."""
        issues = []
        
        # Basic reliability checks
        if resource_type in ['Microsoft.Web/sites', 'Microsoft.Sql/servers']:
            issues.append({
                'resource': resource_name,
                'description': 'Consider implementing backup and disaster recovery',
                'severity': 'medium'
            })
        
        return issues
    
    def _evaluate_cost_rule(self, rule: Dict[str, Any], properties: Dict[str, Any]) -> bool:
        """Evaluate if a cost rule applies to resource properties."""
        # Simplified evaluation for demo
        condition = rule.get('condition', {})
        
        if 'sku' in condition:
            return properties.get('sku') == condition['sku']
        
        return True  # Default to applicable
    
    def _evaluate_performance_rule(self, rule: Dict[str, Any], properties: Dict[str, Any]) -> bool:
        """Evaluate if a performance rule applies to resource properties."""
        # Simplified evaluation for demo
        return True
    
    def _initialize_cost_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize cost optimization rules."""
        return {
            'Microsoft.Compute/virtualMachines': [
                {
                    'title': 'Downsize VM {resource_name}',
                    'description': 'VM appears to be over-provisioned based on typical usage patterns',
                    'condition': {'sku': 'Standard_D4s_v3'},
                    'savings': 200,
                    'priority': 'high',
                    'impact': 'high',
                    'effort': 'low',
                    'steps': ['Analyze current usage', 'Resize to appropriate SKU', 'Monitor performance']
                }
            ],
            'Microsoft.Storage/storageAccounts': [
                {
                    'title': 'Optimize storage tier for {resource_name}',
                    'description': 'Consider using cool or archive tier for infrequently accessed data',
                    'savings': 50,
                    'priority': 'medium',
                    'impact': 'medium',
                    'effort': 'low',
                    'steps': ['Analyze access patterns', 'Configure lifecycle policies', 'Set appropriate storage tiers']
                }
            ]
        }
    
    def _initialize_performance_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize performance optimization rules."""
        return {
            'Microsoft.Web/sites': [
                {
                    'type': 'scaling',
                    'description': 'Web app may experience performance issues under load',
                    'severity': 'medium',
                    'recommendation': 'Configure auto-scaling rules based on CPU and memory metrics'
                }
            ],
            'Microsoft.Sql/servers/databases': [
                {
                    'type': 'indexing',
                    'description': 'Database may benefit from additional indexing',
                    'severity': 'low',
                    'recommendation': 'Review query patterns and add appropriate indexes'
                }
            ]
        }
    
    def _initialize_resource_pricing(self) -> Dict[str, float]:
        """Initialize simplified resource pricing (monthly costs in USD)."""
        return {
            'Microsoft.Web/sites': 50.0,
            'Microsoft.Web/serverfarms': 75.0,
            'Microsoft.Storage/storageAccounts': 25.0,
            'Microsoft.KeyVault/vaults': 10.0,
            'Microsoft.Sql/servers': 200.0,
            'Microsoft.Sql/servers/databases': 300.0,
            'Microsoft.Compute/virtualMachines': 400.0,
            'Microsoft.Network/virtualNetworks': 5.0,
            'Microsoft.Insights/components': 15.0
        }