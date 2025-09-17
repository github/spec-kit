"""Dependency verification for APM-CLI."""

import os
from pathlib import Path
import yaml
from ..factory import PackageManagerFactory, ClientFactory


def load_apm_config(config_file="apm.yml"):
    """Load the APM configuration file.
    
    Args:
        config_file (str, optional): Path to the configuration file. Defaults to "apm.yml".
        
    Returns:
        dict: The configuration, or None if loading failed.
    """
    try:
        config_path = Path(config_file)
        if not config_path.exists():
            print(f"Configuration file {config_file} not found.")
            return None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    except Exception as e:
        print(f"Error loading {config_file}: {e}")
        return None


def verify_dependencies(config_file="apm.yml"):
    """Check if apm.yml servers are installed.
    
    Args:
        config_file (str, optional): Path to the configuration file. Defaults to "apm.yml".
        
    Returns:
        tuple: (bool, list, list) - All installed status, list of installed, list of missing
    """
    config = load_apm_config(config_file)
    if not config or 'servers' not in config:
        return False, [], []
    
    try:
        package_manager = PackageManagerFactory.create_package_manager()
        installed = package_manager.list_installed()
        
        # Check which servers are missing
        required_servers = config['servers']
        missing = [server for server in required_servers if server not in installed]
        installed_servers = [server for server in required_servers if server in installed]
        
        all_installed = len(missing) == 0
        
        return all_installed, installed_servers, missing
    except Exception as e:
        print(f"Error verifying dependencies: {e}")
        return False, [], []


def install_missing_dependencies(config_file="apm.yml", client_type="vscode"):
    """Install missing dependencies from apm.yml for specified client.
    
    Args:
        config_file (str, optional): Path to the configuration file. Defaults to "apm.yml".
        client_type (str, optional): Type of client to configure. Defaults to "vscode".
        
    Returns:
        tuple: (bool, list) - Success status and list of installed packages
    """
    _, _, missing = verify_dependencies(config_file)
    
    if not missing:
        return True, []
    
    installed = []
    
    # Get client adapter and package manager
    client = ClientFactory.create_client(client_type)
    package_manager = PackageManagerFactory.create_package_manager()
    
    for server in missing:
        try:
            # Install the package using the package manager
            install_result = package_manager.install(server)
            
            if install_result:
                # Configure the client to use the server
                # For VSCode this updates the .vscode/mcp.json file in the project root
                client_result = client.configure_mcp_server(server, server_name=server)
                
                if client_result:
                    installed.append(server)
                else:
                    print(f"Warning: Package {server} installed but client configuration failed")
            
        except Exception as e:
            print(f"Error installing {server}: {e}")
    
    return len(installed) == len(missing), installed