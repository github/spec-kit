#!/usr/bin/env bash
# Incrementally update agent context files based on new feature plan
# Supports: CLAUDE.md, GEMINI.md, and .github/copilot-instructions.md
# O(1) operation - only reads current context file and new plan.md

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
FEATURE_DIR="$REPO_ROOT/specs/$CURRENT_BRANCH"
NEW_PLAN="$FEATURE_DIR/plan.md"

# Determine which agent context files to update
CLAUDE_FILE="$REPO_ROOT/CLAUDE.md"
GEMINI_FILE="$REPO_ROOT/GEMINI.md"
COPILOT_FILE="$REPO_ROOT/.github/copilot-instructions.md"

# Allow override via argument
AGENT_TYPE="$1"

if [ ! -f "$NEW_PLAN" ]; then
    echo "ERROR: No plan.md found at $NEW_PLAN"
    exit 1
fi

echo "=== Updating agent context files for feature $CURRENT_BRANCH ==="

# Extract tech from new plan
# Function to extract a field from plan.md
extract_field() {
    local field="$1"
    local plan_file="$2"
    local value
    value=$(grep "^\\*\\*${field}\\*\\*: " "$plan_file" 2>/dev/null | head -1 | sed "s|^\\*\\*${field}\\*\\*: ||")
    # Filter out "NEEDS CLARIFICATION" for all except Project Type
    if [[ "$field" == "Storage" ]]; then
        value=$(echo "$value" | grep -v "N/A" | grep -v "NEEDS CLARIFICATION")
    elif [[ "$field" == "Language/Version" || "$field" == "Primary Dependencies" || "$field" == "Testing" ]]; then
        value=$(echo "$value" | grep -v "NEEDS CLARIFICATION")
    fi
    echo "${value:-}"
}

NEW_LANG=$(extract_field "Language/Version" "$NEW_PLAN")
NEW_FRAMEWORK=$(extract_field "Primary Dependencies" "$NEW_PLAN")
NEW_TESTING=$(extract_field "Testing" "$NEW_PLAN")
NEW_DB=$(extract_field "Storage" "$NEW_PLAN")
NEW_PROJECT_TYPE=$(extract_field "Project Type" "$NEW_PLAN")
# Function to update a single agent context file
update_agent_file() {
    local target_file="$1"
    local agent_name="$2"
    
    echo "Updating $agent_name context file: $target_file"
    
    # Create temp file for new context
    local temp_file=$(mktemp)
    
    # If file doesn't exist, create from template
    if [ ! -f "$target_file" ]; then
        echo "Creating new $agent_name context file..."
        
        # Check if this is the SDD repo itself
        if [ -f "$REPO_ROOT/templates/agent-file-template.md" ]; then
            cp "$REPO_ROOT/templates/agent-file-template.md" "$temp_file"
        else
            echo "ERROR: Template not found at $REPO_ROOT/templates/agent-file-template.md"
            return 1
        fi
        
        # Replace placeholders
        sed -i.bak "s/\\[PROJECT NAME\\]/$(basename $REPO_ROOT)/" "$temp_file"
        sed -i.bak "s/\\[DATE\\]/$(date +%Y-%m-%d)/" "$temp_file"
        sed -i.bak "s/\\[EXTRACTED FROM ALL PLAN.MD FILES\\]/- $NEW_LANG + $NEW_FRAMEWORK ($CURRENT_BRANCH)/" "$temp_file"
        
        # Add project structure based on type
        if [[ "$NEW_PROJECT_TYPE" == *"web"* ]]; then
            sed -i.bak "s|\\[ACTUAL STRUCTURE FROM PLANS\\]|backend/\nfrontend/\ntests/|" "$temp_file"
        else
            sed -i.bak "s|\\[ACTUAL STRUCTURE FROM PLANS\\]|src/\ntests/|" "$temp_file"
        fi
        
        # Add minimal commands
        if [[ "$NEW_LANG" == *"Python"* ]]; then
            COMMANDS="cd src && pytest && ruff check ."
        elif [[ "$NEW_LANG" == *"Rust"* ]]; then
            COMMANDS="cargo test && cargo clippy"
        elif [[ "$NEW_LANG" == *"JavaScript"* ]] || [[ "$NEW_LANG" == *"TypeScript"* ]]; then
            COMMANDS="npm test && npm run lint"
        else
            COMMANDS="# Add commands for $NEW_LANG"
        fi
        sed -i.bak "s|\\[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES\\]|$COMMANDS|" "$temp_file"
        
        # Add code style
        sed -i.bak "s|\\[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE\\]|$NEW_LANG: Follow standard conventions|" "$temp_file"
        
        # Add recent changes
        sed -i.bak "s|\\[LAST 3 FEATURES AND WHAT THEY ADDED\\]|- $CURRENT_BRANCH: Added $NEW_LANG + $NEW_FRAMEWORK|" "$temp_file"
        
        rm "$temp_file.bak"
    else
        echo "Updating existing $agent_name context file..."
        
        # Extract manual additions
        local manual_start=$(grep -n "<!-- MANUAL ADDITIONS START -->" "$target_file" | cut -d: -f1)
        local manual_end=$(grep -n "<!-- MANUAL ADDITIONS END -->" "$target_file" | cut -d: -f1)
        
        if [ ! -z "$manual_start" ] && [ ! -z "$manual_end" ]; then
            sed -n "${manual_start},${manual_end}p" "$target_file" > /tmp/manual_additions.txt
        fi
        
        # Export variables for Python script
        export TARGET_FILE="$target_file"
        export NEW_LANG="$NEW_LANG"
        export NEW_FRAMEWORK="$NEW_FRAMEWORK"
        export NEW_DB="$NEW_DB"
        export CURRENT_BRANCH="$CURRENT_BRANCH"
        export NEW_PROJECT_TYPE="$NEW_PROJECT_TYPE"
        export TEMP_FILE="$temp_file"
        
        # Parse existing file and create updated version
        python3 - << 'EOF'
import re
import sys
import os
from datetime import datetime

# Get environment variables from bash
target_file = os.environ.get('TARGET_FILE', '')
new_lang = os.environ.get('NEW_LANG', '')
new_framework = os.environ.get('NEW_FRAMEWORK', '')
new_db = os.environ.get('NEW_DB', '')
current_branch = os.environ.get('CURRENT_BRANCH', '')
new_project_type = os.environ.get('NEW_PROJECT_TYPE', '')
temp_file = os.environ.get('TEMP_FILE', '')

# Read existing file
with open(target_file, 'r') as f:
    content = f.read()

# Check if new tech already exists
tech_section = re.search(r'## Active Technologies\n(.*?)\n\n', content, re.DOTALL)
if tech_section:
    existing_tech = tech_section.group(1)
    
    # Add new tech if not already present
    new_additions = []
    if new_lang and new_lang not in existing_tech:
        new_additions.append(f"- {new_lang} + {new_framework} ({current_branch})")
    if new_db and new_db not in existing_tech and new_db != "N/A":
        new_additions.append(f"- {new_db} ({current_branch})")
    
    if new_additions:
        updated_tech = existing_tech + "\n" + "\n".join(new_additions)
        content = content.replace(tech_section.group(0), f"## Active Technologies\n{updated_tech}\n\n")

# Update project structure if needed
if new_project_type == "web" and "frontend/" not in content:
    struct_section = re.search(r'## Project Structure\n```\n(.*?)\n```', content, re.DOTALL)
    if struct_section:
        updated_struct = struct_section.group(1) + "\nfrontend/src/      # Web UI"
        content = re.sub(r'(## Project Structure\n```\n).*?(\n```)', 
                        f'\\1{updated_struct}\\2', content, flags=re.DOTALL)

# Add new commands if language is new
if new_lang and new_lang not in content:
    commands_section = re.search(r'## Commands\n```bash\n(.*?)\n```', content, re.DOTALL)
    if not commands_section:
        commands_section = re.search(r'## Commands\n(.*?)\n\n', content, re.DOTALL)
    
    if commands_section:
        new_commands = commands_section.group(1)
        if "Python" in new_lang:
            new_commands += "\ncd src && pytest && ruff check ."
        elif "Rust" in new_lang:
            new_commands += "\ncargo test && cargo clippy"
        elif "JavaScript" in new_lang or "TypeScript" in new_lang:
            new_commands += "\nnpm test && npm run lint"
        
        if "```bash" in content:
            content = re.sub(r'(## Commands\n```bash\n).*?(\n```)', 
                            f'\\1{new_commands}\\2', content, flags=re.DOTALL)
        else:
            content = re.sub(r'(## Commands\n).*?(\n\n)', 
                            f'\\1{new_commands}\\2', content, flags=re.DOTALL)

# Update recent changes (keep only last 3)
changes_section = re.search(r'## Recent Changes\n(.*?)(\n\n|$)', content, re.DOTALL)
if changes_section:
    changes = changes_section.group(1).strip().split('\n')
    changes.insert(0, f"- {current_branch}: Added {new_lang} + {new_framework}")
    # Keep only last 3
    changes = changes[:3]
    content = re.sub(r'(## Recent Changes\n).*?(\n\n|$)', 
                    f'\\1{chr(10).join(changes)}\\2', content, flags=re.DOTALL)

# Update date
content = re.sub(r'Last updated: \d{4}-\d{2}-\d{2}', 
                f'Last updated: {datetime.now().strftime("%Y-%m-%d")}', content)

# Write to temp file
with open(temp_file, 'w') as f:
    f.write(content)
EOF

        # Restore manual additions if they exist
        if [ -f /tmp/manual_additions.txt ]; then
            # Remove old manual section from temp file
            sed -i.bak '/<!-- MANUAL ADDITIONS START -->/,/<!-- MANUAL ADDITIONS END -->/d' "$temp_file"
            # Append manual additions
            cat /tmp/manual_additions.txt >> "$temp_file"
            rm /tmp/manual_additions.txt "$temp_file.bak"
        fi
    fi
    
    # Move temp file to final location
    mv "$temp_file" "$target_file"
    echo "✅ $agent_name context file updated successfully"
}

# Update files based on argument or detect existing files
case "$AGENT_TYPE" in
    "claude")
        update_agent_file "$CLAUDE_FILE" "Claude Code"
        ;;
    "gemini") 
        update_agent_file "$GEMINI_FILE" "Gemini CLI"
        ;;
    "copilot")
        update_agent_file "$COPILOT_FILE" "GitHub Copilot"
        ;;
    "")
        # Update all existing files
        [ -f "$CLAUDE_FILE" ] && update_agent_file "$CLAUDE_FILE" "Claude Code"
        [ -f "$GEMINI_FILE" ] && update_agent_file "$GEMINI_FILE" "Gemini CLI" 
        [ -f "$COPILOT_FILE" ] && update_agent_file "$COPILOT_FILE" "GitHub Copilot"
        
        # If no files exist, create based on current directory or ask user
        if [ ! -f "$CLAUDE_FILE" ] && [ ! -f "$GEMINI_FILE" ] && [ ! -f "$COPILOT_FILE" ]; then
            echo "No agent context files found. Creating Claude Code context file by default."
            update_agent_file "$CLAUDE_FILE" "Claude Code"
        fi
        ;;
    *)
        echo "ERROR: Unknown agent type '$AGENT_TYPE'. Use: claude, gemini, copilot, or leave empty for all."
        exit 1
        ;;
esac
echo ""
echo "Summary of changes:"
if [ ! -z "$NEW_LANG" ]; then
    echo "- Added language: $NEW_LANG"
fi
if [ ! -z "$NEW_FRAMEWORK" ]; then
    echo "- Added framework: $NEW_FRAMEWORK"
fi
if [ ! -z "$NEW_DB" ] && [ "$NEW_DB" != "N/A" ]; then
    echo "- Added database: $NEW_DB"
fi

echo ""
echo "Usage: $0 [claude|gemini|copilot]"
echo "  - No argument: Update all existing agent context files"
echo "  - claude: Update only CLAUDE.md"
echo "  - gemini: Update only GEMINI.md" 
echo "  - copilot: Update only .github/copilot-instructions.md"