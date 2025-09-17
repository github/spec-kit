"""MCP server operations and installation logic."""

import os
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path

from .client import SimpleRegistryClient


class MCPServerOperations:
    """Handles MCP server operations like conflict detection and installation status."""
    
    def __init__(self, registry_url: Optional[str] = None):
        """Initialize MCP server operations.
        
        Args:
            registry_url: Optional registry URL override
        """
        self.registry_client = SimpleRegistryClient(registry_url)
    
    def check_servers_needing_installation(self, target_runtimes: List[str], server_references: List[str]) -> List[str]:
        """Check which MCP servers actually need installation across target runtimes.
        
        This method checks the actual MCP configuration files to see which servers
        are already installed by comparing server IDs (UUIDs), not names.
        
        Args:
            target_runtimes: List of target runtimes to check
            server_references: List of MCP server references (names or IDs)
            
        Returns:
            List of server references that need installation in at least one runtime
        """
        servers_needing_installation = set()
        
        # Check each server reference
        for server_ref in server_references:
            try:
                # Get server info from registry to find the canonical ID
                server_info = self.registry_client.find_server_by_reference(server_ref)
                
                if not server_info:
                    # Server not found in registry, might be a local/custom server
                    # Add to installation list for safety
                    servers_needing_installation.add(server_ref)
                    continue
                
                server_id = server_info.get("id")
                if not server_id:
                    # No ID available, add to installation list
                    servers_needing_installation.add(server_ref)
                    continue
                
                # Check if this server needs installation in ANY of the target runtimes
                needs_installation = False
                for runtime in target_runtimes:
                    runtime_installed_ids = self._get_installed_server_ids([runtime])
                    if server_id not in runtime_installed_ids:
                        needs_installation = True
                        break
                
                if needs_installation:
                    servers_needing_installation.add(server_ref)
                    
            except Exception as e:
                # If we can't check the server, assume it needs installation
                servers_needing_installation.add(server_ref)
        
        return list(servers_needing_installation)
    
    def _get_installed_server_ids(self, target_runtimes: List[str]) -> Set[str]:
        """Get all installed server IDs across target runtimes.
        
        Args:
            target_runtimes: List of runtimes to check
            
        Returns:
            Set of server IDs that are currently installed
        """
        installed_ids = set()
        
        # Import here to avoid circular imports
        try:
            from ..factory import ClientFactory
        except ImportError:
            return installed_ids
        
        for runtime in target_runtimes:
            try:
                client = ClientFactory.create_client(runtime)
                config = client.get_current_config()
                
                if isinstance(config, dict):
                    if runtime == 'copilot':
                        # Copilot stores servers in mcpServers object in mcp-config.json
                        mcp_servers = config.get("mcpServers", {})
                        for server_name, server_config in mcp_servers.items():
                            if isinstance(server_config, dict):
                                server_id = server_config.get("id")
                                if server_id:
                                    installed_ids.add(server_id)
                                    
                    elif runtime == 'codex':
                        # Codex stores servers as mcp_servers.{name} sections in config.toml
                        mcp_servers = config.get("mcp_servers", {})
                        for server_name, server_config in mcp_servers.items():
                            if isinstance(server_config, dict):
                                server_id = server_config.get("id")
                                if server_id:
                                    installed_ids.add(server_id)
                                    
                    elif runtime == 'vscode':
                        # VS Code stores servers in settings.json with different structure
                        # Check both mcpServers and any nested structure
                        mcp_servers = config.get("mcpServers", {})
                        for server_name, server_config in mcp_servers.items():
                            if isinstance(server_config, dict):
                                server_id = (
                                    server_config.get("id") or
                                    server_config.get("serverId") or
                                    server_config.get("server_id")
                                )
                                if server_id:
                                    installed_ids.add(server_id)
                            
            except Exception:
                # If we can't read a runtime's config, skip it
                continue
        
        return installed_ids
    
    def validate_servers_exist(self, server_references: List[str]) -> Tuple[List[str], List[str]]:
        """Validate that all servers exist in the registry before attempting installation.
        
        This implements fail-fast validation similar to npm's behavior.
        
        Args:
            server_references: List of MCP server references to validate
            
        Returns:
            Tuple of (valid_servers, invalid_servers)
        """
        valid_servers = []
        invalid_servers = []
        
        for server_ref in server_references:
            try:
                server_info = self.registry_client.find_server_by_reference(server_ref)
                if server_info:
                    valid_servers.append(server_ref)
                else:
                    invalid_servers.append(server_ref)
            except Exception:
                invalid_servers.append(server_ref)
                
        return valid_servers, invalid_servers
    
    def batch_fetch_server_info(self, server_references: List[str]) -> Dict[str, Optional[Dict]]:
        """Batch fetch server info for all servers to avoid duplicate registry calls.
        
        Args:
            server_references: List of MCP server references
            
        Returns:
            Dictionary mapping server reference to server info (or None if not found)
        """
        server_info_cache = {}
        
        for server_ref in server_references:
            try:
                server_info = self.registry_client.find_server_by_reference(server_ref)
                server_info_cache[server_ref] = server_info
            except Exception:
                server_info_cache[server_ref] = None
                
        return server_info_cache
    
    def collect_runtime_variables(self, server_references: List[str], server_info_cache: Dict[str, Optional[Dict]] = None) -> Dict[str, str]:
        """Collect runtime variables from runtime_arguments.variables fields.
        
        These are NOT environment variables but CLI argument placeholders that need
        to be substituted directly into the command arguments (e.g., {ado_org}).
        
        Args:
            server_references: List of MCP server references
            server_info_cache: Pre-fetched server info to avoid duplicate registry calls
            
        Returns:
            Dictionary mapping runtime variable names to their values
        """
        all_required_vars = {}  # var_name -> {description, required, etc.}
        
        # Use cached server info if available, otherwise fetch on-demand
        if server_info_cache is None:
            server_info_cache = self.batch_fetch_server_info(server_references)
        
        # Collect all unique runtime variables from runtime_arguments
        for server_ref in server_references:
            try:
                server_info = server_info_cache.get(server_ref)
                if not server_info:
                    continue
                
                # Extract runtime variables from runtime_arguments
                packages = server_info.get("packages", [])
                for package in packages:
                    if isinstance(package, dict):
                        runtime_arguments = package.get("runtime_arguments", [])
                        for arg in runtime_arguments:
                            if isinstance(arg, dict) and "variables" in arg:
                                variables = arg.get("variables", {})
                                for var_name, var_info in variables.items():
                                    if isinstance(var_info, dict):
                                        all_required_vars[var_name] = {
                                            "description": var_info.get("description", ""),
                                            "required": var_info.get("is_required", True)
                                        }
                            
            except Exception:
                # Skip servers we can't analyze
                continue
        
        # Prompt user for each runtime variable
        if all_required_vars:
            return self._prompt_for_environment_variables(all_required_vars)
        
        return {}
    
    def collect_environment_variables(self, server_references: List[str], server_info_cache: Dict[str, Optional[Dict]] = None) -> Dict[str, str]:
        """Collect environment variables needed by the specified servers.
        
        Args:
            server_references: List of MCP server references
            server_info_cache: Pre-fetched server info to avoid duplicate registry calls
            
        Returns:
            Dictionary mapping environment variable names to their values
        """
        shared_env_vars = {}
        all_required_vars = {}  # var_name -> {description, required, etc.}
        
        # Use cached server info if available, otherwise fetch on-demand
        if server_info_cache is None:
            server_info_cache = self.batch_fetch_server_info(server_references)
        
        # Collect all unique environment variables needed
        for server_ref in server_references:
            try:
                server_info = server_info_cache.get(server_ref)
                if not server_info:
                    continue
                
                # Extract environment variables from Docker args (legacy support)
                if "docker" in server_info and "args" in server_info["docker"]:
                    docker_args = server_info["docker"]["args"]
                    if isinstance(docker_args, list):
                        for arg in docker_args:
                            if isinstance(arg, str) and arg.startswith("${") and arg.endswith("}"):
                                var_name = arg[2:-1]  # Remove ${ and }
                                if var_name not in all_required_vars:
                                    all_required_vars[var_name] = {
                                        "description": f"Environment variable for {server_info.get('name', server_ref)}",
                                        "required": True
                                    }
                
                # Check packages for environment variables (preferred method)
                packages = server_info.get("packages", [])
                for package in packages:
                    if isinstance(package, dict):
                        # Try both camelCase and snake_case field names
                        env_vars = package.get("environmentVariables", []) or package.get("environment_variables", [])
                        for env_var in env_vars:
                            if isinstance(env_var, dict) and "name" in env_var:
                                var_name = env_var["name"]
                                all_required_vars[var_name] = {
                                    "description": env_var.get("description", ""),
                                    "required": env_var.get("required", True)
                                }
                            
            except Exception:
                # Skip servers we can't analyze
                continue
        
        # Prompt user for each environment variable
        if all_required_vars:
            shared_env_vars = self._prompt_for_environment_variables(all_required_vars)
        
        return shared_env_vars
    
    def _prompt_for_environment_variables(self, required_vars: Dict[str, Dict]) -> Dict[str, str]:
        """Prompt user for environment variables.
        
        Args:
            required_vars: Dictionary mapping var names to their metadata
            
        Returns:
            Dictionary mapping variable names to their values
        """
        env_vars = {}
        
        # Check if we're in E2E test mode or CI environment - don't prompt interactively
        is_e2e_tests = os.getenv('APM_E2E_TESTS', '').lower() in ('1', 'true', 'yes')
        is_ci_environment = any(os.getenv(var) for var in ['CI', 'GITHUB_ACTIONS', 'TRAVIS', 'JENKINS_URL', 'BUILDKITE'])
        
        if is_e2e_tests or is_ci_environment:
            # In E2E tests or CI, provide reasonable defaults instead of prompting
            for var_name in sorted(required_vars.keys()):
                var_info = required_vars[var_name]
                existing_value = os.getenv(var_name)
                
                if existing_value:
                    env_vars[var_name] = existing_value
                else:
                    # Provide sensible defaults for known variables
                    if var_name == 'GITHUB_DYNAMIC_TOOLSETS':
                        env_vars[var_name] = '1'  # Enable dynamic toolsets for GitHub MCP server
                    elif 'token' in var_name.lower() or 'key' in var_name.lower():
                        # For tokens/keys, try environment defaults with fallback chain
                        # Priority: GITHUB_APM_PAT (APM modules) > GITHUB_TOKEN (user tokens)
                        env_vars[var_name] = os.getenv('GITHUB_APM_PAT') or os.getenv('GITHUB_TOKEN', '')
                    else:
                        # For other variables, use empty string or reasonable default
                        env_vars[var_name] = ''
            
            if is_e2e_tests:
                print("E2E test mode detected")
            else:
                print("CI environment detected")
            
            return env_vars
        
        try:
            # Try to use Rich for better prompts
            from rich.console import Console
            from rich.prompt import Prompt
            
            console = Console()
            console.print("Environment variables needed:", style="cyan")
            
            for var_name in sorted(required_vars.keys()):
                var_info = required_vars[var_name]
                description = var_info.get("description", "")
                required = var_info.get("required", True)
                
                # Check if already set in environment
                existing_value = os.getenv(var_name)
                
                if existing_value:
                    console.print(f"  ✅ {var_name}: [dim]using existing value[/dim]")
                    env_vars[var_name] = existing_value
                else:
                    # Determine if this looks like a password/secret
                    is_sensitive = any(keyword in var_name.lower() 
                                     for keyword in ['password', 'secret', 'key', 'token', 'api'])
                    
                    prompt_text = f"  {var_name}"
                    if description:
                        prompt_text += f" ({description})"
                    
                    if required:
                        value = Prompt.ask(prompt_text, password=is_sensitive)
                    else:
                        value = Prompt.ask(prompt_text, default="", password=is_sensitive)
                    
                    env_vars[var_name] = value
            
            console.print()
            
        except ImportError:
            # Fallback to simple input
            import click
            
            click.echo("Environment variables needed:")
            
            for var_name in sorted(required_vars.keys()):
                var_info = required_vars[var_name]
                description = var_info.get("description", "")
                
                existing_value = os.getenv(var_name)
                
                if existing_value:
                    click.echo(f"  ✅ {var_name}: using existing value")
                    env_vars[var_name] = existing_value
                else:
                    prompt_text = f"  {var_name}"
                    if description:
                        prompt_text += f" ({description})"
                    
                    # Simple input for fallback
                    is_sensitive = any(keyword in var_name.lower() 
                                     for keyword in ['password', 'secret', 'key', 'token', 'api'])
                    
                    value = click.prompt(prompt_text, hide_input=is_sensitive, default="", show_default=False)
                    env_vars[var_name] = value
            
            click.echo()
        
        return env_vars