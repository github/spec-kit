"""Centralized GitHub token management for different AI runtimes.

This module handles the complex token environment setup required by different
AI CLI tools, each of which expects different environment variable names for
GitHub authentication and API access.

Token Architecture:
- GITHUB_COPILOT_PAT: User-scoped PAT specifically for Copilot
- GITHUB_APM_PAT: Fine-grained PAT for APM module access
- GITHUB_TOKEN: User-scoped PAT for GitHub Models API access
- GITHUB_NPM_PAT: Classic PAT for GitHub npm registry access

Runtime Requirements:
- Codex CLI: Uses GITHUB_TOKEN (must be user-scoped for GitHub Models)
"""

import os
from typing import Dict, Optional, Tuple


class GitHubTokenManager:
    """Manages GitHub token environment setup for different AI runtimes."""
    
    # Define token precedence for different use cases
    TOKEN_PRECEDENCE = {
        'copilot': ['GITHUB_COPILOT_PAT', 'GITHUB_TOKEN', 'GITHUB_APM_PAT'],
        'models': ['GITHUB_TOKEN'],  # GitHub Models requires user-scoped PAT
        'modules': ['GITHUB_APM_PAT', 'GITHUB_TOKEN'],  # APM module access
        'npm': ['GITHUB_NPM_PAT']  # npm registry access
    }
    
    # Runtime-specific environment variable mappings
    RUNTIME_ENV_VARS = {
        'copilot': ['GH_TOKEN', 'GITHUB_PERSONAL_ACCESS_TOKEN'],
        'codex': ['GITHUB_TOKEN'],  # Uses GITHUB_TOKEN directly
        'llm': ['GITHUB_MODELS_KEY'],  # LLM-specific variable for GitHub Models
    }
    
    def __init__(self, preserve_existing: bool = True):
        """Initialize token manager.
        
        Args:
            preserve_existing: If True, never overwrite existing environment variables
        """
        self.preserve_existing = preserve_existing
        
    def setup_environment(self, env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Set up complete token environment for all runtimes.
        
        Args:
            env: Environment dictionary to modify (defaults to os.environ.copy())
            
        Returns:
            Updated environment dictionary with all required tokens set
        """
        if env is None:
            env = os.environ.copy()
        
        # Get available tokens
        available_tokens = self._get_available_tokens(env)
        
        # Set up tokens for each runtime without overwriting existing values
        self._setup_copilot_tokens(env, available_tokens)
        self._setup_codex_tokens(env, available_tokens)
        self._setup_llm_tokens(env, available_tokens)
        
        return env
    
    def get_token_for_purpose(self, purpose: str, env: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Get the best available token for a specific purpose.
        
        Args:
            purpose: Token purpose ('copilot', 'models', 'modules', 'npm')
            env: Environment to check (defaults to os.environ)
            
        Returns:
            Best available token for the purpose, or None if not available
        """
        if env is None:
            env = os.environ
            
        if purpose not in self.TOKEN_PRECEDENCE:
            raise ValueError(f"Unknown purpose: {purpose}")
            
        for token_var in self.TOKEN_PRECEDENCE[purpose]:
            token = env.get(token_var)
            if token:
                return token
        return None
    
    def validate_tokens(self, env: Optional[Dict[str, str]] = None) -> Tuple[bool, str]:
        """Validate that required tokens are available.
        
        Args:
            env: Environment to check (defaults to os.environ)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if env is None:
            env = os.environ
            
        # Check for at least one valid token
        has_any_token = any(
            self.get_token_for_purpose(purpose, env) 
            for purpose in ['copilot', 'models', 'modules']
        )
        
        if not has_any_token:
            return False, (
                "No GitHub tokens found. Set one of:\n"
                "- GITHUB_TOKEN (user-scoped PAT for GitHub Models)\n"
                "- GITHUB_APM_PAT (fine-grained PAT for APM modules)"
            )
        
        # Warn about GitHub Models access if only fine-grained PAT is available
        models_token = self.get_token_for_purpose('models', env)
        if not models_token:
            has_fine_grained = env.get('GITHUB_APM_PAT')
            if has_fine_grained:
                return True, (
                    "Warning: Only fine-grained PAT available. "
                    "GitHub Models requires GITHUB_TOKEN (user-scoped PAT)"
                )
        
        return True, "Token validation passed"
    
    def _get_available_tokens(self, env: Dict[str, str]) -> Dict[str, str]:
        """Get all available GitHub tokens from environment."""
        tokens = {}
        for purpose, token_vars in self.TOKEN_PRECEDENCE.items():
            for token_var in token_vars:
                if token_var in env and env[token_var]:
                    tokens[token_var] = env[token_var]
        return tokens
    
    def _setup_copilot_tokens(self, env: Dict[str, str], available_tokens: Dict[str, str]):
        """Set up tokens for Copilot."""
        copilot_token = self.get_token_for_purpose('copilot', available_tokens)
        if not copilot_token:
            return
            
        for env_var in self.RUNTIME_ENV_VARS['copilot']:
            if self.preserve_existing and env_var in env:
                continue
            env[env_var] = copilot_token
    
    def _setup_codex_tokens(self, env: Dict[str, str], available_tokens: Dict[str, str]):
        """Set up tokens for Codex CLI (preserve existing GITHUB_TOKEN)."""
        # Codex uses GITHUB_TOKEN directly - only set if missing
        if self.preserve_existing and 'GITHUB_TOKEN' in env:
            return
            
        models_token = self.get_token_for_purpose('models', available_tokens)
        if models_token and 'GITHUB_TOKEN' not in env:
            env['GITHUB_TOKEN'] = models_token
    
    def _setup_llm_tokens(self, env: Dict[str, str], available_tokens: Dict[str, str]):
        """Set up tokens for LLM CLI."""
        # LLM uses GITHUB_MODELS_KEY, prefer GITHUB_TOKEN if available
        if self.preserve_existing and 'GITHUB_MODELS_KEY' in env:
            return
            
        models_token = self.get_token_for_purpose('models', available_tokens)
        if models_token:
            env['GITHUB_MODELS_KEY'] = models_token


# Convenience functions for common use cases
def setup_runtime_environment(env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Set up complete runtime environment for all AI CLIs."""
    manager = GitHubTokenManager()
    return manager.setup_environment(env)


def validate_github_tokens(env: Optional[Dict[str, str]] = None) -> Tuple[bool, str]:
    """Validate GitHub token setup."""
    manager = GitHubTokenManager()
    return manager.validate_tokens(env)


def get_github_token_for_runtime(runtime: str, env: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Get the appropriate GitHub token for a specific runtime."""
    manager = GitHubTokenManager()
    
    # Map runtime names to purposes
    runtime_to_purpose = {
        'copilot': 'copilot',
        'codex': 'models',
        'llm': 'models',
    }
    
    purpose = runtime_to_purpose.get(runtime)
    if not purpose:
        raise ValueError(f"Unknown runtime: {runtime}")
        
    return manager.get_token_for_purpose(purpose, env)