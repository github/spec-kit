"""Factory classes for creating adapters."""

from .adapters.client.vscode import VSCodeClientAdapter
from .adapters.client.codex import CodexClientAdapter
from .adapters.package_manager.default_manager import DefaultMCPPackageManager


class ClientFactory:
    """Factory for creating MCP client adapters."""
    
    @staticmethod
    def create_client(client_type):
        """Create a client adapter based on the specified type.
        
        Args:
            client_type (str): Type of client adapter to create.
        
        Returns:
            MCPClientAdapter: An instance of the specified client adapter.
        
        Raises:
            ValueError: If the client type is not supported.
        """
        clients = {
            "vscode": VSCodeClientAdapter,
            "codex": CodexClientAdapter,
            # Add more clients as needed
        }
        
        if client_type.lower() not in clients:
            raise ValueError(f"Unsupported client type: {client_type}")
            
        return clients[client_type.lower()]()


class PackageManagerFactory:
    """Factory for creating MCP package manager adapters."""
    
    @staticmethod
    def create_package_manager(manager_type="default"):
        """Create a package manager adapter based on the specified type.
        
        Args:
            manager_type (str, optional): Type of package manager adapter to create.
                Defaults to "default".
        
        Returns:
            MCPPackageManagerAdapter: An instance of the specified package manager adapter.
        
        Raises:
            ValueError: If the package manager type is not supported.
        """
        managers = {
            "default": DefaultMCPPackageManager,
            # Add more package managers as they emerge
        }
        
        if manager_type.lower() not in managers:
            raise ValueError(f"Unsupported package manager type: {manager_type}")
            
        return managers[manager_type.lower()]()
