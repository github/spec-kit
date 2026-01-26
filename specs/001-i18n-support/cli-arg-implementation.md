# CLI Argument Implementation Summary

## Overview

The i18n system has been updated to use **`--lang` CLI argument** as the primary language selection method, with `SPECIFY_LANG` environment variable as a fallback. This provides better discoverability and flexibility for users.

## Changes Made

### 1. Core Module Updates (`src/specify_cli/i18n/core.py`)

**Updated Functions:**

```python
def get_active_locale(cli_lang: Optional[str] = None) -> str:
    """Priority: CLI arg > env var > default (en_US)"""
    
def setup_i18n(cli_lang: Optional[str] = None) -> tuple[...]:
    """Initialize i18n with optional CLI language argument"""
    
def get_template_path(template_name: str, locale: Optional[str] = None, 
                     cli_lang: Optional[str] = None) -> Path:
    """Get template path with CLI language support"""
```

**Priority Order:**

1. `cli_lang` parameter (from `--lang` argument) - **highest priority**
2. `SPECIFY_LANG` environment variable - persistent default
3. `"en_US"` - fallback default

### 2. CLI Integration (`src/specify_cli/__init__.py`)

**Global Language Option:**

```python
@app.callback()
def callback(
    ctx: typer.Context,
    lang: Optional[str] = typer.Option(
        None,
        "--lang",
        help="Language for CLI output (en_US, zh_CN)",
        envvar="SPECIFY_LANG",  # Also reads from env var
    ),
):
    """Re-initialize i18n with CLI language argument."""
    global _, ngettext, _cli_lang
    _cli_lang = lang
    _, ngettext = setup_i18n(cli_lang=lang)
    # ... rest of callback
```

**Key Features:**

- `--lang` option available on ALL commands (global option)
- `envvar="SPECIFY_LANG"` automatically reads from environment
- Translation functions re-initialized with user's choice

### 3. Test Updates

All tests updated to reflect CLI argument support:

```python
# Test CLI arg takes precedence
def test_cli_arg_takes_precedence_over_env(self, monkeypatch):
    monkeypatch.setenv("SPECIFY_LANG", "en_US")
    assert get_active_locale(cli_lang="zh_CN") == "zh_CN"

# Test env var fallback
def test_env_var_used_when_no_cli_arg(self, monkeypatch):
    monkeypatch.setenv("SPECIFY_LANG", "zh_CN")
    assert get_active_locale() == "zh_CN"
```

### 4. Documentation Updates

**Updated Files:**

- `specs/001-i18n-support/quickstart.md` - Added CLI argument examples
- `specs/001-i18n-support/research.md` - Updated Decision 2 rationale

## Usage Examples

### Option 1: CLI Argument (Recommended for ad-hoc use)

```bash
# View help in Chinese
specify --lang zh_CN --help

# Initialize project with Chinese output
specify --lang zh_CN init my-project

# Check prerequisites in Chinese  
specify --lang zh_CN check
```

### Option 2: Environment Variable (For persistent default)

```bash
# Set persistent default
export SPECIFY_LANG=zh_CN

# All commands now use Chinese
specify init my-project
specify check

# Override with CLI argument
specify --lang en_US init another-project  # Uses English
```

### Option 3: Per-Command Override

```bash
# Environment set to Chinese
export SPECIFY_LANG=zh_CN

# But use English for specific command
specify --lang en_US --help  # Shows English help
```

## Benefits

### 1. **Discoverability**

- `--lang` appears in `--help` output
- Users immediately know the feature exists
- No need to search documentation

### 2. **Flexibility**

- CLI argument overrides environment variable
- Users can test different languages without changing env
- Perfect for one-off command execution

### 3. **Standard Practice**

- Follows conventions of major CLI tools
- Intuitive for developers familiar with other tools
- Works alongside environment variable for CI/CD

### 4. **User-Friendly**

- Easy to remember: `--lang zh_CN`
- Clear, self-documenting
- No hidden configuration

## Implementation Status

✅ **Completed:**

- Core module updated with `cli_lang` parameter
- CLI callback adds `--lang` global option
- Translation functions re-initialized per-command
- Tests updated and passing
- Documentation updated

⏸️ **Remaining Work:**

- Wrap CLI strings with `_()` function (T024-T034)
- Extract messages to POT file (T025)
- Create Chinese translations (T028-T032)
- Compile translations to MO files (T033)
- Integration testing (T035-T038)

## Migration Notes

**For Users:**

- `SPECIFY_LANG` still works exactly as before
- `--lang` is now the recommended method
- Both can be used together (CLI arg takes precedence)

**For Developers:**

- All new i18n functions accept optional `cli_lang` parameter
- Call `setup_i18n(cli_lang=user_choice)` to reinitialize
- Tests should use `cli_lang=` parameter instead of monkeypatching env vars

## Next Steps

1. **Complete Phase 3 (US1):** Wrap remaining CLI strings
2. **Extract Messages:** Run `./scripts/i18n/extract-messages.sh`
3. **Initialize Catalogs:** Create zh_CN and en_US .po files
4. **Translate:** Get native Chinese speaker to translate ~200-300 messages
5. **Compile:** Generate .mo files with `./scripts/i18n/compile-translations.sh`
6. **Test:** Validate with `specify --lang zh_CN --help`

---

**Date:** 2026-01-26  
**Feature:** 001-i18n-support  
**Status:** Phase 2 Complete, Phase 3 In Progress
