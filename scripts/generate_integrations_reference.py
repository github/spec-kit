#!/usr/bin/env python3
"""Generate the integrations reference table from integrations/catalog.json."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from specify_cli.catalog_docs import (  # noqa: E402
    INTEGRATIONS_CATALOG_PATH,
    INTEGRATIONS_REFERENCE_PATH,
    render_integrations_reference,
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Rewrite docs/reference/integrations.md in place",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if the generated file would differ from the committed file",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=INTEGRATIONS_CATALOG_PATH,
        help="Path to integrations/catalog.json",
    )
    parser.add_argument(
        "--doc",
        type=Path,
        default=INTEGRATIONS_REFERENCE_PATH,
        help="Path to docs/reference/integrations.md",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    generated = render_integrations_reference(args.catalog, args.doc)

    if args.check:
        current = args.doc.read_text(encoding="utf-8")
        if current != generated:
            return 1
        return 0

    if args.write:
        args.doc.write_text(generated, encoding="utf-8")
        return 0

    sys.stdout.write(generated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
