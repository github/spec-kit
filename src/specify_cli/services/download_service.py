"""
Download Service for spec-kit - Handles GitHub template downloads and archive extraction.

This module provides services for downloading templates from GitHub repositories,
extracting archives, and validating template packages. Extracted from the monolithic
__init__.py implementation to provide a cleaner, testable interface.
"""

import shutil
import tarfile
import tempfile
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


class DownloadService(ABC):
    """Abstract base class for download services."""

    @abstractmethod
    def download_template(self, template_url: str, destination_path: Path) -> bool:
        """Download a template from a URL to the specified destination.

        Args:
            template_url: URL to download the template from
            destination_path: Where to save the downloaded template

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def download_github_repo(
        self, repo_url: str, destination_path: Path, _branch: str = "main"
    ) -> bool:
        """Download a GitHub repository to the specified destination.

        Args:
            repo_url: GitHub repository URL (e.g., "owner/repo")
            destination_path: Where to save the downloaded repo
            branch: Git branch to download (default: "main")

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def extract_archive(self, archive_path: Path, destination_path: Path) -> bool:
        """Extract an archive (ZIP or TAR) to the specified destination.

        Args:
            archive_path: Path to the archive file
            destination_path: Where to extract the archive

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def validate_template_package(
        self, template_path: Path
    ) -> Tuple[bool, Optional[str]]:
        """Validate a template package structure.

        Args:
            template_path: Path to the template directory

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    def get_available_templates(self, repo_url: str) -> List[str]:
        """Get list of available templates from a repository.

        Args:
            repo_url: GitHub repository URL

        Returns:
            List of template names available
        """
        pass

    @abstractmethod
    def download_specific_template(
        self, repo_url: str, template_name: str, destination_path: Path
    ) -> bool:
        """Download a specific template from a repository.

        Args:
            repo_url: GitHub repository URL
            template_name: Name of the specific template
            destination_path: Where to save the template

        Returns:
            True if successful, False otherwise
        """
        pass


class HttpxDownloadService(DownloadService):
    """Download service implementation using httpx for HTTP requests."""

    def __init__(
        self,
        console: Optional[Console] = None,
        timeout: int = 30,
        default_repo_owner: str = "barisgit",
        default_repo_name: str = "spec-kit-improved",
    ):
        """Initialize the service.

        Args:
            console: Rich console for output (optional)
            timeout: Request timeout in seconds (default: 30)
            default_repo_owner: Default GitHub repository owner for templates
            default_repo_name: Default GitHub repository name for templates
        """
        self.console = console or Console()
        self.timeout = timeout
        self.default_repo_owner = default_repo_owner
        self.default_repo_name = default_repo_name

    def download_template(self, template_url: str, destination_path: Path) -> bool:
        """Download a template from a URL to the specified destination."""
        try:
            response = httpx.get(
                template_url, timeout=self.timeout, follow_redirects=True
            )
            response.raise_for_status()

            # Ensure destination directory exists
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            with open(destination_path, "wb") as f:
                f.write(response.content)

            return True

        except (httpx.RequestError, OSError) as e:
            self.console.print(f"[red]Error downloading template:[/red] {e}")
            return False

    def download_github_repo(
        self, repo_url: str, destination_path: Path, _branch: str = "main"
    ) -> bool:
        """Download a GitHub repository to the specified destination.

        This method downloads the latest release from the GitHub repository
        using the same logic as the original monolithic implementation.
        """
        try:
            # Parse repo URL to extract owner and repo name
            if "/" not in repo_url:
                self.console.print(f"[red]Invalid repo URL format:[/red] {repo_url}")
                return False

            parts = repo_url.strip("/").split("/")
            if len(parts) < 2:
                self.console.print(f"[red]Invalid repo URL format:[/red] {repo_url}")
                return False

            repo_owner = parts[-2]
            repo_name = parts[-1]

            # Get latest release information from GitHub API
            api_url = (
                f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
            )
            response = httpx.get(api_url, timeout=self.timeout, follow_redirects=True)
            response.raise_for_status()
            release_data = response.json()

            # For now, download the first asset (ZIP file)
            assets = release_data.get("assets", [])
            if not assets:
                self.console.print("[red]No assets found in the latest release[/red]")
                return False

            # Find a ZIP asset
            zip_asset = None
            for asset in assets:
                if asset["name"].endswith(".zip"):
                    zip_asset = asset
                    break

            if not zip_asset:
                self.console.print("[red]No ZIP asset found in the release[/red]")
                return False

            download_url = zip_asset["browser_download_url"]

            # Download to temporary location first
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
                temp_path = Path(tmp_file.name)

            if self.download_template(download_url, temp_path) and self.extract_archive(
                temp_path, destination_path
            ):
                # Clean up temporary file
                temp_path.unlink()
                return True

            # Clean up on failure
            if temp_path.exists():
                temp_path.unlink()
            return False

        except (httpx.RequestError, KeyError, ValueError) as e:
            self.console.print(f"[red]Error downloading GitHub repo:[/red] {e}")
            return False

    def download_github_release_template(
        self, ai_assistant: str, destination_path: Path
    ) -> Tuple[bool, Dict]:
        """Download template from spec-kit GitHub releases.

        This method replicates the original download_template_from_github logic.

        Args:
            ai_assistant: AI assistant type ("claude", "gemini", "copilot")
            destination_path: Where to save the downloaded template

        Returns:
            Tuple of (success, metadata_dict)
        """
        repo_owner = self.default_repo_owner
        repo_name = self.default_repo_name

        try:
            # Fetch release information
            api_url = (
                f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
            )
            response = httpx.get(api_url, timeout=self.timeout, follow_redirects=True)
            response.raise_for_status()
            release_data = response.json()

            # Find the template asset for the specified AI assistant
            pattern = f"spec-kit-template-{ai_assistant}"
            matching_assets = [
                asset
                for asset in release_data.get("assets", [])
                if pattern in asset["name"] and asset["name"].endswith(".zip")
            ]

            if not matching_assets:
                self.console.print(
                    f"[red]Error:[/red] No template found for AI assistant '{ai_assistant}'"
                )
                available_assets = [
                    asset["name"] for asset in release_data.get("assets", [])
                ]
                self.console.print(
                    f"[yellow]Available assets:[/yellow] {available_assets}"
                )
                return False, {}

            # Use the first matching asset
            asset = matching_assets[0]
            download_url = asset["browser_download_url"]
            filename = asset["name"]
            file_size = asset["size"]

            # Download the file with progress
            zip_path = destination_path / filename
            success = self._download_with_progress(download_url, zip_path, file_size)

            metadata = (
                {
                    "filename": filename,
                    "size": file_size,
                    "release": release_data["tag_name"],
                    "asset_url": download_url,
                }
                if success
                else {}
            )

            return success, metadata

        except (httpx.RequestError, KeyError) as e:
            self.console.print(f"[red]Error fetching release information:[/red] {e}")
            return False, {}

    def _download_with_progress(
        self, url: str, destination: Path, file_size: int
    ) -> bool:
        """Download a file with progress bar."""
        try:
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)

            with httpx.stream(
                "GET", url, timeout=self.timeout, follow_redirects=True
            ) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("content-length", file_size))

                with open(destination, "wb") as f:
                    if total_size == 0:
                        # No content-length header, download without progress
                        for chunk in response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
                    else:
                        # Show progress bar
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                            console=self.console,
                        ) as progress:
                            task = progress.add_task("Downloading...", total=total_size)
                            downloaded = 0
                            for chunk in response.iter_bytes(chunk_size=8192):
                                f.write(chunk)
                                downloaded += len(chunk)
                                progress.update(task, completed=downloaded)

            return True

        except (httpx.RequestError, OSError) as e:
            self.console.print(f"[red]Error downloading file:[/red] {e}")
            if destination.exists():
                destination.unlink()
            return False

    def extract_archive(self, archive_path: Path, destination_path: Path) -> bool:
        """Extract an archive (ZIP or TAR) to the specified destination."""
        if not archive_path.exists():
            self.console.print(f"[red]Archive not found:[/red] {archive_path}")
            return False

        try:
            # Ensure destination exists
            destination_path.mkdir(parents=True, exist_ok=True)

            # Determine archive type and extract
            if archive_path.suffix.lower() == ".zip":
                return self._extract_zip(archive_path, destination_path)
            elif archive_path.suffix.lower() in [".tar", ".tar.gz", ".tgz", ".tar.bz2"]:
                return self._extract_tar(archive_path, destination_path)
            else:
                self.console.print(
                    f"[red]Unsupported archive format:[/red] {archive_path.suffix}"
                )
                return False

        except Exception as e:
            self.console.print(f"[red]Error extracting archive:[/red] {e}")
            return False

    def _extract_zip(self, zip_path: Path, destination_path: Path) -> bool:
        """Extract a ZIP archive."""
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(destination_path)

                # Handle GitHub-style ZIP with single root directory
                extracted_items = list(destination_path.iterdir())
                if len(extracted_items) == 1 and extracted_items[0].is_dir():
                    # Flatten nested directory structure
                    nested_dir = extracted_items[0]
                    temp_dir = destination_path.parent / f"{destination_path.name}_temp"

                    # Move nested content to temp location
                    shutil.move(str(nested_dir), str(temp_dir))
                    # Remove empty destination
                    destination_path.rmdir()
                    # Move temp to final destination
                    shutil.move(str(temp_dir), str(destination_path))

            return True

        except (zipfile.BadZipFile, OSError) as e:
            self.console.print(f"[red]Error extracting ZIP:[/red] {e}")
            return False

    def _extract_tar(self, tar_path: Path, destination_path: Path) -> bool:
        """Extract a TAR archive."""
        try:
            with tarfile.open(tar_path, "r:*") as tar_ref:
                tar_ref.extractall(destination_path)

                # Handle single root directory (similar to ZIP)
                extracted_items = list(destination_path.iterdir())
                if len(extracted_items) == 1 and extracted_items[0].is_dir():
                    # Flatten nested directory structure
                    nested_dir = extracted_items[0]
                    temp_dir = destination_path.parent / f"{destination_path.name}_temp"

                    shutil.move(str(nested_dir), str(temp_dir))
                    destination_path.rmdir()
                    shutil.move(str(temp_dir), str(destination_path))

            return True

        except (tarfile.TarError, OSError) as e:
            self.console.print(f"[red]Error extracting TAR:[/red] {e}")
            return False

    def validate_template_package(
        self, template_path: Path
    ) -> Tuple[bool, Optional[str]]:
        """Validate a template package structure."""
        if not template_path.exists():
            return False, f"Template path does not exist: {template_path}"

        if not template_path.is_dir():
            return False, f"Template path is not a directory: {template_path}"

        # Basic validation - check for common template files
        expected_files = ["README.md", "CONSTITUTION.md"]
        missing_files = []

        for expected_file in expected_files:
            if not (template_path / expected_file).exists():
                missing_files.append(expected_file)

        if missing_files:
            return False, f"Missing expected template files: {', '.join(missing_files)}"

        return True, None

    def get_available_templates(self, repo_url: str) -> List[str]:
        """Get list of available templates from a repository."""
        try:
            # Parse repo URL
            if "/" not in repo_url:
                return []

            parts = repo_url.strip("/").split("/")
            if len(parts) < 2:
                return []

            repo_owner = parts[-2]
            repo_name = parts[-1]

            # Get latest release information
            api_url = (
                f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
            )
            response = httpx.get(api_url, timeout=self.timeout, follow_redirects=True)
            response.raise_for_status()
            release_data = response.json()

            # Extract template names from assets
            templates = []
            for asset in release_data.get("assets", []):
                name = asset["name"]
                if "template" in name.lower() and name.endswith(".zip"):
                    # Extract template type from filename
                    # e.g., "spec-kit-template-claude.zip" -> "claude"
                    parts = name.replace(".zip", "").split("-")
                    if len(parts) >= 4 and parts[-2] == "template":
                        templates.append(parts[-1])

            return templates

        except (httpx.RequestError, KeyError) as e:
            self.console.print(f"[red]Error getting available templates:[/red] {e}")
            return []

    def download_specific_template(
        self, repo_url: str, template_name: str, destination_path: Path
    ) -> bool:
        """Download a specific template from a repository."""
        try:
            # For spec-kit, use the release-based download
            if "spec-kit" in repo_url.lower():
                success, metadata = self.download_github_release_template(
                    template_name, destination_path.parent
                )
                if success and metadata:
                    # The download method saves to destination_path.parent, so we need to move/extract
                    zip_path = destination_path.parent / metadata["filename"]
                    if zip_path.exists():
                        return self.extract_archive(zip_path, destination_path)
                return success
            else:
                # Generic GitHub repo download
                return self.download_github_repo(repo_url, destination_path)

        except Exception as e:
            self.console.print(f"[red]Error downloading specific template:[/red] {e}")
            return False


def create_download_service(console: Optional[Console] = None) -> DownloadService:
    """Factory function to create a download service instance."""
    return HttpxDownloadService(console=console)
