"""
Graceful degradation configuration for memory system.

Defines how system behaves when external dependencies are unavailable.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from ..logging import get_logger


class DegradationConfig:
    """Configuration for graceful degradation behavior."""

    DEFAULT_CONFIG = {
        "ollama": {
            "required": False,
            "fallback": "file_based",
            "warning_once": True,
            "warning_message": "Vector memory unavailable (Ollama not found). Using file-based memory only."
        },
        "agent_memory_mcp": {
            "required": False,
            "fallback": "grep_search",
            "warning_once": True,
            "warning_message": "agent-memory-mcp unavailable. Using grep search fallback."
        },
        "skillsmp": {
            "required": False,
            "fallback": "skip",
            "warning_once": True,
            "warning_message": "SkillsMP unavailable. Skill search disabled."
        }
    }

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize degradation config.

        Args:
            config_path: Path to config file
        """
        self.logger = get_logger()

        if config_path is None:
            from ..config import MemoryConfigManager
            config_mgr = MemoryConfigManager()
            config_path = config_mgr.config_dir / "degradation.json"

        self.config_path = config_path
        self.config = self._load_or_create_config()

    def _load_or_create_config(self) -> Dict[str, Any]:
        """Load existing config or create default.

        Returns:
            Configuration dict
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Error loading config, using defaults: {e}")

        # Create default
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.DEFAULT_CONFIG, f, indent=2)

        return self.DEFAULT_CONFIG.copy()

    def is_required(self, component: str) -> bool:
        """Check if component is required.

        Args:
            component: "ollama", "agent_memory_mcp", or "skillsmp"

        Returns:
            True if component is required
        """
        if component not in self.config:
            return False

        return self.config[component].get("required", False)

    def get_fallback(self, component: str) -> str:
        """Get fallback behavior for component.

        Args:
            component: Component name

        Returns:
            Fallback strategy name
        """
        if component not in self.config:
            return "skip"

        return self.config[component].get("fallback", "skip")

    def should_warn(self, component: str) -> bool:
        """Check if warning should be shown for component.

        Args:
            component: Component name

        Returns:
            True if warning not yet shown
        """
        if component not in self.config:
            return False

        if not self.config[component].get("warning_once", True):
            return False

        return True

    def mark_warning_shown(self, component: str) -> None:
        """Mark warning as shown for component.

        Args:
            component: Component name
        """
        if component in self.config:
            self.config[component]["warning_shown"] = True

            # Persist to disk
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)

    def get_warning_message(self, component: str) -> str:
        """Get warning message for component.

        Args:
            component: Component name

        Returns:
            Warning message string
        """
        if component not in self.config:
            return ""

        return self.config[component].get("warning_message", "")

    def update_config(
        self,
        component: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update configuration for a component.

        Args:
            component: Component name
            updates: Dict with keys to update

        Returns:
            True if successful
        """
        if component not in self.config:
            self.config[component] = {}

        self.config[component].update(updates)

        # Persist
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error updating config: {e}")
            return False
