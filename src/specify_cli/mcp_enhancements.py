import json
import shutil
from pathlib import Path
from dataclasses import asdict

from .domain_analysis import DomainAnalyzer
from .template_populator import TemplatePopulator
from .error_handling import get_error_handler


def ping() -> str:
    """Simple health‑check tool."""
    return "pong"


def check_prereqs() -> str:
    """Return a short report of common development tool availability."""
    tools = {
        "Git": shutil.which("git") is not None,
        "Python": shutil.which("python3") is not None,
        "Node.js": shutil.which("node") is not None,
        "Docker": shutil.which("docker") is not None,
        "VS Code": shutil.which("code") is not None,
    }
    lines = ["# Prerequisite Check"]
    for name, ok in tools.items():
        status = "✅ Available" if ok else "❌ Not Found"
        lines.append(f"- **{name}**: {status}")
    return "\n".join(lines)


def error_summary() -> str:
    """Return the current error handler summary as plain text."""
    handler = get_error_handler()
    if hasattr(handler, "get_summary"):
        return handler.get_summary()
    try:
        return handler.print_error_summary()
    except Exception:
        return "No error summary available."


def analyze_domain(data_directory: str) -> str:
    """Run `DomainAnalyzer` on the given directory and return a JSON representation of the model."""
    analyzer = DomainAnalyzer(data_directory)
    model = analyzer.analyze()
    def recursive_asdict(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return {k: recursive_asdict(v) for k, v in asdict(obj).items()}
        if isinstance(obj, list):
            return [recursive_asdict(i) for i in obj]
        return obj
    model_dict = recursive_asdict(model)
    return json.dumps(model_dict, indent=2)


def populate_template(spec_file: str, data_directory: str) -> str:
    """Analyze the domain and populate the given spec template.

    Returns a short success message.
    """
    analyzer = DomainAnalyzer(data_directory)
    model = analyzer.analyze()
    pop = TemplatePopulator(spec_file, model)
    pop.populate_specification()
    return f"Template `{spec_file}` populated from analysis of `{data_directory}`."
