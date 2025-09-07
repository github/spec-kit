"""
Template service for rendering Jinja2 templates in spec-kit

This module provides an interface and implementation for template processing,
supporting Jinja2 template rendering with context variables.
"""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple, cast

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, TemplateSyntaxError
from jinja2.meta import find_undeclared_variables

from specify_cli.models.project import TemplateContext, TemplateFile


class TemplateService(ABC):
    """Abstract base class for template processing services"""

    @abstractmethod
    def load_template_package(self, ai_assistant: str, template_dir: Path) -> bool:
        """
        Load template package for specified AI assistant

        Args:
            ai_assistant: Name of the AI assistant (e.g., "claude", "gpt")
            template_dir: Path to directory containing templates

        Returns:
            True if templates loaded successfully, False otherwise
        """
        pass

    @abstractmethod
    def render_template(self, template_name: str, context: TemplateContext) -> str:
        """
        Render a specific template with given context

        Args:
            template_name: Name of template file to render
            context: Template context with variables

        Returns:
            Rendered template content as string

        Raises:
            Exception: If template not found or rendering fails
        """
        pass

    @abstractmethod
    def render_project_templates(
        self, context: TemplateContext, output_dir: Path
    ) -> List[TemplateFile]:
        """
        Render all templates in the loaded package

        Args:
            context: Template context with variables
            output_dir: Directory where rendered files should be created

        Returns:
            List of TemplateFile objects with rendered content
        """
        pass

    @abstractmethod
    def validate_template_syntax(
        self, template_path: Path
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate template syntax

        Args:
            template_path: Path to template file

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    def get_template_variables(self, template_path: Path) -> List[str]:
        """
        Extract variables used in template

        Args:
            template_path: Path to template file

        Returns:
            List of variable names used in template
        """
        pass

    @abstractmethod
    def set_custom_template_dir(self, template_dir: Optional[Path]) -> bool:
        """
        Set custom template directory

        Args:
            template_dir: Path to custom template directory, or None to reset

        Returns:
            True if set successfully, False otherwise
        """
        pass


class JinjaTemplateService(TemplateService):
    """Jinja2-based template service implementation"""

    def __init__(self):
        self._template_dir: Optional[Path] = None
        self._custom_template_dir: Optional[Path] = None
        self._ai_assistant: Optional[str] = None
        self._environment: Optional[Environment] = None

    def load_template_package(self, ai_assistant: str, template_dir: Path) -> bool:
        """Load template package for specified AI assistant"""
        try:
            if not template_dir.exists() or not template_dir.is_dir():
                return False

            # Check if directory contains template files
            template_files = list(template_dir.glob("*.j2"))
            if not template_files:
                # Also check for templates without .j2 extension
                template_files = [
                    f
                    for f in template_dir.iterdir()
                    if f.is_file() and not f.name.startswith(".")
                ]

            self._template_dir = template_dir
            self._ai_assistant = ai_assistant
            self._environment = Environment(
                loader=FileSystemLoader(str(template_dir)),
                keep_trailing_newline=True,
                # Don't use StrictUndefined as it's too strict for template conditionals
            )

            # Add custom filters (register as a plain callable for typing compatibility)
            def regex_replace(value: str, pattern: str, replacement: str = "") -> str:
                return self._regex_replace_filter(value, pattern, replacement)

            self._environment.filters["regex_replace"] = cast(
                Callable[..., Any], regex_replace
            )

            return True

        except Exception:
            return False

    def render_template(self, template_name: str, context: TemplateContext) -> str:
        """Render a specific template with given context"""
        if self._environment is None:
            raise RuntimeError(
                "No template package loaded. Call load_template_package first."
            )

        try:
            template = self._environment.get_template(template_name)
            # Convert context to dict, handling both test and real TemplateContext
            context_dict = self._prepare_context(context)
            return template.render(**context_dict)

        except TemplateNotFound as e:
            raise FileNotFoundError(f"Template not found: {template_name}") from e
        except Exception as e:
            raise RuntimeError(
                f"Failed to render template '{template_name}': {str(e)}"
            ) from e

    def render_project_templates(
        self, context: TemplateContext, output_dir: Path
    ) -> List[TemplateFile]:
        """Render all templates in the loaded package"""
        if self._template_dir is None:
            return []

        template_files = []
        context_dict = self._prepare_context(context)

        # Find all template files
        for template_path in self._template_dir.iterdir():
            if not template_path.is_file() or template_path.name.startswith("."):
                continue

            try:
                # Determine output filename (remove .j2 extension if present)
                output_filename = template_path.name
                if output_filename.endswith(".j2"):
                    output_filename = output_filename[:-3]

                output_path = str(output_dir / output_filename)

                # Render template
                if self._environment:
                    template = self._environment.get_template(template_path.name)
                    content = template.render(**context_dict)
                else:
                    # Fallback for direct file reading
                    with open(template_path, "r", encoding="utf-8") as f:
                        content = f.read()

                # Determine if executable (simple heuristic)
                is_executable = self._is_executable_template(template_path, content)

                template_file = TemplateFile(
                    template_path=template_path,
                    output_path=output_path,
                    content=content,
                    is_executable=is_executable,
                )
                template_files.append(template_file)

            except Exception:
                # Skip problematic templates but continue processing others
                continue

        return template_files

    def validate_template_syntax(
        self, template_path: Path
    ) -> Tuple[bool, Optional[str]]:
        """Validate template syntax"""
        try:
            if not template_path.exists():
                return False, f"Template file not found: {template_path}"

            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            # Try to parse and compile template to catch more errors
            env = Environment()
            ast = env.parse(template_content)
            env.compile(ast)
            return True, None

        except TemplateSyntaxError as e:
            return False, f"Template syntax error: {str(e)}"
        except Exception as e:
            return False, f"Error validating template: {str(e)}"

    def get_template_variables(self, template_path: Path) -> List[str]:
        """Extract variables used in template"""
        try:
            if not template_path.exists():
                return []

            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            env = Environment()
            ast = env.parse(template_content)
            variables = find_undeclared_variables(ast)
            return sorted(variables)

        except Exception:
            return []

    def set_custom_template_dir(self, template_dir: Optional[Path]) -> bool:
        """Set custom template directory"""
        try:
            if template_dir is None:
                self._custom_template_dir = None
                return True

            if not template_dir.exists() or not template_dir.is_dir():
                return False

            self._custom_template_dir = template_dir
            return True

        except Exception:
            return False

    def _prepare_context(self, context: TemplateContext) -> dict:
        """
        Prepare context for template rendering

        Handles both test TemplateContext (with limited fields) and
        real TemplateContext (with full model).
        """
        # Use to_dict method if available (both test and real contexts should have it now)
        if hasattr(context, "to_dict"):
            return context.to_dict()
        else:
            # Fallback: extract common attributes manually
            context_dict = {}

            # Extract standard fields
            for attr in [
                "project_name",
                "ai_assistant",
                "feature_name",
                "branch_type",
                "author",
                "version",
                "branch_name",
                "task_name",
                "author_name",
                "author_email",
                "creation_date",
                "creation_year",
                "project_description",
            ]:
                if hasattr(context, attr):
                    context_dict[attr] = getattr(context, attr)

            # Handle additional_vars separately
            if hasattr(context, "additional_vars"):
                additional_vars = context.additional_vars
                if isinstance(additional_vars, dict):
                    context_dict["additional_vars"] = additional_vars
                    # Also merge the values directly for backwards compatibility
                    context_dict.update(additional_vars)

            # Handle template_variables and custom_fields
            if hasattr(context, "template_variables"):
                template_vars = context.template_variables
                if isinstance(template_vars, dict):
                    context_dict.update(template_vars)

            if hasattr(context, "custom_fields"):
                custom_fields = context.custom_fields
                if isinstance(custom_fields, dict):
                    context_dict.update(custom_fields)

            return context_dict

    def _regex_replace_filter(
        self, value: str, pattern: str, replacement: str = ""
    ) -> str:
        """Jinja2 filter for regex replacement"""
        try:
            return re.sub(pattern, replacement, str(value))
        except Exception:
            return str(value)  # Return original if regex fails

    def _is_executable_template(self, template_path: Path, content: str) -> bool:
        """Determine if template should produce an executable file"""
        # Check file extension patterns
        executable_extensions = {".sh", ".py", ".rb", ".pl", ".js"}

        # Remove .j2 extension if present for checking
        check_name = template_path.name
        if check_name.endswith(".j2"):
            check_name = check_name[:-3]

        check_path = Path(check_name)
        if check_path.suffix in executable_extensions:
            return True

        # Check for shebang in content
        if content.startswith("#!"):
            return True

        # Check for specific executable patterns in filename
        executable_patterns = ["run", "start", "stop", "deploy", "build", "test"]
        return any(pattern in check_name.lower() for pattern in executable_patterns)
