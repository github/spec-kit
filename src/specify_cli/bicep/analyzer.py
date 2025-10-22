"""Core project analysis logic.

This module implements the main project analysis functionality that scans project files,
analyzes technology stacks, and determines Azure resource requirements.
"""

import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import json
import yaml
import re
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import mimetypes
import xml.etree.ElementTree as ET
from datetime import datetime

from .models.project_analysis import (
    ProjectAnalysisResult, FileAnalysisResult, ProjectType, FrameworkType,
    SecurityAnalysis, PerformanceAnalysis
)
from .models.resource_requirement import ResourceRequirement, ResourceType, PriorityLevel, ComplianceRequirement
from .models.template_update import (
    TemplateUpdateManifest, FileChange, ResourceChange, ChangeType, 
    ChangeSeverity, ChangeImpact
)
from ..utils.file_scanner import FileScanner, FileInfo
from .mcp_client import MCPClient

logger = logging.getLogger(__name__)


@dataclass
class TechnologyPattern:
    """Pattern for identifying technologies in project files."""
    name: str
    indicators: List[str]  # File patterns, package names, etc.
    confidence_boost: float  # How much this increases confidence
    resource_implications: List[ResourceType] = field(default_factory=list)


class ProjectAnalyzer:
    """Analyzes projects to determine technology stack and resource requirements."""
    
    # Technology detection patterns
    FRAMEWORK_PATTERNS = {
        FrameworkType.REACT: TechnologyPattern(
            name="React",
            indicators=[
                "package.json:react",
                "src/App.jsx",
                "src/App.js",
                "public/index.html",
                "react-scripts",
                "@types/react"
            ],
            confidence_boost=0.3,
            resource_implications=[ResourceType.STATIC_WEB_APP, ResourceType.CDN]
        ),
        FrameworkType.ANGULAR: TechnologyPattern(
            name="Angular",
            indicators=[
                "package.json:@angular/core",
                "angular.json",
                "src/app/app.component.ts",
                "src/main.ts",
                "@angular/cli"
            ],
            confidence_boost=0.3,
            resource_implications=[ResourceType.STATIC_WEB_APP, ResourceType.CDN]
        ),
        FrameworkType.VUE: TechnologyPattern(
            name="Vue.js",
            indicators=[
                "package.json:vue",
                "vue.config.js",
                "src/App.vue",
                "src/main.js",
                "@vue/cli"
            ],
            confidence_boost=0.3,
            resource_implications=[ResourceType.STATIC_WEB_APP, ResourceType.CDN]
        ),
        FrameworkType.ASP_NET_CORE: TechnologyPattern(
            name="ASP.NET Core",
            indicators=[
                "*.csproj:Microsoft.AspNetCore",
                "Program.cs",
                "Startup.cs",
                "appsettings.json",
                "Controllers/",
                "wwwroot/"
            ],
            confidence_boost=0.4,
            resource_implications=[ResourceType.APP_SERVICE, ResourceType.APPLICATION_INSIGHTS]
        ),
        FrameworkType.EXPRESS_JS: TechnologyPattern(
            name="Express.js",
            indicators=[
                "package.json:express",
                "server.js",
                "app.js",
                "routes/",
                "middleware/"
            ],
            confidence_boost=0.3,
            resource_implications=[ResourceType.APP_SERVICE, ResourceType.APPLICATION_INSIGHTS]
        ),
        FrameworkType.DJANGO: TechnologyPattern(
            name="Django",
            indicators=[
                "requirements.txt:Django",
                "manage.py",
                "settings.py",
                "urls.py",
                "models.py",
                "views.py"
            ],
            confidence_boost=0.4,
            resource_implications=[ResourceType.APP_SERVICE, ResourceType.POSTGRESQL]
        ),
        FrameworkType.FLASK: TechnologyPattern(
            name="Flask",
            indicators=[
                "requirements.txt:Flask",
                "app.py",
                "wsgi.py",
                "templates/",
                "static/"
            ],
            confidence_boost=0.3,
            resource_implications=[ResourceType.APP_SERVICE]
        ),
        FrameworkType.FASTAPI: TechnologyPattern(
            name="FastAPI",
            indicators=[
                "requirements.txt:fastapi",
                "main.py",
                "api/",
                "routers/",
                "requirements.txt:uvicorn"
            ],
            confidence_boost=0.3,
            resource_implications=[ResourceType.APP_SERVICE, ResourceType.APPLICATION_INSIGHTS]
        ),
        FrameworkType.SPRING_BOOT: TechnologyPattern(
            name="Spring Boot",
            indicators=[
                "pom.xml:spring-boot",
                "build.gradle:spring-boot",
                "application.properties",
                "application.yml",
                "src/main/java/",
                "@SpringBootApplication"
            ],
            confidence_boost=0.4,
            resource_implications=[ResourceType.APP_SERVICE, ResourceType.APPLICATION_INSIGHTS]
        )
    }
    
    # Database patterns
    DATABASE_PATTERNS = {
        ResourceType.SQL_DATABASE: TechnologyPattern(
            name="SQL Server",
            indicators=[
                "connectionStrings:SqlServer",
                "System.Data.SqlClient",
                "Microsoft.EntityFrameworkCore.SqlServer",
                "appsettings.json:ConnectionStrings"
            ],
            confidence_boost=0.4
        ),
        ResourceType.POSTGRESQL: TechnologyPattern(
            name="PostgreSQL",
            indicators=[
                "requirements.txt:psycopg2",
                "package.json:pg",
                "Npgsql",
                "postgresql://"
            ],
            confidence_boost=0.4
        ),
        ResourceType.MYSQL: TechnologyPattern(
            name="MySQL",
            indicators=[
                "requirements.txt:PyMySQL",
                "package.json:mysql2",
                "MySql.Data",
                "mysql://"
            ],
            confidence_boost=0.4
        ),
        ResourceType.COSMOS_DB: TechnologyPattern(
            name="Cosmos DB",
            indicators=[
                "Microsoft.Azure.Cosmos",
                "@azure/cosmos",
                "azure-cosmos",
                "cosmosdb"
            ],
            confidence_boost=0.5
        )
    }
    
    # Infrastructure patterns
    INFRASTRUCTURE_PATTERNS = {
        ResourceType.REDIS_CACHE: TechnologyPattern(
            name="Redis Cache",
            indicators=[
                "StackExchange.Redis",
                "redis-py",
                "node_redis",
                "redis://"
            ],
            confidence_boost=0.4
        ),
        ResourceType.SERVICE_BUS: TechnologyPattern(
            name="Service Bus",
            indicators=[
                "Azure.Messaging.ServiceBus",
                "@azure/service-bus",
                "azure-servicebus"
            ],
            confidence_boost=0.5
        ),
        ResourceType.EVENT_HUB: TechnologyPattern(
            name="Event Hub",
            indicators=[
                "Azure.Messaging.EventHubs",
                "@azure/event-hubs",
                "azure-eventhub"
            ],
            confidence_boost=0.5
        ),
        ResourceType.STORAGE_ACCOUNT: TechnologyPattern(
            name="Storage Account",
            indicators=[
                "Azure.Storage.Blobs",
                "@azure/storage-blob",
                "azure-storage-blob",
                "blob.core.windows.net"
            ],
            confidence_boost=0.4
        ),
        ResourceType.KEY_VAULT: TechnologyPattern(
            name="Key Vault",
            indicators=[
                "Azure.Security.KeyVault",
                "@azure/keyvault-secrets",
                "azure-keyvault",
                "vault.azure.net"
            ],
            confidence_boost=0.5
        )
    }
    
    def __init__(self, file_scanner: FileScanner, mcp_client: Optional[MCPClient] = None):
        """Initialize the project analyzer."""
        self.file_scanner = file_scanner
        self.mcp_client = mcp_client
        self._analysis_cache: Dict[str, Any] = {}
        
    async def analyze_project(self, project_path: Path, deep_scan: bool = True) -> ProjectAnalysisResult:
        """Analyze a project to determine technology stack and requirements."""
        logger.info(f"Starting project analysis for: {project_path}")
        
        try:
            # Scan project files
            scan_result = await self.file_scanner.scan_directory(project_path)
            
            # Analyze files to determine project type and frameworks
            project_type, frameworks, confidence = await self._analyze_technology_stack(scan_result.files)
            
            # Analyze individual files
            file_analyses = []
            if deep_scan:
                file_analyses = await self._analyze_files_detailed(scan_result.files[:50])  # Limit for performance
            
            # Determine resource requirements
            resource_requirements = await self._determine_resource_requirements(
                project_type, frameworks, scan_result.files
            )
            
            # Security analysis
            security_analysis = await self._analyze_security(scan_result.files)
            
            # Performance analysis
            performance_analysis = await self._analyze_performance(scan_result.files, project_type)
            
            # Compliance analysis
            compliance_requirements = await self._analyze_compliance(scan_result.files)
            
            result = ProjectAnalysisResult(
                project_path=project_path,
                project_type=project_type,
                detected_frameworks=frameworks,
                confidence_score=confidence,
                total_files=len(scan_result.files),
                analyzed_files=len(file_analyses),
                file_analyses=file_analyses,
                resource_requirements=resource_requirements,
                security_analysis=security_analysis,
                performance_analysis=performance_analysis,
                compliance_requirements=compliance_requirements,
                scan_metadata=scan_result.to_dict()
            )
            
            logger.info(f"Project analysis completed. Type: {project_type}, Confidence: {confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing project: {e}")
            raise
    
    async def _analyze_technology_stack(self, files: List[FileInfo]) -> Tuple[ProjectType, List[FrameworkType], float]:
        """Analyze files to determine project type and frameworks."""
        framework_scores = {framework: 0.0 for framework in FrameworkType}
        project_type_scores = {ptype: 0.0 for ptype in ProjectType}
        
        # Create file lookup for efficient searching
        file_paths = {f.relative_path.as_posix().lower() for f in files}
        file_contents = {}
        
        # Read key configuration files
        key_files = ['package.json', 'requirements.txt', 'pom.xml', 'build.gradle', '*.csproj']
        for file_info in files:
            file_path_lower = file_info.relative_path.as_posix().lower()
            for pattern in key_files:
                if pattern.replace('*', '') in file_path_lower or file_path_lower.endswith(pattern.replace('*', '')):
                    try:
                        content = await self._read_file_content(file_info.full_path)
                        file_contents[file_path_lower] = content
                    except Exception:
                        continue
        
        # Analyze framework patterns
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            score = 0.0
            
            for indicator in pattern.indicators:
                if ':' in indicator:
                    # File content indicator (e.g., "package.json:react")
                    file_pattern, content_pattern = indicator.split(':', 1)
                    file_key = file_pattern.lower()
                    
                    if file_key in file_contents:
                        content = file_contents[file_key]
                        if content_pattern.lower() in content.lower():
                            score += pattern.confidence_boost
                else:
                    # File path indicator
                    indicator_lower = indicator.lower()
                    
                    # Check direct matches
                    if indicator_lower in file_paths:
                        score += pattern.confidence_boost
                    
                    # Check pattern matches (e.g., "Controllers/")
                    if indicator.endswith('/'):
                        for file_path in file_paths:
                            if indicator_lower.rstrip('/') in file_path:
                                score += pattern.confidence_boost * 0.5
                                break
            
            framework_scores[framework] = score
        
        # Determine project type based on frameworks and files
        web_frameworks = [FrameworkType.REACT, FrameworkType.ANGULAR, FrameworkType.VUE]
        backend_frameworks = [FrameworkType.ASP_NET_CORE, FrameworkType.EXPRESS_JS, 
                            FrameworkType.DJANGO, FrameworkType.FLASK, FrameworkType.FASTAPI, 
                            FrameworkType.SPRING_BOOT]
        
        # Score project types
        if any(framework_scores[f] > 0 for f in web_frameworks):
            project_type_scores[ProjectType.WEB_APPLICATION] += 0.4
            
            if any(framework_scores[f] > 0 for f in backend_frameworks):
                project_type_scores[ProjectType.FULL_STACK_APPLICATION] += 0.6
            else:
                project_type_scores[ProjectType.STATIC_WEBSITE] += 0.3
        
        if any(framework_scores[f] > 0 for f in backend_frameworks):
            project_type_scores[ProjectType.WEB_APPLICATION] += 0.5
            project_type_scores[ProjectType.API_SERVICE] += 0.4
        
        # Check for mobile indicators
        mobile_indicators = ['ios/', 'android/', 'xamarin', 'react-native', 'flutter']
        if any(indicator in ' '.join(file_paths) for indicator in mobile_indicators):
            project_type_scores[ProjectType.MOBILE_APPLICATION] += 0.5
        
        # Check for desktop indicators
        desktop_indicators = ['.wpf', '.winforms', 'electron', 'tauri']
        if any(indicator in ' '.join(file_paths) for indicator in desktop_indicators):
            project_type_scores[ProjectType.DESKTOP_APPLICATION] += 0.5
        
        # Determine final project type and frameworks
        detected_project_type = max(project_type_scores.items(), key=lambda x: x[1])[0]
        detected_frameworks = [f for f, score in framework_scores.items() if score > 0.1]
        
        # Calculate overall confidence
        max_framework_score = max(framework_scores.values()) if framework_scores.values() else 0
        max_project_score = max(project_type_scores.values()) if project_type_scores.values() else 0
        overall_confidence = min((max_framework_score + max_project_score) / 2, 1.0)
        
        return detected_project_type, detected_frameworks, overall_confidence
    
    async def _analyze_files_detailed(self, files: List[FileInfo]) -> List[FileAnalysisResult]:
        """Perform detailed analysis of individual files."""
        analyses = []
        
        # Use thread pool for file I/O
        with ThreadPoolExecutor(max_workers=4) as executor:
            tasks = []
            for file_info in files:
                if self._should_analyze_file(file_info):
                    task = asyncio.create_task(self._analyze_single_file(file_info))
                    tasks.append(task)
            
            if tasks:
                analyses = await asyncio.gather(*tasks, return_exceptions=True)
                # Filter out exceptions
                analyses = [a for a in analyses if isinstance(a, FileAnalysisResult)]
        
        return analyses
    
    def _should_analyze_file(self, file_info: FileInfo) -> bool:
        """Determine if a file should be analyzed in detail."""
        # Skip binary files, large files, and uninteresting files
        if file_info.size > 1024 * 1024:  # Skip files > 1MB
            return False
        
        skip_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz'}
        if file_info.full_path.suffix.lower() in skip_extensions:
            return False
        
        skip_dirs = {'node_modules', '.git', '__pycache__', 'bin', 'obj', 'dist', 'build'}
        if any(skip_dir in file_info.relative_path.parts for skip_dir in skip_dirs):
            return False
        
        return True
    
    async def _analyze_single_file(self, file_info: FileInfo) -> FileAnalysisResult:
        """Analyze a single file for technologies and patterns."""
        try:
            content = await self._read_file_content(file_info.full_path)
            
            # Determine file type
            file_type = self._get_file_type(file_info.full_path, content)
            
            # Extract technologies
            technologies = self._extract_technologies(content, file_info.full_path.suffix)
            
            # Check for security issues
            security_issues = self._check_file_security(content, file_type)
            
            # Check for configuration
            is_config = self._is_configuration_file(file_info.full_path)
            config_data = {}
            if is_config:
                config_data = self._parse_configuration(content, file_info.full_path.suffix)
            
            return FileAnalysisResult(
                file_path=file_info.relative_path,
                file_type=file_type,
                size_bytes=file_info.size,
                technologies_detected=technologies,
                security_issues=security_issues,
                is_configuration=is_config,
                configuration_data=config_data,
                analysis_timestamp=file_info.last_modified
            )
            
        except Exception as e:
            logger.warning(f"Failed to analyze file {file_info.relative_path}: {e}")
            return FileAnalysisResult(
                file_path=file_info.relative_path,
                file_type="unknown",
                size_bytes=file_info.size,
                analysis_timestamp=file_info.last_modified
            )
    
    async def _determine_resource_requirements(self, 
                                             project_type: ProjectType, 
                                             frameworks: List[FrameworkType],
                                             files: List[FileInfo]) -> List[ResourceRequirement]:
        """Determine Azure resource requirements based on analysis."""
        requirements = []
        
        # Base requirements by project type
        if project_type in [ProjectType.WEB_APPLICATION, ProjectType.FULL_STACK_APPLICATION]:
            # Web applications need App Service
            requirements.append(ResourceRequirement(
                resource_type=ResourceType.APP_SERVICE,
                name="main-app-service",
                priority=PriorityLevel.HIGH,
                justification="Web application hosting",
                estimated_cost_monthly=50.0
            ))
            
            # Application Insights for monitoring
            requirements.append(ResourceRequirement(
                resource_type=ResourceType.APPLICATION_INSIGHTS,
                name="app-insights",
                priority=PriorityLevel.MEDIUM,
                justification="Application monitoring and diagnostics",
                estimated_cost_monthly=10.0
            ))
        
        elif project_type == ProjectType.STATIC_WEBSITE:
            # Static sites can use Static Web Apps
            requirements.append(ResourceRequirement(
                resource_type=ResourceType.STATIC_WEB_APP,
                name="static-web-app",
                priority=PriorityLevel.HIGH,
                justification="Static website hosting",
                estimated_cost_monthly=0.0  # Free tier available
            ))
        
        elif project_type == ProjectType.API_SERVICE:
            # APIs need App Service or Function App
            requirements.append(ResourceRequirement(
                resource_type=ResourceType.APP_SERVICE,
                name="api-service",
                priority=PriorityLevel.HIGH,
                justification="API service hosting",
                estimated_cost_monthly=50.0
            ))
        
        # Framework-specific requirements
        for framework in frameworks:
            pattern = self.FRAMEWORK_PATTERNS.get(framework)
            if pattern and pattern.resource_implications:
                for resource_type in pattern.resource_implications:
                    if not any(req.resource_type == resource_type for req in requirements):
                        requirements.append(ResourceRequirement(
                            resource_type=resource_type,
                            name=f"{resource_type.value.lower().replace('_', '-')}",
                            priority=PriorityLevel.MEDIUM,
                            justification=f"Required by {framework.value}",
                            estimated_cost_monthly=25.0
                        ))
        
        # Database requirements
        db_requirements = await self._detect_database_requirements(files)
        requirements.extend(db_requirements)
        
        # Infrastructure requirements
        infra_requirements = await self._detect_infrastructure_requirements(files)
        requirements.extend(infra_requirements)
        
        # Always include Key Vault for secrets
        if not any(req.resource_type == ResourceType.KEY_VAULT for req in requirements):
            requirements.append(ResourceRequirement(
                resource_type=ResourceType.KEY_VAULT,
                name="key-vault",
                priority=PriorityLevel.MEDIUM,
                justification="Secure secrets and configuration management",
                estimated_cost_monthly=5.0
            ))
        
        return requirements
    
    async def _detect_database_requirements(self, files: List[FileInfo]) -> List[ResourceRequirement]:
        """Detect database requirements from project files."""
        requirements = []
        
        # Read configuration files to look for connection strings
        config_files = [f for f in files if self._is_configuration_file(f.full_path)]
        
        for file_info in config_files[:10]:  # Limit for performance
            try:
                content = await self._read_file_content(file_info.full_path)
                
                # Check database patterns
                for resource_type, pattern in self.DATABASE_PATTERNS.items():
                    for indicator in pattern.indicators:
                        if indicator.lower() in content.lower():
                            requirements.append(ResourceRequirement(
                                resource_type=resource_type,
                                name=f"{resource_type.value.lower().replace('_', '-')}",
                                priority=PriorityLevel.HIGH,
                                justification=f"Database detected via {indicator}",
                                estimated_cost_monthly=100.0
                            ))
                            break
            except Exception:
                continue
        
        return requirements
    
    async def _detect_infrastructure_requirements(self, files: List[FileInfo]) -> List[ResourceRequirement]:
        """Detect infrastructure requirements from project files."""
        requirements = []
        
        # Similar to database detection but for infrastructure components
        for file_info in files[:20]:  # Limit for performance
            try:
                content = await self._read_file_content(file_info.full_path)
                
                for resource_type, pattern in self.INFRASTRUCTURE_PATTERNS.items():
                    for indicator in pattern.indicators:
                        if indicator.lower() in content.lower():
                            requirements.append(ResourceRequirement(
                                resource_type=resource_type,
                                name=f"{resource_type.value.lower().replace('_', '-')}",
                                priority=PriorityLevel.MEDIUM,
                                justification=f"Infrastructure component detected via {indicator}",
                                estimated_cost_monthly=30.0
                            ))
                            break
            except Exception:
                continue
        
        return requirements
    
    async def _analyze_security(self, files: List[FileInfo]) -> SecurityAnalysis:
        """Analyze project for security concerns."""
        security_issues = []
        recommendations = []
        compliance_level = "basic"
        
        # Check for common security issues
        config_files = [f for f in files if self._is_configuration_file(f.full_path)]
        
        for file_info in config_files[:5]:  # Limit for performance
            try:
                content = await self._read_file_content(file_info.full_path)
                
                # Check for hardcoded secrets
                secret_patterns = [
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'secret\s*=\s*["\'][^"\']+["\']',
                    r'key\s*=\s*["\'][^"\']+["\']',
                    r'token\s*=\s*["\'][^"\']+["\']'
                ]
                
                for pattern in secret_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        security_issues.append(f"Potential hardcoded secret in {file_info.relative_path}")
                        break
                
            except Exception:
                continue
        
        # Security recommendations
        recommendations.extend([
            "Use Azure Key Vault for secrets management",
            "Enable HTTPS-only communication",
            "Implement proper authentication and authorization",
            "Enable security headers and CORS policies"
        ])
        
        return SecurityAnalysis(
            security_issues=security_issues,
            recommendations=recommendations,
            compliance_level=compliance_level
        )
    
    async def _analyze_performance(self, files: List[FileInfo], project_type: ProjectType) -> PerformanceAnalysis:
        """Analyze project for performance considerations."""
        bottlenecks = []
        optimizations = []
        scaling_requirements = []
        
        # Basic performance analysis based on project type
        if project_type in [ProjectType.WEB_APPLICATION, ProjectType.FULL_STACK_APPLICATION]:
            optimizations.extend([
                "Enable CDN for static assets",
                "Implement application-level caching",
                "Use connection pooling for databases",
                "Enable compression"
            ])
            
            scaling_requirements.extend([
                "Auto-scaling for App Service",
                "Load balancing for high availability"
            ])
        
        return PerformanceAnalysis(
            potential_bottlenecks=bottlenecks,
            optimization_recommendations=optimizations,
            scaling_requirements=scaling_requirements
        )
    
    async def _analyze_compliance(self, files: List[FileInfo]) -> List[ComplianceRequirement]:
        """Analyze project for compliance requirements."""
        requirements = []
        
        # Basic compliance requirements for web applications
        requirements.append(ComplianceRequirement(
            framework="Security Baseline",
            requirements=["HTTPS enforcement", "Secure headers", "Input validation"],
            priority="medium"
        ))
        
        return requirements
    
    async def _read_file_content(self, file_path: Path) -> str:
        """Read file content safely."""
        try:
            # Try different encodings
            for encoding in ['utf-8', 'utf-8-sig', 'latin1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, return empty string
            return ""
        except Exception:
            return ""
    
    def _get_file_type(self, file_path: Path, content: str) -> str:
        """Determine file type from path and content."""
        extension = file_path.suffix.lower()
        
        # Map common extensions to types
        type_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.cs': 'csharp',
            '.java': 'java',
            '.json': 'json',
            '.xml': 'xml',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.md': 'markdown',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql',
            '.sh': 'shell',
            '.ps1': 'powershell'
        }
        
        return type_map.get(extension, 'text')
    
    def _extract_technologies(self, content: str, file_extension: str) -> List[str]:
        """Extract technologies from file content."""
        technologies = []
        
        # Technology patterns to look for
        patterns = {
            'React': ['import React', 'from "react"', 'react-dom'],
            'Angular': ['@angular/', '@Component', '@Injectable'],
            'Vue': ['Vue.js', 'vue-router', 'vuex'],
            'Express': ['express()', 'app.listen', 'require("express")'],
            'ASP.NET': ['using Microsoft.AspNetCore', '[ApiController]', 'ConfigureServices'],
            'Django': ['from django', 'django.urls', 'models.Model'],
            'Flask': ['from flask', 'Flask(__name__)', '@app.route'],
            'Spring': ['@SpringBootApplication', 'spring-boot', '@RestController'],
            'Docker': ['FROM ', 'RUN ', 'COPY '],
            'Kubernetes': ['apiVersion:', 'kind:', 'metadata:']
        }
        
        for tech, tech_patterns in patterns.items():
            if any(pattern in content for pattern in tech_patterns):
                technologies.append(tech)
        
        return technologies
    
    def _check_file_security(self, content: str, file_type: str) -> List[str]:
        """Check file for security issues."""
        issues = []
        
        # Common security issues
        if re.search(r'password\s*=\s*["\'][^"\']+["\']', content, re.IGNORECASE):
            issues.append("Hardcoded password detected")
        
        if re.search(r'api[_-]?key\s*=\s*["\'][^"\']+["\']', content, re.IGNORECASE):
            issues.append("Hardcoded API key detected")
        
        if 'eval(' in content:
            issues.append("Use of eval() function (security risk)")
        
        return issues
    
    def _is_configuration_file(self, file_path: Path) -> bool:
        """Check if file is a configuration file."""
        config_files = {
            'package.json', 'requirements.txt', 'pom.xml', 'build.gradle',
            'appsettings.json', 'web.config', 'app.config', 'settings.py',
            'config.json', 'config.yml', 'config.yaml', '.env'
        }
        
        return file_path.name.lower() in config_files or file_path.suffix in ['.config', '.ini', '.properties']
    
    def _parse_configuration(self, content: str, file_extension: str) -> Dict[str, Any]:
        """Parse configuration file content."""
        try:
            if file_extension in ['.json']:
                return json.loads(content)
            elif file_extension in ['.yml', '.yaml']:
                return yaml.safe_load(content)
            elif file_extension == '.xml':
                root = ET.fromstring(content)
                return {'xml_root': root.tag}
        except Exception:
            pass
        
        return {}
    
    # ==================== CHANGE DETECTION METHODS ====================
    
    def compute_file_hash(self, file_path: Path) -> Optional[str]:
        """Compute SHA-256 hash of a file for change detection."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to compute hash for {file_path}: {e}")
            return None
    
    def analyze_project_changes(
        self, 
        project_path: Path, 
        previous_manifest: Optional[TemplateUpdateManifest] = None
    ) -> TemplateUpdateManifest:
        """
        Analyze project for changes since last analysis.
        
        Args:
            project_path: Root path of the project
            previous_manifest: Previous update manifest (if any)
            
        Returns:
            Updated manifest with detected changes
        """
        logger.info(f"Analyzing project changes in {project_path}")
        
        # Initialize or update manifest
        if previous_manifest is None:
            manifest = TemplateUpdateManifest(
                project_path=project_path,
                project_name=project_path.name
            )
        else:
            manifest = previous_manifest
        
        # Track previous file states
        previous_files = {fc.file_path: fc for fc in manifest.file_changes}
        
        # Scan all project files
        scanner = FileScanner()
        current_files = scanner.scan_directory(project_path)
        
        # Detect file changes
        file_changes = self._detect_file_changes(current_files, previous_files)
        
        # Add new file changes to manifest
        for change in file_changes:
            manifest.add_file_change(change)
        
        # Analyze resource changes based on file changes
        resource_changes = self._detect_resource_changes(file_changes, project_path)
        
        # Add resource changes to manifest
        for change in resource_changes:
            manifest.add_resource_change(change)
        
        # Update analysis timestamp
        manifest.last_analysis_run = datetime.utcnow()
        manifest.updated_at = datetime.utcnow()
        
        logger.info(f"Detected {len(file_changes)} file changes and {len(resource_changes)} resource changes")
        
        return manifest
    
    def _detect_file_changes(
        self, 
        current_files: List[FileInfo], 
        previous_files: Dict[Path, FileChange]
    ) -> List[FileChange]:
        """Detect changes in project files."""
        changes = []
        current_paths = {f.path for f in current_files}
        previous_paths = set(previous_files.keys())
        
        # Detect new files
        new_files = current_paths - previous_paths
        for file_path in new_files:
            file_info = next(f for f in current_files if f.path == file_path)
            changes.append(FileChange(
                file_path=file_path,
                change_type="added",
                hash_after=self.compute_file_hash(file_path),
                lines_added=self._count_lines(file_path)
            ))
        
        # Detect deleted files
        deleted_files = previous_paths - current_paths
        for file_path in deleted_files:
            previous_change = previous_files[file_path]
            changes.append(FileChange(
                file_path=file_path,
                change_type="deleted",
                hash_before=previous_change.hash_after,
                lines_removed=previous_change.lines_added
            ))
        
        # Detect modified files
        common_files = current_paths & previous_paths
        for file_path in common_files:
            current_hash = self.compute_file_hash(file_path)
            previous_change = previous_files[file_path]
            
            if current_hash != previous_change.hash_after:
                current_lines = self._count_lines(file_path)
                previous_lines = previous_change.lines_added
                
                changes.append(FileChange(
                    file_path=file_path,
                    change_type="modified",
                    hash_before=previous_change.hash_after,
                    hash_after=current_hash,
                    lines_added=max(0, current_lines - previous_lines),
                    lines_removed=max(0, previous_lines - current_lines),
                    affected_functions=self._detect_function_changes(file_path),
                    affected_dependencies=self._detect_dependency_changes(file_path)
                ))
        
        return changes
    
    def _detect_resource_changes(
        self, 
        file_changes: List[FileChange], 
        project_path: Path
    ) -> List[ResourceChange]:
        """Detect Azure resource changes based on file modifications."""
        resource_changes = []
        
        for file_change in file_changes:
            # Analyze different file types for resource implications
            if self._is_infrastructure_file(file_change.file_path):
                changes = self._analyze_infrastructure_changes(file_change, project_path)
                resource_changes.extend(changes)
            
            elif self._is_configuration_file(file_change.file_path):
                changes = self._analyze_configuration_changes(file_change, project_path)
                resource_changes.extend(changes)
            
            elif self._is_code_file(file_change.file_path):
                changes = self._analyze_code_changes(file_change, project_path)
                resource_changes.extend(changes)
        
        return resource_changes
    
    def _is_infrastructure_file(self, file_path: Path) -> bool:
        """Check if file is related to infrastructure."""
        infra_patterns = [
            'bicep', 'arm', 'terraform', 'cloudformation',
            'docker', 'kubernetes', 'helm', 'yaml', 'yml'
        ]
        
        return (
            any(pattern in file_path.name.lower() for pattern in infra_patterns) or
            file_path.suffix.lower() in ['.bicep', '.json', '.tf', '.yaml', '.yml'] or
            'infrastructure' in str(file_path).lower() or
            'deploy' in str(file_path).lower()
        )
    
    def _is_code_file(self, file_path: Path) -> bool:
        """Check if file contains application code."""
        code_extensions = {'.py', '.js', '.ts', '.cs', '.java', '.go', '.rb', '.php'}
        return file_path.suffix.lower() in code_extensions
    
    def _analyze_infrastructure_changes(
        self, 
        file_change: FileChange, 
        project_path: Path
    ) -> List[ResourceChange]:
        """Analyze infrastructure file changes for resource impact."""
        changes = []
        
        try:
            content = self._read_file_safely(file_change.file_path)
            
            # For Bicep files, analyze resource definitions
            if file_change.file_path.suffix.lower() == '.bicep':
                changes.extend(self._analyze_bicep_changes(file_change, content))
            
            # For ARM templates
            elif file_change.file_path.suffix.lower() == '.json' and 'template' in content:
                changes.extend(self._analyze_arm_changes(file_change, content))
            
            # For Docker files
            elif 'dockerfile' in file_change.file_path.name.lower():
                changes.extend(self._analyze_docker_changes(file_change, content))
            
            # For Kubernetes manifests
            elif file_change.file_path.suffix.lower() in ['.yaml', '.yml']:
                changes.extend(self._analyze_k8s_changes(file_change, content))
        
        except Exception as e:
            logger.warning(f"Failed to analyze infrastructure changes in {file_change.file_path}: {e}")
        
        return changes
    
    def _analyze_configuration_changes(
        self, 
        file_change: FileChange, 
        project_path: Path
    ) -> List[ResourceChange]:
        """Analyze configuration file changes for resource impact."""
        changes = []
        
        try:
            content = self._read_file_safely(file_change.file_path)
            
            # Package.json changes
            if file_change.file_path.name == 'package.json':
                changes.extend(self._analyze_package_json_changes(file_change, content))
            
            # Requirements.txt changes
            elif file_change.file_path.name == 'requirements.txt':
                changes.extend(self._analyze_requirements_changes(file_change, content))
            
            # App settings changes
            elif 'appsettings' in file_change.file_path.name.lower():
                changes.extend(self._analyze_app_settings_changes(file_change, content))
            
            # Environment files
            elif file_change.file_path.name.startswith('.env'):
                changes.extend(self._analyze_env_changes(file_change, content))
        
        except Exception as e:
            logger.warning(f"Failed to analyze configuration changes in {file_change.file_path}: {e}")
        
        return changes
    
    def _analyze_code_changes(
        self, 
        file_change: FileChange, 
        project_path: Path
    ) -> List[ResourceChange]:
        """Analyze code file changes for resource impact."""
        changes = []
        
        try:
            content = self._read_file_safely(file_change.file_path)
            
            # Look for Azure SDK usage changes
            azure_patterns = {
                'Azure Storage': ['BlobServiceClient', 'TableServiceClient', 'QueueServiceClient'],
                'Azure SQL': ['SqlConnection', 'pyodbc', 'mssql'],
                'Azure KeyVault': ['SecretClient', 'KeyClient', 'CertificateClient'],
                'Azure ServiceBus': ['ServiceBusClient', 'ServiceBusSender', 'ServiceBusReceiver'],
                'Azure Functions': ['func.', 'azure-functions', '@azure/functions']
            }
            
            for service, patterns in azure_patterns.items():
                if any(pattern in content for pattern in patterns):
                    changes.append(ResourceChange(
                        resource_type=self._map_service_to_resource_type(service),
                        resource_name=f"{service.lower().replace(' ', '_')}_resource",
                        change_type=ChangeType.DEPENDENCY_ADDED if file_change.change_type == "added" else ChangeType.DEPENDENCY_MODIFIED,
                        severity=ChangeSeverity.MEDIUM,
                        impact=ChangeImpact.LOCAL,
                        property_path=f"code.{service}",
                        new_value=f"Usage detected in {file_change.file_path.name}"
                    ))
        
        except Exception as e:
            logger.warning(f"Failed to analyze code changes in {file_change.file_path}: {e}")
        
        return changes
    
    def _analyze_bicep_changes(self, file_change: FileChange, content: str) -> List[ResourceChange]:
        """Analyze Bicep file changes."""
        changes = []
        
        # Extract resource definitions
        resource_pattern = r'resource\s+(\w+)\s+\'([^\']+)\'\s*='
        matches = re.findall(resource_pattern, content)
        
        for name, resource_type in matches:
            changes.append(ResourceChange(
                resource_type=resource_type,
                resource_name=name,
                change_type=ChangeType.RESOURCE_ADDED if file_change.change_type == "added" else ChangeType.RESOURCE_MODIFIED,
                severity=ChangeSeverity.HIGH,
                impact=ChangeImpact.REGIONAL,
                requires_validation=True,
                requires_redeployment=True
            ))
        
        return changes
    
    def _analyze_arm_changes(self, file_change: FileChange, content: str) -> List[ResourceChange]:
        """Analyze ARM template changes."""
        changes = []
        
        try:
            template = json.loads(content)
            resources = template.get('resources', [])
            
            for resource in resources:
                resource_type = resource.get('type', 'Unknown')
                resource_name = resource.get('name', 'unnamed')
                
                changes.append(ResourceChange(
                    resource_type=resource_type,
                    resource_name=resource_name,
                    change_type=ChangeType.RESOURCE_ADDED if file_change.change_type == "added" else ChangeType.RESOURCE_MODIFIED,
                    severity=ChangeSeverity.HIGH,
                    impact=ChangeImpact.REGIONAL,
                    requires_validation=True,
                    requires_redeployment=True
                ))
        
        except json.JSONDecodeError:
            pass
        
        return changes
    
    def _analyze_docker_changes(self, file_change: FileChange, content: str) -> List[ResourceChange]:
        """Analyze Dockerfile changes."""
        changes = []
        
        # Docker changes typically affect container registry and app service
        if 'FROM ' in content:
            changes.append(ResourceChange(
                resource_type='Microsoft.ContainerRegistry/registries',
                resource_name='container_registry',
                change_type=ChangeType.DEPENDENCY_MODIFIED,
                severity=ChangeSeverity.MEDIUM,
                impact=ChangeImpact.LOCAL,
                property_path='docker.base_image'
            ))
        
        return changes
    
    def _analyze_k8s_changes(self, file_change: FileChange, content: str) -> List[ResourceChange]:
        """Analyze Kubernetes manifest changes."""
        changes = []
        
        try:
            # Parse YAML content
            docs = yaml.safe_load_all(content)
            
            for doc in docs:
                if isinstance(doc, dict) and 'kind' in doc:
                    kind = doc['kind']
                    name = doc.get('metadata', {}).get('name', 'unnamed')
                    
                    changes.append(ResourceChange(
                        resource_type=f'Kubernetes.{kind}',
                        resource_name=name,
                        change_type=ChangeType.RESOURCE_MODIFIED,
                        severity=ChangeSeverity.MEDIUM,
                        impact=ChangeImpact.DEPENDENT
                    ))
        
        except yaml.YAMLError:
            pass
        
        return changes
    
    def _analyze_package_json_changes(self, file_change: FileChange, content: str) -> List[ResourceChange]:
        """Analyze package.json changes."""
        changes = []
        
        try:
            package_data = json.loads(content)
            dependencies = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
            
            # Look for Azure-related dependencies
            azure_packages = [pkg for pkg in dependencies.keys() if 'azure' in pkg.lower()]
            
            if azure_packages:
                changes.append(ResourceChange(
                    resource_type='Application.Dependencies',
                    resource_name='azure_sdk_packages',
                    change_type=ChangeType.DEPENDENCY_MODIFIED,
                    severity=ChangeSeverity.MEDIUM,
                    impact=ChangeImpact.LOCAL,
                    new_value=azure_packages
                ))
        
        except json.JSONDecodeError:
            pass
        
        return changes
    
    def _analyze_requirements_changes(self, file_change: FileChange, content: str) -> List[ResourceChange]:
        """Analyze requirements.txt changes."""
        changes = []
        
        lines = content.split('\n')
        azure_packages = [line.strip() for line in lines if 'azure' in line.lower()]
        
        if azure_packages:
            changes.append(ResourceChange(
                resource_type='Application.Dependencies',
                resource_name='azure_sdk_packages',
                change_type=ChangeType.DEPENDENCY_MODIFIED,
                severity=ChangeSeverity.MEDIUM,
                impact=ChangeImpact.LOCAL,
                new_value=azure_packages
            ))
        
        return changes
    
    def _analyze_app_settings_changes(self, file_change: FileChange, content: str) -> List[ResourceChange]:
        """Analyze application settings changes."""
        changes = []
        
        try:
            settings = json.loads(content)
            
            # Look for connection strings or Azure service configurations
            connection_strings = settings.get('ConnectionStrings', {})
            
            for key, value in connection_strings.items():
                if any(service in value.lower() for service in ['database', 'storage', 'servicebus']):
                    changes.append(ResourceChange(
                        resource_type='Application.Configuration',
                        resource_name=f'connection_string_{key.lower()}',
                        change_type=ChangeType.CONFIGURATION_CHANGED,
                        severity=ChangeSeverity.HIGH,
                        impact=ChangeImpact.GLOBAL,
                        property_path=f'ConnectionStrings.{key}',
                        requires_validation=True
                    ))
        
        except json.JSONDecodeError:
            pass
        
        return changes
    
    def _analyze_env_changes(self, file_change: FileChange, content: str) -> List[ResourceChange]:
        """Analyze environment file changes."""
        changes = []
        
        lines = content.split('\n')
        
        for line in lines:
            if '=' in line and not line.startswith('#'):
                key, _ = line.split('=', 1)
                key = key.strip()
                
                # Look for Azure-related environment variables
                if any(keyword in key.upper() for keyword in ['AZURE', 'CONNECTION', 'ENDPOINT', 'KEY', 'SECRET']):
                    changes.append(ResourceChange(
                        resource_type='Application.Configuration',
                        resource_name=f'env_var_{key.lower()}',
                        change_type=ChangeType.CONFIGURATION_CHANGED,
                        severity=ChangeSeverity.MEDIUM,
                        impact=ChangeImpact.GLOBAL,
                        property_path=f'Environment.{key}'
                    ))
        
        return changes
    
    def _detect_function_changes(self, file_path: Path) -> List[str]:
        """Detect changed functions in a code file."""
        functions = []
        
        try:
            content = self._read_file_safely(file_path)
            
            # Python function detection
            if file_path.suffix == '.py':
                matches = re.findall(r'def\s+(\w+)', content)
                functions.extend(matches)
            
            # JavaScript/TypeScript function detection
            elif file_path.suffix in ['.js', '.ts']:
                matches = re.findall(r'function\s+(\w+)|const\s+(\w+)\s*=|(\w+):\s*function', content)
                functions.extend([match for group in matches for match in group if match])
            
            # C# method detection
            elif file_path.suffix == '.cs':
                matches = re.findall(r'(public|private|protected|internal)\s+\w+\s+(\w+)\s*\(', content)
                functions.extend([match[1] for match in matches])
        
        except Exception:
            pass
        
        return functions
    
    def _detect_dependency_changes(self, file_path: Path) -> List[str]:
        """Detect changed dependencies in a file."""
        dependencies = []
        
        try:
            content = self._read_file_safely(file_path)
            
            # Python imports
            if file_path.suffix == '.py':
                matches = re.findall(r'(?:from\s+(\S+)\s+import|import\s+(\S+))', content)
                dependencies.extend([match for group in matches for match in group if match])
            
            # JavaScript/TypeScript imports
            elif file_path.suffix in ['.js', '.ts']:
                matches = re.findall(r'import\s+.+\s+from\s+[\'"]([^\'"]+)[\'"]', content)
                dependencies.extend(matches)
            
            # C# using statements
            elif file_path.suffix == '.cs':
                matches = re.findall(r'using\s+([^;]+);', content)
                dependencies.extend(matches)
        
        except Exception:
            pass
        
        return dependencies
    
    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except Exception:
            return 0
    
    def _map_service_to_resource_type(self, service: str) -> str:
        """Map Azure service to resource type."""
        mapping = {
            'Azure Storage': 'Microsoft.Storage/storageAccounts',
            'Azure SQL': 'Microsoft.Sql/servers',
            'Azure KeyVault': 'Microsoft.KeyVault/vaults',
            'Azure ServiceBus': 'Microsoft.ServiceBus/namespaces',
            'Azure Functions': 'Microsoft.Web/sites'
        }
        
        return mapping.get(service, 'Microsoft.Resources/unknown')