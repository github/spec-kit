# Data Model: I18n Support

**Feature**: Internationalization Support  
**Date**: 2026-01-26  
**Status**: Complete

## Entity Definitions

### 1. Language

Represents a supported language with metadata and file paths.

**Attributes**:

- `code` (string, required): Language code in `language_COUNTRY` format (e.g., `"en_US"`, `"zh_CN"`)
- `display_name` (string, required): Human-readable name (e.g., `"English (US)"`, `"简体中文"`)
- `fallback` (string, optional): Fallback language code if translation missing (e.g., `"en_US"`)
- `catalog_path` (Path, required): Path to translation catalog directory (e.g., `Path("src/specify_cli/i18n/zh_CN")`)
- `template_dir` (Path, optional): Path to localized templates (e.g., `Path("templates/i18n/zh_CN")`)
- `plural_forms` (string, required): gettext plural forms expression (e.g., `"nplurals=1; plural=0;"` for Chinese)

**Relationships**:

- One Language has one TranslationCatalog
- One Language has zero or more localized TemplateSets

**Validation Rules**:

- `code` must match format `[a-z]{2}_[A-Z]{2}`
- `code` must be unique across all Language instances
- `fallback` must reference an existing Language code or be None
- `catalog_path` directory must exist or be creatable
- Cannot have circular fallback references (e.g., A→B→A)

**State Transitions**:

- `pending`: Language added to codebase but translations not started
- `in_progress`: Translation work ongoing, coverage < 100%
- `complete`: All messages translated, coverage = 100%
- `active`: Language is available for use in CLI

### 2. TranslationCatalog

Collection of translated messages for a specific language, keyed by message identifier.

**Attributes**:

- `language_code` (string, required): Language this catalog belongs to (e.g., `"zh_CN"`)
- `domain` (string, required): Catalog domain name (e.g., `"specify"`)
- `messages` (dict, required): Dictionary of {message_id: translated_text}
- `pot_file` (Path, required): Path to POT template file (e.g., `"messages.pot"`)
- `po_file` (Path, required): Path to PO source file (e.g., `"zh_CN/LC_MESSAGES/specify.po"`)
- `mo_file` (Path, required): Path to compiled MO binary file (e.g., `"zh_CN/LC_MESSAGES/specify.mo"`)
- `coverage` (float, computed): Percentage of messages translated (0.0-1.0)
- `last_updated` (datetime, required): Last compilation timestamp

**Relationships**:

- One TranslationCatalog belongs to one Language
- One TranslationCatalog contains many TranslationKeys

**Validation Rules**:

- `language_code` must reference existing Language
- `domain` must match across all catalogs (consistent naming)
- `po_file` must be valid PO format (validated by Babel)
- `mo_file` must be compiled from `po_file` (no manual MO edits)
- `coverage` cannot exceed 1.0 (100%)

**State Transitions**:

- `empty`: POT created but PO not initialized
- `draft`: PO created, some translations exist
- `fuzzy`: Marked by translators as needing review
- `final`: All translations complete and reviewed
- `compiled`: MO file generated from PO file

### 3. TemplateSet

Collection of template files for a specific language, maintaining structure parallel to English templates.

**Attributes**:

- `language_code` (string, required): Language this template set belongs to (e.g., `"zh_CN"`)
- `base_dir` (Path, required): Root directory for localized templates (e.g., `Path("templates/i18n/zh_CN")`)
- `templates` (dict, required): Mapping of {template_name: template_path} (e.g., `{"spec-template.md": Path(...)}`)
- `placeholders` (set, required): Set of placeholders that must be preserved (e.g., `{"[FEATURE_NAME]", "[PROJECT_NAME]"}`)
- `coverage` (float, computed): Percentage of templates translated (0.0-1.0)

**Relationships**:

- One TemplateSet belongs to one Language
- One TemplateSet contains many template files
- TemplateSet mirrors structure of English templates

**Validation Rules**:

- `language_code` must reference existing Language
- All `templates` must exist on filesystem
- Localized templates must contain same `placeholders` as English versions
- Template directory structure must mirror English templates
- Template file names must match English names exactly

**State Transitions**:

- `empty`: Directory created but no templates translated
- `partial`: Some templates translated, coverage < 100%
- `complete`: All templates translated, coverage = 100%
- `validated`: Templates tested and confirmed to work with all agents

### 4. LocaleContext

Runtime context containing active language, fallback chain, and translation catalog for current CLI session.

**Attributes**:

- `active_locale` (string, required): Currently active language code (e.g., `"zh_CN"`)
- `fallback_chain` (list, required): Ordered list of fallback locales (e.g., `["zh_CN", "en_US"]`)
- `translator` (callable, required): Translation function (gettext.GNUTranslations.gettext)
- `ntranslator` (callable, required): Plural translation function (gettext.GNUTranslations.ngettext)
- `catalog_loaded` (bool, required): Whether translation catalog successfully loaded
- `catalog_path` (Path, optional): Path to loaded catalog (for diagnostics)
- `encoding` (string, required): Terminal encoding (e.g., `"utf-8"`)
- `encoding_supported` (bool, required): Whether terminal supports Unicode

**Relationships**:

- One LocaleContext exists per CLI session (singleton pattern)
- One LocaleContext references one active Language
- One LocaleContext uses one TranslationCatalog

**Validation Rules**:

- `active_locale` must be in `fallback_chain`
- `fallback_chain` must end with `"en_US"` (final fallback)
- `translator` must be callable and return strings
- `encoding` must be valid Python codec name

**State Transitions**:

- `initializing`: Environment variable read, locale determined
- `loading`: Translation catalog being loaded
- `loaded`: Catalog loaded successfully, ready for use
- `fallback`: Catalog load failed, using English fallback
- `error`: Critical failure, using NullTranslations

### 5. TranslationKey

Unique identifier for each translatable message in the system, with metadata for context.

**Attributes**:

- `key` (string, required): Unique message identifier (e.g., `"cli.init.success"`)
- `msgid` (string, required): Original English message text (e.g., `"Project ready."`)
- `context` (string, optional): Translation context for disambiguating (e.g., `"CLI output"`)
- `source_location` (string, required): File and line where message appears (e.g., `"__init__.py:1234"`)
- `comment` (string, optional): Translator comment explaining usage (e.g., `"Shown after successful init"`)
- `is_plural` (bool, required): Whether message has plural forms
- `variables` (list, optional): Named variables used in message (e.g., `["name", "count"]`)

**Relationships**:

- One TranslationKey exists per unique message across all languages
- One TranslationKey maps to N translations (one per language)
- Many TranslationKeys belong to one TranslationCatalog

**Validation Rules**:

- `key` must be unique within catalog domain
- `msgid` must not be empty
- `variables` must use named format (`{name}`, not positional)
- If `is_plural`, must have both singular and plural `msgid`
- `source_location` should point to actual code location

**State Transitions**:

- `extracted`: Found by `pybabel extract`, in POT file
- `initialized`: Added to PO file, awaiting translation
- `translated`: Translation provided by translator
- `fuzzy`: Marked by translator as needing review
- `approved`: Translation reviewed and approved

## Entity Relationships Diagram

```text
Language (1) ──── (1) TranslationCatalog
    │                       │
    │                       └── (N) TranslationKey
    │
    └──── (0..1) TemplateSet
              │
              └── (N) Template Files

LocaleContext (1) ──── (1) Language
              │
              └──── (1) TranslationCatalog
```text

## Data Storage

### Translation Catalogs (Filesystem)

**Location**: `src/specify_cli/i18n/<locale>/LC_MESSAGES/`

**Files**:

- `specify.po`: Human-editable translation source file (tracked in git)
- `specify.mo`: Compiled binary translation file (generated, included in package)

**Format**: Standard gettext PO/MO format

**Example PO file**:

```po
# Chinese (Simplified) translations for Specify CLI
# Copyright (C) 2026
msgid ""
msgstr ""
"Project-Id-Version: specify-cli 0.0.23\n"
"Language: zh_CN\n"
"Plural-Forms: nplurals=1; plural=0;\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"

#: src/specify_cli/__init__.py:1234
msgid "Project ready."
msgstr "项目已就绪。"

#: src/specify_cli/__init__.py:1245
#, python-format
msgid "Initialized project '{name}'"
msgstr "已初始化项目 '{name}'"
```text

### Localized Templates (Filesystem)

**Location**: `templates/i18n/<locale>/`

**Structure**: Mirrors main templates directory

```text
templates/i18n/zh_CN/
├── spec-template.md
├── plan-template.md
├── tasks-template.md
├── checklist-template.md
├── agent-file-template.md
└── commands/
    ├── analyze.md
    ├── checklist.md
    ├── clarify.md
    ├── constitution.md
    ├── implement.md
    ├── plan.md
    ├── specify.md
    ├── tasks.md
    └── taskstoissues.md
```text

**Format**: Markdown with preserved placeholders

### Runtime Configuration (Environment Variable)

**Variable**: `SPECIFY_LANG`
**Format**: `language_COUNTRY` (e.g., `zh_CN`, `en_US`)
**Default**: `en_US`
**Validation**: Must match one of supported locale codes

### Metadata (Code Constants)

**Location**: `src/specify_cli/i18n/core.py`

```python
SUPPORTED_LANGUAGES = {
    'en_US': Language(
        code='en_US',
        display_name='English (US)',
        fallback=None,
        catalog_path=Path(__file__).parent / 'en_US',
        plural_forms='nplurals=2; plural=(n != 1);'
    ),
    'zh_CN': Language(
        code='zh_CN',
        display_name='简体中文',
        fallback='en_US',
        catalog_path=Path(__file__).parent / 'zh_CN',
        template_dir=Path(__file__).parent.parent.parent / 'templates' / 'i18n' / 'zh_CN',
        plural_forms='nplurals=1; plural=0;'
    ),
}
```text

## Implementation Notes

### Language Detection

```python
def get_active_locale() -> str:
    """Detect active locale from environment."""
    locale = os.getenv('SPECIFY_LANG', 'en_US')
    
    # Validate against supported languages
    if locale not in SUPPORTED_LANGUAGES:
        console.print(f"[yellow]Warning:[/yellow] Unsupported locale '{locale}', using English")
        return 'en_US'
    
    return locale
```text

### Translation Loading

```python
def load_translation_catalog(locale: str) -> gettext.GNUTranslations:
    """Load translation catalog with fallback."""
    lang = SUPPORTED_LANGUAGES[locale]
    
    try:
        return gettext.translation(
            'specify',
            localedir=str(lang.catalog_path.parent),
            languages=[locale, lang.fallback] if lang.fallback else [locale],
            fallback=True
        )
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Failed to load translations: {e}")
        # Return NullTranslations (identity function)
        return gettext.NullTranslations()
```text

### Template Selection

```python
def get_template_path(template_name: str, locale: str) -> Path:
    """Get localized template path with fallback."""
    lang = SUPPORTED_LANGUAGES.get(locale)
    
    # Try localized template
    if lang and lang.template_dir:
        localized_path = lang.template_dir / template_name
        if localized_path.exists():
            return localized_path
    
    # Fallback to English
    base_dir = Path(__file__).parent.parent / 'templates'
    return base_dir / template_name
```text

## Extensibility

### Adding New Languages

1. Add language entry to `SUPPORTED_LANGUAGES` dict
2. Create directory: `src/specify_cli/i18n/<new_locale>/LC_MESSAGES/`
3. Initialize PO file: `pybabel init -i messages.pot -d src/specify_cli/i18n -l <new_locale>`
4. Translate messages in PO file
5. Create template directory: `templates/i18n/<new_locale>/`
6. Translate and copy all template files
7. Compile: `pybabel compile -d src/specify_cli/i18n`
8. Test: `SPECIFY_LANG=<new_locale> specify <command>`
9. Update documentation with new language

### Adding New Messages

1. Mark string as translatable: `_("New message")`
2. Extract: `pybabel extract -F babel.cfg -k _ -o messages.pot src/`
3. Update catalogs: `pybabel update -i messages.pot -d src/specify_cli/i18n`
4. Translators update PO files
5. Compile: `pybabel compile -d src/specify_cli/i18n`
6. Test in all languages

### Adding New Templates

1. Create English template in `templates/`
2. For each supported language:
   a. Copy template to `templates/i18n/<locale>/`
   b. Translate instructional text
   c. Preserve all placeholders exactly
3. Update template selection logic if needed
4. Test template generation in all languages
