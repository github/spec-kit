#!/usr/bin/env python3
"""Update INSTALL_MEMORY.md with SkillsMP step."""

# Read file
with open('docs/INSTALL_MEMORY.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Find insertion point
marker = 'Continuing without agent-memory-mcp (Ollama-only mode).'

if marker not in content:
    print("Marker not found!")
    exit(1)

# New step to insert
new_step = '''

## STEP 7.6: Setup SkillsMP Search (Optional)

**Condition**: Ask user if they want SkillsMP skill search

**Actions**:
1. Ask if user wants SkillsMP integration
2. If yes, request API key
3. Store API key securely
4. Verify API access

**Execute**:
```bash
# Check for existing API key
python -c "
from specify_cli.memory.skillsmp.api_key_storage import APIKeyStorage
storage = APIKeyStorage()
print('API key found' if storage.has_api_key() else 'No API key')
"
```

**Ask user**:

```
SkillsMP provides access to 425K+ agent skills and MCP servers.
This helps find existing solutions before creating new agents.

Options:
1. Enable SkillsMP search (requires API key)
2. Skip (use GitHub fallback only)
3. Decide later

Choose:
```

**If user chooses Enable**:

**Request API key**:

```
SkillsMP API Key Required

To get your API key:
1. Visit: https://skillsmp.com/docs/api
2. Sign up / Login
3. Navigate to API Keys section
4. Generate new API key

Enter your SkillsMP API key (or press Enter to skip):
```

**Store and validate API key**:
```bash
# Python script to store and validate
python -c "
import sys
sys.path.insert(0, 'src')

from specify_cli.memory.skillsmp.api_key_storage import APIKeyStorage
from specify_cli.memory.skillsmp.integration import SkillsMPIntegration

print('Enter SkillsMP API key (or press Enter to skip):')
api_key = input().strip()

if api_key and len(api_key) > 10:
    storage = APIKeyStorage()
    if storage.store_api_key(api_key):
        print('[OK] API key stored securely in system keyring')

        # Validate
        integration = SkillsMPIntegration(api_key=api_key)
        results = integration.search_skills('agent', limit=1)

        if results:
            print('[OK] SkillsMP API working - found', len(results), 'skills')
        else:
            print('[WARNING] API key stored but no results (may be rate limited or invalid)')
    else:
        print('[ERROR] Failed to store API key')
        sys.exit(1)
else:
    print('[SKIP] No API key provided - SkillsMP disabled')
"
```

**If user chooses Skip**:
- Continue without SkillsMP API
- GitHub fallback will be used for skill search
- Note: Limited search capabilities without API

---

'''

# Insert new step after marker
content = content.replace(
    marker + '\n\n---',
    marker + '\n\n' + new_step + '---'
)

# Write back
with open('docs/INSTALL_MEMORY.md', 'w', encoding='utf-8') as f:
    f.write(content)

print('Successfully updated INSTALL_MEMORY.md with SkillsMP step')
