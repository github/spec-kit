from io import StringIO
from unittest.mock import patch, MagicMock
from main import main, create_hello_message, get_user_name, create_greeting_message, display_message, console


def test_create_hello_message():
    """Test that hello message is created correctly."""
    message = create_hello_message()
    assert "Hello, World!" in str(message)
    assert "bold magenta" in repr(message)


def test_create_greeting_message():
    """Test that personalized greeting is created correctly."""
    user_name = "Test User"
    message = create_greeting_message(user_name)
    assert "Test User" in str(message)
    assert "Nice to meet you" in str(message)
    assert "bold cyan on black" in repr(message)


def test_create_greeting_message_empty():
    """Test that greeting is created correctly with empty name."""
    user_name = ""
    message = create_greeting_message(user_name)
    assert "Nice to meet you, !" in str(message)  # Ensure formatting is correct even with empty name


def test_create_greeting_message_special_characters():
    """Test that greeting is created correctly with special characters in name."""
    user_name = "Test@User#123"
    message = create_greeting_message(user_name)
    assert "Test@User#123" in str(message)
    assert "Nice to meet you, Test@User#123!" in str(message)


def test_display_message():
    """Test that message is displayed using rich console."""
    mock_console = MagicMock()
    original_console = console
    # Temporarily replace the console with our mock
    import main
    main.console = mock_console
    
    try:
        test_message = "Test message"
        display_message(test_message)
        mock_console.print.assert_called_once_with(test_message)
    finally:
        # Restore original console
        main.console = original_console


def test_main_function_integration():
    """Test that main function runs without errors and calls expected functions."""
    # Mock input to provide a name to the input() function
    with patch('builtins.input', return_value='Test User') as mock_input:
        # Mock the console to avoid actual display
        with patch('main.console') as mock_console:
            main()
            
            # Verify input was called
            mock_input.assert_called_once_with("What's your name? ")
            
            # Verify console print was called twice (hello message and greeting)
            assert mock_console.print.call_count == 2
            
            # Get the calls to print
            calls = mock_console.print.call_args_list
            
            # First call should contain the hello message
            first_call_arg = str(calls[0][0][0])  # Convert Rich Text to string
            assert "Hello, World!" in first_call_arg
            
            # Second call should contain the greeting
            second_call_arg = str(calls[1][0][0])  # Convert Rich Text to string
            assert "Test User" in second_call_arg
            assert "Nice to meet you" in second_call_arg


def test_main_with_different_names():
    """Test main function with different name inputs."""
    test_cases = [
        "Alice",           # Normal name
        "",                # Empty name
        "O'Connor",        # Name with apostrophe
        "Maria-Jose",      # Name with hyphen
        "李明",              # Unicode name
    ]
    
    for test_name in test_cases:
        with patch('builtins.input', return_value=test_name):
            with patch('main.console'):
                main()
                # If we get here without exception, the test passed for this case


def test_get_user_name():
    """Test that get_user_name function properly calls input."""
    with patch('builtins.input', return_value='Test User') as mock_input:
        result = get_user_name()
        mock_input.assert_called_once_with("What's your name? ")
        assert result == 'Test User'