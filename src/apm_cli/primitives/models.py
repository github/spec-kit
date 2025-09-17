"""Data models for APM context."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Union, Dict


@dataclass
class Chatmode:
    """Represents a chatmode primitive."""
    name: str
    file_path: Path
    description: str
    apply_to: Optional[str]  # Glob pattern for file targeting (optional for chatmodes)
    content: str
    author: Optional[str] = None
    version: Optional[str] = None
    source: Optional[str] = None  # Source of primitive: "local" or "dependency:{package_name}"
    
    def validate(self) -> List[str]:
        """Validate chatmode structure.
        
        Returns:
            List[str]: List of validation errors.
        """
        errors = []
        if not self.description:
            errors.append("Missing 'description' in frontmatter")
        if not self.content.strip():
            errors.append("Empty content")
        return errors


@dataclass
class Instruction:
    """Represents an instruction primitive."""
    name: str
    file_path: Path
    description: str
    apply_to: str  # Glob pattern for file targeting (required for instructions)
    content: str
    author: Optional[str] = None
    version: Optional[str] = None
    source: Optional[str] = None  # Source of primitive: "local" or "dependency:{package_name}"
    
    def validate(self) -> List[str]:
        """Validate instruction structure.
        
        Returns:
            List[str]: List of validation errors.
        """
        errors = []
        if not self.description:
            errors.append("Missing 'description' in frontmatter")
        if not self.apply_to:
            errors.append("Missing 'applyTo' in frontmatter (required for instructions)")
        if not self.content.strip():
            errors.append("Empty content")
        return errors


@dataclass
class Context:
    """Represents a context primitive."""
    name: str
    file_path: Path
    content: str
    description: Optional[str] = None
    author: Optional[str] = None
    version: Optional[str] = None
    source: Optional[str] = None  # Source of primitive: "local" or "dependency:{package_name}"
    
    def validate(self) -> List[str]:
        """Validate context structure.
        
        Returns:
            List[str]: List of validation errors.
        """
        errors = []
        if not self.content.strip():
            errors.append("Empty content")
        return errors


# Union type for all primitive types
Primitive = Union[Chatmode, Instruction, Context]


@dataclass
class PrimitiveConflict:
    """Represents a conflict between primitives from different sources."""
    primitive_name: str
    primitive_type: str  # 'chatmode', 'instruction', 'context'
    winning_source: str  # Source that won the conflict
    losing_sources: List[str]  # Sources that lost the conflict
    file_path: Path  # Path of the winning primitive
    
    def __str__(self) -> str:
        """String representation of the conflict."""
        losing_list = ", ".join(self.losing_sources)
        return f"{self.primitive_type} '{self.primitive_name}': {self.winning_source} overrides {losing_list}"


@dataclass
class PrimitiveCollection:
    """Collection of discovered primitives."""
    chatmodes: List[Chatmode]
    instructions: List[Instruction]  
    contexts: List[Context]
    conflicts: List[PrimitiveConflict]  # Track conflicts during discovery
    
    def __init__(self):
        self.chatmodes = []
        self.instructions = []
        self.contexts = []
        self.conflicts = []
    
    def add_primitive(self, primitive: Primitive) -> None:
        """Add a primitive to the appropriate collection.
        
        If a primitive with the same name already exists, the new primitive
        will only be added if it has higher priority (lower priority primitives
        are tracked as conflicts).
        """
        if isinstance(primitive, Chatmode):
            self._add_with_conflict_detection(primitive, self.chatmodes, "chatmode")
        elif isinstance(primitive, Instruction):
            self._add_with_conflict_detection(primitive, self.instructions, "instruction")
        elif isinstance(primitive, Context):
            self._add_with_conflict_detection(primitive, self.contexts, "context")
        else:
            raise ValueError(f"Unknown primitive type: {type(primitive)}")
    
    def _add_with_conflict_detection(self, new_primitive: Primitive, collection: List[Primitive], primitive_type: str) -> None:
        """Add primitive with conflict detection."""
        # Find existing primitive with same name
        existing_index = None
        for i, existing in enumerate(collection):
            if existing.name == new_primitive.name:
                existing_index = i
                break
        
        if existing_index is None:
            # No conflict, just add the primitive
            collection.append(new_primitive)
        else:
            # Conflict detected - apply priority rules
            existing = collection[existing_index]
            
            # Priority rules:
            # 1. Local always wins over dependency
            # 2. Earlier dependency wins over later dependency
            should_replace = self._should_replace_primitive(existing, new_primitive)
            
            if should_replace:
                # Replace existing with new primitive and record conflict
                conflict = PrimitiveConflict(
                    primitive_name=new_primitive.name,
                    primitive_type=primitive_type,
                    winning_source=new_primitive.source or "unknown",
                    losing_sources=[existing.source or "unknown"],
                    file_path=new_primitive.file_path
                )
                self.conflicts.append(conflict)
                collection[existing_index] = new_primitive
            else:
                # Keep existing and record that new primitive was ignored
                conflict = PrimitiveConflict(
                    primitive_name=existing.name,
                    primitive_type=primitive_type,
                    winning_source=existing.source or "unknown", 
                    losing_sources=[new_primitive.source or "unknown"],
                    file_path=existing.file_path
                )
                self.conflicts.append(conflict)
                # Don't add new_primitive to collection
    
    def _should_replace_primitive(self, existing: Primitive, new: Primitive) -> bool:
        """Determine if new primitive should replace existing based on priority."""
        existing_source = existing.source or "unknown"
        new_source = new.source or "unknown"
        
        # Local always wins
        if existing_source == "local":
            return False  # Never replace local
        if new_source == "local":
            return True   # Always replace with local
        
        # Both are dependencies - this shouldn't happen in correct usage
        # since dependencies should be processed in order, but handle gracefully
        return False  # Keep first dependency (existing)
    
    def all_primitives(self) -> List[Primitive]:
        """Get all primitives as a single list."""
        return self.chatmodes + self.instructions + self.contexts
    
    def count(self) -> int:
        """Get total count of all primitives."""
        return len(self.chatmodes) + len(self.instructions) + len(self.contexts)
    
    def has_conflicts(self) -> bool:
        """Check if any conflicts were detected during discovery."""
        return len(self.conflicts) > 0
    
    def get_conflicts_by_type(self, primitive_type: str) -> List[PrimitiveConflict]:
        """Get conflicts for a specific primitive type."""
        return [c for c in self.conflicts if c.primitive_type == primitive_type]
    
    def get_primitives_by_source(self, source: str) -> List[Primitive]:
        """Get all primitives from a specific source."""
        all_primitives = self.all_primitives()
        return [p for p in all_primitives if p.source == source]