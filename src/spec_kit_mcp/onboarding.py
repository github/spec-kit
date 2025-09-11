#!/usr/bin/env python3
"""
Onboarding functionality for existing projects to adopt spec-driven development.

This module provides tools to analyze existing projects, parse their documentation,
extract requirements, and help migrate them to the spec-kit workflow.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)

# Common file patterns to analyze
DOCUMENTATION_PATTERNS = [
    "README*",
    "*.md", 
    "*.txt",
    "*.rst",
    "*.doc*",
    "CHANGELOG*",
    "CONTRIBUTING*",
    "docs/**/*",
    "documentation/**/*",
]

CODE_PATTERNS = [
    "*.py",
    "*.js", 
    "*.ts",
    "*.java",
    "*.cs",
    "*.cpp",
    "*.c",
    "*.h",
    "*.hpp",
    "package.json",
    "pyproject.toml",
    "requirements*.txt",
    "Dockerfile*",
    "docker-compose*",
]

CONFIG_PATTERNS = [
    "*.yml",
    "*.yaml", 
    "*.json",
    "*.toml",
    "*.ini",
    "*.cfg",
    ".env*",
    "Makefile",
    ".github/**/*",
    ".gitlab/**/*",
]


def analyze_project_structure(project_path: Path, max_depth: int = 3) -> Dict[str, Any]:
    """
    Analyze the structure of an existing project to understand its organization.
    
    Args:
        project_path: Path to the project directory
        max_depth: Maximum directory depth to scan
        
    Returns:
        Dictionary containing project structure analysis
    """
    if not project_path.exists() or not project_path.is_dir():
        raise ValueError(f"Project path does not exist or is not a directory: {project_path}")
    
    analysis = {
        "project_path": str(project_path),
        "project_name": project_path.name,
        "structure": {},
        "documentation_files": [],
        "code_files": [],
        "config_files": [],
        "languages_detected": set(),
        "frameworks_detected": set(),
        "build_systems": set(),
        "has_tests": False,
        "has_ci_cd": False,
        "estimated_size": "unknown",
    }
    
    # Scan directory structure
    try:
        file_count = 0
        dir_count = 0
        
        for item in project_path.rglob("*"):
            if item.is_dir():
                dir_count += 1
                # Skip deep directories and common ignore patterns
                if len(item.parts) - len(project_path.parts) > max_depth:
                    continue
                if any(skip in item.name for skip in ['.git', 'node_modules', '__pycache__', '.venv', 'venv']):
                    continue
            else:
                file_count += 1
                _categorize_file(item, project_path, analysis)
        
        # Estimate project size
        if file_count < 50:
            analysis["estimated_size"] = "small"
        elif file_count < 500:
            analysis["estimated_size"] = "medium"
        else:
            analysis["estimated_size"] = "large"
            
        analysis["file_count"] = file_count
        analysis["dir_count"] = dir_count
        
    except Exception as e:
        logger.warning(f"Error scanning project structure: {e}")
        analysis["scan_error"] = str(e)
    
    # Convert sets to lists for JSON serialization
    analysis["languages_detected"] = list(analysis["languages_detected"])
    analysis["frameworks_detected"] = list(analysis["frameworks_detected"])
    analysis["build_systems"] = list(analysis["build_systems"])
    
    return analysis


def _categorize_file(file_path: Path, project_root: Path, analysis: Dict[str, Any]) -> None:
    """Categorize a file and update analysis."""
    relative_path = file_path.relative_to(project_root)
    file_name = file_path.name.lower()
    file_ext = file_path.suffix.lower()
    
    # Categorize by type
    if _matches_patterns(file_name, DOCUMENTATION_PATTERNS):
        analysis["documentation_files"].append(str(relative_path))
    elif _matches_patterns(file_name, CODE_PATTERNS) or file_ext in ['.py', '.js', '.ts', '.java', '.cs', '.cpp', '.c', '.h']:
        analysis["code_files"].append(str(relative_path))
    elif _matches_patterns(file_name, CONFIG_PATTERNS):
        analysis["config_files"].append(str(relative_path))
    
    # Detect languages
    language_map = {
        '.py': 'Python',
        '.js': 'JavaScript', 
        '.ts': 'TypeScript',
        '.java': 'Java',
        '.cs': 'C#',
        '.cpp': 'C++',
        '.c': 'C',
        '.go': 'Go',
        '.rs': 'Rust',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
    }
    if file_ext in language_map:
        analysis["languages_detected"].add(language_map[file_ext])
    
    # Detect frameworks and tools
    if file_name == 'package.json':
        analysis["frameworks_detected"].add("Node.js")
        analysis["build_systems"].add("npm/yarn")
    elif file_name == 'pyproject.toml':
        analysis["build_systems"].add("Python (pyproject.toml)")
    elif file_name.startswith('requirements'):
        analysis["build_systems"].add("pip")
    elif file_name == 'dockerfile':
        analysis["frameworks_detected"].add("Docker")
    elif 'docker-compose' in file_name:
        analysis["frameworks_detected"].add("Docker Compose")
    elif file_name == 'makefile':
        analysis["build_systems"].add("Make")
    elif file_name in ['pom.xml', 'build.gradle']:
        analysis["build_systems"].add("Maven/Gradle")
    
    # Check for tests
    if 'test' in file_name or 'spec' in file_name or '/test' in str(relative_path):
        analysis["has_tests"] = True
    
    # Check for CI/CD
    if '.github' in str(relative_path) or '.gitlab' in str(relative_path) or file_name in ['jenkinsfile', '.travis.yml', '.circleci']:
        analysis["has_ci_cd"] = True


def _matches_patterns(filename: str, patterns: List[str]) -> bool:
    """Check if filename matches any of the given patterns."""
    import fnmatch
    for pattern in patterns:
        if fnmatch.fnmatch(filename.lower(), pattern.lower()):
            return True
    return False


def parse_existing_documentation(project_path: Path, file_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Parse existing documentation files to extract requirements and specifications.
    
    Args:
        project_path: Path to the project directory
        file_patterns: Optional list of file patterns to search for
        
    Returns:
        Dictionary containing parsed documentation content
    """
    if file_patterns is None:
        file_patterns = DOCUMENTATION_PATTERNS
    
    parsed_docs = {
        "project_path": str(project_path),
        "files_parsed": [],
        "content_sections": {},
        "requirements_found": [],
        "features_found": [],
        "user_stories_found": [],
        "api_endpoints_found": [],
        "technologies_mentioned": set(),
        "parsing_errors": [],
    }
    
    try:
        for pattern in file_patterns:
            for file_path in project_path.rglob(pattern):
                if file_path.is_file() and _is_text_file(file_path):
                    try:
                        _parse_documentation_file(file_path, project_path, parsed_docs)
                    except Exception as e:
                        error_msg = f"Error parsing {file_path}: {e}"
                        logger.warning(error_msg)
                        parsed_docs["parsing_errors"].append(error_msg)
                        
    except Exception as e:
        error_msg = f"Error during documentation parsing: {e}"
        logger.error(error_msg)
        parsed_docs["parsing_errors"].append(error_msg)
    
    # Convert sets to lists for JSON serialization
    parsed_docs["technologies_mentioned"] = list(parsed_docs["technologies_mentioned"])
    
    return parsed_docs


def _is_text_file(file_path: Path) -> bool:
    """Check if a file is likely to be a text file."""
    try:
        # Try to read first few bytes to check if it's text
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\x00' in chunk:  # Null bytes indicate binary
                return False
            # Try to decode as UTF-8
            chunk.decode('utf-8')
            return True
    except (UnicodeDecodeError, IOError):
        return False


def _parse_documentation_file(file_path: Path, project_root: Path, parsed_docs: Dict[str, Any]) -> None:
    """Parse a single documentation file and extract relevant information."""
    relative_path = str(file_path.relative_to(project_root))
    parsed_docs["files_parsed"].append(relative_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try with different encoding
        with open(file_path, 'r', encoding='latin-1') as f:
            content = f.read()
    
    # Store content sections
    parsed_docs["content_sections"][relative_path] = {
        "content": content,
        "headings": _extract_headings(content),
        "word_count": len(content.split()),
    }
    
    # Extract requirements-like content
    _extract_requirements_patterns(content, parsed_docs)
    _extract_feature_patterns(content, parsed_docs)
    _extract_user_story_patterns(content, parsed_docs)
    _extract_api_patterns(content, parsed_docs)
    _extract_technology_mentions(content, parsed_docs)


def _extract_headings(content: str) -> List[str]:
    """Extract markdown-style headings from content."""
    headings = []
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('#'):
            headings.append(line)
    return headings


def _extract_requirements_patterns(content: str, parsed_docs: Dict[str, Any]) -> None:
    """Extract text that looks like requirements."""
    # Look for requirement-like patterns
    req_patterns = [
        r'(?i)requirement\s*\d*[:\-\s]+(.+)',
        r'(?i)must\s+(.+)',
        r'(?i)should\s+(.+)',
        r'(?i)shall\s+(.+)',
        r'(?i)needs?\s+to\s+(.+)',
        r'(?i)has\s+to\s+(.+)',
    ]
    
    for pattern in req_patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        for match in matches:
            if len(match.strip()) > 10:  # Filter out very short matches
                parsed_docs["requirements_found"].append(match.strip())


def _extract_feature_patterns(content: str, parsed_docs: Dict[str, Any]) -> None:
    """Extract text that looks like features."""
    feature_patterns = [
        r'(?i)feature[:\-\s]+(.+)',
        r'(?i)functionality[:\-\s]+(.+)',
        r'(?i)capability[:\-\s]+(.+)',
        r'(?i)the\s+system\s+(.+)',
        r'(?i)users?\s+can\s+(.+)',
        r'(?i)allows?\s+(.+)',
        r'(?i)enables?\s+(.+)',
    ]
    
    for pattern in feature_patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        for match in matches:
            if len(match.strip()) > 10:
                parsed_docs["features_found"].append(match.strip())


def _extract_user_story_patterns(content: str, parsed_docs: Dict[str, Any]) -> None:
    """Extract text that looks like user stories."""
    story_patterns = [
        r'(?i)as\s+a\s+(.+?),?\s+i\s+want\s+(.+?)\s+so\s+that\s+(.+)',
        r'(?i)as\s+an?\s+(.+?),?\s+i\s+want\s+(.+?)\s+so\s+that\s+(.+)',
        r'(?i)user\s+story[:\-\s]+(.+)',
    ]
    
    for pattern in story_patterns:
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        for match in matches:
            if isinstance(match, tuple):
                story = " ".join(match)
            else:
                story = match
            if len(story.strip()) > 15:
                parsed_docs["user_stories_found"].append(story.strip())


def _extract_api_patterns(content: str, parsed_docs: Dict[str, Any]) -> None:
    """Extract API endpoint patterns."""
    api_patterns = [
        r'(?i)(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-_{}:]+)',
        r'(?i)endpoint[:\-\s]+([/\w\-_{}:]+)',
        r'(?i)api[:\-\s]+([/\w\-_{}:]+)',
        r'(?i)route[:\-\s]+([/\w\-_{}:]+)',
    ]
    
    for pattern in api_patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        for match in matches:
            if isinstance(match, tuple):
                endpoint = " ".join(match)
            else:
                endpoint = match
            parsed_docs["api_endpoints_found"].append(endpoint.strip())


def _extract_technology_mentions(content: str, parsed_docs: Dict[str, Any]) -> None:
    """Extract mentions of technologies, frameworks, and tools."""
    # Common technologies to look for
    technologies = [
        'react', 'vue', 'angular', 'node.js', 'python', 'java', 'javascript', 'typescript',
        'docker', 'kubernetes', 'mongodb', 'postgresql', 'mysql', 'redis', 'nginx', 'apache',
        'aws', 'azure', 'gcp', 'firebase', 'django', 'flask', 'fastapi', 'express', 'spring',
        'rails', 'laravel', 'dotnet', '.net', 'graphql', 'rest', 'api', 'microservices',
        'git', 'github', 'gitlab', 'jenkins', 'travis', 'circleci', 'terraform', 'ansible'
    ]
    
    content_lower = content.lower()
    for tech in technologies:
        if tech in content_lower:
            parsed_docs["technologies_mentioned"].add(tech)


def extract_requirements_from_code(project_path: Path, file_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Extract requirements and specifications from code comments and docstrings.
    
    Args:
        project_path: Path to the project directory
        file_patterns: Optional list of file patterns to search for
        
    Returns:
        Dictionary containing extracted requirements from code
    """
    if file_patterns is None:
        file_patterns = CODE_PATTERNS
    
    extracted = {
        "project_path": str(project_path),
        "files_analyzed": [],
        "comments_found": [],
        "docstrings_found": [],
        "todo_items": [],
        "fixme_items": [],
        "function_descriptions": [],
        "class_descriptions": [],
        "api_documentation": [],
        "extraction_errors": [],
    }
    
    try:
        for pattern in file_patterns:
            for file_path in project_path.rglob(pattern):
                if file_path.is_file() and _is_text_file(file_path):
                    try:
                        _extract_from_code_file(file_path, project_path, extracted)
                    except Exception as e:
                        error_msg = f"Error extracting from {file_path}: {e}"
                        logger.warning(error_msg)
                        extracted["extraction_errors"].append(error_msg)
                        
    except Exception as e:
        error_msg = f"Error during code extraction: {e}"
        logger.error(error_msg)
        extracted["extraction_errors"].append(error_msg)
    
    return extracted


def _extract_from_code_file(file_path: Path, project_root: Path, extracted: Dict[str, Any]) -> None:
    """Extract requirements from a single code file."""
    relative_path = str(file_path.relative_to(project_root))
    extracted["files_analyzed"].append(relative_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return  # Skip binary or non-UTF8 files
    
    # Extract comments
    _extract_comments(content, extracted, relative_path)
    
    # Extract docstrings (Python-specific for now)
    if file_path.suffix == '.py':
        _extract_python_docstrings(content, extracted, relative_path)
    
    # Extract TODO/FIXME items
    _extract_todo_fixme(content, extracted, relative_path)


def _extract_comments(content: str, extracted: Dict[str, Any], file_path: str) -> None:
    """Extract comments from code."""
    # Single line comments (// or #)
    single_comment_pattern = r'(?://|#)\s*(.+)'
    
    # Multi-line comments (/* ... */)
    multi_comment_pattern = r'/\*\s*(.*?)\s*\*/'
    
    for match in re.finditer(single_comment_pattern, content, re.MULTILINE):
        comment = match.group(1).strip()
        if len(comment) > 5:  # Filter very short comments
            extracted["comments_found"].append({
                "file": file_path,
                "comment": comment,
                "type": "single_line"
            })
    
    for match in re.finditer(multi_comment_pattern, content, re.MULTILINE | re.DOTALL):
        comment = match.group(1).strip()
        if len(comment) > 5:
            extracted["comments_found"].append({
                "file": file_path,
                "comment": comment,
                "type": "multi_line"
            })


def _extract_python_docstrings(content: str, extracted: Dict[str, Any], file_path: str) -> None:
    """Extract Python docstrings."""
    # Triple quoted strings (docstrings)
    docstring_pattern = r'"""(.*?)"""'
    
    for match in re.finditer(docstring_pattern, content, re.MULTILINE | re.DOTALL):
        docstring = match.group(1).strip()
        if len(docstring) > 10:
            extracted["docstrings_found"].append({
                "file": file_path,
                "docstring": docstring
            })


def _extract_todo_fixme(content: str, extracted: Dict[str, Any], file_path: str) -> None:
    """Extract TODO and FIXME items."""
    todo_pattern = r'(?i)todo[:\-\s]*(.+)'
    fixme_pattern = r'(?i)fixme[:\-\s]*(.+)'
    
    for match in re.finditer(todo_pattern, content, re.MULTILINE):
        todo = match.group(1).strip()
        if len(todo) > 3:
            extracted["todo_items"].append({
                "file": file_path,
                "item": todo
            })
    
    for match in re.finditer(fixme_pattern, content, re.MULTILINE):
        fixme = match.group(1).strip()
        if len(fixme) > 3:
            extracted["fixme_items"].append({
                "file": file_path,
                "item": fixme
            })


def generate_standardized_spec(
    project_analysis: Dict[str, Any],
    documentation_analysis: Dict[str, Any],
    code_analysis: Dict[str, Any],
    template_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate a standardized specification from existing project analysis.
    
    Args:
        project_analysis: Result from analyze_project_structure
        documentation_analysis: Result from parse_existing_documentation
        code_analysis: Result from extract_requirements_from_code
        template_dir: Optional path to template directory
        
    Returns:
        Dictionary containing the generated standardized specification
    """
    spec = {
        "project_name": project_analysis.get("project_name", "Unknown Project"),
        "project_path": project_analysis.get("project_path", ""),
        "generated_from": "existing_project_analysis",
        "analysis_date": _get_current_timestamp(),
        
        # Project Overview
        "overview": _generate_overview(project_analysis, documentation_analysis),
        
        # Requirements
        "functional_requirements": _generate_functional_requirements(documentation_analysis, code_analysis),
        
        # Non-functional requirements  
        "non_functional_requirements": _generate_non_functional_requirements(project_analysis, documentation_analysis),
        
        # User stories
        "user_stories": _generate_user_stories(documentation_analysis, code_analysis),
        
        # Technical details
        "technical_stack": _generate_technical_stack(project_analysis, documentation_analysis),
        
        # API specification
        "api_specification": _generate_api_spec(documentation_analysis, code_analysis),
        
        # Data model
        "data_model": _generate_data_model(project_analysis, code_analysis),
        
        # Implementation guidance
        "implementation_notes": _generate_implementation_notes(project_analysis, documentation_analysis, code_analysis),
        
        # Quality assurance
        "testing_strategy": _generate_testing_strategy(project_analysis),
        
        # Gaps and recommendations
        "gaps_identified": _identify_gaps(project_analysis, documentation_analysis, code_analysis),
        "recommendations": _generate_recommendations(project_analysis, documentation_analysis, code_analysis),
    }
    
    return spec


def _get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime
    return datetime.now().isoformat()


def _generate_overview(project_analysis: Dict[str, Any], documentation_analysis: Dict[str, Any]) -> str:
    """Generate project overview from analysis."""
    overview_parts = []
    
    # Basic project info
    project_name = project_analysis.get("project_name", "Unknown Project")
    size = project_analysis.get("estimated_size", "unknown")
    file_count = project_analysis.get("file_count", 0)
    
    overview_parts.append(f"# {project_name}")
    overview_parts.append(f"This is a {size}-sized project with approximately {file_count} files.")
    
    # Languages and technologies
    languages = project_analysis.get("languages_detected", [])
    if languages:
        overview_parts.append(f"Primary languages: {', '.join(languages)}")
    
    frameworks = project_analysis.get("frameworks_detected", [])
    if frameworks:
        overview_parts.append(f"Frameworks/tools detected: {', '.join(frameworks)}")
    
    # Documentation summary
    doc_files = len(documentation_analysis.get("files_parsed", []))
    if doc_files > 0:
        overview_parts.append(f"Documentation files analyzed: {doc_files}")
    
    return "\n\n".join(overview_parts)


def _generate_functional_requirements(documentation_analysis: Dict[str, Any], code_analysis: Dict[str, Any]) -> List[str]:
    """Generate functional requirements from analysis."""
    requirements = []
    
    # From documentation
    doc_requirements = documentation_analysis.get("requirements_found", [])
    requirements.extend([f"REQ-{i+1}: {req}" for i, req in enumerate(doc_requirements[:10])])
    
    # From features
    features = documentation_analysis.get("features_found", [])
    start_idx = len(requirements)
    requirements.extend([f"REQ-{start_idx+i+1}: System shall {feature}" for i, feature in enumerate(features[:5])])
    
    if not requirements:
        requirements.append("REQ-1: [No specific requirements found - needs manual specification]")
    
    return requirements


def _generate_non_functional_requirements(project_analysis: Dict[str, Any], documentation_analysis: Dict[str, Any]) -> List[str]:
    """Generate non-functional requirements."""
    nfr = []
    
    # Based on project characteristics
    if project_analysis.get("has_tests"):
        nfr.append("NFR-1: System shall maintain test coverage above 80%")
    
    if project_analysis.get("has_ci_cd"):
        nfr.append("NFR-2: System shall support automated CI/CD pipeline")
    
    # Based on technologies
    languages = project_analysis.get("languages_detected", [])
    if "Python" in languages:
        nfr.append("NFR-3: System shall be compatible with Python 3.8+")
    if "JavaScript" in languages:
        nfr.append("NFR-4: System shall support modern JavaScript (ES6+)")
    
    if not nfr:
        nfr.append("NFR-1: [No specific non-functional requirements identified - needs manual specification]")
    
    return nfr


def _generate_user_stories(documentation_analysis: Dict[str, Any], code_analysis: Dict[str, Any]) -> List[str]:
    """Generate user stories from analysis."""
    stories = []
    
    # From documentation
    doc_stories = documentation_analysis.get("user_stories_found", [])
    stories.extend(doc_stories[:10])
    
    # Generate from features if no explicit stories found
    if not stories:
        features = documentation_analysis.get("features_found", [])
        for feature in features[:5]:
            stories.append(f"As a user, I want to {feature} so that I can accomplish my goals")
    
    if not stories:
        stories.append("As a user, I want [specify user need] so that [specify user value]")
    
    return stories


def _generate_technical_stack(project_analysis: Dict[str, Any], documentation_analysis: Dict[str, Any]) -> Dict[str, List[str]]:
    """Generate technical stack information."""
    stack = {
        "languages": project_analysis.get("languages_detected", []),
        "frameworks": project_analysis.get("frameworks_detected", []),
        "build_systems": project_analysis.get("build_systems", []),
        "technologies_mentioned": documentation_analysis.get("technologies_mentioned", []),
    }
    
    return stack


def _generate_api_spec(documentation_analysis: Dict[str, Any], code_analysis: Dict[str, Any]) -> List[str]:
    """Generate API specification from analysis."""
    api_endpoints = documentation_analysis.get("api_endpoints_found", [])
    
    if not api_endpoints:
        return ["[No API endpoints identified - manual specification needed]"]
    
    return api_endpoints[:20]  # Limit to first 20 endpoints


def _generate_data_model(project_analysis: Dict[str, Any], code_analysis: Dict[str, Any]) -> str:
    """Generate data model information."""
    # This is a placeholder - could be enhanced to parse actual data models from code
    return "[Data model needs to be specified based on code analysis]"


def _generate_implementation_notes(
    project_analysis: Dict[str, Any], 
    documentation_analysis: Dict[str, Any],
    code_analysis: Dict[str, Any]
) -> List[str]:
    """Generate implementation notes."""
    notes = []
    
    # TODO items from code
    todos = code_analysis.get("todo_items", [])
    if todos:
        notes.append("TODO items found in code:")
        for todo in todos[:5]:
            notes.append(f"  - {todo['file']}: {todo['item']}")
    
    # FIXME items
    fixmes = code_analysis.get("fixme_items", [])
    if fixmes:
        notes.append("FIXME items found in code:")
        for fixme in fixmes[:5]:
            notes.append(f"  - {fixme['file']}: {fixme['item']}")
    
    if not notes:
        notes.append("[No specific implementation notes found]")
    
    return notes


def _generate_testing_strategy(project_analysis: Dict[str, Any]) -> str:
    """Generate testing strategy based on project analysis."""
    if project_analysis.get("has_tests"):
        return "Existing test infrastructure detected. Maintain and expand current testing approach."
    else:
        return "No existing tests detected. Recommend implementing comprehensive test suite with unit, integration, and end-to-end tests."


def _identify_gaps(
    project_analysis: Dict[str, Any],
    documentation_analysis: Dict[str, Any], 
    code_analysis: Dict[str, Any]
) -> List[str]:
    """Identify gaps in current project structure."""
    gaps = []
    
    # Documentation gaps
    if len(documentation_analysis.get("files_parsed", [])) < 3:
        gaps.append("Limited documentation - consider adding more comprehensive docs")
    
    if not documentation_analysis.get("requirements_found"):
        gaps.append("No explicit requirements found in documentation")
    
    if not documentation_analysis.get("user_stories_found"):
        gaps.append("No user stories identified")
    
    # Technical gaps
    if not project_analysis.get("has_tests"):
        gaps.append("No test infrastructure detected")
    
    if not project_analysis.get("has_ci_cd"):
        gaps.append("No CI/CD pipeline detected")
    
    # Code quality gaps
    todos = len(code_analysis.get("todo_items", []))
    fixmes = len(code_analysis.get("fixme_items", []))
    if todos + fixmes > 10:
        gaps.append(f"High number of TODO/FIXME items ({todos + fixmes}) indicating incomplete implementation")
    
    return gaps


def _generate_recommendations(
    project_analysis: Dict[str, Any],
    documentation_analysis: Dict[str, Any],
    code_analysis: Dict[str, Any]
) -> List[str]:
    """Generate recommendations for adopting spec-driven development."""
    recommendations = []
    
    recommendations.append("Migrate to spec-driven development workflow:")
    
    # Documentation recommendations
    if len(documentation_analysis.get("files_parsed", [])) > 0:
        recommendations.append("- Consolidate existing documentation into standardized specification format")
    else:
        recommendations.append("- Create comprehensive project specification from scratch")
    
    # Requirements recommendations
    if documentation_analysis.get("requirements_found"):
        recommendations.append("- Formalize existing requirements into structured format")
    else:
        recommendations.append("- Conduct requirements gathering and analysis sessions")
    
    # Technical recommendations
    if not project_analysis.get("has_tests"):
        recommendations.append("- Implement comprehensive testing strategy")
    
    if not project_analysis.get("has_ci_cd"):
        recommendations.append("- Set up automated CI/CD pipeline")
    
    # Process recommendations
    recommendations.append("- Establish regular specification review and update process")
    recommendations.append("- Train team on spec-driven development methodology")
    recommendations.append("- Implement specification-to-implementation toolchain")
    
    return recommendations


def create_migration_plan(
    project_analysis: Dict[str, Any],
    standardized_spec: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a migration plan for adopting spec-driven development.
    
    Args:
        project_analysis: Result from analyze_project_structure
        standardized_spec: Result from generate_standardized_spec
        
    Returns:
        Dictionary containing detailed migration plan
    """
    plan = {
        "project_name": project_analysis.get("project_name"),
        "migration_plan_date": _get_current_timestamp(),
        "current_state": _assess_current_state(project_analysis),
        "target_state": "Full spec-driven development workflow",
        "phases": _generate_migration_phases(project_analysis, standardized_spec),
        "timeline_estimate": _estimate_timeline(project_analysis),
        "resources_needed": _estimate_resources(project_analysis),
        "risks_and_mitigations": _identify_risks(project_analysis),
        "success_criteria": _define_success_criteria(),
    }
    
    return plan


def _assess_current_state(project_analysis: Dict[str, Any]) -> str:
    """Assess current state of the project."""
    size = project_analysis.get("estimated_size", "unknown")
    has_docs = len(project_analysis.get("documentation_files", [])) > 0
    has_tests = project_analysis.get("has_tests", False)
    has_cicd = project_analysis.get("has_ci_cd", False)
    
    state_parts = [f"{size} project"]
    
    if has_docs:
        state_parts.append("some documentation")
    else:
        state_parts.append("minimal documentation")
    
    if has_tests:
        state_parts.append("existing tests")
    
    if has_cicd:
        state_parts.append("CI/CD pipeline")
    
    return f"Project is a {', '.join(state_parts)}"


def _generate_migration_phases(project_analysis: Dict[str, Any], standardized_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate migration phases."""
    phases = []
    
    # Phase 1: Assessment and Planning
    phases.append({
        "phase": 1,
        "name": "Assessment and Planning",
        "duration": "1-2 weeks", 
        "description": "Complete project analysis and create migration roadmap",
        "tasks": [
            "Finalize project structure analysis",
            "Complete documentation review",
            "Interview team members for tacit knowledge",
            "Create detailed specification template",
            "Set up spec-kit environment",
        ],
        "deliverables": [
            "Project analysis report",
            "Initial specification draft", 
            "Migration timeline",
            "Team training plan",
        ]
    })
    
    # Phase 2: Specification Creation
    phases.append({
        "phase": 2,
        "name": "Specification Creation",
        "duration": "2-4 weeks",
        "description": "Create comprehensive project specification",
        "tasks": [
            "Consolidate requirements from analysis",
            "Define user stories and acceptance criteria",
            "Document current architecture and APIs",
            "Create implementation plans", 
            "Validate specification with stakeholders",
        ],
        "deliverables": [
            "Complete project specification",
            "Technical implementation plan",
            "API documentation",
            "Data model specification",
        ]
    })
    
    # Phase 3: Process Integration
    phases.append({
        "phase": 3,
        "name": "Process Integration", 
        "duration": "2-3 weeks",
        "description": "Integrate spec-driven processes into development workflow",
        "tasks": [
            "Set up specification-driven branching strategy",
            "Implement specification review process",
            "Configure automated tooling",
            "Train team on new workflow",
            "Create specification templates",
        ],
        "deliverables": [
            "Updated development process documentation",
            "Configured tooling and automation",
            "Team training completion",
            "Specification templates library",
        ]
    })
    
    # Phase 4: Pilot Implementation
    phases.append({
        "phase": 4,
        "name": "Pilot Implementation",
        "duration": "3-4 weeks",
        "description": "Pilot spec-driven development with new features",
        "tasks": [
            "Select pilot feature for spec-driven implementation",
            "Create feature specification using new process",
            "Implement feature following spec-driven approach",
            "Gather feedback and refine process",
            "Document lessons learned",
        ],
        "deliverables": [
            "Pilot feature specification",
            "Implemented pilot feature",
            "Process feedback and improvements",
            "Lessons learned document",
        ]
    })
    
    # Phase 5: Full Adoption
    phases.append({
        "phase": 5,
        "name": "Full Adoption",
        "duration": "Ongoing",
        "description": "Complete transition to spec-driven development",
        "tasks": [
            "Apply spec-driven approach to all new features",
            "Gradually retrofit existing features with specifications",
            "Continuously improve specification quality",
            "Monitor and measure benefits",
            "Scale process across organization",
        ],
        "deliverables": [
            "Complete specification coverage",
            "Established measurement metrics",
            "Process improvement recommendations",
            "Organizational scaling plan",
        ]
    })
    
    return phases


def _estimate_timeline(project_analysis: Dict[str, Any]) -> str:
    """Estimate migration timeline based on project size."""
    size = project_analysis.get("estimated_size", "unknown")
    team_size = "small"  # Could be enhanced to estimate team size
    
    if size == "small":
        return "6-10 weeks for complete migration"
    elif size == "medium":
        return "10-16 weeks for complete migration"
    else:
        return "16-24 weeks for complete migration"


def _estimate_resources(project_analysis: Dict[str, Any]) -> List[str]:
    """Estimate resources needed for migration."""
    return [
        "Dedicated project lead for migration coordination",
        "Technical writing support for specification creation",
        "Development team training (2-4 hours per developer)",
        "DevOps support for tooling integration",
        "Stakeholder time for specification review and validation",
    ]


def _identify_risks(project_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
    """Identify migration risks and mitigations."""
    return [
        {
            "risk": "Team resistance to new process",
            "mitigation": "Provide comprehensive training and demonstrate early wins"
        },
        {
            "risk": "Incomplete specification knowledge",
            "mitigation": "Conduct thorough analysis phase and stakeholder interviews"
        },
        {
            "risk": "Disruption to existing development velocity",
            "mitigation": "Implement gradual migration with pilot projects"
        },
        {
            "risk": "Tool integration challenges",
            "mitigation": "Perform technical proof-of-concept before full implementation"
        },
        {
            "risk": "Specification maintenance overhead",
            "mitigation": "Establish clear ownership and automated validation processes"
        },
    ]


def _define_success_criteria() -> List[str]:
    """Define success criteria for migration."""
    return [
        "All new features implemented using spec-driven approach",
        "90%+ of existing features have documented specifications",
        "Development team reports improved clarity and efficiency",
        "Reduced bug reports due to clearer requirements",
        "Faster onboarding of new team members",
        "Improved stakeholder satisfaction with delivered features",
        "Measurable reduction in requirement-related rework",
    ]