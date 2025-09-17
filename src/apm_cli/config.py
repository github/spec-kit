"""Configuration management for APM-CLI."""

import os
import json


CONFIG_DIR = os.path.expanduser("~/.apm-cli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def ensure_config_exists():
    """Ensure the configuration directory and file exist."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
        
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"default_client": "vscode"}, f)


def get_config():
    """Get the current configuration.
    
    Returns:
        dict: Current configuration.
    """
    ensure_config_exists()
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def update_config(updates):
    """Update the configuration with new values.
    
    Args:
        updates (dict): Dictionary of configuration values to update.
    """
    config = get_config()
    config.update(updates)
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_default_client():
    """Get the default MCP client.
    
    Returns:
        str: Default MCP client type.
    """
    return get_config().get("default_client", "vscode")


def set_default_client(client_type):
    """Set the default MCP client.
    
    Args:
        client_type (str): Type of client to set as default.
    """
    update_config({"default_client": client_type})
