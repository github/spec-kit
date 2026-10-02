"""Tests for the public bundle domain package."""


def test_legacy_bundler_error_import_remains_compatible():
    from specify_cli.bundler import BundlerError as LegacyBundlerError
    from specify_cli.bundles import BundlerError

    assert LegacyBundlerError is BundlerError
