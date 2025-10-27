"""Test update_spec_directory_references function."""

import tempfile
import os
from pathlib import Path
from unittest.mock import patch
import typer

# Import module directly to avoid dependency issues
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from specify_cli import update_spec_directory_references


class TestUpdateSpecDirectoryReferences:
    """Test update_spec_directory_references function."""

    def test_basic_specs_replacement(self):
        """Test basic specs/ directory replacement."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files with various specs/ references
            test_files = {
                'script.sh': '#!/bin/bash\necho "specs/ directory"',
                'script.ps1': 'Write-Host "specs/ directory"',
                'README.md': '# Project\n\nSee specs/ for documentation.',
                'config.json': '{"spec_dir": "specs/"}'
            }
            
            for filename, content in test_files.items():
                file_path = temp_path / filename
                file_path.write_text(content)
            
            # Update references to custom directory
            update_spec_directory_references(temp_path, 'documentation', verbose=False)
            
            # Check that files were updated
            for filename in test_files:
                file_path = temp_path / filename
                updated_content = file_path.read_text()
                assert 'documentation/' in updated_content, f"File {filename} should contain 'documentation/'"
                assert 'specs/' not in updated_content, f"File {filename} should not contain 'specs/'"

    def test_quoted_specs_replacement(self):
        """Test replacement of quoted specs/ references."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create file with quoted specs/ references
            content = '''
echo "specs/"
echo 'specs/'
echo `specs/`
'''
            file_path = temp_path / 'test.sh'
            file_path.write_text(content)
            
            # Update references
            update_spec_directory_references(temp_path, 'requirements', verbose=False)
            
            # Check quotes were handled correctly
            updated_content = file_path.read_text()
            assert 'requirements/' in updated_content
            assert '"specs/"' not in updated_content
            assert "'specs/'" not in updated_content
            assert '`specs/' not in updated_content

    def test_template_placeholder_replacement(self):
        """Test template placeholder updates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create template files with placeholders
            template_content = '''# Template
Input: /{SPEC_DIR}/[feature]/
Path: specs/[feature]/
Mixed: {SPEC_DIR} and specs/
Nested: /{SPEC_DIR}/[feature]/docs
'''
            template_file = temp_path / 'template.md'
            template_file.write_text(template_content)
            
            # Update references
            update_spec_directory_references(temp_path, 'feature-specs', verbose=False)
            
            # Check placeholders were replaced
            updated_content = template_file.read_text()
            assert 'feature-specs/' in updated_content
            assert '{SPEC_DIR}' not in updated_content
            
            # Check that original specs/ patterns were replaced (not part of feature-specs)
            # The line "Path: specs/[feature]/" should become "Path: feature-specs/[feature]/"
            assert 'Path: specs/[feature]/' not in updated_content
            assert 'Mixed: {SPEC_DIR} and specs/' not in updated_content
            # But feature-specs/ should be present as the replacement
            assert 'Path: feature-specs/[feature]/' in updated_content
            assert 'Mixed: feature-specs and feature-specs/' in updated_content

    def test_directory_rename(self):
        """Test that specs/ directory gets renamed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create specs directory with content
            specs_dir = temp_path / 'specs'
            specs_dir.mkdir()
            (specs_dir / 'test.txt').write_text('test content')
            (specs_dir / 'subdir').mkdir()
            (specs_dir / 'subdir' / 'nested.txt').write_text('nested content')
            
            # Update references
            update_spec_directory_references(temp_path, 'documentation', verbose=False)
            
            # Check directory was renamed
            assert not specs_dir.exists(), "Original specs/ directory should not exist"
            
            new_dir = temp_path / 'documentation'
            assert new_dir.exists(), "New documentation/ directory should exist"
            assert (new_dir / 'test.txt').exists(), "Files should be moved"
            assert (new_dir / 'subdir' / 'nested.txt').exists(), "Nested files should be moved"
            assert (new_dir / 'test.txt').read_text() == 'test content'

    def test_directory_rename_no_overwrite(self):
        """Test that existing target directory is not overwritten."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create both specs and target directories
            specs_dir = temp_path / 'specs'
            target_dir = temp_path / 'documentation'
            specs_dir.mkdir()
            target_dir.mkdir()
            
            # Add content to both
            (specs_dir / 'specs_file.txt').write_text('specs content')
            (target_dir / 'existing_file.txt').write_text('existing content')
            
            # Update references (should not overwrite existing target)
            update_spec_directory_references(temp_path, 'documentation', verbose=False)
            
            # Check specs directory still exists (target existed)
            assert specs_dir.exists(), "specs/ directory should still exist when target exists"
            assert target_dir.exists(), "target directory should still exist"
            
            # Target directory should have existing content unchanged
            assert (target_dir / 'existing_file.txt').read_text() == 'existing content'
            
            # specs directory should still have its content
            assert (specs_dir / 'specs_file.txt').read_text() == 'specs content'

    def test_various_file_patterns(self):
        """Test that various file patterns are updated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create files with different extensions
            files_to_create = {
                'script.sh': 'echo "specs/"',
                'script.ps1': 'Write-Host "specs/"',
                'README.md': 'See specs/ for docs',
                'config.json': '{"dir": "specs/"}',
                'settings.yaml': 'path: specs/',
                'setup.yml': 'directory: specs/',
                'project.toml': 'spec_dir = "specs/"'
            }
            
            for filename, content in files_to_create.items():
                file_path = temp_path / filename
                file_path.write_text(content)
            
            # Update references
            update_spec_directory_references(temp_path, 'my-specs', verbose=False)
            
            # Check all files were updated
            for filename, original_content in files_to_create.items():
                file_path = temp_path / filename
                updated_content = file_path.read_text()
                assert 'my-specs/' in updated_content or 'my-specs' in updated_content, f"File {filename} should be updated"
                # Check that the original specs/ pattern was replaced, not that specs/ doesn't appear as substring
                assert original_content not in updated_content, f"File {filename} should be modified"
                # Verify specific replacements occurred
                if 'specs/' in original_content:
                    assert 'specs/' not in updated_content or 'my-specs/' in updated_content, f"File {filename} should have specs/ replaced with my-specs/"

    def test_complex_patterns(self):
        """Test complex spec directory patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test file with various complex patterns
            test_content = '''
# Various specs/ patterns
echo "specs/"
echo 'specs/'
echo "specs"
echo `specs/`
echo /specs/
echo specs/[123]-feature
echo specs-[456]-test
echo "specs/"
echo 'specs/'
echo specs/branch-name
echo git ls-remote | grep specs/
echo find specs/ -name "*.md"
'''
            
            test_file = temp_path / 'complex.sh'
            test_file.write_text(test_content)
            
            # Update references
            update_spec_directory_references(temp_path, 'feature-docs', verbose=False)
            
            # Check all patterns were updated
            updated_content = test_file.read_text()
            assert 'feature-docs/' in updated_content
            assert 'specs/' not in updated_content
            assert '"specs/"' not in updated_content
            assert "'specs/'" not in updated_content
            assert '`specs/' not in updated_content
            assert '/specs/' not in updated_content
            assert 'specs/[123]' not in updated_content
            assert 'specs-[456]' not in updated_content

    def test_no_changes_needed(self):
        """Test that files without specs/ references are not modified."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create file without specs references (no specs word at all)
            content = '''# Project without any specifications
echo "Hello World"
echo "No special directory here"
echo "Just regular content"
'''
            
            test_file = temp_path / 'no-specs.txt'
            test_file.write_text(content)
            original_mtime = test_file.stat().st_mtime
            
            # Update references (should not modify this file)
            update_spec_directory_references(temp_path, 'documentation', verbose=False)
            
            # Check file was not modified
            updated_mtime = test_file.stat().st_mtime
            assert original_mtime == updated_mtime, "File without specs/ should not be modified"

    def test_error_handling(self):
        """Test error handling during file updates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a normal file that should be processed successfully
            test_file = temp_path / 'test.sh'
            test_file.write_text('echo "specs/"')
            
            # Test that function completes without raising exceptions
            # The function has try-catch blocks that should handle individual file errors
            try:
                update_spec_directory_references(temp_path, 'documentation', verbose=False)
                # If we get here, the function handled any potential errors
                error_handling_works = True
            except Exception as e:
                # If an exception escapes, error handling failed
                error_handling_works = False
                print(f"Unexpected exception: {e}")
            
            assert error_handling_works, "Function should handle errors gracefully and not raise exceptions"
            
            # Verify the file was actually updated (normal case)
            updated_content = test_file.read_text()
            assert 'documentation/' in updated_content, "File should be updated successfully"

    def test_verbose_output(self):
        """Test verbose output functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test file
            test_file = temp_path / 'test.md'
            test_file.write_text('See specs/ for documentation.')
            
            # Test with verbose=True
            with patch('specify_cli.console') as mock_console:
                update_spec_directory_references(temp_path, 'documentation', verbose=True)
                
                # Check that verbose output was called
                mock_console.print.assert_called()
                call_args = [call[0][0] for call in mock_console.print.call_args_list]
                
                # Should have updated file message
                update_messages = [msg for msg in call_args if 'Updated:' in msg]
                assert len(update_messages) > 0, "Should have at least one update message"

    def test_nonexistent_directory(self):
        """Test handling of nonexistent project directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            nonexistent_path = temp_path / 'nonexistent'
            
            # Should not raise exception for nonexistent directory
            update_spec_directory_references(nonexistent_path, 'documentation', verbose=False)
            
            # Should complete without error
            assert True  # If we get here, no exception was raised