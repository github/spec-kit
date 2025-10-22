"""Project file scanner utility for analyzing code files.

This module provides functionality to scan project files and identify
Azure service dependencies and requirements.
"""

import os
import re
import json
import logging
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FileType(Enum):
    """Supported file types for analysis."""
    CODE = "code"
    CONFIG = "config"
    DOCUMENTATION = "documentation"
    SCRIPT = "script"
    UNKNOWN = "unknown"


@dataclass
class FileAnalysis:
    """Analysis result for a single file."""
    path: Path
    file_type: FileType
    size: int
    azure_services: Set[str]
    dependencies: Set[str]
    frameworks: Set[str]
    confidence: float


@dataclass
class ProjectAnalysisResult:
    """Complete project analysis result."""
    project_path: Path
    total_files: int
    analyzed_files: int
    detected_services: Set[str]
    detected_frameworks: Set[str]
    file_analyses: List[FileAnalysis]
    confidence_score: float


class ProjectFileScanner:
    """Scanner for analyzing project files to detect Azure service requirements."""
    
    # File extensions to analyze
    CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.cs', '.java', '.go', '.rs', '.rb', '.php',
        '.cpp', '.c', '.h', '.hpp', '.swift', '.kt', '.scala', '.clj'
    }
    
    CONFIG_EXTENSIONS = {
        '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', 
        '.xml', '.properties', '.env'
    }
    
    SCRIPT_EXTENSIONS = {
        '.sh', '.bash', '.ps1', '.cmd', '.bat', '.zsh', '.fish'
    }
    
    DOC_EXTENSIONS = {
        '.md', '.txt', '.rst', '.adoc', '.tex'
    }
    
    # Azure service patterns
    AZURE_SERVICE_PATTERNS = {
        'Microsoft.Storage/storageAccounts': [
            r'azure\.storage',
            r'BlobServiceClient',
            r'StorageAccount',
            r'blob\.core\.windows\.net',
            r'storage.*account'
        ],
        'Microsoft.Web/sites': [
            r'azure\.web',
            r'App.*Service',
            r'WebApp',
            r'azurewebsites\.net',
            r'webapp.*deploy'
        ],
        'Microsoft.KeyVault/vaults': [
            r'azure\.keyvault',
            r'KeyVaultClient',
            r'vault\.azure\.net',
            r'key.*vault',
            r'secrets.*management'
        ],
        'Microsoft.Sql/servers': [
            r'azure\.sql',
            r'SqlConnection',
            r'database\.windows\.net',
            r'sql.*server',
            r'azure.*database'
        ],
        'Microsoft.Insights/components': [
            r'application.*insights',
            r'ApplicationInsights',
            r'telemetry',
            r'monitoring',
            r'instrumentation.*key'
        ]
    }
    
    # Framework patterns
    FRAMEWORK_PATTERNS = {
        'ASP.NET Core': [
            r'Microsoft\.AspNetCore',
            r'app\.UseRouting',
            r'services\.AddControllers',
            r'WebApplication\.CreateBuilder'
        ],
        'Express.js': [
            r'express\(\)',
            r'app\.get\(',
            r'require\([\'"]express[\'"]',
            r'app\.listen\('
        ],
        'Spring Boot': [
            r'@SpringBootApplication',
            r'SpringApplication\.run',
            r'spring-boot-starter',
            r'@RestController'
        ],
        'Django': [
            r'django\.urls',
            r'from django',
            r'INSTALLED_APPS',
            r'django\.contrib'
        ],
        'Flask': [
            r'from flask',
            r'Flask\(__name__\)',
            r'app\.route\(',
            r'@app\.route'
        ]
    }
    
    def __init__(self, max_file_size: int = 1024 * 1024):  # 1MB limit
        """Initialize the file scanner.
        
        Args:
            max_file_size: Maximum file size to analyze in bytes.
        """
        self.max_file_size = max_file_size
        self.excluded_dirs = {
            '.git', '.svn', '.hg', 'node_modules', '__pycache__', 
            '.venv', 'venv', 'env', 'target', 'build', 'dist',
            'bin', 'obj', '.vs', '.idea'
        }
    
    def scan_project(self, project_path: Path) -> ProjectAnalysisResult:
        """Scan a project directory for Azure service indicators.
        
        Args:
            project_path: Path to the project root directory.
            
        Returns:
            ProjectAnalysisResult with detected services and analysis.
        """
        logger.info(f"Starting project scan of {project_path}")
        
        if not project_path.exists() or not project_path.is_dir():
            raise ValueError(f"Project path does not exist or is not a directory: {project_path}")
        
        file_analyses = []
        all_services = set()
        all_frameworks = set()
        total_files = 0
        analyzed_files = 0
        
        for file_path in self._get_files_to_analyze(project_path):
            total_files += 1
            
            try:
                analysis = self._analyze_file(file_path)
                if analysis:
                    file_analyses.append(analysis)
                    all_services.update(analysis.azure_services)
                    all_frameworks.update(analysis.frameworks)
                    analyzed_files += 1
                    
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        # Calculate overall confidence score
        if analyzed_files > 0:
            avg_confidence = sum(f.confidence for f in file_analyses) / analyzed_files
        else:
            avg_confidence = 0.0
        
        logger.info(f"Scan complete: {analyzed_files}/{total_files} files analyzed")
        logger.info(f"Detected services: {', '.join(all_services) if all_services else 'None'}")
        
        return ProjectAnalysisResult(
            project_path=project_path,
            total_files=total_files,
            analyzed_files=analyzed_files,
            detected_services=all_services,
            detected_frameworks=all_frameworks,
            file_analyses=file_analyses,
            confidence_score=avg_confidence
        )
    
    def _get_files_to_analyze(self, project_path: Path) -> List[Path]:
        """Get list of files to analyze, excluding common build/dependency directories.
        
        Args:
            project_path: Project root path.
            
        Returns:
            List of file paths to analyze.
        """
        files_to_analyze = []
        
        for root, dirs, files in os.walk(project_path):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            
            root_path = Path(root)
            
            for file_name in files:
                file_path = root_path / file_name
                
                # Skip files that are too large
                try:
                    if file_path.stat().st_size > self.max_file_size:
                        continue
                except OSError:
                    continue
                
                # Check if file should be analyzed
                if self._should_analyze_file(file_path):
                    files_to_analyze.append(file_path)
        
        return files_to_analyze
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if a file should be analyzed.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            True if file should be analyzed.
        """
        suffix = file_path.suffix.lower()
        
        return (suffix in self.CODE_EXTENSIONS or 
                suffix in self.CONFIG_EXTENSIONS or
                suffix in self.SCRIPT_EXTENSIONS or
                suffix in self.DOC_EXTENSIONS)
    
    def _analyze_file(self, file_path: Path) -> Optional[FileAnalysis]:
        """Analyze a single file for Azure service indicators.
        
        Args:
            file_path: Path to the file to analyze.
            
        Returns:
            FileAnalysis object or None if analysis failed.
        """
        try:
            # Determine file type
            file_type = self._get_file_type(file_path)
            
            # Read file content
            content = self._read_file_safely(file_path)
            if content is None:
                return None
            
            # Analyze content for Azure services
            azure_services = self._detect_azure_services(content)
            
            # Analyze content for frameworks
            frameworks = self._detect_frameworks(content)
            
            # Analyze dependencies
            dependencies = self._detect_dependencies(content, file_path)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(azure_services, frameworks, dependencies, file_type)
            
            return FileAnalysis(
                path=file_path,
                file_type=file_type,
                size=file_path.stat().st_size,
                azure_services=azure_services,
                dependencies=dependencies,
                frameworks=frameworks,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return None
    
    def _get_file_type(self, file_path: Path) -> FileType:
        """Determine the type of a file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            FileType enum value.
        """
        suffix = file_path.suffix.lower()
        
        if suffix in self.CODE_EXTENSIONS:
            return FileType.CODE
        elif suffix in self.CONFIG_EXTENSIONS:
            return FileType.CONFIG
        elif suffix in self.SCRIPT_EXTENSIONS:
            return FileType.SCRIPT
        elif suffix in self.DOC_EXTENSIONS:
            return FileType.DOCUMENTATION
        else:
            return FileType.UNKNOWN
    
    def _read_file_safely(self, file_path: Path) -> Optional[str]:
        """Safely read file content with proper encoding handling.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            File content as string or None if read failed.
        """
        encodings = ['utf-8', 'utf-16', 'latin-1', 'ascii']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")
                break
        
        return None
    
    def _detect_azure_services(self, content: str) -> Set[str]:
        """Detect Azure services mentioned in file content.
        
        Args:
            content: File content to analyze.
            
        Returns:
            Set of detected Azure service types.
        """
        detected_services = set()
        
        for service_type, patterns in self.AZURE_SERVICE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    detected_services.add(service_type)
                    break
        
        return detected_services
    
    def _detect_frameworks(self, content: str) -> Set[str]:
        """Detect frameworks used in the project.
        
        Args:
            content: File content to analyze.
            
        Returns:
            Set of detected frameworks.
        """
        detected_frameworks = set()
        
        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    detected_frameworks.add(framework)
                    break
        
        return detected_frameworks
    
    def _detect_dependencies(self, content: str, file_path: Path) -> Set[str]:
        """Detect dependencies from package files.
        
        Args:
            content: File content to analyze.
            file_path: Path to the file.
            
        Returns:
            Set of detected dependencies.
        """
        dependencies = set()
        file_name = file_path.name.lower()
        
        # Python dependencies
        if file_name in ('requirements.txt', 'pyproject.toml', 'setup.py'):
            dependencies.update(self._parse_python_dependencies(content))
        
        # Node.js dependencies
        elif file_name == 'package.json':
            dependencies.update(self._parse_nodejs_dependencies(content))
        
        # .NET dependencies
        elif file_path.suffix.lower() in ('.csproj', '.fsproj', '.vbproj'):
            dependencies.update(self._parse_dotnet_dependencies(content))
        
        return dependencies
    
    def _parse_python_dependencies(self, content: str) -> Set[str]:
        """Parse Python dependencies from various files."""
        deps = set()
        
        # Simple requirement lines
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name (before ==, >=, etc.)
                match = re.match(r'^([a-zA-Z0-9_-]+)', line)
                if match:
                    deps.add(match.group(1))
        
        return deps
    
    def _parse_nodejs_dependencies(self, content: str) -> Set[str]:
        """Parse Node.js dependencies from package.json."""
        deps = set()
        
        try:
            package_data = json.loads(content)
            for dep_type in ['dependencies', 'devDependencies']:
                if dep_type in package_data:
                    deps.update(package_data[dep_type].keys())
        except json.JSONDecodeError:
            pass
        
        return deps
    
    def _parse_dotnet_dependencies(self, content: str) -> Set[str]:
        """Parse .NET dependencies from project files."""
        deps = set()
        
        # Look for PackageReference elements
        package_refs = re.findall(r'<PackageReference\s+Include="([^"]+)"', content, re.IGNORECASE)
        deps.update(package_refs)
        
        return deps
    
    def _calculate_confidence(self, azure_services: Set[str], frameworks: Set[str], 
                            dependencies: Set[str], file_type: FileType) -> float:
        """Calculate confidence score for the analysis.
        
        Args:
            azure_services: Detected Azure services.
            frameworks: Detected frameworks.
            dependencies: Detected dependencies.
            file_type: Type of the file.
            
        Returns:
            Confidence score between 0.0 and 1.0.
        """
        score = 0.0
        
        # Base score by file type
        type_scores = {
            FileType.CODE: 0.8,
            FileType.CONFIG: 0.9,
            FileType.SCRIPT: 0.7,
            FileType.DOCUMENTATION: 0.5,
            FileType.UNKNOWN: 0.3
        }
        score = type_scores.get(file_type, 0.3)
        
        # Boost score based on detections
        if azure_services:
            score = min(1.0, score + 0.2 * len(azure_services))
        
        if frameworks:
            score = min(1.0, score + 0.1 * len(frameworks))
        
        if dependencies:
            score = min(1.0, score + 0.05 * min(len(dependencies), 10))
        
        return round(score, 2)