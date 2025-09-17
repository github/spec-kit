"""GitHub package downloader for APM dependencies."""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import re

import git
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from ..core.token_manager import GitHubTokenManager
from ..models.apm_package import (
    DependencyReference, 
    PackageInfo, 
    ResolvedReference, 
    GitReferenceType,
    validate_apm_package,
    APMPackage
)


class GitHubPackageDownloader:
    """Downloads and validates APM packages from GitHub repositories."""
    
    def __init__(self):
        """Initialize the GitHub package downloader."""
        self.token_manager = GitHubTokenManager()
        self.git_env = self._setup_git_environment()
    
    def _setup_git_environment(self) -> Dict[str, Any]:
        """Set up Git environment with GitHub authentication using centralized token manager.
        
        Returns:
            Dict containing environment variables for Git operations
        """
        # Use centralized token management
        env = self.token_manager.setup_environment()
        
        # Get the token for modules (APM package access)
        self.github_token = self.token_manager.get_token_for_purpose('modules', env)
        self.has_github_token = self.github_token is not None
        
        # Configure Git security settings
        env['GIT_TERMINAL_PROMPT'] = '0'
        env['GIT_ASKPASS'] = 'echo'  # Prevent interactive credential prompts
        env['GIT_CONFIG_NOSYSTEM'] = '1'
        env['GIT_CONFIG_GLOBAL'] = '/dev/null'
        
        return env
    
    def _sanitize_git_error(self, error_message: str) -> str:
        """Sanitize Git error messages to remove potentially sensitive authentication information.
        
        Args:
            error_message: Raw error message from Git operations
            
        Returns:
            str: Sanitized error message with sensitive data removed
        """
        import re
        
        # Remove any tokens that might appear in URLs (format: https://token@github.com)
        sanitized = re.sub(r'https://[^@\s]+@github\.com', 'https://***@github.com', error_message)
        
        # Remove any tokens that might appear as standalone values
        sanitized = re.sub(r'(ghp_|gho_|ghu_|ghs_|ghr_)[a-zA-Z0-9_]+', '***', sanitized)
        
        # Remove environment variable values that might contain tokens
        sanitized = re.sub(r'(GITHUB_TOKEN|GITHUB_APM_PAT|GH_TOKEN|GITHUB_COPILOT_PAT|GITHUB_NPM_PAT)=[^\s]+', r'\1=***', sanitized)
        
        return sanitized

    def _build_repo_url(self, repo_ref: str, use_ssh: bool = False) -> str:
        """Build the appropriate repository URL for cloning.
        
        Uses GitHub Enterprise authentication format for private repositories:
        - x-access-token format for authenticated HTTPS (GitHub Enterprise standard)
        - SSH URLs for SSH key-based authentication
        - Standard HTTPS URLs as fallback
        
        Args:
            repo_ref: Repository reference in format "owner/repo"
            use_ssh: Whether to use SSH URL for git operations
            
        Returns:
            str: Repository URL suitable for git clone operations
        """
        if use_ssh:
            # Use SSH URL for private repository access with SSH keys
            return f"git@github.com:{repo_ref}.git"
        elif self.github_token:
            # Use GitHub Enterprise x-access-token format for authenticated access
            # This is the standard format for GitHub Actions and Enterprise environments
            return f"https://x-access-token:{self.github_token}@github.com/{repo_ref}.git"
        else:
            # Use standard HTTPS URL for public repositories
            return f"https://github.com/{repo_ref}"
    
    def _clone_with_fallback(self, repo_url_base: str, target_path: Path, **clone_kwargs) -> Repo:
        """Attempt to clone a repository with fallback authentication methods.
        
        Uses GitHub Enterprise authentication patterns:
        1. x-access-token format for private repos (GitHub Enterprise standard)
        2. SSH for SSH key-based authentication
        3. Standard HTTPS for public repos (fallback)
        
        Args:
            repo_url_base: Base repository reference (owner/repo)
            target_path: Target path for cloning
            **clone_kwargs: Additional arguments for Repo.clone_from
            
        Returns:
            Repo: Successfully cloned repository
            
        Raises:
            RuntimeError: If all authentication methods fail
        """
        last_error = None
        
        # Method 1: Try x-access-token format if token is available (GitHub Enterprise)
        if self.github_token:
            try:
                auth_url = self._build_repo_url(repo_url_base, use_ssh=False)
                return Repo.clone_from(auth_url, target_path, env=self.git_env, **clone_kwargs)
            except GitCommandError as e:
                last_error = e
                # Continue to next method
        
        # Method 2: Try SSH if it might work (for SSH key-based authentication)
        try:
            ssh_url = self._build_repo_url(repo_url_base, use_ssh=True)
            return Repo.clone_from(ssh_url, target_path, env=self.git_env, **clone_kwargs)
        except GitCommandError as e:
            last_error = e
            # Continue to next method
        
        # Method 3: Try standard HTTPS as fallback for public repos
        try:
            public_url = f"https://github.com/{repo_url_base}"
            return Repo.clone_from(public_url, target_path, env=self.git_env, **clone_kwargs)
        except GitCommandError as e:
            last_error = e
        
        # All methods failed
        error_msg = f"Failed to clone repository {repo_url_base} using all available methods. "
        if not self.has_github_token:
            error_msg += "For private repositories, set GITHUB_APM_PAT or GITHUB_TOKEN environment variable, " \
                        "or ensure SSH keys are configured."
        else:
            error_msg += "Please check repository access permissions and authentication setup."
        
        if last_error:
            sanitized_error = self._sanitize_git_error(str(last_error))
            error_msg += f" Last error: {sanitized_error}"
        
        raise RuntimeError(error_msg)
    
    def resolve_git_reference(self, repo_ref: str) -> ResolvedReference:
        """Resolve a Git reference (branch/tag/commit) to a specific commit SHA.
        
        Args:
            repo_ref: Repository reference string (e.g., "user/repo#branch")
            
        Returns:
            ResolvedReference: Resolved reference with commit SHA
            
        Raises:
            ValueError: If the reference format is invalid
            RuntimeError: If Git operations fail
        """
        # Parse the repository reference
        try:
            dep_ref = DependencyReference.parse(repo_ref)
        except ValueError as e:
            raise ValueError(f"Invalid repository reference '{repo_ref}': {e}")
        
        # Default to main branch if no reference specified
        ref = dep_ref.reference or "main"
        
        # Pre-analyze the reference type to determine the best approach
        is_likely_commit = re.match(r'^[a-f0-9]{7,40}$', ref.lower()) is not None
        
        # Create a temporary directory for Git operations
        temp_dir = None
        try:
            import tempfile
            temp_dir = Path(tempfile.mkdtemp())
            
            if is_likely_commit:
                # For commit SHAs, clone full repository first, then checkout the commit
                try:
                    repo = self._clone_with_fallback(dep_ref.repo_url, temp_dir)
                    commit = repo.commit(ref)
                    ref_type = GitReferenceType.COMMIT
                    resolved_commit = commit.hexsha
                    ref_name = ref
                except Exception as e:
                    sanitized_error = self._sanitize_git_error(str(e))
                    raise ValueError(f"Could not resolve commit '{ref}' in repository {dep_ref.repo_url}: {sanitized_error}")
            else:
                # For branches and tags, try shallow clone first
                try:
                    # Try to clone with specific branch/tag first
                    repo = self._clone_with_fallback(
                        dep_ref.repo_url,
                        temp_dir,
                        depth=1,
                        branch=ref
                    )
                    ref_type = GitReferenceType.BRANCH  # Could be branch or tag
                    resolved_commit = repo.head.commit.hexsha
                    ref_name = ref
                    
                except GitCommandError:
                    # If branch/tag clone fails, try full clone and resolve reference
                    try:
                        repo = self._clone_with_fallback(dep_ref.repo_url, temp_dir)
                        
                        # Try to resolve the reference
                        try:
                            # Try as branch first
                            try:
                                branch = repo.refs[f"origin/{ref}"]
                                ref_type = GitReferenceType.BRANCH
                                resolved_commit = branch.commit.hexsha
                                ref_name = ref
                            except IndexError:
                                # Try as tag
                                try:
                                    tag = repo.tags[ref]
                                    ref_type = GitReferenceType.TAG
                                    resolved_commit = tag.commit.hexsha
                                    ref_name = ref
                                except IndexError:
                                    raise ValueError(f"Reference '{ref}' not found in repository {dep_ref.repo_url}")
                        
                        except Exception as e:
                            sanitized_error = self._sanitize_git_error(str(e))
                            raise ValueError(f"Could not resolve reference '{ref}' in repository {dep_ref.repo_url}: {sanitized_error}")
                    
                    except GitCommandError as e:
                        # Check if this might be a private repository access issue
                        if "Authentication failed" in str(e) or "remote: Repository not found" in str(e):
                            error_msg = f"Failed to clone repository {dep_ref.repo_url}. "
                            if not self.has_github_token:
                                error_msg += "This might be a private repository that requires authentication. " \
                                           "Please set GITHUB_APM_PAT or GITHUB_TOKEN environment variable."
                            else:
                                error_msg += "Authentication failed. Please check your GitHub token permissions."
                            raise RuntimeError(error_msg)
                        else:
                            sanitized_error = self._sanitize_git_error(str(e))
                            raise RuntimeError(f"Failed to clone repository {dep_ref.repo_url}: {sanitized_error}")
                    
        finally:
            # Clean up temporary directory
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        return ResolvedReference(
            original_ref=repo_ref,
            ref_type=ref_type,
            resolved_commit=resolved_commit,
            ref_name=ref_name
        )
    
    def download_package(self, repo_ref: str, target_path: Path) -> PackageInfo:
        """Download a GitHub repository and validate it as an APM package.
        
        Args:
            repo_ref: Repository reference string (e.g., "user/repo#branch")
            target_path: Local path where package should be downloaded
            
        Returns:
            PackageInfo: Information about the downloaded package
            
        Raises:
            ValueError: If the repository reference is invalid
            RuntimeError: If download or validation fails
        """
        # Parse the repository reference
        try:
            dep_ref = DependencyReference.parse(repo_ref)
        except ValueError as e:
            raise ValueError(f"Invalid repository reference '{repo_ref}': {e}")
        
        # Resolve the Git reference to get specific commit
        resolved_ref = self.resolve_git_reference(repo_ref)
        
        # Create target directory if it doesn't exist
        target_path.mkdir(parents=True, exist_ok=True)
        
        # If directory already exists and has content, remove it
        if target_path.exists() and any(target_path.iterdir()):
            shutil.rmtree(target_path)
            target_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Clone the repository using fallback authentication methods
            # Use shallow clone for performance if we have a specific commit
            if resolved_ref.ref_type == GitReferenceType.COMMIT:
                # For commits, we need to clone and checkout the specific commit
                repo = self._clone_with_fallback(dep_ref.repo_url, target_path)
                repo.git.checkout(resolved_ref.resolved_commit)
            else:
                # For branches and tags, we can use shallow clone
                repo = self._clone_with_fallback(
                    dep_ref.repo_url,
                    target_path,
                    depth=1,
                    branch=resolved_ref.ref_name
                )
            
            # Remove .git directory to save space and prevent treating as a Git repository
            git_dir = target_path / ".git"
            if git_dir.exists():
                shutil.rmtree(git_dir, ignore_errors=True)
                
        except GitCommandError as e:
            # Check if this might be a private repository access issue
            if "Authentication failed" in str(e) or "remote: Repository not found" in str(e):
                error_msg = f"Failed to clone repository {dep_ref.repo_url}. "
                if not self.has_github_token:
                    error_msg += "This might be a private repository that requires authentication. " \
                               "Please set GITHUB_APM_PAT or GITHUB_TOKEN environment variable."
                else:
                    error_msg += "Authentication failed. Please check your GitHub token permissions."
                raise RuntimeError(error_msg)
            else:
                sanitized_error = self._sanitize_git_error(str(e))
                raise RuntimeError(f"Failed to clone repository {dep_ref.repo_url}: {sanitized_error}")
        except RuntimeError:
            # Re-raise RuntimeError from _clone_with_fallback
            raise
        
        # Validate the downloaded package
        validation_result = validate_apm_package(target_path)
        if not validation_result.is_valid:
            # Clean up on validation failure
            if target_path.exists():
                shutil.rmtree(target_path, ignore_errors=True)
            
            error_msg = f"Invalid APM package {dep_ref.repo_url}:\n"
            for error in validation_result.errors:
                error_msg += f"  - {error}\n"
            raise RuntimeError(error_msg.strip())
        
        # Load the APM package metadata
        if not validation_result.package:
            raise RuntimeError(f"Package validation succeeded but no package metadata found for {dep_ref.repo_url}")
        
        package = validation_result.package
        package.source = dep_ref.to_github_url()
        package.resolved_commit = resolved_ref.resolved_commit
        
        # Create and return PackageInfo
        return PackageInfo(
            package=package,
            install_path=target_path,
            resolved_reference=resolved_ref,
            installed_at=datetime.now().isoformat()
        )
    
    def _get_clone_progress_callback(self):
        """Get a progress callback for Git clone operations.
        
        Returns:
            Callable that can be used as progress callback for GitPython
        """
        def progress_callback(op_code, cur_count, max_count=None, message=''):
            """Progress callback for Git operations."""
            if max_count:
                percentage = int((cur_count / max_count) * 100)
                print(f"\r🚀 Cloning: {percentage}% ({cur_count}/{max_count}) {message}", end='', flush=True)
            else:
                print(f"\r🚀 Cloning: {message} ({cur_count})", end='', flush=True)
        
        return progress_callback