"""
Module entry point so the package can be executed with:

    python -m src.specify_cli ...

This simply delegates to specify_cli.main defined in __init__.py.
"""

from . import main


if __name__ == "__main__":
    main()
