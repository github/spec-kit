"""YAML utilities leveraging C-based extensions for better performance."""

import yaml
from typing import Any, IO

try:
    from yaml import CSafeLoader as SafeLoader
    from yaml import CSafeDumper as SafeDumper
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import SafeLoader
    from yaml import SafeDumper
    from yaml import Dumper

def yaml_safe_load(stream: str | bytes | IO[str] | IO[bytes]) -> Any:
    """Safely load YAML data using the fastest available loader."""
    return yaml.load(stream, Loader=SafeLoader)

def yaml_safe_dump(data: Any, stream: IO[Any] | None = None, **kwargs: Any) -> str | Any:
    """Safely dump YAML data using the fastest available dumper."""
    return yaml.dump(data, stream, Dumper=SafeDumper, **kwargs)

def yaml_dump(data: Any, stream: IO[Any] | None = None, **kwargs: Any) -> str | Any:
    """Dump YAML data using the fastest available dumper."""
    return yaml.dump(data, stream, Dumper=Dumper, **kwargs)
