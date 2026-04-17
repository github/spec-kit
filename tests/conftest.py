"""Ensure tests import from the fork's src/ directory, not the installed package."""
import sys
from pathlib import Path

# Insert the fork's src/ at the front so `import specify_cli` resolves here
src_dir = str(Path(__file__).parent.parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
