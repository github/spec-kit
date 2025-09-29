import pytest
from unittest.mock import patch
from main import colorful_hello, main

def test_colorful_hello(capsys):
    """Tests the colorful_hello function."""
    colorful_hello()
    captured = capsys.readouterr()
    assert "Hello, World!" in captured.out

def test_main(capsys):
    """Tests the main function."""
    with patch('rich.console.Console.input', return_value='test'):
        main()
        captured = capsys.readouterr()
        assert "Hello, test!" in captured.out
