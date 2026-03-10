"""
Vector memory integration for SpecKit Global Memory.

Provides:
- Ollama embeddings client
- agent-memory-mcp client wrapper
- Four-level memory system
- RAG indexer for automatic indexing
- Content templates for structured storage
- Unified search API

Usage:
    from specify_cli.memory.vector import (
        OllamaClient,
        AgentMemoryClient,
        FourLevelMemory,
        RAGIndexer,
        MemoryContentTemplate,
        VectorSearchAPI
    )
"""

from .ollama_client import OllamaClient
from .agent_memory_client import AgentMemoryClient
from .memory_types import FourLevelMemory
from .rag_indexer import RAGIndexer
from .content_template import MemoryContentTemplate, StructuredMemory
from .vector_search import VectorSearchAPI

__all__ = [
    "OllamaClient",
    "AgentMemoryClient",
    "FourLevelMemory",
    "RAGIndexer",
    "MemoryContentTemplate",
    "StructuredMemory",
    "VectorSearchAPI"
]
