import stat

from specify_cli import merge_json_files
from specify_cli import handle_vscode_settings

# --- Dimension 2: Polite Deep Merge Strategy ---

def test_merge_json_files_type_mismatch_preservation(tmp_path):
    """If user has a string but template wants a dict, PRESERVE user's string."""
    existing_file = tmp_path / "settings.json"
    # User might have overridden a setting with a simple string or different type
    existing_file.write_text('{"chat.editor.fontFamily": "CustomFont"}')
    
    # Template might expect a dict for the same key (hypothetically)
    new_settings = {
        "chat.editor.fontFamily": {"font": "TemplateFont"}
    }
    
    merged = merge_json_files(existing_file, new_settings)
    # Result is None because user settings were preserved and nothing else changed
    assert merged is None

def test_merge_json_files_deep_nesting(tmp_path):
    """Verify deep recursive merging of new keys."""
    existing_file = tmp_path / "settings.json"
    existing_file.write_text("""
    {
        "a": {
            "b": {
                "c": 1
            }
        }
    }
    """)
    
    new_settings = {
        "a": {
            "b": {
                "d": 2  # New nested key
            },
            "e": 3      # New mid-level key
        }
    }
    
    merged = merge_json_files(existing_file, new_settings)
    assert merged["a"]["b"]["c"] == 1
    assert merged["a"]["b"]["d"] == 2
    assert merged["a"]["e"] == 3

def test_merge_json_files_empty_existing(tmp_path):
    """Merging into an empty/new file."""
    existing_file = tmp_path / "empty.json"
    existing_file.write_text("{}")
    
    new_settings = {"a": 1}
    merged = merge_json_files(existing_file, new_settings)
    assert merged == {"a": 1}

# --- Dimension 3: Real-world Simulation ---

def test_merge_vscode_realistic_scenario(tmp_path):
    """A realistic VSCode settings.json with many existing preferences, comments, and trailing commas."""
    existing_file = tmp_path / "vscode_settings.json"
    existing_file.write_text("""
    {
        "editor.fontSize": 12,
        "editor.formatOnSave": true, /* block comment */
        "files.exclude": {
            "**/.git": true,
            "**/node_modules": true,
        },
        "chat.promptFilesRecommendations": {
            "existing.tool": true,
        } // User comment
    }
    """)
    
    template_settings = {
        "chat.promptFilesRecommendations": {
            "speckit.specify": True,
            "speckit.plan": True
        },
        "chat.tools.terminal.autoApprove": {
            ".specify/scripts/bash/": True
        }
    }
    
    merged = merge_json_files(existing_file, template_settings)
    
    # Check preservation
    assert merged["editor.fontSize"] == 12
    assert merged["files.exclude"]["**/.git"] is True
    assert merged["chat.promptFilesRecommendations"]["existing.tool"] is True
    
    # Check additions
    assert merged["chat.promptFilesRecommendations"]["speckit.specify"] is True
    assert merged["chat.tools.terminal.autoApprove"][".specify/scripts/bash/"] is True

# --- Dimension 4: Error Handling & Robustness ---

def test_merge_json_files_with_bom(tmp_path):
    """Test files with UTF-8 BOM (sometimes created on Windows)."""
    existing_file = tmp_path / "bom.json"
    content = '{"a": 1}'
    # Prepend UTF-8 BOM
    existing_file.write_bytes(b'\xef\xbb\xbf' + content.encode('utf-8'))
    
    new_settings = {"b": 2}
    merged = merge_json_files(existing_file, new_settings)
    assert merged == {"a": 1, "b": 2}

def test_merge_json_files_not_a_dictionary_template(tmp_path):
    """If for some reason new_content is not a dict, PRESERVE existing settings by returning None."""
    existing_file = tmp_path / "ok.json"
    existing_file.write_text('{"a": 1}')
    
    # Secure fallback: return None to skip writing and avoid clobbering
    assert merge_json_files(existing_file, ["not", "a", "dict"]) is None

def test_merge_json_files_unparseable_existing(tmp_path):
    """If the existing file is unparseable JSON, return None to avoid overwriting it."""
    bad_file = tmp_path / "bad.json"
    bad_file.write_text('{"a": 1, missing_value}') # Invalid JSON
    
    assert merge_json_files(bad_file, {"b": 2}) is None


def test_merge_json_files_list_preservation(tmp_path):
    """Verify that existing list values are preserved and NOT merged or overwritten."""
    existing_file = tmp_path / "list.json"
    existing_file.write_text('{"my.list": ["user_item"]}')
    
    template_settings = {
        "my.list": ["template_item"]
    }
    
    merged = merge_json_files(existing_file, template_settings)
    # The polite merge policy says: keep existing values if they exist and aren't both dicts.
    # Since nothing changed, it returns None.
    assert merged is None

def test_merge_json_files_no_changes(tmp_path):
    """If the merge doesn't introduce any new keys or changes, return None to skip rewrite."""
    existing_file = tmp_path / "no_change.json"
    existing_file.write_text('{"a": 1, "b": {"c": 2}}')
    
    template_settings = {
        "a": 1,          # Already exists
        "b": {"c": 2}    # Already exists nested
    }
    
    # Should return None because result == existing
    assert merge_json_files(existing_file, template_settings) is None

def test_merge_json_files_type_mismatch_no_op(tmp_path):
    """If a key exists with different type and we preserve it, it might still result in no change."""
    existing_file = tmp_path / "mismatch_no_op.json"
    existing_file.write_text('{"a": "user_string"}')
    
    template_settings = {
        "a": {"key": "template_dict"} # Mismatch, will be ignored
    }
    
    # Should return None because we preserved the user's string and nothing else changed
    assert merge_json_files(existing_file, template_settings) is None


def test_handle_vscode_settings_preserves_mode_on_atomic_write(tmp_path):
    """Atomic rewrite should preserve existing file mode bits."""
    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir()
    dest_file = vscode_dir / "settings.json"
    template_file = tmp_path / "template_settings.json"

    dest_file.write_text('{"a": 1}\n', encoding="utf-8")
    dest_file.chmod(0o640)
    before_mode = stat.S_IMODE(dest_file.stat().st_mode)

    template_file.write_text('{"b": 2}\n', encoding="utf-8")

    handle_vscode_settings(
        template_file,
        dest_file,
        "settings.json",
        verbose=False,
        tracker=None,
    )

    after_mode = stat.S_IMODE(dest_file.stat().st_mode)
    assert after_mode == before_mode
