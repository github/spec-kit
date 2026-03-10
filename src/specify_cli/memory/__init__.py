"""
Global Agent Memory Integration for SpecKit.

Provides multi-level memory system for AI agents:
- Level 1: Contextual (session-only)
- Level 2: File-based (markdown files)
- Level 3: Vector-based (agent-memory-mcp + Ollama)
- Level 4: Identity (AGENTS.md, SOUL.md, USER.md, MEMORY.md)
"""

from .config import MemoryConfigManager
from .logging import get_logger

__all__ = ['MemoryConfigManager', 'get_logger']
