"""
Code cleanup utilities for the Bicep generator.

This module provides tools for identifying and removing dead code,
unused imports, and improving code organization.
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

console = Console()


@dataclass
class CleanupIssue:
    """Represents a code cleanup issue."""
    
    file_path: Path
    line_number: int
    issue_type: str
    description: str
    severity: str  # "low", "medium", "high"
    
    def __str__(self) -> str:
        """String representation of cleanup issue."""
        return f"{self.file_path}:{self.line_number} [{self.severity}] {self.issue_type}: {self.description}"


class CodeAnalyzer(ast.NodeVisitor):
    """AST visitor for analyzing Python code."""
    
    def __init__(self, file_path: Path):
        """Initialize code analyzer."""
        self.file_path = file_path
        self.imports: Set[str] = set()
        self.used_names: Set[str] = set()
        self.defined_functions: Set[str] = set()
        self.called_functions: Set[str] = set()
        self.defined_classes: Set[str] = set()
        self.instantiated_classes: Set[str] = set()
        self.issues: List[CleanupIssue] = []
    
    def visit_Import(self, node: ast.Import) -> None:
        """Track import statements."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track from...import statements."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name)
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name) -> None:
        """Track name usage."""
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track function definitions."""
        self.defined_functions.add(node.name)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track async function definitions."""
        self.defined_functions.add(node.name)
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call) -> None:
        """Track function calls."""
        if isinstance(node.func, ast.Name):
            self.called_functions.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                self.instantiated_classes.add(node.func.value.id)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track class definitions."""
        self.defined_classes.add(node.name)
        self.generic_visit(node)
    
    def analyze(self, source_code: str) -> None:
        """Analyze source code and identify issues."""
        try:
            tree = ast.parse(source_code)
            self.visit(tree)
            
            # Identify unused imports
            for imp in self.imports:
                if imp not in self.used_names and imp != "*":
                    self.issues.append(CleanupIssue(
                        file_path=self.file_path,
                        line_number=1,  # Would need to track actual line numbers
                        issue_type="unused_import",
                        description=f"Unused import: {imp}",
                        severity="low"
                    ))
            
            # Identify unused functions
            for func in self.defined_functions:
                if func not in self.called_functions and not func.startswith('_'):
                    self.issues.append(CleanupIssue(
                        file_path=self.file_path,
                        line_number=1,
                        issue_type="unused_function",
                        description=f"Potentially unused function: {func}",
                        severity="medium"
                    ))
            
            # Identify unused classes
            for cls in self.defined_classes:
                if cls not in self.instantiated_classes and not cls.startswith('_'):
                    self.issues.append(CleanupIssue(
                        file_path=self.file_path,
                        line_number=1,
                        issue_type="unused_class",
                        description=f"Potentially unused class: {cls}",
                        severity="medium"
                    ))
                    
        except SyntaxError as e:
            self.issues.append(CleanupIssue(
                file_path=self.file_path,
                line_number=e.lineno or 0,
                issue_type="syntax_error",
                description=f"Syntax error: {e.msg}",
                severity="high"
            ))


def analyze_file(file_path: Path) -> List[CleanupIssue]:
    """
    Analyze a single Python file for cleanup opportunities.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        List of cleanup issues found
    """
    if not file_path.exists() or file_path.suffix != '.py':
        return []
    
    analyzer = CodeAnalyzer(file_path)
    
    try:
        source_code = file_path.read_text(encoding='utf-8')
        analyzer.analyze(source_code)
    except Exception as e:
        analyzer.issues.append(CleanupIssue(
            file_path=file_path,
            line_number=0,
            issue_type="read_error",
            description=f"Error reading file: {e}",
            severity="high"
        ))
    
    return analyzer.issues


def analyze_directory(directory: Path) -> Dict[str, List[CleanupIssue]]:
    """
    Analyze all Python files in a directory recursively.
    
    Args:
        directory: Path to directory
        
    Returns:
        Dictionary mapping file paths to cleanup issues
    """
    results = {}
    
    for file_path in directory.rglob('*.py'):
        issues = analyze_file(file_path)
        if issues:
            results[str(file_path)] = issues
    
    return results


def find_duplicate_code(directory: Path, min_lines: int = 5) -> List[Tuple[Path, Path, int]]:
    """
    Find duplicate code blocks in Python files.
    
    Args:
        directory: Path to directory
        min_lines: Minimum number of lines for a duplicate block
        
    Returns:
        List of tuples (file1, file2, similarity_score)
    """
    duplicates = []
    files = list(directory.rglob('*.py'))
    
    for i, file1 in enumerate(files):
        try:
            content1 = file1.read_text(encoding='utf-8')
            lines1 = [line.strip() for line in content1.splitlines() if line.strip() and not line.strip().startswith('#')]
            
            for file2 in files[i+1:]:
                try:
                    content2 = file2.read_text(encoding='utf-8')
                    lines2 = [line.strip() for line in content2.splitlines() if line.strip() and not line.strip().startswith('#')]
                    
                    # Simple similarity check based on line overlap
                    common_lines = set(lines1) & set(lines2)
                    if len(common_lines) >= min_lines:
                        similarity = len(common_lines) / max(len(lines1), len(lines2)) * 100
                        duplicates.append((file1, file2, int(similarity)))
                        
                except Exception:
                    continue
                    
        except Exception:
            continue
    
    return sorted(duplicates, key=lambda x: x[2], reverse=True)


def identify_long_functions(directory: Path, max_lines: int = 50) -> List[Tuple[Path, str, int]]:
    """
    Identify functions that exceed a certain length.
    
    Args:
        directory: Path to directory
        max_lines: Maximum acceptable function length
        
    Returns:
        List of tuples (file_path, function_name, line_count)
    """
    long_functions = []
    
    for file_path in directory.rglob('*.py'):
        try:
            source_code = file_path.read_text(encoding='utf-8')
            tree = ast.parse(source_code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Count lines in function body
                    if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                        line_count = node.end_lineno - node.lineno + 1
                        if line_count > max_lines:
                            long_functions.append((file_path, node.name, line_count))
                            
        except Exception:
            continue
    
    return sorted(long_functions, key=lambda x: x[2], reverse=True)


def identify_complex_functions(directory: Path, max_complexity: int = 10) -> List[Tuple[Path, str, int]]:
    """
    Identify functions with high cyclomatic complexity.
    
    Args:
        directory: Path to directory
        max_complexity: Maximum acceptable complexity
        
    Returns:
        List of tuples (file_path, function_name, complexity)
    """
    complex_functions = []
    
    for file_path in directory.rglob('*.py'):
        try:
            source_code = file_path.read_text(encoding='utf-8')
            tree = ast.parse(source_code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Simple complexity calculation based on control flow statements
                    complexity = 1  # Base complexity
                    
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                            complexity += 1
                        elif isinstance(child, ast.BoolOp):
                            complexity += len(child.values) - 1
                    
                    if complexity > max_complexity:
                        complex_functions.append((file_path, node.name, complexity))
                        
        except Exception:
            continue
    
    return sorted(complex_functions, key=lambda x: x[2], reverse=True)


def display_cleanup_report(results: Dict[str, List[CleanupIssue]]) -> None:
    """
    Display code cleanup report in a formatted table.
    
    Args:
        results: Dictionary of cleanup issues by file
    """
    if not results:
        console.print("[green]✓[/green] No cleanup issues found")
        return
    
    # Count issues by severity
    severity_counts = {"low": 0, "medium": 0, "high": 0}
    for issues in results.values():
        for issue in issues:
            severity_counts[issue.severity] += 1
    
    # Display summary
    console.print("\n[bold cyan]Code Cleanup Report[/bold cyan]\n")
    
    table = Table(title="Issues by Severity")
    table.add_column("Severity", style="bold")
    table.add_column("Count", style="yellow")
    
    table.add_row("High", str(severity_counts["high"]), style="red")
    table.add_row("Medium", str(severity_counts["medium"]), style="yellow")
    table.add_row("Low", str(severity_counts["low"]), style="green")
    
    console.print(table)
    
    # Display issues by file
    console.print("\n[bold]Issues by File:[/bold]\n")
    
    for file_path, issues in results.items():
        tree = Tree(f"[cyan]{file_path}[/cyan] ({len(issues)} issues)")
        
        for issue in issues:
            color = {"low": "green", "medium": "yellow", "high": "red"}[issue.severity]
            tree.add(f"[{color}]{issue.issue_type}[/{color}]: {issue.description}")
        
        console.print(tree)


def display_duplicate_report(duplicates: List[Tuple[Path, Path, int]]) -> None:
    """
    Display duplicate code report.
    
    Args:
        duplicates: List of duplicate file pairs with similarity scores
    """
    if not duplicates:
        console.print("[green]✓[/green] No significant code duplication found")
        return
    
    table = Table(title="Duplicate Code Detected")
    table.add_column("File 1", style="cyan")
    table.add_column("File 2", style="cyan")
    table.add_column("Similarity %", style="yellow")
    
    for file1, file2, similarity in duplicates[:10]:  # Show top 10
        table.add_row(
            str(file1.relative_to(Path.cwd()) if file1.is_relative_to(Path.cwd()) else file1),
            str(file2.relative_to(Path.cwd()) if file2.is_relative_to(Path.cwd()) else file2),
            f"{similarity}%"
        )
    
    console.print(table)


def display_complexity_report(
    long_functions: List[Tuple[Path, str, int]],
    complex_functions: List[Tuple[Path, str, int]]
) -> None:
    """
    Display code complexity report.
    
    Args:
        long_functions: List of overly long functions
        complex_functions: List of overly complex functions
    """
    console.print("\n[bold cyan]Code Complexity Report[/bold cyan]\n")
    
    if long_functions:
        table = Table(title="Long Functions (>50 lines)")
        table.add_column("File", style="cyan")
        table.add_column("Function", style="yellow")
        table.add_column("Lines", style="red")
        
        for file_path, func_name, line_count in long_functions[:10]:
            table.add_row(
                str(file_path.relative_to(Path.cwd()) if file_path.is_relative_to(Path.cwd()) else file_path),
                func_name,
                str(line_count)
            )
        
        console.print(table)
    
    if complex_functions:
        table = Table(title="Complex Functions (>10 cyclomatic complexity)")
        table.add_column("File", style="cyan")
        table.add_column("Function", style="yellow")
        table.add_column("Complexity", style="red")
        
        for file_path, func_name, complexity in complex_functions[:10]:
            table.add_row(
                str(file_path.relative_to(Path.cwd()) if file_path.is_relative_to(Path.cwd()) else file_path),
                func_name,
                str(complexity)
            )
        
        console.print(table)
    
    if not long_functions and not complex_functions:
        console.print("[green]✓[/green] No complexity issues found")


def run_full_cleanup_analysis(directory: Path) -> None:
    """
    Run full code cleanup analysis on directory.
    
    Args:
        directory: Path to directory to analyze
    """
    console.print(f"\n[bold]Analyzing code in: {directory}[/bold]\n")
    
    # Analyze for cleanup issues
    console.print("[cyan]→[/cyan] Analyzing for cleanup opportunities...")
    results = analyze_directory(directory)
    display_cleanup_report(results)
    
    # Find duplicate code
    console.print("\n[cyan]→[/cyan] Searching for duplicate code...")
    duplicates = find_duplicate_code(directory)
    display_duplicate_report(duplicates)
    
    # Check complexity
    console.print("\n[cyan]→[/cyan] Analyzing code complexity...")
    long_functions = identify_long_functions(directory)
    complex_functions = identify_complex_functions(directory)
    display_complexity_report(long_functions, complex_functions)
    
    console.print("\n[green]✓[/green] Analysis complete")
