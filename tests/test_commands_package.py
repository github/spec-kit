"""Test commands package structure."""


def test_commands_package_importable():
    """Test that commands package can be imported."""
    import specify_cli.commands
    assert specify_cli.commands is not None


def test_command_modules_importable():
    """Test that all command modules can be imported."""
    from specify_cli.commands import init, integration, preset, extension, workflow
    assert init is not None
    assert integration is not None
    assert preset is not None
    assert extension is not None
    assert workflow is not None
