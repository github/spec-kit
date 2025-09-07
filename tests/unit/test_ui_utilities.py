"""Unit tests for UI utilities."""

from unittest.mock import MagicMock, patch

from specify_cli.utils.ui import (
    InteractiveMenu,
    KeyboardInput,
    StepTracker,
)
from specify_cli.utils.ui.progress_tracker import StepStatus


class TestStepTracker:
    """Test StepTracker functionality."""

    def test_create_default(self):
        """Test factory method creates instance."""
        tracker = StepTracker.create_default("Test")
        assert tracker.title == "Test"
        assert len(tracker._steps) == 0

    def test_add_step_fluent_interface(self):
        """Test fluent interface for adding steps."""
        tracker = StepTracker("Test")
        result = tracker.add_step("step1", "First Step")

        assert result is tracker  # Fluent interface
        assert "step1" in tracker._steps
        assert tracker._steps["step1"].label == "First Step"
        assert tracker._steps["step1"].status == StepStatus.PENDING

    def test_step_status_updates(self):
        """Test step status update methods."""
        tracker = StepTracker("Test")
        tracker.add_step("step1", "Test Step")

        # Test all status updates
        tracker.start_step("step1", "starting")
        assert tracker._steps["step1"].status == StepStatus.RUNNING
        assert tracker._steps["step1"].detail == "starting"

        tracker.complete_step("step1", "done")
        assert tracker._steps["step1"].status == StepStatus.DONE
        assert tracker._steps["step1"].detail == "done"

        tracker.error_step("step1", "failed")
        assert tracker._steps["step1"].status == StepStatus.ERROR

        tracker.skip_step("step1", "skipped")
        assert tracker._steps["step1"].status == StepStatus.SKIPPED

    def test_hierarchical_steps(self):
        """Test parent-child step relationships."""
        tracker = StepTracker("Test")
        tracker.add_step("parent", "Parent Step")
        tracker.add_step("child", "Child Step", parent="parent")

        assert "child" in tracker._steps["parent"].children
        assert tracker._steps["child"].parent == "parent"

    def test_context_manager(self):
        """Test context manager functionality."""
        with patch("specify_cli.utils.ui.progress_tracker.Live") as mock_live:
            mock_live_instance = MagicMock()
            mock_live.return_value = mock_live_instance

            with StepTracker("Test") as tracker:
                assert isinstance(tracker, StepTracker)

            mock_live_instance.start.assert_called_once()
            mock_live_instance.stop.assert_called_once()

    def test_render_creates_tree(self):
        """Test render method creates Rich tree."""
        tracker = StepTracker("Test")
        tracker.add_step("step1", "Step 1")
        tracker.start_step("step1")

        tree = tracker.render()
        assert tree is not None
        # Tree should be a Rich Tree object
        assert hasattr(tree, "label")
        # Check that the tree has the expected structure
        assert len(tracker._steps) == 1
        assert "step1" in tracker._steps


class TestKeyboardInput:
    """Test KeyboardInput functionality."""

    def test_is_available_static_method(self):
        """Test static method for checking availability."""
        available = KeyboardInput.is_available()
        assert isinstance(available, bool)

    def test_get_capabilities(self):
        """Test capabilities reporting."""
        caps = KeyboardInput.get_capabilities()
        assert isinstance(caps, dict)
        assert "arrow_keys" in caps
        assert "fallback_available" in caps
        assert caps["fallback_available"] is True

    def test_create_handler_factory(self):
        """Test factory method."""
        handler = KeyboardInput.create_handler()
        assert isinstance(handler, KeyboardInput)

    @patch("specify_cli.utils.ui.keyboard_input.READCHAR_AVAILABLE", False)
    def test_fallback_behavior_when_readchar_unavailable(self):
        """Test fallback when readchar is not available."""
        with patch("builtins.input", return_value=""):
            handler = KeyboardInput()
            result = handler.get_key()
            assert result == "enter"

    @patch("specify_cli.utils.ui.keyboard_input.READCHAR_AVAILABLE", True)
    @patch("specify_cli.utils.ui.keyboard_input.readchar")
    def test_key_mapping(self, mock_readchar):
        """Test key mapping functionality."""
        # Mock readchar module
        mock_readchar.readkey.return_value = "test"
        mock_readchar.key.UP = "up_key"
        mock_readchar.key.DOWN = "down_key"
        mock_readchar.key.ENTER = "enter_key"

        handler = KeyboardInput()

        # Test regular key
        result = handler.get_key()
        assert result == "test"


class TestInteractiveMenu:
    """Test InteractiveMenu functionality."""

    def test_create_styled_factory(self):
        """Test styled factory method."""
        menu = InteractiveMenu.create_styled()
        assert isinstance(menu, InteractiveMenu)

    @patch("specify_cli.utils.ui.interactive_menu.KeyboardInput")
    def test_select_with_list_input(self, mock_keyboard_class):
        """Test selection with list input."""
        mock_keyboard = MagicMock()
        mock_keyboard_class.is_available.return_value = False
        mock_keyboard_class.return_value = mock_keyboard

        menu = InteractiveMenu()

        # Mock _fallback_select to return a value
        with patch.object(menu, "_fallback_select", return_value="option1"):
            result = menu.select_with_arrows(["option1", "option2"], "Test")
            assert result == "option1"

    def test_fallback_select_numbered_input(self):
        """Test fallback selection with numbered input."""
        menu = InteractiveMenu()
        options = {"key1": "Option 1", "key2": "Option 2"}

        with patch("builtins.input", return_value="1"):
            result = menu._fallback_select(options, "Test")
            assert result == "key1"

    def test_fallback_select_quit(self):
        """Test fallback selection with quit."""
        menu = InteractiveMenu()
        options = {"key1": "Option 1"}

        with patch("builtins.input", return_value="q"):
            result = menu._fallback_select(options, "Test")
            assert result is None


class TestUIUtilitiesIntegration:
    """Integration tests for UI utilities."""

    @patch("specify_cli.utils.ui.interactive_menu.KeyboardInput")
    def test_step_tracker_with_interactive_menu(self, mock_keyboard_class):
        """Test StepTracker and InteractiveMenu working together."""
        # Mock keyboard input to force fallback behavior
        mock_keyboard_class.is_available.return_value = False

        tracker = StepTracker("Test Process")
        menu = InteractiveMenu()

        tracker.add_step("select", "User Selection")
        tracker.start_step("select")

        # Mock the selection
        with patch.object(menu, "_fallback_select", return_value="option1"):
            result = menu.select_with_arrows(["option1", "option2"], "Choose:")

        tracker.complete_step("select", f"Selected: {result}")

        assert tracker._steps["select"].status == StepStatus.DONE
        assert "option1" in tracker._steps["select"].detail
