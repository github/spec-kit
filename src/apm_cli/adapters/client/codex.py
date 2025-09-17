"""OpenAI Codex CLI implementation of MCP client adapter.

This adapter implements the Codex CLI-specific handling of MCP server configuration,
targeting the global ~/.codex/config.toml file as specified in the MCP installation
architecture specification.
"""

import os
import toml
from pathlib import Path
from .base import MCPClientAdapter
from ...registry.client import SimpleRegistryClient
from ...registry.integration import RegistryIntegration


class CodexClientAdapter(MCPClientAdapter):
    """Codex CLI implementation of MCP client adapter.
    
    This adapter handles Codex CLI-specific configuration for MCP servers using
    a global ~/.codex/config.toml file, following the TOML format for
    MCP server configuration.
    """
    
    def __init__(self, registry_url=None):
        """Initialize the Codex CLI client adapter.
        
        Args:
            registry_url (str, optional): URL of the MCP registry.
                If not provided, uses the MCP_REGISTRY_URL environment variable
                or falls back to the default GitHub registry.
        """
        self.registry_client = SimpleRegistryClient(registry_url)
        self.registry_integration = RegistryIntegration(registry_url)
    
    def get_config_path(self):
        """Get the path to the Codex CLI MCP configuration file.
        
        Returns:
            str: Path to ~/.codex/config.toml
        """
        codex_dir = Path.home() / ".codex"
        return str(codex_dir / "config.toml")
    
    def update_config(self, config_updates):
        """Update the Codex CLI MCP configuration.
        
        Args:
            config_updates (dict): Configuration updates to apply.
        """
        current_config = self.get_current_config()
        
        # Ensure mcp_servers section exists
        if "mcp_servers" not in current_config:
            current_config["mcp_servers"] = {}
        
        # Apply updates to mcp_servers section
        current_config["mcp_servers"].update(config_updates)
        
        # Write back to file
        config_path = Path(self.get_config_path())
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            toml.dump(current_config, f)
    
    def get_current_config(self):
        """Get the current Codex CLI MCP configuration.
        
        Returns:
            dict: Current configuration, or empty dict if file doesn't exist.
        """
        config_path = self.get_config_path()
        
        if not os.path.exists(config_path):
            return {}
        
        try:
            with open(config_path, 'r') as f:
                return toml.load(f)
        except (toml.TomlDecodeError, IOError):
            return {}
    
    def configure_mcp_server(self, server_url, server_name=None, enabled=True, env_overrides=None, server_info_cache=None, runtime_vars=None):
        """Configure an MCP server in Codex CLI configuration.
        
        This method follows the Codex CLI MCP configuration format with
        mcp_servers sections in the TOML configuration.
        
        Args:
            server_url (str): URL or identifier of the MCP server.
            server_name (str, optional): Name of the server. Defaults to None.
            enabled (bool, optional): Ignored parameter, kept for API compatibility.
            env_overrides (dict, optional): Pre-collected environment variable overrides.
            server_info_cache (dict, optional): Pre-fetched server info to avoid duplicate registry calls.
            runtime_vars (dict, optional): Runtime variable values. Defaults to None.
            
        Returns:
            bool: True if successful, False otherwise.
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
            if not server_info:
                print(f"Error: MCP server '{server_url}' not found in registry")
                return False
            
            # Check for remote servers early - Codex doesn't support remote/SSE servers
            remotes = server_info.get("remotes", [])
            packages = server_info.get("packages", [])
            
            # If server has only remote endpoints and no packages, it's a remote-only server
            if remotes and not packages:
                print(f"⚠️  Warning: MCP server '{server_url}' is a remote server (SSE type)")
                print("   Codex CLI only supports local servers with command/args configuration")
                print("   Remote servers are not supported by Codex CLI")
                print("   Skipping installation for Codex CLI")
                return False
            
            # Determine the server name for configuration key
            if server_name:
                # Use explicitly provided server name
                config_key = server_name
            else:
                # Extract name from server_url (part after last slash)
                # For URLs like "microsoft/azure-devops-mcp" -> "azure-devops-mcp"
                # For URLs like "github/github-mcp-server" -> "github-mcp-server"
                if '/' in server_url:
                    config_key = server_url.split('/')[-1]
                else:
                    # Fallback to full server_url if no slash
                    config_key = server_url
            
            # Generate server configuration with environment variable resolution
            server_config = self._format_server_config(server_info, env_overrides, runtime_vars)
            
            # Update configuration using the chosen key
            self.update_config({config_key: server_config})
            
            print(f"Successfully configured MCP server '{config_key}' for Codex CLI")
            return True
            
        except Exception as e:
            print(f"Error configuring MCP server: {e}")
            return False
    
    def _format_server_config(self, server_info, env_overrides=None, runtime_vars=None):
        """Format server information into Codex CLI MCP configuration format.
        
        Args:
            server_info (dict): Server information from registry.
            env_overrides (dict, optional): Pre-collected environment variable overrides.
            runtime_vars (dict, optional): Runtime variable values.
            
        Returns:
            dict: Formatted server configuration for Codex CLI.
        """
        # Default configuration structure with registry ID for conflict detection
        config = {
            "command": "unknown",
            "args": [],
            "env": {},
            "id": server_info.get("id", "")  # Add registry UUID for conflict detection
        }
        
        # Note: Remote servers (SSE type) are handled in configure_mcp_server and rejected early
        # This method only handles local servers with packages
        
        # Get packages from server info
        packages = server_info.get("packages", [])
        
        if not packages:
            # If no packages are available, this indicates incomplete server configuration
            # This should fail installation with a clear error message
            raise ValueError(f"MCP server has no package information available in registry. "
                           f"This appears to be a temporary registry issue or the server is remote-only. "
                           f"Server: {server_info.get('name', 'unknown')}")
        
        if packages:
            # Use the first package for configuration (prioritize npm, then docker, then others)
            package = self._select_best_package(packages)
            
            if package:
                registry_name = package.get("registry_name", "")
                package_name = package.get("name", "")
                runtime_hint = package.get("runtime_hint", "")
                runtime_arguments = package.get("runtime_arguments", [])
                package_arguments = package.get("package_arguments", [])
                env_vars = package.get("environment_variables", [])
                
                # Resolve environment variables first
                resolved_env = self._process_environment_variables(env_vars, env_overrides)
                
                # Process arguments to extract simple string values
                processed_runtime_args = self._process_arguments(runtime_arguments, resolved_env, runtime_vars)
                processed_package_args = self._process_arguments(package_arguments, resolved_env, runtime_vars)
                
                # Generate command and args based on package type
                if registry_name == "npm":
                    config["command"] = runtime_hint or "npx"
                    # For npm packages, use runtime_arguments directly as they contain the complete npx command
                    config["args"] = processed_runtime_args + processed_package_args
                    # For NPM packages, also use env block for environment variables
                    if resolved_env:
                        config["env"] = resolved_env
                elif registry_name == "docker":
                    config["command"] = "docker"
                    
                    # For Docker packages in Codex TOML format:
                    # - Ensure all environment variables from resolved_env are represented as -e flags in args
                    # - Put actual environment variable values in separate [env] section
                    config["args"] = self._ensure_docker_env_flags(processed_runtime_args + processed_package_args, resolved_env)
                    
                    # Environment variables go in separate env section for Codex TOML format
                    if resolved_env:
                        config["env"] = resolved_env
                elif registry_name == "pypi":
                    config["command"] = runtime_hint or "uvx"
                    config["args"] = [package_name] + processed_runtime_args + processed_package_args
                    # For PyPI packages, use env block for environment variables
                    if resolved_env:
                        config["env"] = resolved_env
                elif registry_name == "homebrew":
                    # For homebrew packages, assume the binary name is the command
                    config["command"] = package_name.split('/')[-1] if '/' in package_name else package_name
                    config["args"] = processed_runtime_args + processed_package_args
                    # For Homebrew packages, use env block for environment variables
                    if resolved_env:
                        config["env"] = resolved_env
                else:
                    # Generic package handling
                    config["command"] = runtime_hint or package_name
                    config["args"] = processed_runtime_args + processed_package_args
                    # For generic packages, use env block for environment variables
                    if resolved_env:
                        config["env"] = resolved_env
        
        return config
    
    def _process_arguments(self, arguments, resolved_env=None, runtime_vars=None):
        """Process argument objects to extract simple string values with environment resolution.
        
        Args:
            arguments (list): List of argument objects from registry.
            resolved_env (dict): Resolved environment variables.
            runtime_vars (dict): Runtime variable values.
            
        Returns:
            list: List of processed argument strings.
        """
        if resolved_env is None:
            resolved_env = {}
        if runtime_vars is None:
            runtime_vars = {}
            
        processed = []
        
        for arg in arguments:
            if isinstance(arg, dict):
                # Extract value from argument object
                arg_type = arg.get("type", "")
                if arg_type == "positional":
                    value = arg.get("value", arg.get("default", ""))
                    if value:
                        # Resolve both environment and runtime variable placeholders with actual values
                        processed_value = self._resolve_variable_placeholders(str(value), resolved_env, runtime_vars)
                        processed.append(processed_value)
                elif arg_type == "named":
                    # For named arguments, the flag name is in the "value" field
                    flag_name = arg.get("value", "")
                    if flag_name:
                        processed.append(flag_name)
                        # Some named arguments might have additional values (rare)
                        additional_value = arg.get("name", "")
                        if additional_value and additional_value != flag_name and not additional_value.startswith("-"):
                            processed_value = self._resolve_variable_placeholders(str(additional_value), resolved_env, runtime_vars)
                            processed.append(processed_value)
            elif isinstance(arg, str):
                # Already a string, use as-is but resolve variable placeholders
                processed_value = self._resolve_variable_placeholders(arg, resolved_env, runtime_vars)
                processed.append(processed_value)
        
        return processed
    
    def _process_environment_variables(self, env_vars, env_overrides=None):
        """Process environment variable definitions and resolve actual values.
        
        Args:
            env_vars (list): List of environment variable definitions.
            env_overrides (dict, optional): Pre-collected environment variable overrides.
            
        Returns:
            dict: Dictionary of resolved environment variable values.
        """
        import os
        import sys
        from rich.prompt import Prompt
        
        resolved = {}
        env_overrides = env_overrides or {}
        
        # If env_overrides is provided, it means the CLI has already handled environment variable collection
        # In this case, we should NEVER prompt for additional variables
        skip_prompting = bool(env_overrides)
        
        # Check for CI/automated environment via APM_E2E_TESTS flag (more reliable than TTY detection)
        if os.getenv('APM_E2E_TESTS') == '1':
            skip_prompting = True
            print(f"💡 APM_E2E_TESTS detected, will skip environment variable prompts")
        
        # Also skip prompting if we're in a non-interactive environment (fallback)
        is_interactive = sys.stdin.isatty() and sys.stdout.isatty()
        if not is_interactive:
            skip_prompting = True
        
        # Add default GitHub MCP server environment variables for essential functionality first
        # This ensures variables have defaults when user provides empty values or they're optional
        default_github_env = {
            "GITHUB_TOOLSETS": "context",
            "GITHUB_DYNAMIC_TOOLSETS": "1"
        }
        
        # Track which variables were explicitly provided with empty values (user wants defaults)
        empty_value_vars = set()
        if env_overrides:
            for key, value in env_overrides.items():
                if key in env_overrides and (not value or not value.strip()):
                    empty_value_vars.add(key)
        
        for env_var in env_vars:
            if isinstance(env_var, dict):
                name = env_var.get("name", "")
                description = env_var.get("description", "")
                required = env_var.get("required", True)
                
                if name:
                    # First check overrides, then environment
                    value = env_overrides.get(name) or os.getenv(name)
                    
                    # Only prompt if not provided in overrides or environment AND it's required AND we're not in managed override mode
                    if not value and required and not skip_prompting:
                        # Only prompt if not provided in overrides
                        prompt_text = f"Enter value for {name}"
                        if description:
                            prompt_text += f" ({description})"
                        value = Prompt.ask(prompt_text, password=True if "token" in name.lower() or "key" in name.lower() else False)
                    
                    # Add variable if it has a value OR if user explicitly provided empty and we have a default
                    if value and value.strip():
                        resolved[name] = value
                    elif name in empty_value_vars and name in default_github_env:
                        # User provided empty value and we have a default - use default
                        resolved[name] = default_github_env[name]
                    elif not required and name in default_github_env:
                        # Variable is optional and we have a default - use default
                        resolved[name] = default_github_env[name]
                    elif skip_prompting and name in default_github_env:
                        # Non-interactive environment and we have a default - use default
                        resolved[name] = default_github_env[name]
        
        return resolved
    
    def _resolve_variable_placeholders(self, value, resolved_env, runtime_vars):
        """Resolve both environment and runtime variable placeholders in values.
        
        Args:
            value (str): Value that may contain placeholders like <TOKEN_NAME> or {runtime_var}
            resolved_env (dict): Dictionary of resolved environment variables.
            runtime_vars (dict): Dictionary of resolved runtime variables.
            
        Returns:
            str: Processed value with actual variable values.
        """
        import re
        
        if not value:
            return value
            
        processed = str(value)
        
        # Replace <TOKEN_NAME> with actual values from resolved_env (for Docker env vars)
        env_pattern = r'<([A-Z_][A-Z0-9_]*)>'
        
        def replace_env_var(match):
            env_name = match.group(1)
            return resolved_env.get(env_name, match.group(0))  # Return original if not found
        
        processed = re.sub(env_pattern, replace_env_var, processed)
        
        # Replace {runtime_var} with actual values from runtime_vars
        runtime_pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        
        def replace_runtime_var(match):
            var_name = match.group(1)
            return runtime_vars.get(var_name, match.group(0))  # Return original if not found
        
        processed = re.sub(runtime_pattern, replace_runtime_var, processed)
        
        return processed
    
    def _resolve_env_placeholders(self, value, resolved_env):
        """Legacy method for backward compatibility. Use _resolve_variable_placeholders instead."""
        return self._resolve_variable_placeholders(value, resolved_env, {})
    
    def _ensure_docker_env_flags(self, base_args, env_vars):
        """Ensure all environment variables are represented as -e flags in Docker args.
        
        For Codex TOML format, Docker args should contain -e flags for ALL environment variables
        that will be available to the container, while actual values go in the [env] section.
        
        Args:
            base_args (list): Base Docker arguments from registry.
            env_vars (dict): All environment variables that should be available.
            
        Returns:
            list: Docker arguments with -e flags for all environment variables.
        """
        if not env_vars:
            return base_args
            
        result = []
        existing_env_vars = set()
        
        # First pass: collect existing -e flags and build result with existing args
        i = 0
        while i < len(base_args):
            arg = base_args[i]
            result.append(arg)
            
            # Track existing -e flags
            if arg == "-e" and i + 1 < len(base_args):
                env_var_name = base_args[i + 1]
                existing_env_vars.add(env_var_name)
                result.append(env_var_name)
                i += 2
            else:
                i += 1
        
        # Second pass: add -e flags for any environment variables not already present
        # Insert them after "run" but before the image name (last argument)
        image_name = result[-1] if result else ""
        if image_name and not image_name.startswith("-"):
            # Remove image name temporarily
            result.pop()
            
            # Add missing environment variable flags
            for env_name in sorted(env_vars.keys()):
                if env_name not in existing_env_vars:
                    result.extend(["-e", env_name])
            
            # Add image name back
            result.append(image_name)
        else:
            # If we can't identify image name, just append at the end
            for env_name in sorted(env_vars.keys()):
                if env_name not in existing_env_vars:
                    result.extend(["-e", env_name])
        
        return result
    
    def _inject_docker_env_vars(self, args, env_vars):
        """Inject environment variables into Docker arguments as -e flags.
        
        Args:
            args (list): Original Docker arguments.
            env_vars (dict): Environment variables to inject.
            
        Returns:
            list: Updated arguments with environment variables injected as -e flags.
        """
        if not env_vars:
            return args
            
        result = []
        existing_env_vars = set()
        
        # First pass: collect existing -e flags to avoid duplicates
        i = 0
        while i < len(args):
            if args[i] == "-e" and i + 1 < len(args):
                existing_env_vars.add(args[i + 1])
                i += 2
            else:
                i += 1
        
        # Second pass: build the result with new env vars injected after "run"
        for i, arg in enumerate(args):
            result.append(arg)
            # If this is a docker run command, inject new environment variables after "run"
            if arg == "run":
                for env_name in env_vars.keys():
                    if env_name not in existing_env_vars:
                        result.extend(["-e", env_name])
        
        return result
    
    def _select_best_package(self, packages):
        """Select the best package for installation from available packages.
        
        Prioritizes packages in order: npm, docker, pypi, homebrew, others.
        
        Args:
            packages (list): List of package dictionaries.
            
        Returns:
            dict: Best package to use, or None if no suitable package found.
        """
        priority_order = ["npm", "docker", "pypi", "homebrew"]
        
        # Sort packages by priority
        for registry_name in priority_order:
            for package in packages:
                if package.get("registry_name") == registry_name:
                    return package
        
        # If no priority package found, return the first one
        return packages[0] if packages else None