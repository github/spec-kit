from rich.console import Console
from rich.panel import Panel
from rich.text import Text

def colorful_hello():
    """Prints a colorful 'Hello, World!' message."""
    console = Console()
    text = Text("Hello, World!", style="bold magenta")
    panel = Panel(text, expand=False)
    console.print(panel)

def main():
    """Gets user's name and prints a personalized greeting."""
    console = Console()
    colorful_hello()
    name = console.input("[bold green]What's your name? [/bold green]")
    greeting = Text(f"Hello, {name}!", style="bold blue")
    console.print(greeting)

if __name__ == "__main__":
    main()