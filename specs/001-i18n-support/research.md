# Research Document: I18n Implementation

**Feature**: Internationalization Support for Specify CLI  
**Date**: 2026-01-26  
**Status**: Complete

## Technology Decisions

### Decision 1: Babel + Python gettext for I18n Framework

**What was chosen**: Use Babel (`babel>=2.12.0,<3.0.0`) for extraction/compilation tooling, with Python's built-in `gettext` module for runtime translation.

**Rationale**:

- **Cross-platform**: Babel works on Windows, macOS, Linux without external GNU gettext tools
- **Pure Python**: No system dependencies, easier installation
- **Modern tooling**: `pybabel` CLI provides complete workflow (`extract`, `init`, `update`, `compile`)
- **Runtime efficiency**: Python's `gettext` is lightweight with <10ms catalog load, <1μs message lookup
- **Industry standard**: Widely used, well-documented, proven in production

**Alternatives considered**:

1. **GNU gettext alone**: Requires system tools (xgettext, msgmerge) which are problematic on Windows
2. **fluent-python**: Modern alternative but less mature ecosystem, would be over-engineering
3. **Custom i18n**: Violates YAGNI principle, reinventing the wheel

**Implementation impact**:

- Add `babel` to `pyproject.toml` dependencies
- Create `babel.cfg` configuration file
- Use standard PO/MO file workflow
- No runtime dependencies beyond stdlib gettext

### Decision 2: CLI Argument + Environment Variable for Language Selection

**What was chosen**: Use `--lang` CLI argument as primary method, with `SPECIFY_LANG` environment variable as fallback.

**Rationale**:

- **Discoverability**: `--lang` appears in `--help` output, making feature obvious to users
- **Flexibility**: Users can override persistent settings on a per-command basis
- **Standard CLI practice**: Most tools support language via flags (e.g., `--locale`, `--language`)
- **Environment variable fallback**: Still supports persistent defaults and CI/CD automation
- **Priority order**: CLI arg > env var > default (en_US) provides maximum flexibility

**Implementation**:

```python
def get_active_locale(cli_lang: Optional[str] = None) -> str:
    # Priority: CLI argument > environment variable > default
    return cli_lang or os.getenv("SPECIFY_LANG", "en_US")
```

**Alternatives considered**:

1. **Environment variable only**: Less discoverable, users may not know about feature
2. **CLI flag only**: Tedious for users who want persistent default
3. **Config file**: Over-engineering for simple preference, violates YAGNI
4. **Auto-detection from system locale**: Could cause confusion if system locale doesn't match preference

**Implementation impact**:

- Add `--lang` option to main `callback()` function (global option for all commands)
- Re-initialize i18n in callback with CLI argument
- Fall back to `SPECIFY_LANG` if `--lang` not provided
- Warn users if invalid locale provided

### Decision 3: Separate Localized Template Files

**What was chosen**: Store localized templates in `templates/i18n/<lang>/` as separate files mirroring the main templates structure.

**Rationale**:

- **Simplicity**: No template engine complexity, direct file copying
- **Maintainability**: Easy to see what's translated, diff-friendly
- **Preservation of placeholders**: `[FEATURE_NAME]` etc. stay identical across languages
- **Git-friendly**: Each language is a separate file, no merge conflicts
- **Performance**: No runtime template rendering overhead

**Alternatives considered**:

1. **Jinja2 with i18n extension**: Over-engineering, adds dependency and complexity
2. **Inline translations in single file**: Makes diffs hard to read, error-prone
3. **Markdown i18n libraries**: None are well-maintained or fit the use case

**Implementation impact**:

- Create `templates/i18n/zh_CN/` directory structure
- Copy and translate all template files manually
- Update `init()` command to select templates based on locale
- Fallback to English templates if localized version missing

### Decision 4: Named Arguments for Variable Interpolation

**What was chosen**: Use `.format()` with named arguments (`{name}`, `{count}`) for all translatable messages with variables.

**Rationale**:

- **Reordering freedom**: Chinese grammar may require different word order than English
- **Translator context**: Parameter names (`{filename}`, `{count}`) explain meaning
- **Babel compatibility**: Extraction works correctly with named arguments
- **Future-proofing**: Supports languages with complex grammar rules

**Alternatives considered**:

1. **Positional f-strings**: Cannot be extracted by Babel, breaks with reordered translations
2. **Old-style `%(name)s`**: Works but less readable than `.format()`
3. **Positional `.format()`**: Breaks when translators reorder variables

**Implementation impact**:

- Audit all CLI messages and convert to named arguments
- Pattern: `_("Message '{name}'").format(name=value)`
- Avoid f-strings for translatable text
- Document this pattern for contributors

### Decision 5: PO/MO File Organization

**What was chosen**: Standard gettext directory structure: `src/specify_cli/i18n/<locale>/LC_MESSAGES/specify.{po,mo}`.

**Rationale**:

- **Standard convention**: Matches what gettext expects, works out of the box
- **Tool compatibility**: PO editors (Poedit, Lokalize) understand this structure
- **Build integration**: Babel's `compile` command expects this layout
- **Multiple domains**: Allows future split into multiple catalogs if needed (CLI, templates, docs)

**Alternatives considered**:

1. **Flat structure** (`i18n/zh_CN.po`): Non-standard, harder to extend
2. **Per-module catalogs**: Over-engineering for small CLI, harder to maintain

**Implementation impact**:

- Create directory structure: `src/specify_cli/i18n/{en_US,zh_CN}/LC_MESSAGES/`
- Domain name: `specify`
- Catalog files: `specify.po` (source), `specify.mo` (compiled)
- Include `.mo` files in package distribution

### Decision 6: Chinese Pluralization Handling

**What was chosen**: Use `ngettext()` for consistency even though Chinese has only one plural form.

**Rationale**:

- **Consistency**: Same code works for English and Chinese
- **Future languages**: If we add languages with plural forms, code already supports it
- **Standard pattern**: Follows gettext best practices
- **Simple Chinese case**: Chinese PO files have `nplurals=1; plural=0;`

**Implementation impact**:

- Use `ngettext(singular, plural, count).format(count=count)` for countable messages
- Chinese translators provide single `msgstr[0]` entry
- English has full `msgstr[0]` and `msgstr[1]`

## Best Practices & Patterns

### Message Extraction Pattern

```python
# Mark translatable strings with _()
from gettext import gettext as _

# Simple message
console.print(_("Project ready."))

# Message with variables (always use named arguments)
console.print(_("Initialized project '{name}'").format(name=project_name))

# Plural forms
msg = ngettext(
    "{count} file created",
    "{count} files created",
    count
).format(count=count)
```

### Template Selection Pattern

```python
def get_template_path(template_name: str, locale: str) -> Path:
    """Get localized template path with fallback to English."""
    base_dir = Path(__file__).parent / 'templates'
    
    # Try localized version
    localized = base_dir / 'i18n' / locale / template_name
    if localized.exists():
        return localized
    
    # Fallback to English
    return base_dir / template_name
```

### Initialization Pattern

```python
def setup_i18n() -> callable:
    """Initialize i18n and return translation function."""
    locale = os.getenv('SPECIFY_LANG', 'en_US')
    locale_dir = Path(__file__).parent / 'i18n'
    
    # Validate locale
    valid_locales = ['en_US', 'zh_CN']
    if locale not in valid_locales:
        console.print(f"[yellow]Warning:[/yellow] Unsupported locale '{locale}', using English")
        locale = 'en_US'
    
    # Load translation catalog with fallback
    t = gettext.translation(
        'specify',
        localedir=str(locale_dir),
        languages=[locale, 'en_US'],
        fallback=True
    )
    
    return t.gettext

# At module level
_ = setup_i18n()
```

## Translation Workflow

### For Developers (Adding New Messages)

1. Mark new strings as translatable: `_("New message")`
2. Extract messages: `pybabel extract -F babel.cfg -k _ -o messages.pot src/`
3. Update catalogs: `pybabel update -i messages.pot -d src/specify_cli/i18n`
4. Translators update PO files
5. Compile: `pybabel compile -d src/specify_cli/i18n`
6. Test with `SPECIFY_LANG=zh_CN specify <command>`

### For Translators (Adding Translations)

1. Open `src/specify_cli/i18n/zh_CN/LC_MESSAGES/specify.po` in text editor or Poedit
2. Find `msgid` entries with empty `msgstr`
3. Add Chinese translation to `msgstr`
4. Save file
5. Developer compiles with `pybabel compile`

### Build Integration

```bash
# Add to CI/CD pipeline
pybabel compile -d src/specify_cli/i18n

# Or add as pre-build hook in pyproject.toml
```

## Performance Considerations

### Startup Performance

- **Catalog loading**: <10ms for typical message catalog
- **One-time cost**: Occurs at CLI startup, amortized over command execution
- **No lazy loading needed**: CLI lifespan is short, eager loading is fine

### Runtime Performance

- **Message lookup**: <1μs (dictionary access after catalog load)
- **Caching**: Python gettext caches automatically
- **No optimization needed**: CLI operations (network, disk I/O) far exceed i18n overhead

### Template Selection

- **File system check**: O(1) file existence check per template
- **Fallback cost**: Negligible (one extra Path.exists() call)
- **No caching needed**: Templates read once per CLI invocation

## Risks & Mitigations

### Risk 1: Incomplete Translations

**Risk**: Chinese translations are incomplete at release, users see mixed English/Chinese.

**Mitigation**:

- Create translation coverage script: `scripts/i18n/check-coverage.sh`
- Add CI check to fail build if coverage < 100% for Chinese
- Fallback to English is graceful (shows original message)
- Block release until Chinese translation is 100% complete

### Risk 2: Terminal Encoding Issues

**Risk**: Old Windows terminals may not display Chinese characters correctly.

**Mitigation**:

- Document UTF-8 terminal requirement in README
- Add terminal encoding detection in CLI startup
- Warn users if terminal doesn't support UTF-8
- Provide troubleshooting guide for Windows (chcp 65001)

### Risk 3: Translation Quality

**Risk**: Automated or poor quality translations confuse Chinese users.

**Mitigation**:

- Require native Chinese speaker review before release
- Document technical terms and their standard Chinese translations
- Provide translation context in PO file comments
- Test with native Chinese-speaking developers

### Risk 4: Template Synchronization

**Risk**: English templates updated but Chinese versions not updated, causing inconsistency.

**Mitigation**:

- Add CI check to compare template structure (placeholders must match)
- Document template update workflow
- Create template diff script to highlight untranslated sections
- Consider automation: script to identify new sections needing translation

## Technical Constraints

### Platform Support

- **Linux**: Full UTF-8 support, no issues expected
- **macOS**: Full UTF-8 support, no issues expected
- **Windows**: UTF-8 support varies by terminal (Windows Terminal ✅, CMD ⚠️, PowerShell ✅)

### Python Version

- **Minimum**: Python 3.11 (as per project requirements)
- **gettext**: Built-in, no version constraint
- **Babel**: `>=2.12.0,<3.0.0` for Python 3.11 compatibility

### External Tools

- **No runtime dependencies**: Uses Python stdlib gettext
- **Build-time only**: Babel for extraction/compilation
- **Optional**: Poedit or similar for translator workflow (not required)

## Testing Strategy

### Unit Tests

1. **Translation loading**: Test catalog loads correctly for en_US and zh_CN
2. **Fallback behavior**: Test fallback to English when translation missing
3. **Invalid locale**: Test warning and fallback when `SPECIFY_LANG=invalid`
4. **Message formatting**: Test named arguments work correctly

### Integration Tests

1. **CLI commands**: Run `specify init`, `specify check` with `SPECIFY_LANG=zh_CN`
2. **Template generation**: Verify Chinese templates are selected and placeholders preserved
3. **Error messages**: Trigger errors and verify Chinese messages displayed
4. **Help text**: Run `specify --help` and verify Chinese output

### Manual Testing

1. **Terminal compatibility**: Test on Windows CMD, PowerShell, Windows Terminal, macOS Terminal, Linux terminals
2. **Character display**: Verify Chinese characters render correctly
3. **User workflow**: Complete full SDD workflow in Chinese
4. **Translation quality**: Native speaker review of all translated content

### CI/CD Checks

1. **Translation completeness**: Fail if Chinese coverage < 100%
2. **Compilation**: Ensure MO files compile without errors
3. **Template structure**: Verify Chinese templates have same placeholders as English
4. **Extraction**: Check no untranslated user-facing strings

## Documentation Requirements

### For Users

1. **README.md** (English): Add "Language Support" section explaining `SPECIFY_LANG`
2. **README.md** (Chinese): Full Chinese translation with installation and usage
3. **docs/quickstart.md** (Chinese): Chinese version of quickstart guide
4. **docs/installation.md** (Chinese): Chinese installation instructions

### For Contributors

1. **CONTRIBUTING.md**: Add "Translations" section with workflow
2. **Translation guide**: How to add new languages
3. **Code patterns**: How to mark strings as translatable
4. **Testing guide**: How to test translations locally

### For Translators

1. **Translation guidelines**: Technical terminology standards
2. **PO file structure**: Explanation of msgid/msgstr
3. **Context comments**: How to interpret message context
4. **Pluralization**: How Chinese plural forms work in gettext

## References

- **Babel documentation**: <https://babel.pocoo.org/>
- **Python gettext documentation**: <https://docs.python.org/3/library/gettext.html>
- **GNU gettext manual**: <https://www.gnu.org/software/gettext/manual/>
- **Chinese localization standards**: GB/T 2312 encoding, Simplified Chinese conventions
- **PO file format**: <https://www.gnu.org/software/gettext/manual/html_node/PO-Files.html>
