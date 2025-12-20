"""
Pytest configuration for spec-kit testcontainer validation.

Configures markers and shared fixtures.
"""

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: Integration tests using testcontainers (slow)"
    )
    config.addinivalue_line(
        "markers",
        "requires_docker: Tests that require Docker to be running"
    )
