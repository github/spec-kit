from rich.console import Console
from rich.text import Text

console = Console()

def create_hello_message():
    """Create the colorful hello world message."""
    return Text("Hello, World!", style="bold magenta")

def get_user_name():
    """Get user's name via input."""
    return input("What's your name? ")

def create_greeting_message(user_name):
    """Create personalized greeting using rich."""
    return Text(f"Nice to meet you, {user_name}!", style="bold cyan on black")

def display_message(message):
    """Display the message using rich console."""
    console.print(message)

def main():
    # Create and display the colorful hello world message
    hello_text = create_hello_message()
    display_message(hello_text)
    
    # Get user's name
    user_name = get_user_name()
    
    # Create and display personalized greeting using rich
    greeting = create_greeting_message(user_name)
    display_message(greeting)


if __name__ == "__main__":
    main()
