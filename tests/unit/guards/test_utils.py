from pathlib import Path
from specify_cli.guards.utils import update_makefile, get_project_root


def test_update_makefile_creates_file(temp_project_dir):
    makefile_path = temp_project_dir / "Makefile"
    
    update_makefile(makefile_path, "test-target", "echo 'test'")
    
    assert makefile_path.exists()
    content = makefile_path.read_text()
    assert "test-target" in content
    assert "echo 'test'" in content


def test_update_makefile_idempotent(temp_project_dir):
    makefile_path = temp_project_dir / "Makefile"
    
    update_makefile(makefile_path, "test-target", "echo 'test'")
    first_content = makefile_path.read_text()
    
    update_makefile(makefile_path, "test-target", "echo 'test'")
    second_content = makefile_path.read_text()
    
    assert first_content == second_content


def test_get_project_root(temp_project_dir):
    git_dir = temp_project_dir / ".git"
    git_dir.mkdir()
    
    subdir = temp_project_dir / "some" / "deep" / "directory"
    subdir.mkdir(parents=True)
    
    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(subdir)
        root = get_project_root()
        assert root == temp_project_dir
    finally:
        os.chdir(original_cwd)
