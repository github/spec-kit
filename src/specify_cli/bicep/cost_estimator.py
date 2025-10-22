"""
Cost estimation integration for Azure resources in Bicep templates.

This module provides detailed cost analysis, pricing integration, and cost optimization
recommendations for Azure infrastructure deployments.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
import re
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PricingTier(str, Enum):
    """Azure pricing tiers."""
    
    FREE = "free"
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class BillingModel(str, Enum):
    """Azure billing models."""
    
    CONSUMPTION = "consumption"  # Pay per use
    RESERVED = "reserved"       # Reserved instances
    SPOT = "spot"              # Spot instances
    HYBRID = "hybrid"          # Hybrid benefit


@dataclass
class PricingInfo:
    """Pricing information for an Azure resource."""
    
    resource_type: str
    region: str
    pricing_tier: PricingTier
    billing_model: BillingModel
    
    # Cost breakdown
    hourly_cost: float
    monthly_cost: float
    yearly_cost: float
    
    # Usage-based pricing
    per_transaction_cost: Optional[float] = None
    per_gb_cost: Optional[float] = None
    per_operation_cost: Optional[float] = None
    
    # Additional fees
    network_egress_cost: float = 0.0
    storage_cost: float = 0.0
    backup_cost: float = 0.0
    
    # Metadata
    currency: str = "USD"
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def get_estimated_monthly_cost(
        self, 
        transactions_per_month: int = 0,
        gb_per_month: float = 0.0,
        operations_per_month: int = 0
    ) -> float:
        """Calculate estimated monthly cost including usage."""
        base_cost = self.monthly_cost
        
        # Add usage-based costs
        if self.per_transaction_cost and transactions_per_month:
            base_cost += self.per_transaction_cost * transactions_per_month
        
        if self.per_gb_cost and gb_per_month:
            base_cost += self.per_gb_cost * gb_per_month
        
        if self.per_operation_cost and operations_per_month:
            base_cost += self.per_operation_cost * operations_per_month
        
        # Add additional fees
        base_cost += self.network_egress_cost + self.storage_cost + self.backup_cost
        
        return base_cost


@dataclass
class CostOptimization:
    """Cost optimization recommendation."""
    
    id: str
    title: str
    description: str
    current_monthly_cost: float
    optimized_monthly_cost: float
    annual_savings: float
    
    # Implementation details
    optimization_type: str  # resize, tier_change, reserved_instance, spot_instance
    effort_level: str      # low, medium, high
    risk_level: str        # low, medium, high
    
    # Steps to implement
    implementation_steps: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    considerations: List[str] = field(default_factory=list)
    
    def get_savings_percentage(self) -> float:
        """Calculate savings percentage."""
        if self.current_monthly_cost <= 0:
            return 0.0
        return ((self.current_monthly_cost - self.optimized_monthly_cost) / self.current_monthly_cost) * 100


@dataclass
class CostEstimate:
    """Complete cost estimate for a deployment."""
    
    deployment_name: str
    region: str
    timestamp: datetime
    
    # Resource costs
    resource_costs: Dict[str, PricingInfo] = field(default_factory=dict)
    
    # Total costs
    total_hourly_cost: float = 0.0
    total_monthly_cost: float = 0.0
    total_yearly_cost: float = 0.0
    
    # Optimizations
    optimizations: List[CostOptimization] = field(default_factory=list)
    
    # Projections
    projected_growth: Dict[str, float] = field(default_factory=dict)  # Monthly growth rates
    
    def get_total_potential_savings(self) -> float:
        """Calculate total potential annual savings."""
        return sum(opt.annual_savings for opt in self.optimizations)
    
    def get_optimized_monthly_cost(self) -> float:
        """Calculate monthly cost after optimizations."""
        monthly_savings = sum(
            opt.current_monthly_cost - opt.optimized_monthly_cost 
            for opt in self.optimizations
        )
        return max(0, self.total_monthly_cost - monthly_savings)
    
    def get_cost_breakdown_by_category(self) -> Dict[str, float]:
        """Get cost breakdown by resource category."""
        categories = {
            "Compute": 0.0,
            "Storage": 0.0,
            "Networking": 0.0,
            "Database": 0.0,
            "Security": 0.0,
            "Monitoring": 0.0,
            "Other": 0.0
        }
        
        category_mapping = {
            "Microsoft.Compute": "Compute",
            "Microsoft.Web": "Compute",
            "Microsoft.Storage": "Storage",
            "Microsoft.Network": "Networking",
            "Microsoft.Sql": "Database",
            "Microsoft.DocumentDB": "Database",
            "Microsoft.KeyVault": "Security",
            "Microsoft.Insights": "Monitoring"
        }
        
        for resource_name, pricing in self.resource_costs.items():
            resource_type = pricing.resource_type
            category = "Other"
            
            for type_prefix, cat in category_mapping.items():
                if resource_type.startswith(type_prefix):
                    category = cat
                    break
            
            categories[category] += pricing.monthly_cost
        
        return categories


class CostEstimator:
    """
    Azure cost estimation and optimization engine.
    
    Provides detailed cost analysis, pricing integration, and optimization
    recommendations for Azure infrastructure deployments.
    """
    
    def __init__(self):
        # Initialize pricing database (in production, this would connect to Azure Pricing API)
        self.pricing_database = self._initialize_pricing_database()
        
        # Optimization rules
        self.optimization_rules = self._initialize_optimization_rules()
        
        # Usage patterns for estimation
        self.usage_patterns = self._initialize_usage_patterns()
    
    async def estimate_deployment_cost(
        self,
        resources: List[Dict[str, Any]],
        region: str = "eastus",
        deployment_name: str = "deployment"
    ) -> CostEstimate:
        """
        Estimate cost for a complete deployment.
        
        Args:
            resources: List of Azure resource definitions
            region: Target Azure region
            deployment_name: Name of the deployment
            
        Returns:
            Complete cost estimate with optimizations
        """
        logger.info(f"Estimating costs for deployment '{deployment_name}' in {region}")
        
        estimate = CostEstimate(
            deployment_name=deployment_name,
            region=region,
            timestamp=datetime.utcnow()
        )
        
        # Estimate cost for each resource
        for resource in resources:
            resource_name = resource.get('name', 'unnamed')
            resource_type = resource.get('type', 'unknown')
            properties = resource.get('properties', {})
            
            try:
                pricing_info = await self._get_resource_pricing(
                    resource_type, properties, region
                )
                estimate.resource_costs[resource_name] = pricing_info
                
                # Add to totals
                estimate.total_hourly_cost += pricing_info.hourly_cost
                estimate.total_monthly_cost += pricing_info.monthly_cost
                estimate.total_yearly_cost += pricing_info.yearly_cost
                
            except Exception as e:
                logger.warning(f"Failed to estimate cost for {resource_name}: {e}")
                # Add default estimate
                default_pricing = PricingInfo(
                    resource_type=resource_type,
                    region=region,
                    pricing_tier=PricingTier.STANDARD,
                    billing_model=BillingModel.CONSUMPTION,
                    hourly_cost=5.0,
                    monthly_cost=3600.0,  # 5 * 24 * 30
                    yearly_cost=43800.0   # 5 * 24 * 365
                )
                estimate.resource_costs[resource_name] = default_pricing
                estimate.total_monthly_cost += default_pricing.monthly_cost
        
        # Generate cost optimizations
        estimate.optimizations = await self._generate_cost_optimizations(estimate)
        
        logger.info(f"Cost estimation completed: ${estimate.total_monthly_cost:.2f}/month")
        
        return estimate
    
    async def _get_resource_pricing(
        self,
        resource_type: str,
        properties: Dict[str, Any],
        region: str
    ) -> PricingInfo:
        """Get pricing information for a specific resource."""
        
        # Get base pricing from database
        base_pricing = self.pricing_database.get(resource_type, {})
        
        if not base_pricing:
            logger.warning(f"No pricing data available for {resource_type}")
            # Return default pricing
            return PricingInfo(
                resource_type=resource_type,
                region=region,
                pricing_tier=PricingTier.STANDARD,
                billing_model=BillingModel.CONSUMPTION,
                hourly_cost=2.0,
                monthly_cost=1440.0,
                yearly_cost=17520.0
            )
        
        # Determine pricing tier from properties
        pricing_tier = self._determine_pricing_tier(resource_type, properties)
        
        # Get regional multiplier
        regional_multiplier = self._get_regional_multiplier(region)
        
        # Calculate costs
        base_hourly_cost = base_pricing.get('hourly_cost', {}).get(pricing_tier.value, 2.0)
        hourly_cost = base_hourly_cost * regional_multiplier
        monthly_cost = hourly_cost * 24 * 30
        yearly_cost = hourly_cost * 24 * 365
        
        return PricingInfo(
            resource_type=resource_type,
            region=region,
            pricing_tier=pricing_tier,
            billing_model=BillingModel.CONSUMPTION,
            hourly_cost=hourly_cost,
            monthly_cost=monthly_cost,
            yearly_cost=yearly_cost,
            per_transaction_cost=base_pricing.get('per_transaction'),
            per_gb_cost=base_pricing.get('per_gb'),
            per_operation_cost=base_pricing.get('per_operation')
        )
    
    async def _generate_cost_optimizations(self, estimate: CostEstimate) -> List[CostOptimization]:
        """Generate cost optimization recommendations."""
        optimizations = []
        
        for resource_name, pricing_info in estimate.resource_costs.items():
            resource_optimizations = self._get_resource_optimizations(
                resource_name, pricing_info
            )
            optimizations.extend(resource_optimizations)
        
        # Sort by potential savings
        optimizations.sort(key=lambda x: x.annual_savings, reverse=True)
        
        return optimizations
    
    def _get_resource_optimizations(
        self, 
        resource_name: str, 
        pricing_info: PricingInfo
    ) -> List[CostOptimization]:
        """Get optimization recommendations for a specific resource."""
        optimizations = []
        
        rules = self.optimization_rules.get(pricing_info.resource_type, [])
        
        for rule in rules:
            if self._should_apply_rule(rule, pricing_info):
                optimization = self._create_optimization_from_rule(
                    rule, resource_name, pricing_info
                )
                optimizations.append(optimization)
        
        return optimizations
    
    def _should_apply_rule(
        self, 
        rule: Dict[str, Any], 
        pricing_info: PricingInfo
    ) -> bool:
        """Check if optimization rule should be applied."""
        conditions = rule.get('conditions', {})
        
        # Check pricing tier condition
        if 'min_tier' in conditions:
            tier_order = [PricingTier.FREE, PricingTier.BASIC, PricingTier.STANDARD, PricingTier.PREMIUM, PricingTier.ENTERPRISE]
            min_tier_index = tier_order.index(PricingTier(conditions['min_tier']))
            current_tier_index = tier_order.index(pricing_info.pricing_tier)
            
            if current_tier_index < min_tier_index:
                return False
        
        # Check cost threshold
        if 'min_monthly_cost' in conditions:
            if pricing_info.monthly_cost < conditions['min_monthly_cost']:
                return False
        
        return True
    
    def _create_optimization_from_rule(
        self,
        rule: Dict[str, Any],
        resource_name: str,
        pricing_info: PricingInfo
    ) -> CostOptimization:
        """Create optimization recommendation from rule."""
        
        # Calculate optimized cost
        cost_reduction_percentage = rule.get('cost_reduction_percentage', 20)
        optimized_monthly_cost = pricing_info.monthly_cost * (1 - cost_reduction_percentage / 100)
        annual_savings = (pricing_info.monthly_cost - optimized_monthly_cost) * 12
        
        return CostOptimization(
            id=f"{resource_name}_{rule['id']}",
            title=rule['title'].format(resource_name=resource_name),
            description=rule['description'],
            current_monthly_cost=pricing_info.monthly_cost,
            optimized_monthly_cost=optimized_monthly_cost,
            annual_savings=annual_savings,
            optimization_type=rule['type'],
            effort_level=rule.get('effort_level', 'medium'),
            risk_level=rule.get('risk_level', 'low'),
            implementation_steps=rule.get('steps', []),
            prerequisites=rule.get('prerequisites', []),
            considerations=rule.get('considerations', [])
        )
    
    def _determine_pricing_tier(
        self, 
        resource_type: str, 
        properties: Dict[str, Any]
    ) -> PricingTier:
        """Determine pricing tier from resource properties."""
        
        # Check SKU
        sku = properties.get('sku', {})
        if isinstance(sku, dict):
            sku_name = sku.get('name', '').lower()
        else:
            sku_name = str(sku).lower()
        
        if 'free' in sku_name or 'f1' in sku_name:
            return PricingTier.FREE
        elif 'basic' in sku_name or 'b1' in sku_name:
            return PricingTier.BASIC
        elif 'premium' in sku_name or 'p1' in sku_name or 'p2' in sku_name or 'p3' in sku_name:
            return PricingTier.PREMIUM
        else:
            return PricingTier.STANDARD
    
    def _get_regional_multiplier(self, region: str) -> float:
        """Get cost multiplier for specific region."""
        regional_multipliers = {
            'eastus': 1.0,
            'eastus2': 1.0,
            'westus': 1.05,
            'westus2': 1.02,
            'centralus': 1.01,
            'northcentralus': 1.01,
            'southcentralus': 1.01,
            'westcentralus': 1.02,
            'westeurope': 1.08,
            'northeurope': 1.06,
            'uksouth': 1.10,
            'ukwest': 1.12,
            'eastasia': 1.15,
            'southeastasia': 1.12,
            'japaneast': 1.18,
            'japanwest': 1.20,
            'australiaeast': 1.15,
            'australiasoutheast': 1.18,
        }
        
        return regional_multipliers.get(region.lower(), 1.10)  # Default 10% premium for unknown regions
    
    def _initialize_pricing_database(self) -> Dict[str, Dict[str, Any]]:
        """Initialize pricing database (simplified for demo)."""
        return {
            'Microsoft.Web/sites': {
                'hourly_cost': {
                    'free': 0.0,
                    'basic': 0.075,     # ~$54/month
                    'standard': 0.20,   # ~$144/month
                    'premium': 0.40,    # ~$288/month
                    'enterprise': 0.80  # ~$576/month
                },
                'per_transaction': 0.000001,  # $0.000001 per request
            },
            'Microsoft.Web/serverfarms': {
                'hourly_cost': {
                    'free': 0.0,
                    'basic': 0.075,
                    'standard': 0.20,
                    'premium': 0.40,
                    'enterprise': 0.80
                }
            },
            'Microsoft.Storage/storageAccounts': {
                'hourly_cost': {
                    'standard': 0.05,   # ~$36/month
                    'premium': 0.15     # ~$108/month
                },
                'per_gb': 0.0184,           # $0.0184 per GB/month
                'per_transaction': 0.0004,  # $0.0004 per 10K transactions
            },
            'Microsoft.KeyVault/vaults': {
                'hourly_cost': {
                    'standard': 0.03,   # ~$21.6/month
                    'premium': 0.125    # ~$90/month for HSM
                },
                'per_operation': 0.03,      # $0.03 per 10K operations
            },
            'Microsoft.Sql/servers': {
                'hourly_cost': {
                    'basic': 0.021,     # ~$15/month
                    'standard': 0.125,  # ~$90/month
                    'premium': 0.50     # ~$360/month
                }
            },
            'Microsoft.Sql/servers/databases': {
                'hourly_cost': {
                    'basic': 0.069,     # ~$50/month
                    'standard': 0.417,  # ~$300/month
                    'premium': 1.67     # ~$1200/month
                }
            },
            'Microsoft.Compute/virtualMachines': {
                'hourly_cost': {
                    'basic': 0.50,      # ~$360/month
                    'standard': 1.20,   # ~$864/month
                    'premium': 2.50     # ~$1800/month
                }
            },
            'Microsoft.Network/virtualNetworks': {
                'hourly_cost': {
                    'standard': 0.0014  # ~$1/month
                }
            },
            'Microsoft.Insights/components': {
                'hourly_cost': {
                    'standard': 0.028   # ~$20/month
                },
                'per_gb': 2.88,             # $2.88 per GB ingested
            }
        }
    
    def _initialize_optimization_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize cost optimization rules."""
        return {
            'Microsoft.Web/sites': [
                {
                    'id': 'downsize_app_service',
                    'title': 'Downsize App Service {resource_name}',
                    'description': 'Consider downsizing to a smaller App Service plan based on usage patterns',
                    'type': 'resize',
                    'cost_reduction_percentage': 50,
                    'effort_level': 'low',
                    'risk_level': 'low',
                    'conditions': {
                        'min_tier': 'standard',
                        'min_monthly_cost': 100
                    },
                    'steps': [
                        'Analyze current CPU and memory usage',
                        'Identify appropriate smaller SKU',
                        'Plan maintenance window for change',
                        'Update App Service plan',
                        'Monitor performance after change'
                    ],
                    'prerequisites': ['Usage analysis', 'Performance baseline'],
                    'considerations': ['May impact performance during peak loads']
                }
            ],
            'Microsoft.Storage/storageAccounts': [
                {
                    'id': 'storage_tier_optimization',
                    'title': 'Optimize Storage Tiers for {resource_name}',
                    'description': 'Move infrequently accessed data to cool or archive tiers',
                    'type': 'tier_change',
                    'cost_reduction_percentage': 30,
                    'effort_level': 'medium',
                    'risk_level': 'low',
                    'steps': [
                        'Analyze data access patterns',
                        'Configure lifecycle management policies',
                        'Set up automated tier transitions',
                        'Monitor cost impact'
                    ]
                }
            ],
            'Microsoft.Compute/virtualMachines': [
                {
                    'id': 'reserved_instances',
                    'title': 'Use Reserved Instances for {resource_name}',
                    'description': 'Purchase reserved instances for consistent workloads',
                    'type': 'reserved_instance',
                    'cost_reduction_percentage': 40,
                    'effort_level': 'low',
                    'risk_level': 'medium',
                    'conditions': {
                        'min_monthly_cost': 200
                    },
                    'steps': [
                        'Analyze VM usage patterns',
                        'Purchase appropriate reserved instances',
                        'Apply reservations to VMs'
                    ],
                    'considerations': ['Requires 1-3 year commitment']
                },
                {
                    'id': 'spot_instances',
                    'title': 'Use Spot Instances for {resource_name}',
                    'description': 'Use spot instances for fault-tolerant workloads',
                    'type': 'spot_instance',
                    'cost_reduction_percentage': 80,
                    'effort_level': 'high',
                    'risk_level': 'high',
                    'steps': [
                        'Evaluate workload fault tolerance',
                        'Implement spot instance handling',
                        'Set up automated failover',
                        'Monitor spot pricing'
                    ],
                    'considerations': ['Instances can be preempted', 'Requires fault-tolerant design']
                }
            ]
        }
    
    def _initialize_usage_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize typical usage patterns for cost estimation."""
        return {
            'Microsoft.Web/sites': {
                'requests_per_month': 1000000,  # 1M requests
                'cpu_usage_percentage': 30,
                'memory_usage_percentage': 40
            },
            'Microsoft.Storage/storageAccounts': {
                'gb_stored': 100,               # 100 GB
                'transactions_per_month': 500000,  # 500K transactions
                'egress_gb_per_month': 10       # 10 GB egress
            },
            'Microsoft.KeyVault/vaults': {
                'operations_per_month': 100000   # 100K operations
            },
            'Microsoft.Insights/components': {
                'gb_ingested_per_month': 5      # 5 GB telemetry
            }
        }