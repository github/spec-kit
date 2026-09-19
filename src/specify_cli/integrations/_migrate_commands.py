"""Compatibility imports for the extracted switch and upgrade commands."""

from .command_switch import integration_switch
from .command_upgrade import integration_upgrade
from ._command_upgrade_layout import (
    _PresetRegistryUnreadableError,
    _installed_command_presets_affecting_agent,
    _installed_presets_affecting_agent,
    _legacy_command_root_changed,
    _legacy_command_root_upgrade_pending,
    _manifest_path_under,
    _manifest_tracks_skill_layout,
)

__all__ = [
    "_PresetRegistryUnreadableError",
    "_installed_command_presets_affecting_agent",
    "_installed_presets_affecting_agent",
    "_legacy_command_root_changed",
    "_legacy_command_root_upgrade_pending",
    "_manifest_path_under",
    "_manifest_tracks_skill_layout",
    "integration_switch",
    "integration_upgrade",
]
