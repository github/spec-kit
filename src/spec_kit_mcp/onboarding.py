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


# Progressive Onboarding Functions

def analyze_feature_component(
    project_path: Path, 
    feature_path: str,
    max_depth: int = 2
) -> Dict[str, Any]:
    """
    Analyze a specific feature or component within a project.
    
    Args:
        project_path: Path to the main project directory
        feature_path: Relative path to the feature/component within the project
        max_depth: Maximum directory depth to scan within the feature
        
    Returns:
        Dictionary containing feature-specific analysis
    """
    if not project_path.exists() or not project_path.is_dir():
        raise ValueError(f"Project path does not exist or is not a directory: {project_path}")
    
    feature_full_path = project_path / feature_path
    if not feature_full_path.exists():
        raise ValueError(f"Feature path does not exist: {feature_path}")
    
    analysis = {
        "project_path": str(project_path),
        "feature_path": feature_path,
        "feature_full_path": str(feature_full_path),
        "feature_name": Path(feature_path).name,
        "analysis_scope": "feature_component",
        "structure": {},
        "documentation_files": [],
        "code_files": [],
        "config_files": [],
        "test_files": [],
        "languages_detected": set(),
        "frameworks_detected": set(),
        "dependencies": set(),
        "external_references": [],
        "estimated_complexity": "unknown",
        "interfaces": [],
        "potential_boundaries": [],
    }
    
    try:
        file_count = 0
        
        # Analyze feature directory structure
        for item in feature_full_path.rglob("*"):
            if item.is_dir():
                # Skip deep directories and common ignore patterns
                if len(item.parts) - len(feature_full_path.parts) > max_depth:
                    continue
                if any(skip in item.name for skip in ['.git', 'node_modules', '__pycache__', '.venv', 'venv']):
                    continue
            else:
                file_count += 1
                _categorize_feature_file(item, project_path, feature_full_path, analysis)
        
        # Estimate complexity
        if file_count < 10:
            analysis["estimated_complexity"] = "low"
        elif file_count < 50:
            analysis["estimated_complexity"] = "medium"
        else:
            analysis["estimated_complexity"] = "high"
            
        analysis["file_count"] = file_count
        
        # Analyze external dependencies and references
        _analyze_feature_dependencies(feature_full_path, project_path, analysis)
        
        # Identify potential sub-feature boundaries
        _identify_feature_boundaries(feature_full_path, analysis)
        
    except Exception as e:
        logger.warning(f"Error analyzing feature {feature_path}: {e}")
        analysis["analysis_error"] = str(e)
    
    # Convert sets to lists for JSON serialization
    analysis["languages_detected"] = list(analysis["languages_detected"])
    analysis["frameworks_detected"] = list(analysis["frameworks_detected"])
    analysis["dependencies"] = list(analysis["dependencies"])
    
    return analysis


def _categorize_feature_file(file_path: Path, project_root: Path, feature_root: Path, analysis: Dict[str, Any]) -> None:
    """Categorize a file within a feature and update analysis."""
    relative_to_project = file_path.relative_to(project_root)
    relative_to_feature = file_path.relative_to(feature_root)
    file_name = file_path.name.lower()
    file_ext = file_path.suffix.lower()
    
    # Categorize by type
    if _matches_patterns(file_name, DOCUMENTATION_PATTERNS):
        analysis["documentation_files"].append(str(relative_to_feature))
    elif _matches_patterns(file_name, CODE_PATTERNS) or file_ext in ['.py', '.js', '.ts', '.java', '.cs', '.cpp', '.c', '.h']:
        analysis["code_files"].append(str(relative_to_feature))
    elif _matches_patterns(file_name, CONFIG_PATTERNS):
        analysis["config_files"].append(str(relative_to_feature))
    
    # Check for test files
    if 'test' in file_name or 'spec' in file_name or '/test' in str(relative_to_feature):
        analysis["test_files"].append(str(relative_to_feature))
    
    # Detect languages (same logic as before)
    language_map = {
        '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
        '.java': 'Java', '.cs': 'C#', '.cpp': 'C++', '.c': 'C',
        '.go': 'Go', '.rs': 'Rust', '.php': 'PHP', '.rb': 'Ruby',
        '.swift': 'Swift', '.kt': 'Kotlin',
    }
    if file_ext in language_map:
        analysis["languages_detected"].add(language_map[file_ext])
    
    # Detect frameworks and dependencies specific to this feature
    if file_name == 'package.json':
        analysis["frameworks_detected"].add("Node.js")
        analysis["dependencies"].add("npm/yarn")
    elif file_name == 'requirements.txt':
        analysis["dependencies"].add("pip")
    elif file_name.startswith('dockerfile'):
        analysis["frameworks_detected"].add("Docker")


def _analyze_feature_dependencies(feature_path: Path, project_root: Path, analysis: Dict[str, Any]) -> None:
    """Analyze dependencies and external references for a feature."""
    try:
        # Look for import statements and external references in code files
        for code_file in analysis["code_files"]:
            full_path = feature_path / code_file
            if full_path.exists() and _is_text_file(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract import statements and external references
                    _extract_imports_and_references(content, full_path.suffix, analysis, project_root, feature_path)
                    
                except Exception as e:
                    logger.warning(f"Error analyzing dependencies in {code_file}: {e}")
                    
    except Exception as e:
        logger.warning(f"Error analyzing feature dependencies: {e}")


def _extract_imports_and_references(content: str, file_extension: str, analysis: Dict[str, Any], project_root: Path, feature_path: Path) -> None:
    """Extract import statements and external references from code."""
    # Python imports
    if file_extension == '.py':
        import_patterns = [
            r'from\s+([\w.]+)\s+import',
            r'import\s+([\w.]+)',
        ]
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if '.' in match and not match.startswith('.'):
                    # Check if it's an external reference (not within the current feature)
                    if not _is_internal_reference(match, project_root, feature_path):
                        analysis["external_references"].append(f"Python: {match}")
    
    # JavaScript/TypeScript imports
    elif file_extension in ['.js', '.ts']:
        import_patterns = [
            r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
            r'require\([\'"]([^\'"]+)[\'"]\)',
        ]
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if not match.startswith('.') and not match.startswith('/'):
                    analysis["external_references"].append(f"JS/TS: {match}")


def _is_internal_reference(reference: str, project_root: Path, feature_path: Path) -> bool:
    """Check if a reference is internal to the current feature or project."""
    # This is a simplified check - could be enhanced for more accurate detection
    try:
        # Check if the reference corresponds to a file within the feature
        potential_path = feature_path / reference.replace('.', '/')
        if potential_path.exists() or (potential_path.parent / f"{potential_path.name}.py").exists():
            return True
        
        # Check if it's within the project but outside the feature
        potential_project_path = project_root / reference.replace('.', '/')
        if potential_project_path.exists():
            return False  # It's in the project but external to the feature
            
    except Exception:
        pass
    
    return False  # Assume external if we can't determine


def _identify_feature_boundaries(feature_path: Path, analysis: Dict[str, Any]) -> None:
    """Identify potential sub-feature boundaries within a feature."""
    try:
        subdirs = [d for d in feature_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        for subdir in subdirs:
            # Check if subdirectory has enough content to be a separate feature
            subdir_files = list(subdir.rglob("*"))
            code_files = [f for f in subdir_files if f.is_file() and f.suffix in ['.py', '.js', '.ts', '.java', '.cs']]
            
            if len(code_files) >= 3:  # Arbitrary threshold for potential sub-feature
                analysis["potential_boundaries"].append({
                    "path": str(subdir.relative_to(feature_path)),
                    "file_count": len([f for f in subdir_files if f.is_file()]),
                    "code_file_count": len(code_files),
                    "suggested_as": "sub_feature"
                })
                
    except Exception as e:
        logger.warning(f"Error identifying feature boundaries: {e}")


def extract_feature_boundaries(project_path: Path, analysis_depth: int = 2) -> Dict[str, Any]:
    """
    Identify logical feature boundaries within a project.
    
    Args:
        project_path: Path to the project directory
        analysis_depth: Depth to analyze for feature boundaries
        
    Returns:
        Dictionary containing identified feature boundaries
    """
    if not project_path.exists() or not project_path.is_dir():
        raise ValueError(f"Project path does not exist or is not a directory: {project_path}")
    
    boundaries = {
        "project_path": str(project_path),
        "project_name": project_path.name,
        "analysis_date": _get_current_timestamp(),
        "suggested_features": [],
        "feature_candidates": [],
        "boundary_criteria": {},
    }
    
    try:
        # Analyze top-level directories as potential features
        for item in project_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name not in ['node_modules', '__pycache__', '.git']:
                feature_analysis = _analyze_potential_feature(item, project_path, analysis_depth)
                if feature_analysis["is_feature_candidate"]:
                    boundaries["suggested_features"].append(feature_analysis)
                else:
                    boundaries["feature_candidates"].append(feature_analysis)
        
        # Define boundary criteria used
        boundaries["boundary_criteria"] = {
            "minimum_files": 5,
            "minimum_code_files": 3,
            "has_tests": "preferred",
            "has_documentation": "preferred",
            "logical_cohesion": "required",
        }
        
    except Exception as e:
        logger.error(f"Error extracting feature boundaries: {e}")
        boundaries["extraction_error"] = str(e)
    
    return boundaries


def _analyze_potential_feature(directory: Path, project_root: Path, max_depth: int) -> Dict[str, Any]:
    """Analyze a directory to determine if it's a good feature candidate."""
    relative_path = directory.relative_to(project_root)
    
    analysis = {
        "feature_path": str(relative_path),
        "feature_name": directory.name,
        "is_feature_candidate": False,
        "confidence_score": 0.0,
        "reasons": [],
        "file_count": 0,
        "code_file_count": 0,
        "has_tests": False,
        "has_documentation": False,
        "languages": set(),
        "subdirectories": [],
    }
    
    try:
        files = []
        code_files = []
        
        # Collect files within the directory
        for item in directory.rglob("*"):
            if item.is_file():
                files.append(item)
                if item.suffix in ['.py', '.js', '.ts', '.java', '.cs', '.cpp', '.c', '.h', '.go', '.rs']:
                    code_files.append(item)
                    analysis["languages"].add(item.suffix)
                
                # Check for tests and documentation
                if 'test' in item.name.lower() or 'spec' in item.name.lower():
                    analysis["has_tests"] = True
                if item.suffix.lower() in ['.md', '.txt', '.rst'] or 'readme' in item.name.lower():
                    analysis["has_documentation"] = True
        
        analysis["file_count"] = len(files)
        analysis["code_file_count"] = len(code_files)
        analysis["languages"] = list(analysis["languages"])
        
        # Calculate confidence score
        score = 0.0
        
        # File count criteria
        if analysis["file_count"] >= 5:
            score += 0.3
            analysis["reasons"].append("Has sufficient file count")
        
        if analysis["code_file_count"] >= 3:
            score += 0.3
            analysis["reasons"].append("Has sufficient code files")
        
        # Quality indicators
        if analysis["has_tests"]:
            score += 0.2
            analysis["reasons"].append("Has test files")
        
        if analysis["has_documentation"]:
            score += 0.1
            analysis["reasons"].append("Has documentation")
        
        # Logical cohesion (simplified check)
        if directory.name in ['src', 'lib', 'api', 'frontend', 'backend', 'service', 'component']:
            score += 0.1
            analysis["reasons"].append("Has logical naming pattern")
        
        analysis["confidence_score"] = score
        analysis["is_feature_candidate"] = score >= 0.5
        
    except Exception as e:
        logger.warning(f"Error analyzing potential feature {directory}: {e}")
        analysis["analysis_error"] = str(e)
    
    return analysis


def onboard_project_feature(
    project_path: Path,
    feature_path: str,
    include_dependencies: bool = True
) -> Dict[str, Any]:
    """
    Onboard a specific feature to spec-driven development.
    
    Args:
        project_path: Path to the main project directory
        feature_path: Relative path to the feature within the project
        include_dependencies: Whether to analyze feature dependencies
        
    Returns:
        Dictionary containing complete feature onboarding analysis
    """
    if not project_path.exists() or not project_path.is_dir():
        raise ValueError(f"Project path does not exist or is not a directory: {project_path}")
    
    # Step 1: Analyze feature structure
    feature_analysis = analyze_feature_component(project_path, feature_path)
    
    # Step 2: Parse feature documentation
    feature_full_path = project_path / feature_path
    documentation_analysis = parse_existing_documentation(feature_full_path)
    
    # Step 3: Extract from feature code
    code_analysis = extract_requirements_from_code(feature_full_path)
    
    # Step 4: Generate feature specification
    feature_spec = generate_standardized_spec(
        feature_analysis,
        documentation_analysis,
        code_analysis
    )
    
    # Step 5: Analyze dependencies if requested
    dependency_analysis = None
    if include_dependencies:
        dependency_analysis = _analyze_feature_integration_points(
            project_path, feature_path, feature_analysis
        )
    
    # Combine results
    onboarding_result = {
        "onboarding_date": _get_current_timestamp(),
        "onboarding_scope": "feature",
        "project_path": str(project_path),
        "feature_path": feature_path,
        "feature_analysis": feature_analysis,
        "documentation_analysis": documentation_analysis,
        "code_analysis": code_analysis,
        "feature_specification": feature_spec,
        "dependency_analysis": dependency_analysis,
        "integration_recommendations": _generate_feature_integration_recommendations(
            feature_analysis, dependency_analysis
        ),
        "summary": {
            "feature_name": feature_analysis.get("feature_name"),
            "complexity": feature_analysis.get("estimated_complexity"),
            "languages": feature_analysis.get("languages_detected", []),
            "file_count": feature_analysis.get("file_count", 0),
            "external_dependencies": len(feature_analysis.get("external_references", [])),
            "test_coverage": "detected" if feature_analysis.get("test_files") else "missing",
            "ready_for_spec_driven": _assess_feature_readiness(feature_analysis),
        }
    }
    
    return onboarding_result


def _analyze_feature_integration_points(
    project_path: Path,
    feature_path: str,
    feature_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze how a feature integrates with the rest of the project."""
    integration_analysis = {
        "feature_path": feature_path,
        "incoming_dependencies": [],
        "outgoing_dependencies": [],
        "shared_resources": [],
        "integration_complexity": "unknown",
        "potential_conflicts": [],
    }
    
    try:
        # Analyze external references from the feature
        external_refs = feature_analysis.get("external_references", [])
        integration_analysis["outgoing_dependencies"] = external_refs
        
        # Look for references TO this feature from other parts of the project
        feature_name = Path(feature_path).name
        incoming_deps = _find_incoming_references(project_path, feature_path, feature_name)
        integration_analysis["incoming_dependencies"] = incoming_deps
        
        # Calculate integration complexity
        total_deps = len(external_refs) + len(incoming_deps)
        if total_deps < 3:
            integration_analysis["integration_complexity"] = "low"
        elif total_deps < 10:
            integration_analysis["integration_complexity"] = "medium"
        else:
            integration_analysis["integration_complexity"] = "high"
        
    except Exception as e:
        logger.warning(f"Error analyzing feature integration: {e}")
        integration_analysis["analysis_error"] = str(e)
    
    return integration_analysis


def _find_incoming_references(project_path: Path, feature_path: str, feature_name: str) -> List[str]:
    """Find references to a feature from other parts of the project."""
    incoming_refs = []
    feature_full_path = project_path / feature_path
    
    try:
        # Search for imports/references to this feature in other files
        for file_path in project_path.rglob("*.py"):
            # Skip files within the feature itself
            if file_path.is_relative_to(feature_full_path):
                continue
                
            if _is_text_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Look for imports or references to the feature
                    if feature_name in content or feature_path in content:
                        relative_path = file_path.relative_to(project_path)
                        incoming_refs.append(str(relative_path))
                        
                except Exception:
                    continue
                    
    except Exception as e:
        logger.warning(f"Error finding incoming references: {e}")
    
    return incoming_refs[:10]  # Limit to first 10 references


def _generate_feature_integration_recommendations(
    feature_analysis: Dict[str, Any],
    dependency_analysis: Optional[Dict[str, Any]]
) -> List[str]:
    """Generate recommendations for integrating a feature into spec-driven development."""
    recommendations = []
    
    complexity = feature_analysis.get("estimated_complexity", "unknown")
    has_tests = bool(feature_analysis.get("test_files"))
    external_deps = len(feature_analysis.get("external_references", []))
    
    # Basic recommendations
    recommendations.append(f"Feature complexity is {complexity} - plan accordingly")
    
    if not has_tests:
        recommendations.append("Add comprehensive test coverage before integration")
    else:
        recommendations.append("Existing tests detected - validate they cover key functionality")
    
    if external_deps > 5:
        recommendations.append("High number of external dependencies - document and validate interfaces")
    
    # Integration-specific recommendations
    if dependency_analysis:
        integration_complexity = dependency_analysis.get("integration_complexity", "unknown")
        if integration_complexity == "high":
            recommendations.append("Complex integration detected - consider phased integration approach")
        
        incoming_deps = dependency_analysis.get("incoming_dependencies", [])
        if len(incoming_deps) > 3:
            recommendations.append("Feature is heavily used by other components - coordinate changes carefully")
    
    # Spec-driven recommendations
    recommendations.append("Create detailed API specification for external interfaces")
    recommendations.append("Document dependencies and integration points in specification")
    recommendations.append("Establish clear acceptance criteria for feature boundaries")
    
    return recommendations


def _assess_feature_readiness(feature_analysis: Dict[str, Any]) -> str:
    """Assess how ready a feature is for spec-driven development."""
    score = 0
    
    # File organization
    if feature_analysis.get("file_count", 0) > 5:
        score += 1
    
    # Code quality indicators
    if feature_analysis.get("test_files"):
        score += 2
    
    if feature_analysis.get("documentation_files"):
        score += 1
    
    # Dependency management
    external_deps = len(feature_analysis.get("external_references", []))
    if external_deps < 5:
        score += 1
    
    # Complexity assessment
    complexity = feature_analysis.get("estimated_complexity", "high")
    if complexity == "low":
        score += 1
    elif complexity == "medium":
        score += 0
    else:
        score -= 1
    
    # Determine readiness level
    if score >= 4:
        return "high"
    elif score >= 2:
        return "medium"
    else:
        return "low"


# Specification Assembly and Coordination Functions

def merge_feature_specifications(
    feature_specifications: List[Dict[str, Any]],
    master_project_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Merge multiple feature specifications into a master specification.
    
    Args:
        feature_specifications: List of feature specification dictionaries
        master_project_info: Optional master project information for context
        
    Returns:
        Dictionary containing the merged master specification
    """
    if not feature_specifications:
        raise ValueError("At least one feature specification is required")
    
    # Initialize master specification
    master_spec = {
        "project_name": master_project_info.get("project_name", "Multi-Feature Project") if master_project_info else "Multi-Feature Project",
        "specification_type": "master_assembled",
        "assembly_date": _get_current_timestamp(),
        "source_features": [],
        "overview": "",
        "functional_requirements": [],
        "non_functional_requirements": [],
        "user_stories": [],
        "technical_stack": {
            "languages": set(),
            "frameworks": set(),
            "build_systems": set(),
            "technologies_mentioned": set(),
        },
        "api_specification": [],
        "data_model": "",
        "implementation_notes": [],
        "testing_strategy": "",
        "feature_dependencies": [],
        "integration_points": [],
        "gaps_identified": [],
        "recommendations": [],
        "assembly_metadata": {
            "feature_count": len(feature_specifications),
            "merge_conflicts": [],
            "coordination_notes": [],
        }
    }
    
    try:
        # Process each feature specification
        for i, feature_spec in enumerate(feature_specifications):
            feature_info = {
                "feature_name": feature_spec.get("project_name", f"Feature-{i+1}"),
                "feature_path": feature_spec.get("project_path", ""),
                "complexity": "unknown",
                "requirements_count": len(feature_spec.get("functional_requirements", [])),
            }
            master_spec["source_features"].append(feature_info)
            
            # Merge functional requirements
            feature_reqs = feature_spec.get("functional_requirements", [])
            for req in feature_reqs:
                prefixed_req = f"[{feature_info['feature_name']}] {req}"
                master_spec["functional_requirements"].append(prefixed_req)
            
            # Merge non-functional requirements
            nf_reqs = feature_spec.get("non_functional_requirements", [])
            for req in nf_reqs:
                prefixed_req = f"[{feature_info['feature_name']}] {req}"
                master_spec["non_functional_requirements"].append(prefixed_req)
            
            # Merge user stories
            stories = feature_spec.get("user_stories", [])
            for story in stories:
                prefixed_story = f"[{feature_info['feature_name']}] {story}"
                master_spec["user_stories"].append(prefixed_story)
            
            # Merge technical stack
            tech_stack = feature_spec.get("technical_stack", {})
            if isinstance(tech_stack, dict):
                for key in ["languages", "frameworks", "build_systems", "technologies_mentioned"]:
                    if key in tech_stack:
                        if isinstance(tech_stack[key], list):
                            master_spec["technical_stack"][key].update(tech_stack[key])
            
            # Merge API specifications
            api_specs = feature_spec.get("api_specification", [])
            if isinstance(api_specs, list):
                for api in api_specs:
                    master_spec["api_specification"].append(f"[{feature_info['feature_name']}] {api}")
            
            # Collect implementation notes
            impl_notes = feature_spec.get("implementation_notes", [])
            if isinstance(impl_notes, list):
                master_spec["implementation_notes"].extend([
                    f"[{feature_info['feature_name']}] {note}" for note in impl_notes
                ])
            
            # Collect gaps
            gaps = feature_spec.get("gaps_identified", [])
            if isinstance(gaps, list):
                master_spec["gaps_identified"].extend([
                    f"[{feature_info['feature_name']}] {gap}" for gap in gaps
                ])
        
        # Convert sets to lists for serialization
        for key in master_spec["technical_stack"]:
            master_spec["technical_stack"][key] = list(master_spec["technical_stack"][key])
        
        # Generate master overview
        master_spec["overview"] = _generate_master_overview(master_spec)
        
        # Generate coordination recommendations
        master_spec["recommendations"] = _generate_coordination_recommendations(master_spec)
        
        # Analyze potential conflicts
        conflicts = detect_specification_conflicts(feature_specifications)
        master_spec["assembly_metadata"]["merge_conflicts"] = conflicts.get("conflicts", [])
        
    except Exception as e:
        logger.error(f"Error merging feature specifications: {e}")
        master_spec["assembly_error"] = str(e)
    
    return master_spec


def _generate_master_overview(master_spec: Dict[str, Any]) -> str:
    """Generate an overview for the master specification."""
    overview_parts = []
    
    project_name = master_spec.get("project_name", "Multi-Feature Project")
    feature_count = master_spec["assembly_metadata"]["feature_count"]
    
    overview_parts.append(f"# {project_name}")
    overview_parts.append(f"This is a multi-feature project assembled from {feature_count} individual feature specifications.")
    
    # Technical stack summary
    languages = master_spec["technical_stack"].get("languages", [])
    if languages:
        overview_parts.append(f"Technologies used: {', '.join(languages)}")
    
    frameworks = master_spec["technical_stack"].get("frameworks", [])
    if frameworks:
        overview_parts.append(f"Frameworks: {', '.join(frameworks)}")
    
    # Feature summary
    feature_names = [f["feature_name"] for f in master_spec["source_features"]]
    overview_parts.append(f"Integrated features: {', '.join(feature_names)}")
    
    return "\n\n".join(overview_parts)


def _generate_coordination_recommendations(master_spec: Dict[str, Any]) -> List[str]:
    """Generate recommendations for coordinating multiple features."""
    recommendations = []
    
    feature_count = master_spec["assembly_metadata"]["feature_count"]
    
    recommendations.append("Multi-feature coordination recommendations:")
    
    if feature_count > 3:
        recommendations.append("- Establish regular cross-feature integration meetings")
        recommendations.append("- Implement shared API versioning strategy")
    
    # Technical coordination
    languages = master_spec["technical_stack"].get("languages", [])
    if len(languages) > 2:
        recommendations.append("- Standardize development environments across features")
        recommendations.append("- Establish shared coding standards and practices")
    
    # Process coordination
    recommendations.append("- Implement feature-level specification reviews")
    recommendations.append("- Establish dependency management protocols")
    recommendations.append("- Create integration testing strategy across features")
    
    # Conflict resolution
    conflicts = master_spec["assembly_metadata"].get("merge_conflicts", [])
    if conflicts:
        recommendations.append("- Resolve identified specification conflicts before implementation")
    
    return recommendations


def detect_specification_conflicts(feature_specifications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect conflicts between multiple feature specifications.
    
    Args:
        feature_specifications: List of feature specification dictionaries
        
    Returns:
        Dictionary containing detected conflicts and resolution suggestions
    """
    conflict_analysis = {
        "analysis_date": _get_current_timestamp(),
        "features_analyzed": len(feature_specifications),
        "conflicts": [],
        "potential_conflicts": [],
        "resolution_suggestions": [],
        "conflict_summary": {
            "api_conflicts": 0,
            "requirement_conflicts": 0,
            "technology_conflicts": 0,
            "dependency_conflicts": 0,
        }
    }
    
    try:
        if len(feature_specifications) < 2:
            return conflict_analysis
        
        # Check for API endpoint conflicts
        _detect_api_conflicts(feature_specifications, conflict_analysis)
        
        # Check for conflicting requirements
        _detect_requirement_conflicts(feature_specifications, conflict_analysis)
        
        # Check for technology stack conflicts
        _detect_technology_conflicts(feature_specifications, conflict_analysis)
        
        # Generate resolution suggestions
        conflict_analysis["resolution_suggestions"] = _generate_conflict_resolutions(conflict_analysis)
        
    except Exception as e:
        logger.error(f"Error detecting specification conflicts: {e}")
        conflict_analysis["detection_error"] = str(e)
    
    return conflict_analysis


def _detect_api_conflicts(specifications: List[Dict[str, Any]], conflict_analysis: Dict[str, Any]) -> None:
    """Detect API endpoint conflicts between features."""
    api_endpoints = {}
    
    for spec in specifications:
        feature_name = spec.get("project_name", "Unknown")
        api_specs = spec.get("api_specification", [])
        
        for api in api_specs:
            # Extract endpoint from API specification (simplified)
            endpoint = _extract_endpoint_pattern(api)
            if endpoint:
                if endpoint in api_endpoints:
                    conflict = {
                        "type": "api_conflict",
                        "endpoint": endpoint,
                        "conflicting_features": [api_endpoints[endpoint], feature_name],
                        "severity": "high",
                        "description": f"API endpoint {endpoint} defined in multiple features"
                    }
                    conflict_analysis["conflicts"].append(conflict)
                    conflict_analysis["conflict_summary"]["api_conflicts"] += 1
                else:
                    api_endpoints[endpoint] = feature_name


def _extract_endpoint_pattern(api_spec: str) -> Optional[str]:
    """Extract endpoint pattern from API specification string."""
    # Simple pattern matching for common endpoint formats
    patterns = [
        r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-_{}:]+)',
        r'([/\w\-_{}:]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, api_spec)
        if match:
            if len(match.groups()) == 2:
                return f"{match.group(1)} {match.group(2)}"
            else:
                return match.group(1)
    
    return None


def _detect_requirement_conflicts(specifications: List[Dict[str, Any]], conflict_analysis: Dict[str, Any]) -> None:
    """Detect conflicting requirements between features."""
    # This is a simplified conflict detection - could be enhanced with NLP
    requirement_keywords = {}
    
    for spec in specifications:
        feature_name = spec.get("project_name", "Unknown")
        requirements = spec.get("functional_requirements", [])
        
        for req in requirements:
            # Extract key terms from requirements (simplified)
            key_terms = _extract_requirement_terms(req)
            for term in key_terms:
                if term in requirement_keywords:
                    # Check for conflicting statements
                    if _are_requirements_conflicting(requirement_keywords[term]["requirement"], req):
                        conflict = {
                            "type": "requirement_conflict",
                            "term": term,
                            "conflicting_features": [requirement_keywords[term]["feature"], feature_name],
                            "conflicting_requirements": [requirement_keywords[term]["requirement"], req],
                            "severity": "medium",
                            "description": f"Potentially conflicting requirements for {term}"
                        }
                        conflict_analysis["potential_conflicts"].append(conflict)
                        conflict_analysis["conflict_summary"]["requirement_conflicts"] += 1
                else:
                    requirement_keywords[term] = {"feature": feature_name, "requirement": req}


def _extract_requirement_terms(requirement: str) -> List[str]:
    """Extract key terms from a requirement string."""
    # Simple keyword extraction - could be enhanced with NLP
    common_terms = ['user', 'system', 'data', 'authentication', 'authorization', 'database', 'api', 'interface']
    terms_found = []
    
    req_lower = requirement.lower()
    for term in common_terms:
        if term in req_lower:
            terms_found.append(term)
    
    return terms_found


def _are_requirements_conflicting(req1: str, req2: str) -> bool:
    """Check if two requirements are potentially conflicting."""
    # Simple conflict detection based on contradictory keywords
    conflicting_pairs = [
        ('must', 'must not'),
        ('shall', 'shall not'),
        ('required', 'optional'),
        ('always', 'never'),
        ('public', 'private'),
        ('readonly', 'writable'),
    ]
    
    req1_lower = req1.lower()
    req2_lower = req2.lower()
    
    for positive, negative in conflicting_pairs:
        if positive in req1_lower and negative in req2_lower:
            return True
        if negative in req1_lower and positive in req2_lower:
            return True
    
    return False


def _detect_technology_conflicts(specifications: List[Dict[str, Any]], conflict_analysis: Dict[str, Any]) -> None:
    """Detect technology stack conflicts between features."""
    tech_choices = {}
    
    for spec in specifications:
        feature_name = spec.get("project_name", "Unknown")
        tech_stack = spec.get("technical_stack", {})
        
        # Check for conflicting technology choices
        for category in ["frameworks", "build_systems", "technologies_mentioned"]:
            if category in tech_stack:
                technologies = tech_stack[category] if isinstance(tech_stack[category], list) else []
                for tech in technologies:
                    tech_key = _normalize_technology_name(tech)
                    if tech_key in tech_choices:
                        # Check for potential conflicts (e.g., different versions)
                        if _are_technologies_conflicting(tech_choices[tech_key]["technology"], tech):
                            conflict = {
                                "type": "technology_conflict",
                                "category": category,
                                "technology": tech_key,
                                "conflicting_features": [tech_choices[tech_key]["feature"], feature_name],
                                "conflicting_choices": [tech_choices[tech_key]["technology"], tech],
                                "severity": "medium",
                                "description": f"Potentially conflicting {category} choices"
                            }
                            conflict_analysis["potential_conflicts"].append(conflict)
                            conflict_analysis["conflict_summary"]["technology_conflicts"] += 1
                    else:
                        tech_choices[tech_key] = {"feature": feature_name, "technology": tech}


def _normalize_technology_name(tech_name: str) -> str:
    """Normalize technology name for comparison."""
    return tech_name.lower().replace('-', '').replace('_', '').replace('.', '')


def _are_technologies_conflicting(tech1: str, tech2: str) -> bool:
    """Check if two technology choices are conflicting."""
    # Simple conflict detection - could be enhanced
    tech1_norm = _normalize_technology_name(tech1)
    tech2_norm = _normalize_technology_name(tech2)
    
    # Same base technology but potentially different versions
    if tech1_norm == tech2_norm and tech1 != tech2:
        return True
    
    # Known conflicting technologies
    conflicts = [
        ('angular', 'react'),
        ('vue', 'react'),
        ('angular', 'vue'),
        ('mysql', 'postgresql'),
        ('mongodb', 'postgresql'),
    ]
    
    for tech_a, tech_b in conflicts:
        if (tech_a in tech1_norm and tech_b in tech2_norm) or (tech_b in tech1_norm and tech_a in tech2_norm):
            return True
    
    return False


def _generate_conflict_resolutions(conflict_analysis: Dict[str, Any]) -> List[str]:
    """Generate suggestions for resolving detected conflicts."""
    suggestions = []
    
    api_conflicts = conflict_analysis["conflict_summary"]["api_conflicts"]
    req_conflicts = conflict_analysis["conflict_summary"]["requirement_conflicts"]
    tech_conflicts = conflict_analysis["conflict_summary"]["technology_conflicts"]
    
    if api_conflicts > 0:
        suggestions.append("API Conflicts: Review and redesign conflicting endpoints with namespace/versioning")
        suggestions.append("Consider using API gateway for routing and conflict resolution")
    
    if req_conflicts > 0:
        suggestions.append("Requirement Conflicts: Conduct stakeholder meetings to clarify conflicting requirements")
        suggestions.append("Establish requirement prioritization framework")
    
    if tech_conflicts > 0:
        suggestions.append("Technology Conflicts: Standardize technology stack across features")
        suggestions.append("Create technology decision matrix and governance process")
    
    # General suggestions
    if any([api_conflicts, req_conflicts, tech_conflicts]):
        suggestions.append("Establish cross-feature coordination team")
        suggestions.append("Implement regular architecture review meetings")
        suggestions.append("Create shared design system and standards")
    
    return suggestions


def resolve_feature_dependencies(
    feature_specifications: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyze and document dependencies between features.
    
    Args:
        feature_specifications: List of feature specification dictionaries
        
    Returns:
        Dictionary containing dependency analysis and resolution plan
    """
    dependency_analysis = {
        "analysis_date": _get_current_timestamp(),
        "features_analyzed": len(feature_specifications),
        "dependencies": [],
        "dependency_graph": {},
        "circular_dependencies": [],
        "critical_dependencies": [],
        "resolution_plan": [],
        "implementation_order": [],
    }
    
    try:
        # Extract feature names and paths
        features = []
        for spec in feature_specifications:
            feature_info = {
                "name": spec.get("project_name", "Unknown"),
                "path": spec.get("project_path", ""),
                "external_references": spec.get("external_references", []) if "external_references" in str(spec) else [],
                "api_endpoints": spec.get("api_specification", []),
            }
            features.append(feature_info)
        
        # Analyze dependencies between features
        for i, feature_a in enumerate(features):
            dependencies_found = []
            for j, feature_b in enumerate(features):
                if i != j:
                    # Check if feature_a depends on feature_b
                    dependency_strength = _calculate_dependency_strength(feature_a, feature_b)
                    if dependency_strength > 0:
                        dependency = {
                            "from_feature": feature_a["name"],
                            "to_feature": feature_b["name"],
                            "strength": dependency_strength,
                            "type": _classify_dependency_type(feature_a, feature_b),
                            "details": _extract_dependency_details(feature_a, feature_b),
                        }
                        dependencies_found.append(dependency)
                        dependency_analysis["dependencies"].append(dependency)
            
            dependency_analysis["dependency_graph"][feature_a["name"]] = dependencies_found
        
        # Detect circular dependencies
        dependency_analysis["circular_dependencies"] = _detect_circular_dependencies(
            dependency_analysis["dependency_graph"]
        )
        
        # Identify critical dependencies
        dependency_analysis["critical_dependencies"] = _identify_critical_dependencies(
            dependency_analysis["dependencies"]
        )
        
        # Generate implementation order
        dependency_analysis["implementation_order"] = _generate_implementation_order(
            dependency_analysis["dependency_graph"],
            dependency_analysis["circular_dependencies"]
        )
        
        # Create resolution plan
        dependency_analysis["resolution_plan"] = _create_dependency_resolution_plan(dependency_analysis)
        
    except Exception as e:
        logger.error(f"Error analyzing feature dependencies: {e}")
        dependency_analysis["analysis_error"] = str(e)
    
    return dependency_analysis


def _calculate_dependency_strength(feature_a: Dict[str, Any], feature_b: Dict[str, Any]) -> float:
    """Calculate the strength of dependency from feature_a to feature_b."""
    strength = 0.0
    
    # Check for explicit references in external_references
    external_refs = feature_a.get("external_references", [])
    feature_b_name = feature_b.get("name", "").lower()
    feature_b_path = feature_b.get("path", "").lower()
    
    for ref in external_refs:
        ref_lower = ref.lower()
        if feature_b_name in ref_lower or feature_b_path in ref_lower:
            strength += 0.5
    
    # Check for API dependencies (simplified)
    api_endpoints_b = feature_b.get("api_endpoints", [])
    for endpoint in api_endpoints_b:
        # If feature_a references endpoints that feature_b provides
        if any(endpoint.lower() in ref.lower() for ref in external_refs):
            strength += 0.3
    
    return min(strength, 1.0)  # Cap at 1.0


def _classify_dependency_type(feature_a: Dict[str, Any], feature_b: Dict[str, Any]) -> str:
    """Classify the type of dependency between features."""
    # This is a simplified classification - could be enhanced
    external_refs = feature_a.get("external_references", [])
    
    # Check for API dependencies
    if any("api" in ref.lower() or "endpoint" in ref.lower() for ref in external_refs):
        return "api_dependency"
    
    # Check for data dependencies
    if any("data" in ref.lower() or "model" in ref.lower() for ref in external_refs):
        return "data_dependency"
    
    # Check for service dependencies
    if any("service" in ref.lower() for ref in external_refs):
        return "service_dependency"
    
    return "code_dependency"


def _extract_dependency_details(feature_a: Dict[str, Any], feature_b: Dict[str, Any]) -> List[str]:
    """Extract specific details about dependencies between features."""
    details = []
    
    external_refs = feature_a.get("external_references", [])
    feature_b_name = feature_b.get("name", "").lower()
    
    for ref in external_refs:
        if feature_b_name in ref.lower():
            details.append(f"References: {ref}")
    
    return details[:5]  # Limit to first 5 details


def _detect_circular_dependencies(dependency_graph: Dict[str, List[Dict[str, Any]]]) -> List[List[str]]:
    """Detect circular dependencies in the dependency graph."""
    circular_deps = []
    
    def has_path(start: str, end: str, visited: Set[str]) -> bool:
        if start == end:
            return True
        if start in visited:
            return False
        
        visited.add(start)
        for dep in dependency_graph.get(start, []):
            if has_path(dep["to_feature"], end, visited):
                return True
        visited.remove(start)
        return False
    
    # Check each pair of features for circular dependencies
    features = list(dependency_graph.keys())
    for i, feature_a in enumerate(features):
        for j, feature_b in enumerate(features):
            if i != j:
                # Check if A -> B and B -> A
                if (has_path(feature_a, feature_b, set()) and 
                    has_path(feature_b, feature_a, set())):
                    cycle = sorted([feature_a, feature_b])
                    if cycle not in circular_deps:
                        circular_deps.append(cycle)
    
    return circular_deps


def _identify_critical_dependencies(dependencies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify critical dependencies that require special attention."""
    critical = []
    
    for dep in dependencies:
        if dep["strength"] >= 0.7:  # High strength dependencies
            critical.append(dep)
        elif dep["type"] == "api_dependency":  # API dependencies are often critical
            critical.append(dep)
    
    return critical


def _generate_implementation_order(
    dependency_graph: Dict[str, List[Dict[str, Any]]],
    circular_dependencies: List[List[str]]
) -> List[str]:
    """Generate suggested implementation order based on dependencies."""
    features = list(dependency_graph.keys())
    
    # Calculate dependency counts (how many features depend on each feature)
    dependency_counts = {}
    for feature in features:
        dependency_counts[feature] = 0
    
    for feature, deps in dependency_graph.items():
        for dep in deps:
            dependency_counts[dep["to_feature"]] += 1
    
    # Sort by dependency count (features with fewer dependencies first)
    implementation_order = sorted(features, key=lambda f: dependency_counts[f])
    
    return implementation_order


def _create_dependency_resolution_plan(dependency_analysis: Dict[str, Any]) -> List[str]:
    """Create a plan for resolving dependency issues."""
    plan = []
    
    circular_deps = dependency_analysis.get("circular_dependencies", [])
    critical_deps = dependency_analysis.get("critical_dependencies", [])
    
    if circular_deps:
        plan.append("Resolve circular dependencies:")
        for cycle in circular_deps:
            plan.append(f"  - Break circular dependency between {' and '.join(cycle)}")
        plan.append("  - Consider introducing abstraction layers or event-driven patterns")
    
    if critical_deps:
        plan.append("Address critical dependencies:")
        for dep in critical_deps[:5]:  # Limit to first 5
            plan.append(f"  - Ensure {dep['to_feature']} is implemented before {dep['from_feature']}")
    
    # General recommendations
    plan.append("Implementation strategy:")
    plan.append("  - Follow suggested implementation order")
    plan.append("  - Establish clear interface contracts between features")
    plan.append("  - Implement stub/mock interfaces for dependent features during development")
    plan.append("  - Create integration testing strategy for feature dependencies")
    
    return plan


# Progressive Workflow Management Functions

def create_progressive_migration_plan(
    project_path: Path,
    feature_boundaries: Dict[str, Any],
    priority_features: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a progressive migration plan for incremental adoption of spec-driven development.
    
    Args:
        project_path: Path to the project directory
        feature_boundaries: Result from extract_feature_boundaries
        priority_features: Optional list of features to prioritize
        
    Returns:
        Dictionary containing progressive migration plan
    """
    migration_plan = {
        "project_path": str(project_path),
        "project_name": project_path.name,
        "plan_date": _get_current_timestamp(),
        "migration_strategy": "progressive_incremental",
        "total_features": len(feature_boundaries.get("suggested_features", [])),
        "migration_phases": [],
        "timeline_estimate": "",
        "resource_allocation": {},
        "success_metrics": [],
        "risk_mitigation": [],
        "coordination_plan": {},
    }
    
    try:
        features = feature_boundaries.get("suggested_features", [])
        
        # Prioritize features for migration
        prioritized_features = _prioritize_features_for_migration(features, priority_features)
        
        # Create progressive migration phases
        migration_plan["migration_phases"] = _create_progressive_phases(prioritized_features)
        
        # Estimate timeline
        migration_plan["timeline_estimate"] = _estimate_progressive_timeline(prioritized_features)
        
        # Plan resource allocation
        migration_plan["resource_allocation"] = _plan_progressive_resources(prioritized_features)
        
        # Define success metrics
        migration_plan["success_metrics"] = _define_progressive_success_metrics(prioritized_features)
        
        # Risk mitigation strategies
        migration_plan["risk_mitigation"] = _identify_progressive_risks(prioritized_features)
        
        # Coordination plan
        migration_plan["coordination_plan"] = _create_coordination_plan(prioritized_features)
        
    except Exception as e:
        logger.error(f"Error creating progressive migration plan: {e}")
        migration_plan["planning_error"] = str(e)
    
    return migration_plan


def _prioritize_features_for_migration(
    features: List[Dict[str, Any]], 
    priority_list: Optional[List[str]]
) -> List[Dict[str, Any]]:
    """Prioritize features for progressive migration."""
    prioritized = []
    
    # Add priority features first
    if priority_list:
        for priority_name in priority_list:
            for feature in features:
                if feature.get("feature_name") == priority_name:
                    feature["priority"] = "high"
                    feature["migration_order"] = len(prioritized) + 1
                    prioritized.append(feature)
                    break
    
    # Add remaining features based on complexity and dependencies
    remaining_features = [f for f in features if f not in prioritized]
    
    # Sort by complexity (simple features first) and confidence score
    def priority_score(feature):
        complexity_score = {"low": 3, "medium": 2, "high": 1}.get(
            feature.get("estimated_complexity", "high"), 1
        )
        confidence_score = feature.get("confidence_score", 0.0)
        return complexity_score + confidence_score
    
    remaining_features.sort(key=priority_score, reverse=True)
    
    for feature in remaining_features:
        feature["priority"] = "normal"
        feature["migration_order"] = len(prioritized) + 1
        prioritized.append(feature)
    
    return prioritized


def _create_progressive_phases(features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create progressive migration phases."""
    phases = []
    
    # Phase 1: Pilot - Start with 1-2 simple features
    pilot_features = [f for f in features[:2] if f.get("confidence_score", 0) > 0.5]
    if pilot_features:
        phases.append({
            "phase": 1,
            "name": "Pilot Migration",
            "duration": "2-3 weeks",
            "description": "Start with simple, well-defined features to establish workflow",
            "features": [f["feature_name"] for f in pilot_features],
            "goals": [
                "Establish spec-driven workflow",
                "Train team on new process",
                "Validate tooling and templates",
                "Gather initial feedback",
            ],
            "deliverables": [
                "Pilot feature specifications",
                "Process documentation",
                "Team feedback and improvements",
                "Success metrics baseline",
            ]
        })
    
    # Phase 2: Expansion - Add more features gradually
    remaining_features = features[len(pilot_features):]
    batch_size = min(3, max(1, len(remaining_features) // 3))
    
    for i in range(0, len(remaining_features), batch_size):
        batch = remaining_features[i:i + batch_size]
        phase_num = len(phases) + 1
        
        phases.append({
            "phase": phase_num,
            "name": f"Progressive Expansion {phase_num - 1}",
            "duration": "3-4 weeks",
            "description": f"Migrate {len(batch)} additional features using established workflow",
            "features": [f["feature_name"] for f in batch],
            "goals": [
                "Apply spec-driven process to more features",
                "Refine and optimize workflow",
                "Address integration challenges",
                "Build team expertise",
            ],
            "deliverables": [
                "Feature specifications for batch",
                "Integration documentation",
                "Process refinements",
                "Cross-feature dependency analysis",
            ]
        })
    
    # Final phase: Integration and optimization
    if len(phases) > 1:
        phases.append({
            "phase": len(phases) + 1,
            "name": "Integration and Optimization",
            "duration": "2-3 weeks",
            "description": "Integrate all features and optimize the overall system",
            "features": ["All features"],
            "goals": [
                "Create master specification",
                "Resolve cross-feature dependencies",
                "Optimize development workflow",
                "Establish maintenance procedures",
            ],
            "deliverables": [
                "Master project specification",
                "Integration test suite",
                "Process optimization guide",
                "Long-term maintenance plan",
            ]
        })
    
    return phases


def _estimate_progressive_timeline(features: List[Dict[str, Any]]) -> str:
    """Estimate timeline for progressive migration."""
    feature_count = len(features)
    
    # Base time estimates
    pilot_weeks = 3
    feature_batch_weeks = 3
    integration_weeks = 2
    
    # Calculate based on feature count and complexity
    complex_features = len([f for f in features if f.get("confidence_score", 0) < 0.3])
    complexity_multiplier = 1.0 + (complex_features * 0.2)
    
    batch_count = max(1, (feature_count - 2) // 3)  # Subtract pilot features
    total_weeks = pilot_weeks + (batch_count * feature_batch_weeks) + integration_weeks
    total_weeks = int(total_weeks * complexity_multiplier)
    
    return f"{total_weeks}-{total_weeks + 4} weeks total ({total_weeks // 4}-{(total_weeks + 4) // 4} months)"


def _plan_progressive_resources(features: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Plan resource allocation for progressive migration."""
    return {
        "team_roles_needed": [
            "Migration lead (0.5-1.0 FTE)",
            "Technical writer (0.25-0.5 FTE)",
            "Developer representatives from each feature team",
            "Architecture reviewer",
        ],
        "training_requirements": [
            "Spec-driven development methodology (4 hours)",
            "Feature specification writing (2 hours)",
            "Integration and dependency management (2 hours)",
            "Tool usage and workflow (1 hour)",
        ],
        "infrastructure_needs": [
            "Specification repository setup",
            "CI/CD integration for specs",
            "Documentation hosting",
            "Progress tracking tools",
        ],
        "coordination_overhead": f"Estimated 10-15% additional time for cross-feature coordination",
    }


def _define_progressive_success_metrics(features: List[Dict[str, Any]]) -> List[str]:
    """Define success metrics for progressive migration."""
    return [
        f"Complete specifications for all {len(features)} identified features",
        "90%+ team satisfaction with new development process",
        "25%+ reduction in requirement-related rework",
        "Faster onboarding of new developers (baseline vs. after migration)",
        "Improved stakeholder feedback on delivered features",
        "Successful integration of all feature specifications",
        "Established and documented cross-feature dependency management",
        "Active use of spec-driven workflow for new feature development",
    ]


def _identify_progressive_risks(features: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Identify risks specific to progressive migration."""
    return [
        {
            "risk": "Inconsistent adoption across feature teams",
            "mitigation": "Establish clear governance and regular check-ins with all teams"
        },
        {
            "risk": "Integration challenges between early and late adopters",
            "mitigation": "Define clear interface contracts and maintain compatibility matrix"
        },
        {
            "risk": "Process drift over time",
            "mitigation": "Regular process reviews and continuous improvement cycles"
        },
        {
            "risk": "Resource competition between feature teams",
            "mitigation": "Clear resource allocation plan and executive sponsorship"
        },
        {
            "risk": "Specification quality degradation",
            "mitigation": "Peer review process and specification quality gates"
        },
        {
            "risk": "Dependency discovery late in migration",
            "mitigation": "Early dependency analysis and continuous integration testing"
        },
    ]


def _create_coordination_plan(features: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a coordination plan for progressive migration."""
    return {
        "governance_structure": [
            "Migration steering committee (weekly meetings)",
            "Feature team representatives (bi-weekly sync)",
            "Technical architecture review board (monthly)",
        ],
        "communication_channels": [
            "Dedicated Slack/Teams channel for migration",
            "Weekly progress reports",
            "Monthly stakeholder updates",
            "Quarterly migration review meetings",
        ],
        "coordination_activities": [
            "Cross-feature dependency review sessions",
            "Specification quality peer reviews",
            "Integration planning workshops",
            "Process improvement retrospectives",
        ],
        "decision_making_process": [
            "Feature-level decisions: Feature team leads",
            "Cross-feature decisions: Migration steering committee",
            "Architecture decisions: Technical review board",
            "Process decisions: Migration lead with team input",
        ],
    }


def track_onboarding_progress(
    project_path: Path,
    migration_plan: Dict[str, Any],
    completed_features: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Track progress of progressive onboarding migration.
    
    Args:
        project_path: Path to the project directory
        migration_plan: Result from create_progressive_migration_plan
        completed_features: List of features that have been completed
        
    Returns:
        Dictionary containing progress tracking information
    """
    progress_report = {
        "project_path": str(project_path),
        "tracking_date": _get_current_timestamp(),
        "migration_plan_reference": migration_plan.get("plan_date"),
        "overall_progress": {},
        "phase_progress": [],
        "feature_status": [],
        "blockers_and_issues": [],
        "next_actions": [],
        "recommendations": [],
    }
    
    try:
        phases = migration_plan.get("migration_phases", [])
        total_features = migration_plan.get("total_features", 0)
        completed_features = completed_features or []
        
        # Calculate overall progress
        progress_report["overall_progress"] = {
            "total_features": total_features,
            "completed_features": len(completed_features),
            "completion_percentage": (len(completed_features) / total_features * 100) if total_features > 0 else 0,
            "features_remaining": total_features - len(completed_features),
        }
        
        # Track phase progress
        for phase in phases:
            phase_features = phase.get("features", [])
            if "All features" in phase_features:
                # Integration phase
                phase_completed = len(completed_features) == total_features
                phase_completion = 100 if phase_completed else 0
            else:
                completed_in_phase = [f for f in phase_features if f in completed_features]
                phase_completion = (len(completed_in_phase) / len(phase_features) * 100) if phase_features else 0
            
            phase_status = {
                "phase": phase.get("phase"),
                "name": phase.get("name"),
                "completion_percentage": phase_completion,
                "status": _determine_phase_status(phase_completion),
                "features_in_phase": len(phase_features) if "All features" not in phase_features else total_features,
                "features_completed": len([f for f in phase_features if f in completed_features]) if "All features" not in phase_features else len(completed_features),
            }
            progress_report["phase_progress"].append(phase_status)
        
        # Track individual feature status
        all_features = set()
        for phase in phases:
            if "All features" not in phase.get("features", []):
                all_features.update(phase.get("features", []))
        
        for feature in all_features:
            status = "completed" if feature in completed_features else "pending"
            progress_report["feature_status"].append({
                "feature_name": feature,
                "status": status,
                "phase": _find_feature_phase(feature, phases),
            })
        
        # Generate recommendations and next actions
        progress_report["next_actions"] = _generate_next_actions(progress_report, phases)
        progress_report["recommendations"] = _generate_progress_recommendations(progress_report)
        
    except Exception as e:
        logger.error(f"Error tracking onboarding progress: {e}")
        progress_report["tracking_error"] = str(e)
    
    return progress_report


def _determine_phase_status(completion_percentage: float) -> str:
    """Determine phase status based on completion percentage."""
    if completion_percentage == 0:
        return "not_started"
    elif completion_percentage < 100:
        return "in_progress"
    else:
        return "completed"


def _find_feature_phase(feature_name: str, phases: List[Dict[str, Any]]) -> int:
    """Find which phase a feature belongs to."""
    for phase in phases:
        if feature_name in phase.get("features", []):
            return phase.get("phase", 0)
    return 0


def _generate_next_actions(progress_report: Dict[str, Any], phases: List[Dict[str, Any]]) -> List[str]:
    """Generate next actions based on current progress."""
    actions = []
    
    # Find current phase
    current_phase = None
    for phase_status in progress_report["phase_progress"]:
        if phase_status["status"] == "in_progress":
            current_phase = phase_status
            break
        elif phase_status["status"] == "not_started":
            current_phase = phase_status
            break
    
    if current_phase:
        phase_num = current_phase["phase"]
        phase_info = next((p for p in phases if p.get("phase") == phase_num), None)
        
        if phase_info:
            if current_phase["status"] == "not_started":
                actions.append(f"Start {phase_info['name']} phase")
                goals = phase_info.get("goals", [])
                if goals:
                    actions.append(f"Focus on: {goals[0]}")
            else:
                remaining_features = current_phase["features_in_phase"] - current_phase["features_completed"]
                actions.append(f"Complete remaining {remaining_features} features in {phase_info['name']}")
    
    # General actions
    completion_pct = progress_report["overall_progress"]["completion_percentage"]
    if completion_pct < 50:
        actions.append("Maintain regular team communication and feedback collection")
    elif completion_pct < 90:
        actions.append("Begin planning for integration phase")
    else:
        actions.append("Prepare for final integration and optimization")
    
    return actions


def _generate_progress_recommendations(progress_report: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on progress analysis."""
    recommendations = []
    
    completion_pct = progress_report["overall_progress"]["completion_percentage"]
    
    if completion_pct < 25:
        recommendations.append("Focus on early wins and team confidence building")
        recommendations.append("Collect and address early feedback promptly")
    elif completion_pct < 50:
        recommendations.append("Assess and refine process based on pilot results")
        recommendations.append("Scale successful practices to remaining features")
    elif completion_pct < 75:
        recommendations.append("Begin cross-feature integration planning")
        recommendations.append("Address any emerging coordination challenges")
    else:
        recommendations.append("Prepare comprehensive integration testing")
        recommendations.append("Document lessons learned for future projects")
    
    # Check for potential issues
    phase_statuses = [p["status"] for p in progress_report["phase_progress"]]
    if "in_progress" in phase_statuses and phase_statuses.count("in_progress") > 1:
        recommendations.append("Multiple phases in progress - consider focusing efforts")
    
    return recommendations


def validate_specification_consistency(
    feature_specifications: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Validate consistency across multiple feature specifications.
    
    Args:
        feature_specifications: List of feature specification dictionaries
        
    Returns:
        Dictionary containing consistency validation results
    """
    validation_report = {
        "validation_date": _get_current_timestamp(),
        "specifications_validated": len(feature_specifications),
        "consistency_score": 0.0,
        "validation_results": {
            "format_consistency": {},
            "naming_consistency": {},
            "requirement_consistency": {},
            "technical_consistency": {},
        },
        "inconsistencies_found": [],
        "recommendations": [],
        "overall_status": "unknown",
    }
    
    try:
        if len(feature_specifications) < 2:
            validation_report["overall_status"] = "insufficient_data"
            return validation_report
        
        # Validate format consistency
        format_score = _validate_format_consistency(feature_specifications, validation_report)
        
        # Validate naming consistency
        naming_score = _validate_naming_consistency(feature_specifications, validation_report)
        
        # Validate requirement consistency
        requirement_score = _validate_requirement_consistency(feature_specifications, validation_report)
        
        # Validate technical consistency
        technical_score = _validate_technical_consistency(feature_specifications, validation_report)
        
        # Calculate overall consistency score
        validation_report["consistency_score"] = (format_score + naming_score + requirement_score + technical_score) / 4
        
        # Determine overall status
        if validation_report["consistency_score"] >= 0.8:
            validation_report["overall_status"] = "consistent"
        elif validation_report["consistency_score"] >= 0.6:
            validation_report["overall_status"] = "mostly_consistent"
        else:
            validation_report["overall_status"] = "inconsistent"
        
        # Generate recommendations
        validation_report["recommendations"] = _generate_consistency_recommendations(validation_report)
        
    except Exception as e:
        logger.error(f"Error validating specification consistency: {e}")
        validation_report["validation_error"] = str(e)
    
    return validation_report


def _validate_format_consistency(specifications: List[Dict[str, Any]], report: Dict[str, Any]) -> float:
    """Validate format consistency across specifications."""
    format_results = {
        "required_sections_present": 0,
        "section_naming_consistent": 0,
        "structure_consistent": 0,
    }
    
    # Define expected sections
    expected_sections = [
        "project_name", "overview", "functional_requirements", 
        "non_functional_requirements", "user_stories", "technical_stack"
    ]
    
    section_presence = {}
    for section in expected_sections:
        section_presence[section] = sum(1 for spec in specifications if section in spec)
    
    # Check if all specs have required sections
    total_specs = len(specifications)
    consistent_sections = sum(1 for count in section_presence.values() if count == total_specs)
    format_results["required_sections_present"] = consistent_sections / len(expected_sections)
    
    # Check section naming consistency (simplified)
    format_results["section_naming_consistent"] = 0.8  # Placeholder
    format_results["structure_consistent"] = 0.8  # Placeholder
    
    report["validation_results"]["format_consistency"] = format_results
    return sum(format_results.values()) / len(format_results)


def _validate_naming_consistency(specifications: List[Dict[str, Any]], report: Dict[str, Any]) -> float:
    """Validate naming consistency across specifications."""
    naming_results = {
        "feature_naming_pattern": 0,
        "requirement_numbering": 0,
        "terminology_consistency": 0,
    }
    
    # Check feature naming patterns
    feature_names = [spec.get("project_name", "") for spec in specifications]
    naming_patterns = set()
    for name in feature_names:
        if "_" in name:
            naming_patterns.add("underscore")
        elif "-" in name:
            naming_patterns.add("hyphen")
        elif name.replace(" ", "").isalnum():
            naming_patterns.add("camelcase_or_words")
    
    naming_results["feature_naming_pattern"] = 1.0 if len(naming_patterns) == 1 else 0.5
    
    # Check requirement numbering consistency (simplified)
    naming_results["requirement_numbering"] = 0.7  # Placeholder
    naming_results["terminology_consistency"] = 0.8  # Placeholder
    
    report["validation_results"]["naming_consistency"] = naming_results
    return sum(naming_results.values()) / len(naming_results)


def _validate_requirement_consistency(specifications: List[Dict[str, Any]], report: Dict[str, Any]) -> float:
    """Validate requirement consistency across specifications."""
    requirement_results = {
        "requirement_format": 0,
        "acceptance_criteria": 0,
        "priority_definitions": 0,
    }
    
    # Check requirement format consistency
    all_requirements = []
    for spec in specifications:
        all_requirements.extend(spec.get("functional_requirements", []))
    
    # Simple format check - requirements should start with "REQ-" or similar
    formatted_requirements = sum(1 for req in all_requirements if req.startswith(("REQ-", "FR-", "F-")))
    if all_requirements:
        requirement_results["requirement_format"] = formatted_requirements / len(all_requirements)
    
    requirement_results["acceptance_criteria"] = 0.6  # Placeholder
    requirement_results["priority_definitions"] = 0.7  # Placeholder
    
    report["validation_results"]["requirement_consistency"] = requirement_results
    return sum(requirement_results.values()) / len(requirement_results)


def _validate_technical_consistency(specifications: List[Dict[str, Any]], report: Dict[str, Any]) -> float:
    """Validate technical consistency across specifications."""
    technical_results = {
        "technology_stack_alignment": 0,
        "api_conventions": 0,
        "architecture_patterns": 0,
    }
    
    # Check technology stack alignment
    all_languages = set()
    all_frameworks = set()
    
    for spec in specifications:
        tech_stack = spec.get("technical_stack", {})
        if isinstance(tech_stack, dict):
            languages = tech_stack.get("languages", [])
            frameworks = tech_stack.get("frameworks", [])
            if isinstance(languages, list):
                all_languages.update(languages)
            if isinstance(frameworks, list):
                all_frameworks.update(frameworks)
    
    # Higher consistency if fewer different technologies are used
    tech_diversity = len(all_languages) + len(all_frameworks)
    technical_results["technology_stack_alignment"] = max(0, 1.0 - (tech_diversity * 0.1))
    
    technical_results["api_conventions"] = 0.7  # Placeholder
    technical_results["architecture_patterns"] = 0.8  # Placeholder
    
    report["validation_results"]["technical_consistency"] = technical_results
    return sum(technical_results.values()) / len(technical_results)


def _generate_consistency_recommendations(validation_report: Dict[str, Any]) -> List[str]:
    """Generate recommendations for improving specification consistency."""
    recommendations = []
    
    consistency_score = validation_report.get("consistency_score", 0)
    
    if consistency_score < 0.6:
        recommendations.append("Significant inconsistencies detected - review and standardize specifications")
    
    # Format recommendations
    format_results = validation_report["validation_results"].get("format_consistency", {})
    if format_results.get("required_sections_present", 0) < 0.8:
        recommendations.append("Ensure all specifications include required sections")
    
    # Naming recommendations
    naming_results = validation_report["validation_results"].get("naming_consistency", {})
    if naming_results.get("feature_naming_pattern", 0) < 0.8:
        recommendations.append("Establish and enforce consistent feature naming conventions")
    
    # Technical recommendations
    technical_results = validation_report["validation_results"].get("technical_consistency", {})
    if technical_results.get("technology_stack_alignment", 0) < 0.7:
        recommendations.append("Review technology choices for better alignment across features")
    
    # General recommendations
    recommendations.append("Create specification template and style guide")
    recommendations.append("Implement peer review process for specifications")
    recommendations.append("Regular consistency audits during development")
    
    return recommendations