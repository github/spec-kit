"""Cross-platform keyboard input handling using readchar."""

from typing import TYPE_CHECKING, Optional

from rich.console import Console

if TYPE_CHECKING:
    import readchar

try:
    import readchar  # type: ignore[import-untyped]

    READCHAR_AVAILABLE = True
except ImportError:
    READCHAR_AVAILABLE = False
    readchar = None  # type: ignore[assignment]


class KeyboardInput:
    """Cross-platform keyboard input handling with fallback support."""

    @staticmethod
    def get_key() -> str:
        """Get single keypress across platforms.

        Returns:
            String representation of the key pressed

        Raises:
            ImportError: If readchar is not available and no fallback works
            KeyboardInterrupt: If Ctrl+C is pressed
        """
        if not READCHAR_AVAILABLE:
            # Fallback to input() for basic functionality
            console = Console()
            console.print(
                "[yellow]Arrow key navigation not available. Using basic input.[/yellow]"
            )
            return input("Press Enter to continue: ").strip() or "enter"

        try:
            # Type guard: readchar is guaranteed to be available here
            assert readchar is not None, (
                "readchar should be available when READCHAR_AVAILABLE is True"
            )
            key = readchar.readkey()

            # Arrow keys
            if key == readchar.key.UP:
                return "up"
            if key == readchar.key.DOWN:
                return "down"
            if key == readchar.key.LEFT:
                return "left"
            if key == readchar.key.RIGHT:
                return "right"

            # Special keys
            if key == readchar.key.ENTER:
                return "enter"
            if key == readchar.key.ESC:
                return "escape"
            if key == readchar.key.SPACE:
                return "space"
            if key == readchar.key.BACKSPACE:
                return "backspace"
            if key == readchar.key.TAB:
                return "tab"

            # Control keys
            if key == readchar.key.CTRL_C:
                raise KeyboardInterrupt
            if key == readchar.key.CTRL_D:
                return "ctrl_d"
            if key == readchar.key.CTRL_Z:
                return "ctrl_z"

            # Return the character as-is for regular keys
            return key

        except KeyboardInterrupt:
            raise
        except Exception:
            # Fallback for any readchar issues
            return "unknown"

    @staticmethod
    def get_arrow_key() -> Optional[str]:
        """Get arrow key direction or None.

        Returns:
            Arrow direction ("up", "down", "left", "right") or None
        """
        if not READCHAR_AVAILABLE:
            return None

        try:
            key = KeyboardInput.get_key()
            if key in ["up", "down", "left", "right"]:
                return key
            return None
        except (KeyboardInterrupt, Exception):
            return None

    @classmethod
    def create_handler(cls) -> "KeyboardInput":
        """Factory for platform-specific handler.

        Returns:
            KeyboardInput instance
        """
        return cls()

    def wait_for_enter(self, prompt: str = "Press Enter to continue...") -> None:
        """Wait for Enter key with prompt.

        Args:
            prompt: Text to display while waiting
        """
        console = Console()
        console.print(f"[dim]{prompt}[/dim]")

        if READCHAR_AVAILABLE:
            while True:
                try:
                    key = self.get_key()
                    if key == "enter":
                        break
                except KeyboardInterrupt:
                    console.print("\n[yellow]Cancelled[/yellow]")
                    raise
        else:
            input()

    def confirm_action(self, prompt: str, default: bool = True) -> bool:
        """Y/n confirmation prompt.

        Args:
            prompt: Question to ask user
            default: Default value if user just presses Enter

        Returns:
            True for yes, False for no
        """
        console = Console()

        options = "[Y/n]" if default else "[y/N]"

        console.print(f"{prompt} {options}")

        if READCHAR_AVAILABLE:
            while True:
                try:
                    key = self.get_key().lower()

                    if key == "enter":
                        return default
                    elif key == "y":
                        console.print("y")
                        return True
                    elif key == "n":
                        console.print("n")
                        return False
                    elif key == "escape" or key == "ctrl_c":
                        console.print("\n[yellow]Cancelled[/yellow]")
                        raise KeyboardInterrupt

                except KeyboardInterrupt:
                    raise
        else:
            # Fallback to input()
            try:
                response = input().strip().lower()
                if not response:
                    return default
                return response.startswith("y")
            except KeyboardInterrupt:
                console.print("\n[yellow]Cancelled[/yellow]")
                raise

    @staticmethod
    def is_available() -> bool:
        """Check if advanced keyboard input is available.

        Returns:
            True if readchar is available, False otherwise
        """
        return READCHAR_AVAILABLE

    @staticmethod
    def get_capabilities() -> dict:
        """Get information about input capabilities.

        Returns:
            Dictionary describing available features
        """
        return {
            "arrow_keys": READCHAR_AVAILABLE,
            "special_keys": READCHAR_AVAILABLE,
            "raw_input": READCHAR_AVAILABLE,
            "fallback_available": True,
        }
