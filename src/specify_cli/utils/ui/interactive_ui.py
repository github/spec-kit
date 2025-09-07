"""Interactive UI components with Rich styling and keyboard navigation."""

from typing import Callable, Dict, List, Optional, Union

from rich.console import Console

from .interactive_menu import InteractiveMenu


class InteractiveUI:
    """Rich-styled interactive UI components with keyboard navigation."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize InteractiveUI.

        Args:
            console: Rich console instance (creates new if None)
        """
        self._console = console or Console()
        self._menu = InteractiveMenu(self._console)
        self._theme_name: Optional[str] = None

    @classmethod
    def create_themed(cls, theme: str = "specify_theme") -> "InteractiveUI":
        """Create with custom theme for consistent branding.

        Args:
            theme: Theme name ('specify_theme' or 'default')

        Returns:
            InteractiveUI instance with theme applied
        """
        instance = cls()
        instance._theme_name = theme
        return instance

    def select(
        self,
        message: str,
        choices: Union[Dict[str, str], List[str]],
        default: Optional[str] = None,
    ) -> str:
        """Rich-styled selection with arrow key navigation.

        Args:
            message: Question/prompt to display
            choices: Dict {key: description} or List of strings
            default: Default selection key

        Returns:
            Selected choice value

        Raises:
            KeyboardInterrupt: If user cancels selection
        """
        result = self._menu.select_with_arrows(
            options=choices,
            prompt=message,
            default_key=default,
        )

        if result is None:
            raise KeyboardInterrupt

        return result

    def multiselect(
        self,
        message: str,
        choices: Union[Dict[str, str], List[str]],
        default: Optional[List[str]] = None,
        min_selections: int = 0,
        max_selections: Optional[int] = None,
    ) -> List[str]:
        """Multi-selection interface with arrow keys.

        Args:
            message: Question/prompt to display
            choices: Dict {key: description} or List of strings
            default: Default selected choices
            min_selections: Minimum number of selections required
            max_selections: Maximum number of selections allowed

        Returns:
            List of selected choice values

        Raises:
            KeyboardInterrupt: If user cancels selection
        """
        result = self._menu.multi_select_with_arrows(
            options=choices,
            prompt=message,
            default=default,
            min_selections=min_selections,
            max_selections=max_selections,
        )

        return result

    def confirm(self, message: str, default: bool = True) -> bool:
        """Styled confirmation prompts.

        Args:
            message: Question to ask
            default: Default answer

        Returns:
            True for yes, False for no

        Raises:
            KeyboardInterrupt: If user cancels
        """
        choices = {"yes": "Yes", "no": "No"}
        default_key = "yes" if default else "no"

        result = self.select(message, choices, default_key)
        return result == "yes"

    def text(
        self,
        message: str,
        default: Optional[str] = None,
        validate: Optional[Callable] = None,
    ) -> str:
        """Text input with Rich styling and validation.

        Args:
            message: Input prompt
            default: Default text value
            validate: Validation function

        Returns:
            User input text

        Raises:
            KeyboardInterrupt: If user cancels
        """
        self._console.print(f"[bold]{message}[/bold]")
        if default:
            self._console.print(f"[dim]Default: {default}[/dim]")

        while True:
            try:
                result = input("> ").strip()
                if not result and default:
                    return default

                if validate and not validate(result):
                    self._console.print("[red]Invalid input. Please try again.[/red]")
                    continue

                return result
            except KeyboardInterrupt:
                self._console.print("\n[yellow]Input cancelled[/yellow]")
                raise

    def path(
        self,
        message: str,
        default: Optional[str] = None,
        only_directories: bool = False,
        validate: Optional[Callable] = None,
    ) -> str:
        """Path input with validation.

        Args:
            message: Input prompt
            default: Default path
            only_directories: Restrict to directories only
            validate: Additional validation function

        Returns:
            Selected/entered path

        Raises:
            KeyboardInterrupt: If user cancels
        """
        path_type = "directory" if only_directories else "path"
        return self.text(f"{message} ({path_type})", default, validate)

    @staticmethod
    def is_available() -> bool:
        """Check if interactive UI is available.

        Returns:
            True if interactive UI is available, False otherwise
        """
        return True  # Always available since we use our own components

    @staticmethod
    def get_capabilities() -> Dict[str, bool]:
        """Get information about UI capabilities.

        Returns:
            Dictionary describing available features
        """
        return {
            "rich_styling": True,
            "arrow_navigation": True,
            "multiselect": True,
            "validation": True,
            "path_input": True,
            "confirmation": True,
        }
