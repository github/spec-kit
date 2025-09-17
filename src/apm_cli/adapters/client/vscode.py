"""VSCode implementation of MCP client adapter.

This adapter implements the VSCode-specific handling of MCP server configuration,
following the official documentation at:
https://code.visualstudio.com/docs/copilot/chat/mcp-servers
"""

import json
import os
from pathlib import Path
from .base import MCPClientAdapter
from ...registry.client import SimpleRegistryClient
from ...registry.integration import RegistryIntegration


class VSCodeClientAdapter(MCPClientAdapter):
    """VSCode implementation of MCP client adapter.
    
    This adapter handles VSCode-specific configuration for MCP servers using
    a repository-level .vscode/mcp.json file, following the format specified
    in the VSCode documentation.
    """
    
    def __init__(self, registry_url=None):
        """Initialize the VSCode client adapter.
        
        Args:
            registry_url (str, optional): URL of the MCP registry.
                If not provided, uses the MCP_REGISTRY_URL environment variable
                or falls back to the default demo registry.
        """
        self.registry_client = SimpleRegistryClient(registry_url)
        self.registry_integration = RegistryIntegration(registry_url)
    
    def get_config_path(self):
        """Get the path to the VSCode MCP configuration file in the repository.
        
        Returns:
            str: Path to the .vscode/mcp.json file.
        """
        # Use the current working directory as the repository root
        repo_root = Path(os.getcwd())
        
        # Path to .vscode/mcp.json in the repository
        vscode_dir = repo_root / ".vscode"
        mcp_config_path = vscode_dir / "mcp.json"
        
        # Create the .vscode directory if it doesn't exist
        try:
            if not vscode_dir.exists():
                vscode_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create .vscode directory: {e}")
            
        return str(mcp_config_path)
    
    def update_config(self, new_config):
        """Update the VSCode MCP configuration with new values.
        
        Args:
            new_config (dict): Complete configuration object to write.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        config_path = self.get_config_path()
        
        try:
            # Write the updated config
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(new_config, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error updating VSCode MCP configuration: {e}")
            return False
    
    def get_current_config(self):
        """Get the current VSCode MCP configuration.
        
        Returns:
            dict: Current VSCode MCP configuration from the local .vscode/mcp.json file.
        """
        config_path = self.get_config_path()
        
        try:
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return {}
        except Exception as e:
            print(f"Error reading VSCode MCP configuration: {e}")
            return {}
    
    def configure_mcp_server(self, server_url, server_name=None, enabled=True, env_overrides=None, server_info_cache=None, runtime_vars=None):
        """Configure an MCP server in VS Code mcp.json file.
        
        This method updates the .vscode/mcp.json file to add or update
        an MCP server configuration.
        
        Args:
            server_url (str): URL or identifier of the MCP server.
            server_name (str, optional): Name of the server. Defaults to None.
            enabled (bool, optional): Whether to enable the server. Defaults to True.
            env_overrides (dict, optional): Environment variable overrides. Defaults to None.
            server_info_cache (dict, optional): Pre-fetched server info to avoid duplicate registry calls.
            
        Returns:
            bool: True if successful, False otherwise.
            
        Raises:
            ValueError: If server is not found in registry.
        """
        if not server_url:
            print("Error: server_url cannot be empty")
            return False
            
        try:
            # Use cached server info if available, otherwise fetch from registry
            if server_info_cache and server_url in server_info_cache:
                server_info = server_info_cache[server_url]
            else:
                # Fallback to registry lookup if not cached
                server_info = self.registry_client.find_server_by_reference(server_url)
            
            # Fail if server is not found in registry - security requirement
            # This raises ValueError as expected by tests
            if not server_info:
                raise ValueError(f"Failed to retrieve server details for '{server_url}'. Server not found in registry.")
            
            # Generate server configuration
            server_config, input_vars = self._format_server_config(server_info)
            
            if not server_config:
                print(f"Unable to configure server: {server_url}")
                return False
            
            # Use provided server name or fallback to server_url
            config_key = server_name or server_url
            
            # Get current config
            current_config = self.get_current_config()
            
            # Ensure servers and inputs sections exist
            if "servers" not in current_config:
                current_config["servers"] = {}
            if "inputs" not in current_config:
                current_config["inputs"] = []
            
            # Add the server configuration
            current_config["servers"][config_key] = server_config
            
            # Add input variables (avoiding duplicates)
            existing_input_ids = {var.get("id") for var in current_config["inputs"] if isinstance(var, dict)}
            for var in input_vars:
                if var.get("id") not in existing_input_ids:
                    current_config["inputs"].append(var)
                    existing_input_ids.add(var.get("id"))
            
            # Update the configuration
            result = self.update_config(current_config)
            
            if result:
                print(f"Successfully configured MCP server '{config_key}' for VS Code")
            return result
            
        except ValueError:
            # Re-raise ValueError for registry errors
            raise
        except Exception as e:
            print(f"Error configuring MCP server: {e}")
            return False

    def _format_server_config(self, server_info):
        """Format server details into VSCode mcp.json compatible format.
        
        Args:
            server_info (dict): Server information from registry.
            
        Returns:
            tuple: (server_config, input_vars) where:
                - server_config is the formatted server configuration for mcp.json
                - input_vars is a list of input variable definitions
        """
        # Initialize the base config structure
        server_config = {}
        input_vars = []
        
        # Check for packages information
        if "packages" in server_info and server_info["packages"]:
            package = server_info["packages"][0]
            runtime_hint = package.get("runtime_hint", "")
            
            # Handle npm packages
            if runtime_hint == "npx" or "npm" in package.get("registry_name", "").lower():
                # Get args directly from runtime_arguments
                args = []
                if "runtime_arguments" in package and package["runtime_arguments"]:
                    for arg in package["runtime_arguments"]:
                        if arg.get("is_required", False) and arg.get("value_hint"):
                            args.append(arg.get("value_hint"))
                
                # Fallback if no runtime_arguments are provided
                if not args and package.get("name"):
                    args = [package.get("name")]
                
                server_config = {
                    "type": "stdio",
                    "command": "npx",
                    "args": args
                }
            
            # Handle docker packages
            elif runtime_hint == "docker":
                # Get args directly from runtime_arguments
                args = []
                if "runtime_arguments" in package and package["runtime_arguments"]:
                    for arg in package["runtime_arguments"]:
                        if arg.get("is_required", False) and arg.get("value_hint"):
                            args.append(arg.get("value_hint"))
                
                # Fallback if no runtime_arguments are provided - use standard docker run command
                if not args:
                    args = ["run", "-i", "--rm", package.get("name")]
                
                server_config = {
                    "type": "stdio",
                    "command": "docker",
                    "args": args
                }
            
            # Handle Python packages
            elif runtime_hint in ["uvx", "pip", "python"] or "python" in runtime_hint or package.get("registry_name", "").lower() == "pypi":
                # Determine the command based on runtime_hint
                if runtime_hint == "uvx":
                    command = "uvx"
                elif "python" in runtime_hint:
                    # Use the specified Python path if it's a full path, otherwise default to python3
                    command = "python3" if runtime_hint in ["python", "pip"] else runtime_hint
                else:
                    command = "python3"
                
                # Get args directly from runtime_arguments
                args = []
                if "runtime_arguments" in package and package["runtime_arguments"]:
                    for arg in package["runtime_arguments"]:
                        if arg.get("is_required", False) and arg.get("value_hint"):
                            args.append(arg.get("value_hint"))
                
                # Fallback if no runtime_arguments are provided
                if not args:
                    if runtime_hint == "uvx":
                        module_name = package.get("name", "").replace("mcp-server-", "")
                        args = [f"mcp-server-{module_name}"]
                    else:
                        module_name = package.get("name", "").replace("mcp-server-", "").replace("-", "_")
                        args = ["-m", f"mcp_server_{module_name}"]
                
                server_config = {
                    "type": "stdio",
                    "command": command,
                    "args": args
                }
            
            # Add environment variables if present
            if "environment_variables" in package and package["environment_variables"]:
                server_config["env"] = {}
                for env_var in package["environment_variables"]:
                    if "name" in env_var:
                        # Convert variable name to lowercase and replace underscores with hyphens for VS Code convention
                        input_var_name = env_var["name"].lower().replace("_", "-")
                        
                        # Create the input variable reference
                        server_config["env"][env_var["name"]] = f"${{input:{input_var_name}}}"
                        
                        # Create the input variable definition
                        input_var_def = {
                            "type": "promptString",
                            "id": input_var_name,
                            "description": env_var.get("description", f"{env_var['name']} for MCP server"),
                            "password": True  # Default to True for security
                        }
                        input_vars.append(input_var_def)
            
        # If no server config was created from packages, check for other server types
        if not server_config:
            # Check for SSE endpoints
            if "sse_endpoint" in server_info:
                server_config = {
                    "type": "sse",
                    "url": server_info["sse_endpoint"],
                    "headers": server_info.get("sse_headers", {})
                }
            # Check for remotes (similar to Copilot adapter)
            elif "remotes" in server_info and server_info["remotes"]:
                remotes = server_info["remotes"]
                remote = remotes[0]  # Take the first remote
                if remote.get("transport_type") == "sse":
                    server_config = {
                        "type": "sse",
                        "url": remote.get("url", ""),
                        "headers": remote.get("headers", {})
                    }
            # If no packages AND no endpoints/remotes, fail with clear error
            else:
                raise ValueError(f"MCP server has incomplete configuration in registry - no package information or remote endpoints available. "
                               f"This appears to be a temporary registry issue. "
                               f"Server: {server_info.get('name', 'unknown')}")
        
        return server_config, input_vars
