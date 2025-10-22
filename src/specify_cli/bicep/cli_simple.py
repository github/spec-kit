"""Simplified CLI integration for Bicep Generator.

This module provides a working CLI interface without requiring all the complex
dependencies that are still being integrated.
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass


@dataclass
class DetectedResource:
    """Simple resource detection result."""
    resource_type: str
    name: str
    confidence: float
    evidence: List[str]


class SimpleBicepAnalyzer:
    """Simplified analyzer for CLI demonstration."""
    
    # Azure SDK package patterns
    AZURE_PACKAGES = {
        'azure-storage-blob': ('Azure Storage Account', 'Blob Storage'),
        'azure-storage-queue': ('Azure Storage Account', 'Queue Storage'),
        'azure-storage-file-share': ('Azure Storage Account', 'File Storage'),
        'azure-keyvault-secrets': ('Azure Key Vault', 'Secrets'),
        'azure-keyvault-keys': ('Azure Key Vault', 'Keys'),
        'azure-keyvault-certificates': ('Azure Key Vault', 'Certificates'),
        'azure-cosmos': ('Azure Cosmos DB', 'NoSQL Database'),
        'psycopg2': ('Azure Database for PostgreSQL', 'Relational Database'),
        'psycopg2-binary': ('Azure Database for PostgreSQL', 'Relational Database'),
        'pymongo': ('Azure Cosmos DB', 'MongoDB API'),
        'redis': ('Azure Cache for Redis', 'In-Memory Cache'),
        'azure-servicebus': ('Azure Service Bus', 'Messaging'),
        'azure-eventhub': ('Azure Event Hubs', 'Event Streaming'),
        'azure-functions': ('Azure Functions', 'Serverless Compute'),
        'azure-identity': ('Azure Identity', 'Authentication'),
    }
    
    # Framework detection for App Service
    FRAMEWORK_PATTERNS = {
        'flask': 'Python - Flask',
        'django': 'Python - Django',
        'fastapi': 'Python - FastAPI',
        'express': 'Node.js - Express',
        'next': 'Node.js - Next.js',
        'react': 'Node.js - React',
        'angular': 'Node.js - Angular',
        'vue': 'Node.js - Vue',
    }
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.detected_resources: List[DetectedResource] = []
        self.config_values: Dict[str, str] = {}
        
    def analyze(self) -> Tuple[List[DetectedResource], Dict[str, str]]:
        """Analyze project and detect Azure resources."""
        
        # Detect web framework (implies App Service)
        framework = self._detect_framework()
        if framework:
            self.detected_resources.append(DetectedResource(
                resource_type="Azure App Service",
                name=self.config_values.get('app_name', 'myapp'),
                confidence=0.95,
                evidence=[f"Detected {framework} framework"]
            ))
            
            # App Service needs a service plan
            self.detected_resources.append(DetectedResource(
                resource_type="Azure App Service Plan",
                name=self.config_values.get('plan_name', 'myapp-plan'),
                confidence=0.95,
                evidence=["Required for App Service"]
            ))
        
        # Detect Azure services from dependencies
        dependencies = self._read_dependencies()
        for dep in dependencies:
            if dep in self.AZURE_PACKAGES:
                service_type, description = self.AZURE_PACKAGES[dep]
                
                # Try to extract resource name from config
                resource_name = self._extract_resource_name(service_type)
                
                self.detected_resources.append(DetectedResource(
                    resource_type=service_type,
                    name=resource_name,
                    confidence=0.90,
                    evidence=[f"Found dependency: {dep}", description]
                ))
        
        # Read environment variables for additional context
        self._read_env_file()
        
        return self.detected_resources, self.config_values
    
    def _detect_framework(self) -> str:
        """Detect web framework from dependencies."""
        deps = self._read_dependencies()
        
        for dep, framework in self.FRAMEWORK_PATTERNS.items():
            if any(dep in d for d in deps):
                return framework
        
        return ""
    
    def _read_dependencies(self) -> List[str]:
        """Read project dependencies from various files."""
        dependencies = []
        
        # Python: requirements.txt
        req_file = self.project_path / "requirements.txt"
        if req_file.exists():
            content = req_file.read_text(encoding='utf-8', errors='ignore')
            for line in content.splitlines():
                line = line.strip().split('#')[0].strip()  # Remove comments
                if line and not line.startswith('-'):
                    # Extract package name (before ==, >=, etc.)
                    pkg = re.split(r'[=<>!]', line)[0].strip()
                    dependencies.append(pkg.lower())
        
        # Node.js: package.json
        pkg_file = self.project_path / "package.json"
        if pkg_file.exists():
            import json
            try:
                data = json.loads(pkg_file.read_text(encoding='utf-8'))
                for dep_type in ['dependencies', 'devDependencies']:
                    if dep_type in data:
                        dependencies.extend(data[dep_type].keys())
            except:
                pass
        
        return dependencies
    
    def _read_env_file(self):
        """Read environment variables from .env file."""
        env_file = self.project_path / ".env"
        if env_file.exists():
            content = env_file.read_text(encoding='utf-8', errors='ignore')
            for line in content.splitlines():
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    self.config_values[key.strip()] = value.strip()
    
    def _extract_resource_name(self, service_type: str) -> str:
        """Extract resource name from config or generate default."""
        
        # Map service types to common env var patterns
        env_patterns = {
            'Azure Storage Account': ['AZURE_STORAGE_ACCOUNT_NAME', 'STORAGE_ACCOUNT'],
            'Azure Key Vault': ['AZURE_KEY_VAULT_NAME', 'KEY_VAULT_NAME', 'KEYVAULT_NAME'],
            'Azure Database for PostgreSQL': ['DATABASE_HOST', 'POSTGRES_HOST', 'DB_HOST'],
            'Azure Cache for Redis': ['REDIS_HOST', 'CACHE_HOST'],
            'Azure Cosmos DB': ['COSMOS_ENDPOINT', 'COSMOSDB_ENDPOINT'],
        }
        
        if service_type in env_patterns:
            for pattern in env_patterns[service_type]:
                if pattern in self.config_values:
                    value = self.config_values[pattern]
                    # Extract just the name part from full URLs/hosts
                    if '.' in value:
                        return value.split('.')[0]
                    return value
        
        # Generate default name
        return service_type.lower().replace(' ', '-').replace('azure-', '')
