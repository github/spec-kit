from specify_cli._console import console
from rich.console import Console


def test_console_is_rich_console():
    assert isinstance(console, Console)


def test_console_imported_in_init():
    import specify_cli
    assert hasattr(specify_cli, 'console')
