"""Tests for the shared version operation."""

import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

from specify_cli import _operation_version
from specify_cli._operation_version import (
    VERSION_OPERATION,
    VersionResult,
    VersionRuntime,
    VersionSystem,
    collect_version_result,
)

EXPECTED_FEATURES = {
    "controlled_multi_install_integrations": True,
    "integration_use_command": True,
    "multi_install_safe_registry_metadata": True,
    "integration_upgrade_command": True,
    "self_check_command": True,
    "workflow_catalog": True,
    "bundled_templates": True,
}


def test_version_operation_descriptor_is_stable():
    """Adapters share one stable operation identity and capability contract."""
    assert VERSION_OPERATION.operation_id == "version"
    assert VERSION_OPERATION.contract_version == "1"
    assert VERSION_OPERATION.capabilities == frozenset({"local-read"})
    assert VERSION_OPERATION.network_access == "none"


def test_collect_version_result_returns_complete_typed_result():
    """The operation owns complete semantic version collection."""
    with (
        patch(
            "specify_cli._operation_version.get_speckit_version",
            return_value="1.2.3",
        ),
        patch(
            "specify_cli._operation_version.platform.python_version",
            return_value="3.13.1",
        ),
        patch(
            "specify_cli._operation_version.platform.system",
            return_value="ExampleOS",
        ),
        patch(
            "specify_cli._operation_version.platform.machine",
            return_value="example64",
        ),
        patch(
            "specify_cli._operation_version.platform.version",
            return_value="ExampleOS 4.5",
        ),
        patch(
            "specify_cli._operation_version._openssl_version",
            return_value="OpenSSL 3.4.0",
        ),
    ):
        result = collect_version_result()

    assert result == VersionResult(
        cli_version="1.2.3",
        runtime=VersionRuntime(
            python="3.13.1",
            openssl="OpenSSL 3.4.0",
        ),
        system=VersionSystem(
            platform="ExampleOS",
            architecture="example64",
            os_version="ExampleOS 4.5",
        ),
        features=EXPECTED_FEATURES,
    )


def test_openssl_version_returns_loaded_runtime(monkeypatch):
    """The operation reports the OpenSSL runtime loaded by Python."""
    monkeypatch.setitem(
        sys.modules,
        "ssl",
        SimpleNamespace(OPENSSL_VERSION="OpenSSL test"),
    )

    assert _operation_version._openssl_version() == "OpenSSL test"


def test_openssl_version_returns_none_when_unavailable(monkeypatch):
    """The operation treats a missing ssl module as unavailable."""
    monkeypatch.setitem(sys.modules, "ssl", None)

    assert _operation_version._openssl_version() is None


def test_feature_capabilities_are_stable_and_ordered():
    """Feature names and order remain part of the semantic result."""
    result = collect_version_result(
        include_environment=False,
        cli_version_getter=lambda: "1.2.3",
    )

    assert result.features == EXPECTED_FEATURES
    assert list(result.features) == list(EXPECTED_FEATURES)
    assert result.runtime is None
    assert result.system is None


def test_feature_only_collection_skips_environment_probes():
    """Focused capability collection does not touch runtime or system probes."""
    openssl_version_getter = Mock(side_effect=AssertionError("must not run"))
    with (
        patch(
            "specify_cli._operation_version.platform.python_version",
            side_effect=AssertionError("must not run"),
        ),
        patch(
            "specify_cli._operation_version.platform.system",
            side_effect=AssertionError("must not run"),
        ),
    ):
        result = collect_version_result(
            include_environment=False,
            cli_version_getter=lambda: "1.2.3",
            openssl_version_getter=openssl_version_getter,
        )

    assert result.cli_version == "1.2.3"
    openssl_version_getter.assert_not_called()


def test_operation_contract_is_transport_neutral():
    """The operation module exposes semantic data without adapter dependencies."""
    forbidden_names = {"typer", "rich", "mcp"}

    assert forbidden_names.isdisjoint(_operation_version.__dict__)
    assert VersionResult.__module__ == "specify_cli._operation_version"
