# Quickstart Guide: Using I18n in Specify CLI

**Feature**: Internationalization Support  
**Audience**: Developers and Users  
**Last Updated**: 2026-01-26

## For Users: Using Specify CLI in Chinese

### 1. Set Your Language Preference

#### Option A: Use --lang Flag (Recommended)

Pass `--lang zh_CN` to any command:

```bash
# View help in Chinese
specify --lang zh_CN --help

# Initialize project with Chinese output
specify --lang zh_CN init my-project

# Check prerequisites in Chinese
specify --lang zh_CN check
```

#### Option B: Set Environment Variable (Persistent Default)

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, or `~/.profile`):

```bash
export SPECIFY_LANG=zh_CN
```

Or set for a single session:

```bash
# Bash/Zsh
export SPECIFY_LANG=zh_CN

# Windows PowerShell
$env:SPECIFY_LANG = "zh_CN"

# Windows CMD
set SPECIFY_LANG=zh_CN
```

**Priority Order:**

1. `--lang` CLI argument (highest priority) - overrides everything
2. `SPECIFY_LANG` environment variable - persistent default
3. English (en_US) - fallback default

### 2. Use Specify CLI Normally

All commands will now display in Chinese:

```bash
# Help text in Chinese
specify --help

# Initialize project in Chinese
specify init my-project --ai claude

# Check tools in Chinese
specify check
```

### 3. Switch Back to English

```bash
unset SPECIFY_LANG   # Bash/Zsh
$env:SPECIFY_LANG = ""  # PowerShell
set SPECIFY_LANG=    # CMD
```

### 4. Supported Languages

| Code | Language | Status |
| ------ | ---------- | -------- |
| `en_US` | English (US) | ✅ Default |
| `zh_CN` | 简体中文 (Simplified Chinese) | ✅ Complete |

### 5. Troubleshooting

**Chinese characters not displaying?**

- **Windows CMD**: Run `chcp 65001` to enable UTF-8
- **Windows PowerShell**: Should work by default
- **Windows Terminal**: Should work by default
- **macOS/Linux**: Should work by default (UTF-8)

**Mixed English/Chinese output?**

- Check `SPECIFY_LANG` is set: `echo $SPECIFY_LANG`
- Ensure value is exactly `zh_CN` (case-sensitive)
- Try restarting your terminal

**Fallback to English?**

- Translation missing: Will show English for untranslated messages
- Invalid locale: Check for typos in environment variable
- Catalog not found: Reinstall Specify CLI

---

## For Developers: Adding Translatable Messages

### 1. Mark Strings as Translatable

```python
from gettext import gettext as _

# Simple message
console.print(_("Project ready."))

# Message with variables (ALWAYS use named arguments)
console.print(_("Initialized project '{name}'").format(name=project_name))

# Plural forms
from gettext import ngettext
msg = ngettext(
    "{count} file created",
    "{count} files created",
    count
).format(count=count)
```

### 2. Extract Messages

```bash
cd /path/to/spec-kit
pybabel extract -F babel.cfg -k _ -o messages.pot src/
```

### 3. Update Translation Catalogs

```bash
pybabel update -i messages.pot -d src/specify_cli/i18n
```

This updates `src/specify_cli/i18n/*/LC_MESSAGES/specify.po` with new messages.

### 4. Compile Translations

```bash
pybabel compile -d src/specify_cli/i18n
```

This generates `.mo` files from `.po` files.

### 5. Test Your Changes

```bash
# Test in Chinese
SPECIFY_LANG=zh_CN specify <your-command>

# Test in English (default)
unset SPECIFY_LANG
specify <your-command>
```

### 6. Important Patterns

#### ✅ DO

```python
# Named arguments
_("Project '{name}' initialized").format(name=project)

# Plural forms
ngettext("{count} file", "{count} files", n).format(count=n)

# Rich markup preserved
_("[green]Success:[/green] Created {count} files").format(count=n)
```

#### ❌ DON'T

```python
# F-strings (can't be extracted)
_(f"Project {name} initialized")

# Positional arguments (breaks translations)
_("Project '{}' initialized").format(project)

# String concatenation
_("Project ") + name + _(" initialized")
```

---

## For Translators: Adding Chinese Translations

### 1. Open the PO File

```bash
# Use text editor
vim src/specify_cli/i18n/zh_CN/LC_MESSAGES/specify.po

# Or use Poedit (GUI)
poedit src/specify_cli/i18n/zh_CN/LC_MESSAGES/specify.po
```

### 2. Find Untranslated Messages

Look for entries with empty `msgstr`:

```po
#: src/specify_cli/__init__.py:1234
msgid "Project ready."
msgstr ""
```

### 3. Add Translation

```po
#: src/specify_cli/__init__.py:1234
msgid "Project ready."
msgstr "项目已就绪。"
```

### 4. Handle Variables

Variables in `{curly braces}` must be preserved:

```po
#: src/specify_cli/__init__.py:1245
#, python-format
msgid "Initialized project '{name}'"
msgstr "已初始化项目 '{name}'"
```

**Note**: You can reorder variables if Chinese grammar requires it:

```po
msgid "Found {count} files in '{directory}'"
msgstr "在 '{directory}' 中找到 {count} 个文件"
```

### 5. Handle Plural Forms

Chinese has only one plural form:

```po
#: src/specify_cli/__init__.py:1256
msgid "{count} file created"
msgid_plural "{count} files created"
msgstr[0] "已创建 {count} 个文件"
```

### 6. Save and Ask Developer to Compile

After saving `specify.po`, ask a developer to run:

```bash
pybabel compile -d src/specify_cli/i18n
```

Or if you have Python/Babel installed:

```bash
cd /path/to/spec-kit
pybabel compile -d src/specify_cli/i18n
```

### 7. Translation Guidelines

#### Technical Terms

- **Specify CLI**: 保持英文 "Specify CLI" 或翻译为 "Specify 命令行工具"
- **template**: 模板
- **specification**: 规格 或 规范
- **feature**: 功能
- **branch**: 分支
- **repository**: 仓库
- **commit**: 提交

#### Tone

- **Formal but friendly**: Use polite Chinese, avoid overly casual language
- **Clear and concise**: Chinese can be more concise than English
- **Consistent terminology**: Use the same translation for repeated terms

#### Formatting

- **Preserve Rich markup**: `[green]Success:[/green]` → `[green]成功：[/green]`
- **Preserve placeholders**: `{name}`, `{count}`, etc. must stay in English
- **Punctuation**: Use Chinese punctuation (，。！？) in Chinese text

### 8. Testing Your Translations

```bash
SPECIFY_LANG=zh_CN specify --help
SPECIFY_LANG=zh_CN specify init test-project --ai claude
SPECIFY_LANG=zh_CN specify check
```

---

## For Template Translators: Localizing Templates

### 1. Template Location

English templates: `templates/`
Chinese templates: `templates/i18n/zh_CN/`

### 2. Translate a Template

```bash
# Copy English template
cp templates/spec-template.md templates/i18n/zh_CN/spec-template.md

# Edit Chinese version
vim templates/i18n/zh_CN/spec-template.md
```

### 3. Translation Rules

#### ✅ DO Translate

- Section headings
- Instructional comments
- Examples and descriptions
- Inline documentation

#### ❌ DON'T Translate

- Placeholders: `[FEATURE_NAME]`, `[PROJECT_NAME]`, etc.
- Code examples (keep technical)
- URLs and links
- Command syntax: `/speckit.specify`, `specify init`, etc.

### 4. Example: Spec Template

**English** (`templates/spec-template.md`):

```markdown
# Feature Specification: [FEATURE_NAME]

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys...
-->

### User Story 1 - [Brief Title] (Priority: P1)

[Describe this user journey in plain language]
```

**Chinese** (`templates/i18n/zh_CN/spec-template.md`):

```markdown
# 功能规格： [FEATURE_NAME]

## 用户场景与测试 *(必填)*

<!--
  重要提示：用户故事应按照用户旅程的重要性排序...
-->

### 用户故事 1 - [简短标题] (优先级: P1)

[用简单的语言描述此用户旅程]
```

### 5. Verify Placeholders Match

After translation, check that all `[PLACEHOLDERS]` are identical:

```bash
# Extract English placeholders
grep -o '\[.*\]' templates/spec-template.md | sort | uniq > en-placeholders.txt

# Extract Chinese placeholders
grep -o '\[.*\]' templates/i18n/zh_CN/spec-template.md | sort | uniq > zh-placeholders.txt

# Compare
diff en-placeholders.txt zh-placeholders.txt
```

Should show no differences.

### 6. Test Template Generation

```bash
# Initialize project with Chinese locale
SPECIFY_LANG=zh_CN specify init test-project --ai claude

# Check generated templates
cat test-project/.specify/templates/spec-template.md
```

---

## For Maintainers: I18n Workflow

### Adding a New Language

```bash
# 1. Extract current messages
pybabel extract -F babel.cfg -k _ -o messages.pot src/

# 2. Initialize new language
pybabel init -i messages.pot -d src/specify_cli/i18n -l fr_FR

# 3. Create template directory
mkdir -p templates/i18n/fr_FR/commands

# 4. Add language to SUPPORTED_LANGUAGES in src/specify_cli/i18n/core.py

# 5. Translators work on PO files and templates

# 6. Compile translations
pybabel compile -d src/specify_cli/i18n

# 7. Test
SPECIFY_LANG=fr_FR specify --help
```

### Updating Translations After Code Changes

```bash
# 1. Extract new/changed messages
pybabel extract -F babel.cfg -k _ -o messages.pot src/

# 2. Update all language catalogs
pybabel update -i messages.pot -d src/specify_cli/i18n

# 3. Notify translators to update PO files

# 4. After translation, compile
pybabel compile -d src/specify_cli/i18n
```

### Checking Translation Coverage

```bash
# Check for untranslated messages
msgfmt --statistics src/specify_cli/i18n/zh_CN/LC_MESSAGES/specify.po
```

Output: `X translated messages, Y fuzzy translations, Z untranslated messages.`

Target: `0 fuzzy, 0 untranslated` before release.

### CI/CD Integration

```yaml
# .github/workflows/i18n-check.yml
name: I18n Check

on: [pull_request]

jobs:
  translation-coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install Babel
        run: pip install babel
      - name: Check translation completeness
        run: |
          for po in src/specify_cli/i18n/*/LC_MESSAGES/specify.po; do
            echo "Checking $po..."
            msgfmt --statistics --check $po 2>&1 | tee /dev/stderr | grep -q "0 untranslated"
          done
```

---

## Quick Reference

### Environment Variables

- `SPECIFY_LANG`: Set user language (`en_US`, `zh_CN`)

### Developer Commands

- `pybabel extract`: Extract translatable strings
- `pybabel init`: Initialize new language
- `pybabel update`: Update existing translations
- `pybabel compile`: Compile PO to MO files

### Files

- `babel.cfg`: Extraction configuration
- `messages.pot`: Translation template
- `*.po`: Human-editable translations
- `*.mo`: Compiled binary translations

### Translation Markers

- `_(...)`: Mark string as translatable
- `ngettext(...)`: Plural forms
- `{name}`: Named variable placeholder

### Testing

- `SPECIFY_LANG=zh_CN specify <command>`: Test Chinese
- `unset SPECIFY_LANG`: Test English (default)

---

## Resources

- **Babel Documentation**: <https://babel.pocoo.org/>
- **Python gettext**: <https://docs.python.org/3/library/gettext.html>
- **Poedit (GUI editor)**: <https://poedit.net/>
- **PO file format**: <https://www.gnu.org/software/gettext/manual/html_node/PO-Files.html>

---

## Getting Help

- **Translation issues**: Open issue with `i18n` label
- **Missing translations**: Check `specify.po` file
- **Display issues**: Check terminal UTF-8 support
- **Questions**: See README.md or CONTRIBUTING.md
