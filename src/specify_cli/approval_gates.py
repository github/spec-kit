"""Approval Gates Configuration Handler

Loads and validates .speckit/approval-gates.yaml from user projects.
"""

from pathlib import Path
from typing import Optional, Dict
import yaml


class ApprovalGatesConfig:
    """Load and validate approval gates from .speckit/approval-gates.yaml"""

    CONFIG_FILE = Path(".speckit/approval-gates.yaml")

    @classmethod
    def load(cls) -> Optional['ApprovalGatesConfig']:
        """Load approval gates config if it exists in user's project

        Returns None if no approval gates configured.
        """
        if not cls.CONFIG_FILE.exists():
            return None  # No approval gates configured - this is OK

        with open(cls.CONFIG_FILE) as f:
            data = yaml.safe_load(f)

        if data is None:
            return None

        return cls(data)

    def __init__(self, config: Dict):
        self.gates = config.get("approval_gates", {})

    def is_phase_gated(self, phase: str) -> bool:
        """Check if a phase requires approval"""
        gate = self.gates.get(phase, {})
        return gate.get("enabled", False)

    def get_phase_gate(self, phase: str) -> Optional[Dict]:
        """Get gate configuration for a specific phase"""
        if self.is_phase_gated(phase):
            return self.gates.get(phase)
        return None