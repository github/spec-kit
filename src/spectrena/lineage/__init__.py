#!/usr/bin/env python3
"""Lineage tracking module."""

from pathlib import Path

# Re-export for convenience
from spectrena.lineage.db import LineageDB, create_mcp_server

__all__ = ["LineageDB", "create_mcp_server", "init_lineage_db"]


async def init_lineage_db():
    """Initialize lineage database with schema."""
    from spectrena.config import Config

    config = Config.load()
    if not config.spectrena.enabled:
        return

    db = LineageDB(Path(config.spectrena.lineage_db))
    schema_path = Path(__file__).parent / "schema.surql"
    await db.init_schema(schema_path)
