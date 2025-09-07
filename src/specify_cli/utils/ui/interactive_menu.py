"""Interactive menu system with arrow key navigation using Rich."""

from typing import Dict, List, Optional, Union

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from .keyboard_input import KeyboardInput


class InteractiveMenu:
    """Arrow key-based selection menu with Rich styling and fallback support."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize interactive menu.

        Args:
            console: Rich console instance (creates new if None)
        """
        self._console = console or Console()
        self._keyboard = KeyboardInput()

    @classmethod
    def create_styled(cls) -> "InteractiveMenu":
        """Factory method with predefined styling themes.

        Returns:
            InteractiveMenu instance with theme applied
        """
        # For now, just return default instance
        # Future: implement different color schemes
        return cls()

    def select_with_arrows(
        self,
        options: Union[Dict[str, str], List[str]],
        prompt: str = "Select an option:",
        selected_style: str = "bright_cyan",
        unselected_style: str = "white",
        default_key: Optional[str] = None,
    ) -> Optional[str]:
        """Interactive selection with arrow keys.

        Args:
            options: Dict {key: description} or List of strings
            prompt: Text to show above options
            selected_style: Rich style for selected option
            unselected_style: Rich style for unselected options
            default_key: Default option to start with

        Returns:
            Selected option key/value or None if cancelled
        """
        # Normalize options to dict format
        if isinstance(options, list):
            option_dict = {str(i): item for i, item in enumerate(options)}
            option_keys = [str(i) for i in range(len(options))]
        else:
            option_dict = options
            option_keys = list(options.keys())

        if not option_keys:
            self._console.print("[red]No options provided[/red]")
            return None

        # Set initial selection
        if default_key and default_key in option_keys:
            selected_index = option_keys.index(default_key)
        else:
            selected_index = 0

        # Check if advanced input is available
        if not KeyboardInput.is_available():
            return self._fallback_select(option_dict, prompt)

        selected_key = None

        def create_selection_panel():
            """Create the selection panel with current selection highlighted."""
            table = Table.grid(padding=(0, 2))
            table.add_column(style="bright_cyan", justify="left", width=3)
            table.add_column(justify="left")

            for i, key in enumerate(option_keys):
                if isinstance(options, list):
                    # For list options, show the actual value
                    display_text = options[i]
                else:
                    # For dict options, show key: value format
                    display_text = f"{key}: {option_dict[key]}"

                if i == selected_index:
                    table.add_row(
                        "▶", f"[{selected_style}]{display_text}[/{selected_style}]"
                    )
                else:
                    table.add_row(
                        " ", f"[{unselected_style}]{display_text}[/{unselected_style}]"
                    )

            table.add_row("", "")
            table.add_row(
                "", "[dim]Use ↑/↓ to navigate, Enter to select, Esc to cancel[/dim]"
            )

            return Panel(
                table,
                title=f"[bold]{prompt}[/bold]",
                border_style="cyan",
                padding=(1, 2),
            )

        self._console.print()

        try:
            with Live(
                create_selection_panel(),
                console=self._console,
                transient=True,
                auto_refresh=False,
            ) as live:
                while True:
                    try:
                        key = self._keyboard.get_key()

                        if key == "up":
                            selected_index = (selected_index - 1) % len(option_keys)
                        elif key == "down":
                            selected_index = (selected_index + 1) % len(option_keys)
                        elif key == "enter":
                            if isinstance(options, list):
                                selected_key = options[selected_index]
                            else:
                                selected_key = option_keys[selected_index]
                            break
                        elif key == "escape":
                            self._console.print(
                                "\n[yellow]Selection cancelled[/yellow]"
                            )
                            return None

                        live.update(create_selection_panel(), refresh=True)

                    except KeyboardInterrupt:
                        self._console.print("\n[yellow]Selection cancelled[/yellow]")
                        return None

        except Exception as e:
            # Fallback on any error
            self._console.print(
                f"[yellow]Input error, falling back to numbered selection: {e}[/yellow]"
            )
            return self._fallback_select(option_dict, prompt)

        return selected_key

    def multi_select_with_arrows(
        self,
        options: Union[Dict[str, str], List[str]],
        prompt: str = "Select options (Space to toggle, Enter to confirm):",
        default: Optional[List[str]] = None,
        min_selections: int = 0,
        max_selections: Optional[int] = None,
    ) -> List[str]:
        """Multi-selection interface with arrow keys.

        Args:
            options: Dict {key: description} or List of strings
            prompt: Text to show above options
            default: Default selected choices
            min_selections: Minimum number of selections required
            max_selections: Maximum number of selections allowed

        Returns:
            List of selected option keys/values
        """
        # Normalize options to dict format
        if isinstance(options, list):
            option_dict = {str(i): item for i, item in enumerate(options)}
            option_keys = [str(i) for i in range(len(options))]
        else:
            option_dict = options
            option_keys = list(options.keys())

        if not option_keys:
            self._console.print("[red]No options provided[/red]")
            return []

        # Check if advanced input is available
        if not KeyboardInput.is_available():
            return self._fallback_multi_select(option_dict, prompt, min_selections)

        selected_index = 0
        selected_items = set()

        # Initialize with default selections if provided
        if default:
            for default_item in default:
                if default_item in option_keys:
                    selected_items.add(default_item)

        def create_multi_selection_panel():
            """Create multi-selection panel."""
            table = Table.grid(padding=(0, 1))
            table.add_column(style="bright_cyan", justify="left", width=3)
            table.add_column(style="white", justify="left", width=3)
            table.add_column(justify="left")

            for i, key in enumerate(option_keys):
                display_text = (
                    option_dict[key] if isinstance(options, dict) else options[i]
                )

                cursor = "▶" if i == selected_index else " "
                checkbox = "[x]" if key in selected_items else "[ ]"

                style = "bright_cyan" if i == selected_index else "white"

                table.add_row(cursor, checkbox, f"[{style}]{display_text}[/{style}]")

            table.add_row("", "", "")
            table.add_row(
                "",
                "",
                "[dim]Use ↑/↓ to navigate, Space to toggle, Enter to confirm, Esc to cancel[/dim]",
            )

            return Panel(
                table,
                title=f"[bold]{prompt}[/bold]",
                border_style="cyan",
                padding=(1, 2),
            )

        self._console.print()

        try:
            with Live(
                create_multi_selection_panel(),
                console=self._console,
                transient=True,
                auto_refresh=False,
            ) as live:
                while True:
                    try:
                        key = self._keyboard.get_key()

                        if key == "up":
                            selected_index = (selected_index - 1) % len(option_keys)
                        elif key == "down":
                            selected_index = (selected_index + 1) % len(option_keys)
                        elif key == "space":
                            current_key = option_keys[selected_index]
                            if current_key in selected_items:
                                selected_items.remove(current_key)
                            else:
                                if (
                                    max_selections is None
                                    or len(selected_items) < max_selections
                                ):
                                    selected_items.add(current_key)
                        elif key == "enter":
                            if len(selected_items) >= min_selections:
                                break
                            else:
                                # Flash a message about minimum selections
                                pass
                        elif key == "escape":
                            self._console.print(
                                "\n[yellow]Selection cancelled[/yellow]"
                            )
                            return []

                        live.update(create_multi_selection_panel(), refresh=True)

                    except KeyboardInterrupt:
                        self._console.print("\n[yellow]Selection cancelled[/yellow]")
                        return []

        except Exception as e:
            # Fallback on any error
            self._console.print(
                f"[yellow]Input error, falling back to numbered selection: {e}[/yellow]"
            )
            return self._fallback_multi_select(option_dict, prompt, min_selections)

        # Convert selected keys back to values if using list input
        if isinstance(options, list):
            return [
                options[int(key)]
                for key in sorted(selected_items, key=lambda x: int(x))
            ]
        else:
            return list(selected_items)

    def _fallback_select(
        self, option_dict: Dict[str, str], prompt: str
    ) -> Optional[str]:
        """Fallback selection using numbered input.

        Args:
            option_dict: Options dictionary
            prompt: Selection prompt

        Returns:
            Selected option key or None
        """
        self._console.print(f"\n[bold]{prompt}[/bold]")

        option_keys = list(option_dict.keys())
        for i, key in enumerate(option_keys):
            self._console.print(f"  {i + 1}. {option_dict[key]}")

        while True:
            try:
                choice = input(
                    f"\nEnter number (1-{len(option_keys)}) or 'q' to quit: "
                ).strip()

                if choice.lower() == "q":
                    return None

                choice_num = int(choice)
                if 1 <= choice_num <= len(option_keys):
                    return option_keys[choice_num - 1]
                else:
                    self._console.print(
                        f"[red]Please enter a number between 1 and {len(option_keys)}[/red]"
                    )

            except (ValueError, KeyboardInterrupt):
                self._console.print("[yellow]Selection cancelled[/yellow]")
                return None

    def _fallback_multi_select(
        self, option_dict: Dict[str, str], prompt: str, min_selections: int
    ) -> List[str]:
        """Fallback multi-selection using numbered input.

        Args:
            option_dict: Options dictionary
            prompt: Selection prompt
            min_selections: Minimum selections required

        Returns:
            List of selected option keys
        """
        self._console.print(f"\n[bold]{prompt}[/bold]")

        option_keys = list(option_dict.keys())
        for i, key in enumerate(option_keys):
            self._console.print(f"  {i + 1}. {option_dict[key]}")

        self._console.print(
            f"\nEnter numbers separated by commas (minimum {min_selections} required)"
        )

        while True:
            try:
                choices = input("Selection: ").strip()
                if not choices:
                    continue

                selected_nums = [int(x.strip()) for x in choices.split(",")]
                selected_keys = []

                for num in selected_nums:
                    if 1 <= num <= len(option_keys):
                        selected_keys.append(option_keys[num - 1])
                    else:
                        self._console.print(f"[red]Invalid number: {num}[/red]")
                        break
                else:
                    if len(selected_keys) >= min_selections:
                        return selected_keys
                    else:
                        self._console.print(
                            f"[red]Please select at least {min_selections} options[/red]"
                        )

            except (ValueError, KeyboardInterrupt):
                self._console.print("[yellow]Selection cancelled[/yellow]")
                return []
