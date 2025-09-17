"""Integration module for connecting registry client with package manager."""

import requests
from typing import Dict, List, Any, Optional
from .client import SimpleRegistryClient


class RegistryIntegration:
    """Integration class for connecting registry discovery to package manager."""

    def __init__(self, registry_url: Optional[str] = None):
        """Initialize the registry integration.

        Args:
            registry_url (str, optional): URL of the MCP registry.
                If not provided, uses the MCP_REGISTRY_URL environment variable
                or falls back to the default demo registry.
        """
        self.client = SimpleRegistryClient(registry_url)

    def list_available_packages(self) -> List[Dict[str, Any]]:
        """List all available packages in the registry.

        Returns:
            List[Dict[str, Any]]: List of package metadata dictionaries.
        """
        servers, _ = self.client.list_servers()
        # Transform server data to package format for backward compatibility
        return [self._server_to_package(server) for server in servers]

    def search_packages(self, query: str) -> List[Dict[str, Any]]:
        """Search for packages in the registry.

        Args:
            query (str): Search query string.

        Returns:
            List[Dict[str, Any]]: List of matching package metadata dictionaries.
        """
        servers = self.client.search_servers(query)
        # Transform server data to package format for backward compatibility
        return [self._server_to_package(server) for server in servers]

    def get_package_info(self, name: str) -> Dict[str, Any]:
        """Get detailed information about a specific package.

        Args:
            name (str): Name of the package.

        Returns:
            Dict[str, Any]: Package metadata dictionary.
            
        Raises:
            ValueError: If the package is not found.
        """
        # Use find_server_by_reference which handles all identifier formats:
        # - UUIDs (direct lookup)
        # - Full identifiers like "io.github.github/github-mcp-server"
        # - Registry names like "github/github-mcp-server"
        # - Simple names like "github-mcp-server"
        server_info = self.client.find_server_by_reference(name)
        if not server_info:
            raise ValueError(f"Package '{name}' not found in registry")
        return self._server_to_package_detail(server_info)

    def get_latest_version(self, name: str) -> str:
        """Get the latest version of a package.

        Args:
            name (str): Name of the package.

        Returns:
            str: Latest version string.

        Raises:
            ValueError: If the package has no versions.
        """
        package_info = self.get_package_info(name)
        
        # Check for version_detail in server format
        if "version_detail" in package_info:
            version_detail = package_info.get("version_detail", {})
            if version_detail and "version" in version_detail:
                return version_detail["version"]
        
        # Check packages list for version information
        packages = package_info.get("packages", [])
        if packages:
            for pkg in packages:
                if "version" in pkg:
                    return pkg["version"]
        
        # Fall back to versions list (backward compatibility)
        versions = package_info.get("versions", [])
        if versions:
            return versions[-1].get("version", "latest")
            
        raise ValueError(f"Package '{name}' has no versions")
    
    def _server_to_package(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """Convert server data format to package format for compatibility.
        
        Args:
            server (Dict[str, Any]): Server data from registry.
            
        Returns:
            Dict[str, Any]: Package formatted data.
        """
        package = {
            "id": server.get("id", ""),
            "name": server.get("name", "Unknown"),
            "description": server.get("description", "No description available"),
        }
        
        # Add repository information if available
        if "repository" in server:
            package["repository"] = server["repository"]
            
        # Add version information if available
        if "version_detail" in server:
            package["version_detail"] = server["version_detail"]
            
        return package
    
    def _server_to_package_detail(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """Convert detailed server data to package detail format.
        
        Args:
            server (Dict[str, Any]): Server data from registry.
            
        Returns:
            Dict[str, Any]: Package detail formatted data.
        """
        # Start with the basic package data
        package_detail = self._server_to_package(server)
        
        # Add packages information
        if "packages" in server:
            package_detail["packages"] = server["packages"]
            
        # Add remotes information (crucial for deployment type detection)
        if "remotes" in server:
            package_detail["remotes"] = server["remotes"]
            
        if "package_canonical" in server:
            package_detail["package_canonical"] = server["package_canonical"]
            
        # For backward compatibility, create a versions list
        if "version_detail" in server and server["version_detail"]:
            version_info = server["version_detail"]
            package_detail["versions"] = [{
                "version": version_info.get("version", "latest"),
                "release_date": version_info.get("release_date", ""),
                "is_latest": version_info.get("is_latest", True)
            }]
        
        return package_detail