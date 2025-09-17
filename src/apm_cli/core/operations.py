"""Core operations for APM-CLI."""

from ..factory import ClientFactory, PackageManagerFactory
from .safe_installer import SafeMCPInstaller


def configure_client(client_type, config_updates):
    """Configure an MCP client.
    
    Args:
        client_type (str): Type of client to configure.
        config_updates (dict): Configuration updates to apply.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        client = ClientFactory.create_client(client_type)
        client.update_config(config_updates)
        return True
    except Exception as e:
        print(f"Error configuring client: {e}")
        return False


def install_package(client_type, package_name, version=None, shared_env_vars=None, server_info_cache=None, shared_runtime_vars=None):
    """Install an MCP package for a specific client type.
    
    Args:
        client_type (str): Type of client to configure.
        package_name (str): Name of the package to install.
        version (str, optional): Version of the package to install.
        shared_env_vars (dict, optional): Pre-collected environment variables to use.
        server_info_cache (dict, optional): Pre-fetched server info to avoid duplicate registry calls.
        shared_runtime_vars (dict, optional): Pre-collected runtime variables to use.
    
    Returns:
        dict: Result with 'success' (bool), 'installed' (bool), 'skipped' (bool) keys.
    """
    try:
        # Use safe installer with conflict detection
        safe_installer = SafeMCPInstaller(client_type)
        
        # Pass shared environment and runtime variables and server info cache if available
        if shared_env_vars is not None or server_info_cache is not None or shared_runtime_vars is not None:
            summary = safe_installer.install_servers(
                [package_name], 
                env_overrides=shared_env_vars,
                server_info_cache=server_info_cache,
                runtime_vars=shared_runtime_vars
            )
        else:
            summary = safe_installer.install_servers([package_name])
        
        return {
            'success': True,
            'installed': len(summary.installed) > 0,
            'skipped': len(summary.skipped) > 0,
            'failed': len(summary.failed) > 0
        }
        
    except Exception as e:
        print(f"Error installing package {package_name} for {client_type}: {e}")
        return {
            'success': False,
            'installed': False,
            'skipped': False,
            'failed': True
        }


def uninstall_package(client_type, package_name):
    """Uninstall an MCP package.
    
    Args:
        client_type (str): Type of client to configure.
        package_name (str): Name of the package to uninstall.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        client = ClientFactory.create_client(client_type)
        package_manager = PackageManagerFactory.create_package_manager()
        
        # Uninstall the package
        result = package_manager.uninstall(package_name)
        
        # Remove any legacy config entries if they exist
        current_config = client.get_current_config()
        config_updates = {}
        if f"mcp.package.{package_name}.enabled" in current_config:
            config_updates = {f"mcp.package.{package_name}.enabled": None}  # Set to None to remove the entry
            client.update_config(config_updates)
        
        return result
    except Exception as e:
        print(f"Error uninstalling package: {e}")
        return False
