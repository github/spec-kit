"""Test update_spec_directory_references function."""

import tempfile
import os
from pathlib import Path
from unittest.mock import patch

from specify_cli import update_spec_directory_references


def test_update_spec_directory_references_basic():
    """Test basic spec directory reference updates."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files with various specs/ references
        test_files = {
            'script.sh': '#!/bin/bash\necho "specs/ directory"',
            'script.ps1': 'Write-Host "specs/ directory"',
            'README.md': '# Project\n\nSee specs/ for documentation.',
            'config.json': '{"spec_dir": "specs/"}',
            'test.txt': 'This file has specs/ references'
        }
        
        for filename, content in test_files.items():
            file_path = temp_path / filename
            file_path.write_text(content)
        
        # Update references to custom directory
        update_spec_directory_references(temp_path, 'documentation', verbose=False)
        
        # Check that files were updated
        updated_content = (temp_path / 'script.sh').read_text()
        assert 'documentation/' in updated_content
        assert 'specs/' not in updated_content
        
        updated_content = (temp_path / 'README.md').read_text()
        assert 'documentation/' in updated_content
        assert 'specs/' not in updated_content


def test_update_spec_directory_references_template_placeholders():
    """Test template placeholder updates."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create template files with placeholders
        template_content = '''# Template
Input: /{SPEC_DIR}/[feature]/
Path: specs/[feature]/
Mixed: {SPEC_DIR} and specs/
'''
        
        template_file = temp_path / 'template.md'
        template_file.write_text(template_content)
        
        # Update references
        update_spec_directory_references(temp_path, 'requirements', verbose=False)
        
        # Check placeholders were replaced
        updated_content = template_file.read_text()
        assert 'requirements/' in updated_content
        assert '{SPEC_DIR}' not in updated_content
        assert 'specs/' not in updated_content


def test_update_spec_directory_references_directory_rename():
    """Test that specs/ directory gets renamed."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create specs directory
        specs_dir = temp_path / 'specs'
        specs_dir.mkdir()
        (specs_dir / 'test.txt').write_text('test')
        
        # Update references
        update_spec_directory_references(temp_path, 'documentation', verbose=False)
        
        # Check directory was renamed
        assert not specs_dir.exists()
        new_dir = temp_path / 'documentation'
        assert new_dir.exists()
        assert (new_dir / 'test.txt').exists()


def test_update_spec_directory_references_no_overwrite():
    """Test that existing target directory is not overwritten."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create both specs and target directories
        specs_dir = temp_path / 'specs'
        target_dir = temp_path / 'documentation'
        specs_dir.mkdir()
        target_dir.mkdir()
        (specs_dir / 'test.txt').write_text('specs content')
        (target_dir / 'existing.txt').write_text('existing content')
        
        # Update references (should not overwrite existing target)
        update_spec_directory_references(temp_path, 'documentation', verbose=False)
        
        # Check specs directory still exists (target existed)
        assert specs_dir.exists()
        assert target_dir.exists()
        # Target directory should have existing content unchanged
        assert (target_dir / 'existing.txt').read_text() == 'existing content'


def test_update_spec_directory_references_various_patterns():
    """Test various spec directory patterns are updated."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test file with various patterns
        test_content = '''
# Various specs/ patterns
echo "specs/"
echo 'specs/'
echo "specs"
echo `specs/`
echo /specs/
echo specs/[123]-feature
echo "specs/"
echo 'specs/'
'''
        
        test_file = temp_path / 'test.sh'
        test_file.write_text(test_content)
        
        # Update references
        update_spec_directory_references(temp_path, 'my-specs', verbose=False)
        
        # Check all patterns were updated
        updated_content = test_file.read_text()
        assert 'my-specs/' in updated_content
        assert 'specs/' not in updated_content
        assert '"specs/"' not in updated_content
        assert "'specs/'" not in updated_content
        assert '`specs/' not in updated_content
        assert '/specs/' not in updated_content


if __name__ == '__main__':
    test_update_spec_directory_references_basic()
    test_update_spec_directory_references_template_placeholders()
    test_update_spec_directory_references_directory_rename()
    test_update_spec_directory_references_no_overwrite()
    test_update_spec_directory_references_various_patterns()
    print("All tests passed!")