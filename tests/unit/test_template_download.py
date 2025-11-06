"""
Unit tests for template download and extraction.
"""
import json
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import httpx

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from specify_cli import (
    download_template_from_github,
    handle_vscode_settings,
)


@pytest.mark.unit
class TestTemplateDownload:
    """Tests for template download from GitHub."""

    def test_download_template_success(self, temp_dir: Path, mock_release_data: dict, mock_template_zip: Path):
        """Test successful template download."""
        mock_client = Mock(spec=httpx.Client)

        # Mock release API response
        mock_release_response = Mock()
        mock_release_response.status_code = 200
        mock_release_response.json.return_value = mock_release_data

        # Mock template download response
        mock_download_response = Mock()
        mock_download_response.status_code = 200
        mock_download_response.content = mock_template_zip.read_bytes()

        def mock_get(url, **kwargs):
            if "releases/latest" in url:
                return mock_release_response
            else:
                return mock_download_response

        mock_client.get = Mock(side_effect=mock_get)

        # Execute download
        zip_path, release_info = download_template_from_github(
            ai_assistant="claude",
            download_dir=temp_dir,
            script_type="sh",
            verbose=False,
            show_progress=False,
            client=mock_client,
        )

        assert zip_path.exists()
        assert zip_path.suffix == ".zip"
        assert release_info["tag_name"] == "v1.0.0"

    def test_download_template_api_error(self, temp_dir: Path):
        """Test handling of GitHub API errors."""
        mock_client = Mock(spec=httpx.Client)

        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response

        with pytest.raises(SystemExit):
            download_template_from_github(
                ai_assistant="claude",
                download_dir=temp_dir,
                script_type="sh",
                verbose=False,
                show_progress=False,
                client=mock_client,
            )

    def test_download_template_invalid_json(self, temp_dir: Path):
        """Test handling of invalid JSON response."""
        mock_client = Mock(spec=httpx.Client)

        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Invalid response"
        mock_client.get.return_value = mock_response

        with pytest.raises(SystemExit):
            download_template_from_github(
                ai_assistant="claude",
                download_dir=temp_dir,
                script_type="sh",
                verbose=False,
                show_progress=False,
                client=mock_client,
            )

    def test_download_template_no_matching_asset(self, temp_dir: Path, mock_release_data: dict):
        """Test handling when no matching template asset found."""
        mock_client = Mock(spec=httpx.Client)

        # Remove matching assets
        mock_release_data["assets"] = [
            {
                "name": "spec-kit-template-other-sh.zip",
                "browser_download_url": "https://example.com/other.zip",
            }
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_release_data
        mock_client.get.return_value = mock_response

        with pytest.raises(SystemExit):
            download_template_from_github(
                ai_assistant="claude",
                download_dir=temp_dir,
                script_type="sh",
                verbose=False,
                show_progress=False,
                client=mock_client,
            )

    def test_download_template_with_github_token(self, temp_dir: Path, mock_release_data: dict, mock_template_zip: Path):
        """Test template download with GitHub token."""
        mock_client = Mock(spec=httpx.Client)

        mock_release_response = Mock()
        mock_release_response.status_code = 200
        mock_release_response.json.return_value = mock_release_data

        mock_download_response = Mock()
        mock_download_response.status_code = 200
        mock_download_response.content = mock_template_zip.read_bytes()

        call_count = [0]

        def mock_get(url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # Verify auth header is present
                assert "headers" in kwargs
                assert "Authorization" in kwargs["headers"]
                assert kwargs["headers"]["Authorization"] == "Bearer test_token"
                return mock_release_response
            else:
                return mock_download_response

        mock_client.get = Mock(side_effect=mock_get)

        zip_path, release_info = download_template_from_github(
            ai_assistant="claude",
            download_dir=temp_dir,
            script_type="sh",
            verbose=False,
            show_progress=False,
            client=mock_client,
            github_token="test_token",
        )

        assert zip_path.exists()

    def test_download_template_network_timeout(self, temp_dir: Path):
        """Test handling of network timeout."""
        mock_client = Mock(spec=httpx.Client)
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")

        with pytest.raises(SystemExit):
            download_template_from_github(
                ai_assistant="claude",
                download_dir=temp_dir,
                script_type="sh",
                verbose=False,
                show_progress=False,
                client=mock_client,
            )

    def test_download_template_connection_error(self, temp_dir: Path):
        """Test handling of connection errors."""
        mock_client = Mock(spec=httpx.Client)
        mock_client.get.side_effect = httpx.ConnectError("Connection failed")

        with pytest.raises(SystemExit):
            download_template_from_github(
                ai_assistant="claude",
                download_dir=temp_dir,
                script_type="sh",
                verbose=False,
                show_progress=False,
                client=mock_client,
            )


@pytest.mark.unit
class TestVSCodeSettingsHandling:
    """Tests for .vscode/settings.json handling."""

    def test_handle_vscode_settings_new_file(self, temp_dir: Path):
        """Test copying settings when no existing file."""
        source_file = temp_dir / "source.json"
        dest_file = temp_dir / "dest.json"

        settings = {"editor.fontSize": 14}
        source_file.write_text(json.dumps(settings))

        handle_vscode_settings(source_file, dest_file, "settings.json", verbose=False)

        assert dest_file.exists()
        with open(dest_file) as f:
            result = json.load(f)
        assert result == settings

    def test_handle_vscode_settings_merge_existing(self, temp_dir: Path):
        """Test merging with existing settings file."""
        source_file = temp_dir / "source.json"
        dest_file = temp_dir / "dest.json"

        existing_settings = {"editor.fontSize": 12, "editor.tabSize": 2}
        new_settings = {"editor.fontSize": 14, "editor.wordWrap": "on"}

        dest_file.write_text(json.dumps(existing_settings))
        source_file.write_text(json.dumps(new_settings))

        handle_vscode_settings(source_file, dest_file, "settings.json", verbose=False)

        with open(dest_file) as f:
            result = json.load(f)

        # Verify merge: fontSize updated, tabSize preserved, wordWrap added
        assert result["editor.fontSize"] == 14
        assert result["editor.tabSize"] == 2
        assert result["editor.wordWrap"] == "on"

    def test_handle_vscode_settings_invalid_json(self, temp_dir: Path):
        """Test handling of invalid JSON in source."""
        source_file = temp_dir / "source.json"
        dest_file = temp_dir / "dest.json"

        source_file.write_text("invalid json")

        # Should fall back to copying
        handle_vscode_settings(source_file, dest_file, "settings.json", verbose=False)

        assert dest_file.exists()

    def test_handle_vscode_settings_with_tracker(self, temp_dir: Path):
        """Test settings handling with tracker."""
        source_file = temp_dir / "source.json"
        dest_file = temp_dir / "dest.json"
        mock_tracker = Mock()

        settings = {"editor.fontSize": 14}
        source_file.write_text(json.dumps(settings))

        handle_vscode_settings(source_file, dest_file, "settings.json", verbose=False, tracker=mock_tracker)

        assert dest_file.exists()


@pytest.mark.unit
class TestTemplateExtraction:
    """Tests for template extraction logic."""

    def test_extract_template_basic_structure(self, temp_dir: Path, mock_template_zip: Path):
        """Test basic template extraction."""
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir()

        with zipfile.ZipFile(mock_template_zip, 'r') as zf:
            zf.extractall(extract_dir)

        # Verify key files exist
        assert (extract_dir / "README.md").exists()
        assert (extract_dir / ".claude" / "commands" / "test.md").exists()
        assert (extract_dir / "scripts" / "bash" / "test.sh").exists()

    def test_extract_template_preserves_structure(self, temp_dir: Path, mock_template_zip: Path):
        """Test extraction preserves directory structure."""
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir()

        with zipfile.ZipFile(mock_template_zip, 'r') as zf:
            zf.extractall(extract_dir)

        # Verify directory structure
        assert (extract_dir / ".claude" / "commands").is_dir()
        assert (extract_dir / "scripts" / "bash").is_dir()
        assert (extract_dir / ".vscode").is_dir()

    def test_extract_template_file_permissions(self, temp_dir: Path, mock_template_zip: Path):
        """Test extraction handles file permissions."""
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir()

        with zipfile.ZipFile(mock_template_zip, 'r') as zf:
            zf.extractall(extract_dir)

        # Shell scripts should exist (permissions tested separately)
        assert (extract_dir / "scripts" / "bash" / "test.sh").exists()

    def test_extract_template_nested_directories(self, temp_dir: Path):
        """Test extraction handles deeply nested directories."""
        # Create a zip with nested structure
        zip_path = temp_dir / "nested.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("a/b/c/d/file.txt", "content")

        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir()

        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)

        assert (extract_dir / "a" / "b" / "c" / "d" / "file.txt").exists()

    def test_extract_template_empty_directories(self, temp_dir: Path):
        """Test extraction handles empty directories."""
        zip_path = temp_dir / "empty_dirs.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Create empty directory entry
            zf.writestr("empty_dir/", "")
            zf.writestr("another_dir/.keep", "")

        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir()

        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)

        assert (extract_dir / "empty_dir").exists()
        assert (extract_dir / "another_dir").exists()


@pytest.mark.unit
class TestAssetSelection:
    """Tests for template asset selection logic."""

    def test_select_correct_agent_template(self, mock_release_data: dict):
        """Test selecting the correct agent template."""
        assets = mock_release_data["assets"]
        pattern = "spec-kit-template-claude-sh"

        matching = [a for a in assets if pattern in a["name"] and a["name"].endswith(".zip")]

        assert len(matching) == 1
        assert "claude-sh" in matching[0]["name"]

    def test_select_correct_script_type(self, mock_release_data: dict):
        """Test selecting the correct script type."""
        assets = mock_release_data["assets"]
        pattern = "spec-kit-template-claude-ps"

        matching = [a for a in assets if pattern in a["name"] and a["name"].endswith(".zip")]

        assert len(matching) == 1
        assert "ps" in matching[0]["name"]

    def test_no_matching_asset(self, mock_release_data: dict):
        """Test handling when no matching asset found."""
        assets = mock_release_data["assets"]
        pattern = "spec-kit-template-nonexistent-sh"

        matching = [a for a in assets if pattern in a["name"] and a["name"].endswith(".zip")]

        assert len(matching) == 0
