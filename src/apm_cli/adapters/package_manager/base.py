"""Base adapter interface for MCP package managers."""

from abc import ABC, abstractmethod


class MCPPackageManagerAdapter(ABC):
    """Base adapter for MCP package managers."""
    
    @abstractmethod
    def install(self, package_name, version=None):
        """Install an MCP package."""
        pass
    
    @abstractmethod
    def uninstall(self, package_name):
        """Uninstall an MCP package."""
        pass
    
    @abstractmethod
    def list_installed(self):
        """List all installed MCP packages."""
        pass
    
    @abstractmethod
    def search(self, query):
        """Search for MCP packages."""
        pass
