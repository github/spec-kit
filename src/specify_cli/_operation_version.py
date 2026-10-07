"""Shared application operation for version information collection."""

from __future__ import annotations

import platform
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from ._assets import get_speckit_version


@dataclass(frozen=True)
class VersionRuntime:
    """Runtime versions reported by the version operation."""

    python: str
    openssl: str | None


@dataclass(frozen=True)
class VersionSystem:
    """Host system information reported by the version operation."""

    platform: str
    architecture: str
    os_version: str


@dataclass(frozen=True)
class VersionResult:
    """Transport-neutral result of the version operation."""

    cli_version: str
    runtime: VersionRuntime | None
    system: VersionSystem | None
    features: dict[str, bool]


@dataclass(frozen=True)
class VersionOperationDescriptor:
    """Stable metadata shared by delivery adapters for ``version``."""

    operation_id: Literal["version"]
    contract_version: Literal["1"]
    capabilities: frozenset[Literal["local-read"]]
    network_access: Literal["none"]


VERSION_OPERATION = VersionOperationDescriptor(
    operation_id="version",
    contract_version="1",
    capabilities=frozenset({"local-read"}),
    network_access="none",
)


def _feature_capabilities() -> dict[str, bool]:
    """Return stable local CLI capability flags for humans and agents."""
    return {
        "controlled_multi_install_integrations": True,
        "integration_use_command": True,
        "multi_install_safe_registry_metadata": True,
        "integration_upgrade_command": True,
        "self_check_command": True,
        "workflow_catalog": True,
        "bundled_templates": True,
    }


def _openssl_version() -> str | None:
    """Return the loaded OpenSSL version, or None when unavailable."""
    try:
        import ssl
    except ImportError:
        return None

    value = getattr(ssl, "OPENSSL_VERSION", None)
    return value if isinstance(value, str) and value else None


def collect_version_result(
    *,
    include_environment: bool = True,
    cli_version_getter: Callable[[], str] | None = None,
    openssl_version_getter: Callable[[], str | None] | None = None,
    feature_capabilities_getter: Callable[[], dict[str, bool]] | None = None,
) -> VersionResult:
    """Collect semantic version information for any delivery adapter."""
    get_cli_version = cli_version_getter or get_speckit_version
    get_openssl_version = openssl_version_getter or _openssl_version
    get_feature_capabilities = feature_capabilities_getter or _feature_capabilities

    cli_version = get_cli_version()
    features = get_feature_capabilities()
    if not include_environment:
        return VersionResult(
            cli_version=cli_version,
            runtime=None,
            system=None,
            features=features,
        )

    return VersionResult(
        cli_version=cli_version,
        runtime=VersionRuntime(
            python=platform.python_version(),
            openssl=get_openssl_version(),
        ),
        system=VersionSystem(
            platform=platform.system(),
            architecture=platform.machine(),
            os_version=platform.version(),
        ),
        features=features,
    )
