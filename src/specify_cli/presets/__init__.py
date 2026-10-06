"""Preset domain exports; ``_commands.py`` registers the CLI handlers.

Handlers live in ``command_*.py`` and ``catalog/``. Domain implementations
live in private modules; package-level names preserve existing internal imports.
"""

from .._download_security import (
    MAX_JSON_CATALOG_BYTES as MAX_JSON_CATALOG_BYTES,
)
from .._download_security import (
    read_response_limited as read_response_limited,
)
from ..extensions import ExtensionRegistry as ExtensionRegistry
from ..shared_infra import verify_archive_sha256 as verify_archive_sha256
from ._catalog import PresetCatalog as PresetCatalog
from ._catalog import PresetCatalogEntry as PresetCatalogEntry
from ._manager import (
    _CONSTITUTION_PROVENANCE_FILE as _CONSTITUTION_PROVENANCE_FILE,
)
from ._manager import (
    _CONSTITUTION_SYNC_PRESET_ID as _CONSTITUTION_SYNC_PRESET_ID,
)
from ._manager import (
    PresetManager as PresetManager,
)
from ._manager import (
    _constitution_is_generated as _constitution_is_generated,
)
from ._manager import (
    _constitution_provenance_matches_preset as _constitution_provenance_matches_preset,
)
from ._manager import (
    _content_sha256 as _content_sha256,
)
from ._manager import (
    _is_comparable_version as _is_comparable_version,
)
from ._manager import (
    _materialize_constitution_template as _materialize_constitution_template,
)
from ._manager_commands import _substitute_core_template as _substitute_core_template
from ._manifest import (
    VALID_PRESET_STRATEGIES as VALID_PRESET_STRATEGIES,
)
from ._manifest import (
    VALID_PRESET_TEMPLATE_TYPES as VALID_PRESET_TEMPLATE_TYPES,
)
from ._manifest import (
    VALID_SCRIPT_STRATEGIES as VALID_SCRIPT_STRATEGIES,
)
from ._manifest import (
    PresetCompatibilityError as PresetCompatibilityError,
)
from ._manifest import (
    PresetError as PresetError,
)
from ._manifest import (
    PresetManifest as PresetManifest,
)
from ._manifest import (
    PresetValidationError as PresetValidationError,
)
from ._registry import PresetRegistry as PresetRegistry
from ._resolver import PresetResolver as PresetResolver
