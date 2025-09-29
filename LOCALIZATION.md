# Localization Guide

Spec Kit supports multiple languages for generated templates and user-facing messages while keeping all commands and technical structures in English.

## Current Language Support

- **English (en)** - Default language
- **Korean (ko)** - Korean localization

## Usage

### Command Line Options

```bash
# Use default English
specify init my-project --ai claude

# Use Korean templates and messages
specify init my-project --ai claude --lang ko

# Interactive selection (includes language choice)
specify init my-project --ai claude
```

### Interactive Selection

When running `specify init` without the `--lang` option, you'll see:

```
Choose your AI assistant:
▶ copilot (GitHub Copilot)
  claude (Claude Code)
  ...

Choose script type:
▶ sh (POSIX Shell (bash/zsh))
  ps (PowerShell)

Choose template language:
▶ en (English)
  ko (한국어 (Korean))
```

## Implementation Details

### Architecture

- **Commands stay in English**: All CLI commands (`init`, `check`) and options (`--ai`, `--script`) remain in English
- **Templates are localized**: Generated documentation templates use the selected language
- **YAML-based configuration**: Translations are stored in `locales/*.yaml` files
- **Fallback system**: Missing translations fall back to English

### File Structure

```
locales/
├── en.yaml          # English translations
└── ko.yaml          # Korean translations

src/specify_cli/
└── locale.py        # Localization management
```

### Translation Markers

Templates use translation markers in the format `{{locale:key.path}}`:

```markdown
# {{locale:templates.spec.title}}: [FEATURE NAME]

## {{locale:templates.spec.sections.requirements}}
```

These markers are automatically replaced with localized text during template processing.

## Adding New Languages

### 1. Create Language File

Create a new YAML file in the `locales/` directory:

```bash
# For Japanese support
touch locales/ja.yaml
```

### 2. Add Translation Content

Use the English file as a template:

```yaml
# locales/ja.yaml
templates:
  spec:
    title: "機能仕様書"
    sections:
      user_scenarios: "ユーザーシナリオとテスト"
      requirements: "要件"
      # ... more translations
```

### 3. Update Language Choices

Add the new language to `LANGUAGE_CHOICES` in `src/specify_cli/__init__.py`:

```python
LANGUAGE_CHOICES = {
    "en": "English",
    "ko": "한국어 (Korean)",
    "ja": "日本語 (Japanese)"  # Add this line
}
```

### 4. Test the Implementation

```bash
# Test with new language
specify init test-project --lang ja
```

## Translation Keys Structure

### Templates Section

```yaml
templates:
  spec:
    title: "Feature Specification"
    sections:
      user_scenarios: "User Scenarios & Testing"
      requirements: "Requirements"
      # ... section names
    guidelines:
      focus_what: "Focus on WHAT users need and WHY"
      # ... guidelines
    content:
      describe_main_journey: "Describe the main user journey"
      # ... content templates
```

### Messages Section

```yaml
messages:
  errors:
    no_description: "No feature description provided"
    no_spec: "No feature spec at {path}"
  success:
    spec_ready: "spec ready for planning"
  warnings:
    spec_uncertainties: "Spec has uncertainties"
```

## API Reference

### LocaleManager Class

```python
from specify_cli.locale import LocaleManager

# Initialize
lm = LocaleManager()

# Set locale
lm.set_locale("ko")

# Get translated text
title = lm.get_text("templates.spec.title")

# Translate template
translated = lm.translate_template(template_content)
```

### Global Functions

```python
from specify_cli.locale import set_locale, get_text, translate_template

# Set global locale
set_locale("ko")

# Get text with formatting
error_msg = get_text("messages.errors.no_spec", path="/some/path")

# Translate template content
result = translate_template("# {{locale:templates.spec.title}}")
```

## Testing

Run localization tests:

```bash
# Basic functionality test
uv run python tests/test_locale.py

# Test CLI with different languages
uv run specify init test-en --lang en --ignore-agent-tools --no-git
uv run specify init test-ko --lang ko --ignore-agent-tools --no-git
```

## Contributing Translations

1. Fork the repository
2. Add your language file in `locales/`
3. Update `LANGUAGE_CHOICES` in the CLI
4. Test your translations
5. Submit a pull request

For contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Design Principles

1. **Technical Terms in English**: Commands, options, and technical terminology remain in English for consistency
2. **User Content Localized**: Templates, messages, and user-facing content are translated
3. **Graceful Fallback**: Missing translations fall back to English automatically
4. **Non-Breaking**: Adding languages doesn't affect existing functionality
5. **Maintainable**: YAML-based system makes translations easy to manage