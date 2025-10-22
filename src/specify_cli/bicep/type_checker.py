"""
Type checking and code quality utilities for Bicep generator.

This module provides tools for adding type hints, improving error messages,
and enhancing code documentation.
"""

import ast
import inspect
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, get_type_hints

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

console = Console()


@dataclass
class TypeHintIssue:
    """Represents a missing or incomplete type hint."""
    
    file_path: Path
    line_number: int
    function_name: str
    issue_type: str  # "missing_param", "missing_return", "missing_annotation"
    parameter_name: Optional[str] = None
    suggestion: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation."""
        if self.parameter_name:
            return f"{self.file_path}:{self.line_number} - {self.function_name}: {self.issue_type} for '{self.parameter_name}'"
        return f"{self.file_path}:{self.line_number} - {self.function_name}: {self.issue_type}"


@dataclass
class DocstringIssue:
    """Represents a missing or incomplete docstring."""
    
    file_path: Path
    line_number: int
    name: str
    element_type: str  # "function", "class", "method"
    issue_type: str  # "missing", "incomplete"
    missing_sections: List[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.missing_sections is None:
            self.missing_sections = []
    
    def __str__(self) -> str:
        """String representation."""
        if self.missing_sections:
            sections = ", ".join(self.missing_sections)
            return f"{self.file_path}:{self.line_number} - {self.name}: Missing sections: {sections}"
        return f"{self.file_path}:{self.line_number} - {self.name}: {self.issue_type} docstring"


@dataclass
class ErrorMessageIssue:
    """Represents an error message that could be improved."""
    
    file_path: Path
    line_number: int
    current_message: str
    issue_type: str  # "generic", "unclear", "no_context"
    suggestion: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.file_path}:{self.line_number} - {self.issue_type}: '{self.current_message}'"


class TypeHintAnalyzer(ast.NodeVisitor):
    """Analyzes Python code for missing type hints."""
    
    def __init__(self, file_path: Path):
        """Initialize analyzer."""
        self.file_path = file_path
        self.issues: List[TypeHintIssue] = []
        self.current_class: Optional[str] = None
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        self._check_function(node)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        self._check_function(node)
        self.generic_visit(node)
    
    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Check function for type hints."""
        # Skip private functions (starting with _) for now
        if node.name.startswith('_') and node.name != '__init__':
            return
        
        # Check return type annotation
        if node.returns is None and node.name != '__init__':
            self.issues.append(TypeHintIssue(
                file_path=self.file_path,
                line_number=node.lineno,
                function_name=node.name,
                issue_type="missing_return",
                suggestion="Add return type annotation (e.g., -> None, -> str)"
            ))
        
        # Check parameter annotations
        for arg in node.args.args:
            if arg.arg == 'self' or arg.arg == 'cls':
                continue
            
            if arg.annotation is None:
                self.issues.append(TypeHintIssue(
                    file_path=self.file_path,
                    line_number=node.lineno,
                    function_name=node.name,
                    issue_type="missing_param",
                    parameter_name=arg.arg,
                    suggestion=f"Add type annotation for parameter '{arg.arg}'"
                ))


class DocstringAnalyzer(ast.NodeVisitor):
    """Analyzes Python code for missing or incomplete docstrings."""
    
    def __init__(self, file_path: Path):
        """Initialize analyzer."""
        self.file_path = file_path
        self.issues: List[DocstringIssue] = []
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        if not node.name.startswith('_'):
            self._check_docstring(node, "class")
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        if not node.name.startswith('_'):
            self._check_docstring(node, "function")
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        if not node.name.startswith('_'):
            self._check_docstring(node, "function")
        self.generic_visit(node)
    
    def _check_docstring(
        self,
        node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
        element_type: str
    ) -> None:
        """Check if node has adequate docstring."""
        docstring = ast.get_docstring(node)
        
        if docstring is None:
            self.issues.append(DocstringIssue(
                file_path=self.file_path,
                line_number=node.lineno,
                name=node.name,
                element_type=element_type,
                issue_type="missing"
            ))
            return
        
        # Check for sections in function/method docstrings
        if element_type == "function" and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            missing = []
            
            # Check for Args section if function has parameters
            has_params = any(
                arg.arg not in ('self', 'cls')
                for arg in node.args.args
            )
            if has_params and "Args:" not in docstring and "Parameters:" not in docstring:
                missing.append("Args")
            
            # Check for Returns section if function has return annotation
            if node.returns is not None and "Returns:" not in docstring:
                missing.append("Returns")
            
            if missing:
                self.issues.append(DocstringIssue(
                    file_path=self.file_path,
                    line_number=node.lineno,
                    name=node.name,
                    element_type=element_type,
                    issue_type="incomplete",
                    missing_sections=missing
                ))


class ErrorMessageAnalyzer(ast.NodeVisitor):
    """Analyzes error messages for clarity and context."""
    
    def __init__(self, file_path: Path):
        """Initialize analyzer."""
        self.file_path = file_path
        self.issues: List[ErrorMessageIssue] = []
    
    def visit_Raise(self, node: ast.Raise) -> None:
        """Visit raise statement."""
        if node.exc and isinstance(node.exc, ast.Call):
            # Check if exception has a message
            if node.exc.args:
                for arg in node.exc.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        self._check_error_message(arg.value, node.lineno)
        self.generic_visit(node)
    
    def _check_error_message(self, message: str, line_number: int) -> None:
        """Check error message quality."""
        # Check for generic messages
        generic_patterns = [
            r"^error$",
            r"^failed$",
            r"^invalid$",
            r"^something went wrong$",
            r"^an error occurred$",
        ]
        
        for pattern in generic_patterns:
            if re.match(pattern, message.lower().strip()):
                self.issues.append(ErrorMessageIssue(
                    file_path=self.file_path,
                    line_number=line_number,
                    current_message=message,
                    issue_type="generic",
                    suggestion="Provide specific details about what failed and why"
                ))
                return
        
        # Check for lack of context (very short messages)
        if len(message.strip()) < 10:
            self.issues.append(ErrorMessageIssue(
                file_path=self.file_path,
                line_number=line_number,
                current_message=message,
                issue_type="unclear",
                suggestion="Add more context about the error condition"
            ))


def analyze_type_hints(file_path: Path) -> List[TypeHintIssue]:
    """
    Analyze a Python file for missing type hints.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        List of type hint issues
    """
    if not file_path.exists() or file_path.suffix != '.py':
        return []
    
    try:
        source = file_path.read_text(encoding='utf-8')
        tree = ast.parse(source)
        
        analyzer = TypeHintAnalyzer(file_path)
        analyzer.visit(tree)
        
        return analyzer.issues
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not analyze {file_path}: {e}")
        return []


def analyze_docstrings(file_path: Path) -> List[DocstringIssue]:
    """
    Analyze a Python file for missing or incomplete docstrings.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        List of docstring issues
    """
    if not file_path.exists() or file_path.suffix != '.py':
        return []
    
    try:
        source = file_path.read_text(encoding='utf-8')
        tree = ast.parse(source)
        
        analyzer = DocstringAnalyzer(file_path)
        analyzer.visit(tree)
        
        return analyzer.issues
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not analyze {file_path}: {e}")
        return []


def analyze_error_messages(file_path: Path) -> List[ErrorMessageIssue]:
    """
    Analyze a Python file for error message quality.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        List of error message issues
    """
    if not file_path.exists() or file_path.suffix != '.py':
        return []
    
    try:
        source = file_path.read_text(encoding='utf-8')
        tree = ast.parse(source)
        
        analyzer = ErrorMessageAnalyzer(file_path)
        analyzer.visit(tree)
        
        return analyzer.issues
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not analyze {file_path}: {e}")
        return []


def analyze_directory(directory: Path) -> Dict[str, Any]:
    """
    Analyze all Python files in directory for code quality.
    
    Args:
        directory: Path to directory
        
    Returns:
        Dictionary with analysis results
    """
    results = {
        "type_hints": {},
        "docstrings": {},
        "error_messages": {},
        "summary": {
            "total_files": 0,
            "files_with_issues": 0,
            "type_hint_issues": 0,
            "docstring_issues": 0,
            "error_message_issues": 0
        }
    }
    
    for file_path in directory.rglob('*.py'):
        results["summary"]["total_files"] += 1
        
        # Analyze type hints
        type_issues = analyze_type_hints(file_path)
        if type_issues:
            results["type_hints"][str(file_path)] = type_issues
            results["summary"]["type_hint_issues"] += len(type_issues)
        
        # Analyze docstrings
        doc_issues = analyze_docstrings(file_path)
        if doc_issues:
            results["docstrings"][str(file_path)] = doc_issues
            results["summary"]["docstring_issues"] += len(doc_issues)
        
        # Analyze error messages
        error_issues = analyze_error_messages(file_path)
        if error_issues:
            results["error_messages"][str(file_path)] = error_issues
            results["summary"]["error_message_issues"] += len(error_issues)
        
        # Count files with issues
        if type_issues or doc_issues or error_issues:
            results["summary"]["files_with_issues"] += 1
    
    return results


def display_code_quality_report(results: Dict[str, Any]) -> None:
    """
    Display code quality analysis report.
    
    Args:
        results: Analysis results from analyze_directory
    """
    summary = results["summary"]
    
    console.print("\n[bold cyan]Code Quality Analysis Report[/bold cyan]\n")
    
    # Summary table
    table = Table(title="Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="yellow")
    
    table.add_row("Total Files Analyzed", str(summary["total_files"]))
    table.add_row("Files with Issues", str(summary["files_with_issues"]))
    table.add_row("Type Hint Issues", str(summary["type_hint_issues"]))
    table.add_row("Docstring Issues", str(summary["docstring_issues"]))
    table.add_row("Error Message Issues", str(summary["error_message_issues"]))
    
    total_issues = (
        summary["type_hint_issues"] +
        summary["docstring_issues"] +
        summary["error_message_issues"]
    )
    table.add_row("[bold]Total Issues[/bold]", f"[bold]{total_issues}[/bold]")
    
    console.print(table)
    
    # Type hint issues
    if results["type_hints"]:
        console.print("\n[bold yellow]Type Hint Issues:[/bold yellow]\n")
        for file_path, issues in list(results["type_hints"].items())[:5]:
            tree = Tree(f"[cyan]{Path(file_path).name}[/cyan] ({len(issues)} issues)")
            for issue in issues[:10]:
                tree.add(f"[yellow]Line {issue.line_number}:[/yellow] {issue.function_name} - {issue.issue_type}")
            console.print(tree)
    
    # Docstring issues
    if results["docstrings"]:
        console.print("\n[bold yellow]Docstring Issues:[/bold yellow]\n")
        for file_path, issues in list(results["docstrings"].items())[:5]:
            tree = Tree(f"[cyan]{Path(file_path).name}[/cyan] ({len(issues)} issues)")
            for issue in issues[:10]:
                sections = f" - Missing: {', '.join(issue.missing_sections)}" if issue.missing_sections else ""
                tree.add(f"[yellow]Line {issue.line_number}:[/yellow] {issue.name}{sections}")
            console.print(tree)
    
    # Error message issues
    if results["error_messages"]:
        console.print("\n[bold yellow]Error Message Issues:[/bold yellow]\n")
        for file_path, issues in list(results["error_messages"].items())[:5]:
            tree = Tree(f"[cyan]{Path(file_path).name}[/cyan] ({len(issues)} issues)")
            for issue in issues[:10]:
                tree.add(f"[yellow]Line {issue.line_number}:[/yellow] {issue.issue_type} - '{issue.current_message}'")
            console.print(tree)
    
    # Overall status
    console.print()
    if total_issues == 0:
        console.print("[green]✓[/green] No code quality issues found!")
    elif total_issues < 50:
        console.print(f"[yellow]⚠[/yellow] Found {total_issues} issues - consider addressing them")
    else:
        console.print(f"[red]✗[/red] Found {total_issues} issues - significant improvements needed")


def generate_improvement_suggestions(results: Dict[str, Any]) -> List[str]:
    """
    Generate actionable improvement suggestions.
    
    Args:
        results: Analysis results from analyze_directory
        
    Returns:
        List of improvement suggestions
    """
    suggestions = []
    summary = results["summary"]
    
    if summary["type_hint_issues"] > 0:
        suggestions.append(
            f"Add type hints to {summary['type_hint_issues']} locations. "
            "Use `from typing import Any, Dict, List, Optional` for complex types."
        )
    
    if summary["docstring_issues"] > 0:
        suggestions.append(
            f"Add or improve docstrings for {summary['docstring_issues']} items. "
            "Follow Google or NumPy docstring style for consistency."
        )
    
    if summary["error_message_issues"] > 0:
        suggestions.append(
            f"Improve {summary['error_message_issues']} error messages. "
            "Include context about what failed, why it failed, and how to fix it."
        )
    
    if not suggestions:
        suggestions.append("Code quality looks good! Continue maintaining high standards.")
    
    return suggestions


def display_improvement_suggestions(suggestions: List[str]) -> None:
    """
    Display improvement suggestions.
    
    Args:
        suggestions: List of suggestions
    """
    console.print("\n[bold cyan]Improvement Suggestions:[/bold cyan]\n")
    
    for i, suggestion in enumerate(suggestions, 1):
        console.print(f"  [yellow]{i}.[/yellow] {suggestion}")
    
    console.print()
