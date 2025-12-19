"""
Artifact storage implementations for spec-kit.

This module provides storage backends for persisting workflow artifacts:
- StorageBase: Abstract base class defining the storage interface
- FileStorage: File-based storage using Markdown files
"""

from speckit.storage.base import StorageBase
from speckit.storage.file_storage import FileStorage

__all__ = [
    "StorageBase",
    "FileStorage",
]
