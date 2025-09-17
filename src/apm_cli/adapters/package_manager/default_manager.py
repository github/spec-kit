"""Implementation of the default MCP package manager."""

from .base import MCPPackageManagerAdapter
from ...config import get_default_client
from ...registry.integration import RegistryIntegration


class DefaultMCPPackageManager(MCPPackageManagerAdapter):
    """Implementation of the default MCP package manager."""
    
    def install(self, package_name, version=None):
        """Install an MCP package.
        
        Args:
            package_name (str): Name of the package to install.
            version (str, optional): Version of the package to install.
        
        Returns:
            bool: True if successful, False otherwise.
        """

        try:
            # Import here to avoid circular import
            from ...factory import ClientFactory
            
            client_type = get_default_client()
            client_adapter = ClientFactory.create_client(client_type)
            
            # For VSCode, configure MCP server in mcp.json
            result = client_adapter.configure_mcp_server(package_name, package_name, True)
            
            if result:
                print(f"Successfully installed {package_name}")
            return result
        except Exception as e:
            print(f"Error installing package {package_name}: {e}")
            return False
    
    def uninstall(self, package_name):
        """Uninstall an MCP package.
        
        Args:
            package_name (str): Name of the package to uninstall.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        
        try:
            # Import here to avoid circular import
            from ...factory import ClientFactory
            
            client_type = get_default_client()
            client_adapter = ClientFactory.create_client(client_type)
            config = client_adapter.get_current_config()
            
            # For VSCode, remove the server from mcp.json
            if "servers" in config and package_name in config["servers"]:
                servers = config["servers"]
                servers.pop(package_name, None)
                result = client_adapter.update_config({"servers": servers})
                
                if result:
                    print(f"Successfully uninstalled {package_name}")
                return result
            else:
                print(f"Package {package_name} not found in configuration")
                return False
                
        except Exception as e:
            print(f"Error uninstalling package {package_name}: {e}")
            return False
    
    def list_installed(self):
        """List all installed MCP packages.
        
        Returns:
            list: List of installed packages.
        """
        
        try:
            # Import here to avoid circular import
            from ...factory import ClientFactory
            
            # Get client type from configuration (default is vscode)
            client_type = get_default_client()
            
            # Create client adapter
            client_adapter = ClientFactory.create_client(client_type)
            
            # Get config from local .vscode/mcp.json file
            config = client_adapter.get_current_config()
            
            # Extract server names from the config
            servers = config.get("servers", {})
            
            # Return the list of server names
            return list(servers.keys())
        except Exception as e:
            print(f"Error retrieving installed MCP servers: {e}")
            return []
    
    def search(self, query):
        """Search for MCP packages.
        
        Args:
            query (str): Search query.
        
        Returns:
            list: List of packages matching the query.
        """
        
        try:
            # Use the registry integration to search for packages
            registry = RegistryIntegration()
            packages = registry.search_packages(query)
            
            # Return the list of package IDs/names
            return [pkg.get("id", pkg.get("name", "Unknown")) for pkg in packages] if packages else []
            
        except Exception as e:
            print(f"Error searching for packages: {e}")
            return []
