"""MCP server conflict detection and resolution."""

from typing import Dict, Any
from ..adapters.client.base import MCPClientAdapter


class MCPConflictDetector:
    """Handles detection and resolution of MCP server configuration conflicts."""
    
    def __init__(self, runtime_adapter: MCPClientAdapter):
        """Initialize the conflict detector.
        
        Args:
            runtime_adapter: The MCP client adapter for the target runtime.
        """
        self.adapter = runtime_adapter
    
    def check_server_exists(self, server_reference: str) -> bool:
        """Check if a server already exists in the configuration.
        
        Args:
            server_reference: Server reference to check (e.g., 'github', 'io.github.github/github-mcp-server').
            
        Returns:
            True if server already exists, False otherwise.
        """
        existing_servers = self.get_existing_server_configs()
        
        # Try to get server info from registry for UUID comparison
        try:
            server_info = self.adapter.registry_client.find_server_by_reference(server_reference)
            if server_info and "id" in server_info:
                server_uuid = server_info["id"]
                
                # Check if any existing server has the same UUID
                for existing_name, existing_config in existing_servers.items():
                    if isinstance(existing_config, dict) and existing_config.get("id") == server_uuid:
                        return True
        except Exception:
            # If registry lookup fails, fall back to canonical name comparison
            canonical_name = self.get_canonical_server_name(server_reference)
            
            # Check for exact canonical name match
            if canonical_name in existing_servers:
                return True
                
            # Check if any existing server resolves to the same canonical name
            for existing_name in existing_servers.keys():
                if existing_name != canonical_name:  # Avoid duplicate checking
                    try:
                        existing_canonical = self.get_canonical_server_name(existing_name)
                        if existing_canonical == canonical_name:
                            return True
                    except Exception:
                        # If we can't resolve an existing server name, skip it
                        continue
                
        return False
    
    def get_canonical_server_name(self, server_ref: str) -> str:
        """Get canonical server name from MCP Registry.
        
        Args:
            server_ref: Server reference to resolve.
            
        Returns:
            Canonical server name if found in registry, otherwise the original reference.
        """
        try:
            # Use existing registry client that's already initialized in adapters
            server_info = self.adapter.registry_client.find_server_by_reference(server_ref)
            
            if server_info:
                # Use the server name from x-github.name field, or fallback to server.name
                if "x-github" in server_info and "name" in server_info["x-github"]:
                    return server_info["x-github"]["name"]
                elif "name" in server_info:
                    return server_info["name"]
        except Exception:
            # Graceful fallback on registry failure
            pass
        
        # Fallback: return the reference as-is if not found in registry
        return server_ref
    
    def get_existing_server_configs(self) -> Dict[str, Any]:
        """Extract all existing server configurations.
        
        Returns:
            Dictionary of existing server configurations keyed by server name.
        """
        # Get fresh config each time
        existing_config = self.adapter.get_current_config()
        
        # Determine runtime type from adapter class name or type
        adapter_class_name = getattr(self.adapter, '__class__', type(self.adapter)).__name__.lower()
        
        if "copilot" in adapter_class_name:
            return existing_config.get("mcpServers", {})
        elif "codex" in adapter_class_name:
            # Extract mcp_servers section from TOML config, handling both nested and flat formats
            servers = {}
            
            # Direct mcp_servers section
            if "mcp_servers" in existing_config:
                servers.update(existing_config["mcp_servers"])
            
            # Handle TOML-style nested keys like 'mcp_servers.github' and 'mcp_servers."quoted-name"'
            for key, value in existing_config.items():
                if key.startswith("mcp_servers."):
                    # Extract server name from key
                    server_name = key[len("mcp_servers."):]
                    # Remove quotes if present
                    if server_name.startswith('"') and server_name.endswith('"'):
                        server_name = server_name[1:-1]
                    
                    # Only add if it looks like server config (has command or args)
                    if isinstance(value, dict) and ('command' in value or 'args' in value):
                        servers[server_name] = value
            
            return servers
        elif "vscode" in adapter_class_name:
            return existing_config.get("servers", {})
        
        return {}
    
    def get_conflict_summary(self, server_reference: str) -> Dict[str, Any]:
        """Get detailed information about a conflict.
        
        Args:
            server_reference: Server reference to analyze.
            
        Returns:
            Dictionary with conflict details.
        """
        canonical_name = self.get_canonical_server_name(server_reference)
        existing_servers = self.get_existing_server_configs()
        
        conflict_info = {
            "exists": False,
            "canonical_name": canonical_name,
            "conflicting_servers": []
        }
        
        # Check for exact canonical name match
        if canonical_name in existing_servers:
            conflict_info["exists"] = True
            conflict_info["conflicting_servers"].append({
                "name": canonical_name,
                "type": "exact_match"
            })
        
        # Check if any existing server resolves to the same canonical name
        for existing_name in existing_servers.keys():
            if existing_name != canonical_name:  # Avoid duplicate reporting
                existing_canonical = self.get_canonical_server_name(existing_name)
                if existing_canonical == canonical_name:
                    conflict_info["exists"] = True
                    conflict_info["conflicting_servers"].append({
                        "name": existing_name,
                        "type": "canonical_match",
                        "resolves_to": existing_canonical
                    })
        
        return conflict_info