"""Validation utilities for spec-kit CLI inputs."""

import re
from pathlib import Path
from typing import Any, Callable, List, Optional, Union

from rich.console import Console


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


class Validators:
    """Collection of validation utilities for CLI inputs."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize validators utility.

        Args:
            console: Rich console for error display
        """
        self._console = console or Console()

    @staticmethod
    def project_name(name: str) -> bool:
        """Validate project name format.

        Args:
            name: Project name to validate

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid with reason
        """
        if not name:
            raise ValidationError("Project name cannot be empty")

        if len(name) > 50:
            raise ValidationError("Project name too long (max 50 characters)")

        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$", name):
            raise ValidationError(
                "Project name must start with letter/number and contain only "
                "letters, numbers, hyphens, and underscores"
            )

        # Avoid reserved names
        reserved = {"con", "prn", "aux", "nul", "com1", "com2", "lpt1", "lpt2"}
        if name.lower() in reserved:
            raise ValidationError(f"'{name}' is a reserved name")

        return True

    @staticmethod
    def directory_path(
        path: Union[str, Path], must_exist: bool = False, must_be_empty: bool = False
    ) -> bool:
        """Validate directory path.

        Args:
            path: Directory path to validate
            must_exist: Whether directory must already exist
            must_be_empty: Whether directory must be empty (if exists)

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid with reason
        """
        dir_path = Path(path)

        if must_exist and not dir_path.exists():
            raise ValidationError(f"Directory does not exist: {path}")

        if dir_path.exists() and not dir_path.is_dir():
            raise ValidationError(f"Path exists but is not a directory: {path}")

        if must_be_empty and dir_path.exists() and any(dir_path.iterdir()):
            raise ValidationError(f"Directory is not empty: {path}")

        # Check if we can create the directory (parent must exist and be writable)
        if not dir_path.exists():
            parent = dir_path.parent
            if not parent.exists():
                raise ValidationError(f"Parent directory does not exist: {parent}")

            # Try to check if parent is writable (may not work on all systems)
            try:
                test_file = parent / ".write_test"
                test_file.touch()
                test_file.unlink()
            except (PermissionError, OSError) as e:
                raise ValidationError(
                    f"No write permission in parent directory: {parent}"
                ) from e

        return True

    @staticmethod
    def file_path(
        path: Union[str, Path],
        must_exist: bool = False,
        allowed_extensions: Optional[List[str]] = None,
    ) -> bool:
        """Validate file path.

        Args:
            path: File path to validate
            must_exist: Whether file must already exist
            allowed_extensions: List of allowed file extensions (including dot)

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid with reason
        """
        file_path = Path(path)

        if must_exist and not file_path.exists():
            raise ValidationError(f"File does not exist: {path}")

        if file_path.exists() and not file_path.is_file():
            raise ValidationError(f"Path exists but is not a file: {path}")

        if allowed_extensions and file_path.suffix.lower() not in [
            ext.lower() for ext in allowed_extensions
        ]:
            raise ValidationError(
                f"File extension '{file_path.suffix}' not allowed. "
                f"Allowed: {', '.join(allowed_extensions)}"
            )

        return True

    @staticmethod
    def ai_assistant(assistant: str) -> bool:
        """Validate AI assistant choice.

        Args:
            assistant: AI assistant name

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid with reason
        """
        valid_assistants = ["claude", "gemini", "copilot"]
        if assistant not in valid_assistants:
            raise ValidationError(
                f"Invalid AI assistant '{assistant}'. "
                f"Valid options: {', '.join(valid_assistants)}"
            )
        return True

    @staticmethod
    def branch_name(name: str) -> bool:
        """Validate git branch name format.

        Args:
            name: Branch name to validate

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid with reason
        """
        if not name:
            raise ValidationError("Branch name cannot be empty")

        # Git branch naming rules
        if name.startswith(".") or name.endswith("."):
            raise ValidationError("Branch name cannot start or end with '.'")

        if ".." in name:
            raise ValidationError("Branch name cannot contain '..'")

        if name.endswith(".lock"):
            raise ValidationError("Branch name cannot end with '.lock'")

        # Invalid characters for git branch names
        invalid_chars = set(" ~^:?*[\\")
        if any(char in name for char in invalid_chars):
            raise ValidationError(
                f"Branch name contains invalid characters: {invalid_chars}"
            )

        # Check for control characters
        if any(ord(char) < 32 or ord(char) == 127 for char in name):
            raise ValidationError("Branch name cannot contain control characters")

        return True

    @staticmethod
    def template_name(name: str) -> bool:
        """Validate template name format.

        Args:
            name: Template name to validate

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid with reason
        """
        if not name:
            raise ValidationError("Template name cannot be empty")

        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$", name):
            raise ValidationError(
                "Template name must contain only letters, numbers, hyphens, and underscores"
            )

        if len(name) > 30:
            raise ValidationError("Template name too long (max 30 characters)")

        return True

    def create_questionary_validator(
        self, validation_func: Callable[[str], bool]
    ) -> Callable:
        """Create a validator function compatible with questionary.

        Args:
            validation_func: Function that raises ValidationError on invalid input

        Returns:
            Questionary-compatible validator function
        """

        def questionary_validator(text: str) -> Union[bool, str]:
            try:
                validation_func(text)
                return True
            except ValidationError as e:
                return str(e)

        return questionary_validator

    @staticmethod
    def non_empty_string(text: str, field_name: str = "Input") -> bool:
        """Validate that string is not empty.

        Args:
            text: Text to validate
            field_name: Name of field for error message

        Returns:
            True if valid

        Raises:
            ValidationError: If empty
        """
        if not text or not text.strip():
            raise ValidationError(f"{field_name} cannot be empty")
        return True

    @staticmethod
    def url_format(url: str) -> bool:
        """Validate URL format.

        Args:
            url: URL to validate

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid format
        """
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
            r"localhost|"  # localhost
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if not url_pattern.match(url):
            raise ValidationError("Invalid URL format")

        return True

    def validate_and_prompt(
        self, value: Any, validator_func: Callable, prompt: str, max_attempts: int = 3
    ) -> Any:
        """Validate value and re-prompt if invalid.

        Args:
            value: Initial value to validate
            validator_func: Validation function
            prompt: Prompt for re-input
            max_attempts: Maximum retry attempts

        Returns:
            Valid value

        Raises:
            ValidationError: If max attempts exceeded
        """
        attempts = 0
        current_value = value

        while attempts < max_attempts:
            try:
                validator_func(current_value)
                return current_value
            except ValidationError as e:
                attempts += 1
                self._console.print(f"[red]Validation error:[/red] {e}")

                if attempts >= max_attempts:
                    raise ValidationError(
                        f"Max validation attempts ({max_attempts}) exceeded"
                    ) from None

                try:
                    current_value = input(f"{prompt}: ").strip()
                except KeyboardInterrupt:
                    raise ValidationError("Input cancelled by user") from None

        return current_value
