"""Tests for Gemini extension setup functionality."""

import json
import tempfile
from pathlib import Path
import pytest

# Import the function we want to test
from specify_cli import setup_gemini_extension


def test_setup_gemini_extension_creates_directory_structure():
    """Test that setup_gemini_extension creates the correct directory structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        
        # Call the function
        result = setup_gemini_extension(workspace)
        
        # Check that it returned True
        assert result is True
        
        # Check that the directory structure was created
        extension_dir = workspace / ".gemini" / "extensions" / "spec-kit"
        assert extension_dir.exists()
        assert extension_dir.is_dir()


def test_setup_gemini_extension_creates_json_file():
    """Test that setup_gemini_extension creates gemini-extension.json with correct contents."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        
        # Call the function
        result = setup_gemini_extension(workspace)
        
        # Check that it returned True
        assert result is True
        
        # Check that the JSON file was created
        extension_dir = workspace / ".gemini" / "extensions" / "spec-kit"
        json_file = extension_dir / "gemini-extension.json"
        assert json_file.exists()
        assert json_file.is_file()
        
        # Check the contents of the JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        expected_config = {
            "name": "spec-kit",
            "version": "1.0.0",
            "description": "Spec-kit Gemini CLI extension"
        }
        assert config == expected_config


def test_setup_gemini_extension_creates_markdown_file():
    """Test that setup_gemini_extension creates GEMINI.md with correct contents."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        
        # Call the function
        result = setup_gemini_extension(workspace)
        
        # Check that it returned True
        assert result is True
        
        # Check that the markdown file was created
        extension_dir = workspace / ".gemini" / "extensions" / "spec-kit"
        md_file = extension_dir / "GEMINI.md"
        assert md_file.exists()
        assert md_file.is_file()
        
        # Check the contents of the markdown file
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        expected_content = """# GEMINI Extension for Spec Kit

This extension integrates Spec Kit with Gemini CLI.
"""
        assert content == expected_content


def test_setup_gemini_extension_handles_existing_directory():
    """Test that setup_gemini_extension works when directory already exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        
        # Create the directory structure first
        extension_dir = workspace / ".gemini" / "extensions" / "spec-kit"
        extension_dir.mkdir(parents=True, exist_ok=True)
        
        # Call the function
        result = setup_gemini_extension(workspace)
        
        # Check that it returned True
        assert result is True
        
        # Check that the files were still created
        json_file = extension_dir / "gemini-extension.json"
        md_file = extension_dir / "GEMINI.md"
        assert json_file.exists()
        assert md_file.exists()


def test_setup_gemini_extension_handles_permission_error():
    """Test that setup_gemini_extension handles permission errors gracefully."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        
        # Create a file with the same name as the directory we want to create
        # This will cause a permission error when trying to create the directory
        extension_dir = workspace / ".gemini" / "extensions" / "spec-kit"
        extension_dir.parent.mkdir(parents=True, exist_ok=True)
        extension_dir.touch()  # Create a file instead of directory
        
        # Call the function
        result = setup_gemini_extension(workspace)
        
        # Check that it returned False due to the error
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])
