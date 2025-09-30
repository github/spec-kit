#!/usr/bin/env fish

# Update agent context files with information from plan.md
#
# This script maintains AI agent context files by parsing feature specifications 
# and updating agent-specific configuration files with project information.
#
# MAIN FUNCTIONS:
# 1. Environment Validation
#    - Verifies git repository structure and branch information
#    - Checks for required plan.md files and templates
#    - Validates file permissions and accessibility
#
# 2. Plan Data Extraction
#    - Parses plan.md files to extract project metadata
#    - Identifies language/version, frameworks, databases, and project types
#    - Handles missing or incomplete specification data gracefully
#
# 3. Agent File Management
#    - Creates new agent context files from templates when needed
#    - Updates existing agent files with new project information
#    - Preserves manual additions and custom configurations
#    - Supports multiple AI agent formats and directory structures
#
# 4. Content Generation
#    - Generates language-specific build/test commands
#    - Creates appropriate project directory structures
#    - Updates technology stacks and recent changes sections
#    - Maintains consistent formatting and timestamps
#
# 5. Multi-Agent Support
#    - Handles agent-specific file paths and naming conventions
#    - Supports: Claude, Gemini, Copilot, Cursor, Qwen, opencode, Codex, Windsurf
#    - Can update single agents or all existing agent files
#    - Creates default Claude file if no agent files exist
#
# Usage: ./update-agent-context.fish [agent_type]
# Agent types: claude|gemini|copilot|cursor|qwen|opencode|codex|windsurf|kilocode|auggie|roo

#==============================================================================
# Configuration and Global Variables
#==============================================================================

# Get script directory and load common functions
set -l SCRIPT_DIR (dirname (status filename))
source "$SCRIPT_DIR/common.fish"

# Get all paths and variables from common functions
eval (get_feature_paths)

set -g NEW_PLAN "$IMPL_PLAN"  # Alias for compatibility with existing code
set -l AGENT_TYPE $argv[1]

# Agent-specific file paths  
set -g CLAUDE_FILE "$REPO_ROOT/CLAUDE.md"
set -g GEMINI_FILE "$REPO_ROOT/GEMINI.md"
set -g COPILOT_FILE "$REPO_ROOT/.github/copilot-instructions.md"
set -g CURSOR_FILE "$REPO_ROOT/.cursor/rules/specify-rules.mdc"
set -g QWEN_FILE "$REPO_ROOT/QWEN.md"
set -g AGENTS_FILE "$REPO_ROOT/AGENTS.md"
set -g WINDSURF_FILE "$REPO_ROOT/.windsurf/rules/specify-rules.md"
set -g KILOCODE_FILE "$REPO_ROOT/.kilocode/rules/specify-rules.md"
set -g AUGGIE_FILE "$REPO_ROOT/.augment/rules/specify-rules.md"
set -g ROO_FILE "$REPO_ROOT/.roo/rules/specify-rules.md"

# Template file
set -g TEMPLATE_FILE "$REPO_ROOT/.specify/templates/agent-file-template.md"

# Global variables for parsed plan data
set -g NEW_LANG ""
set -g NEW_FRAMEWORK ""
set -g NEW_DB ""
set -g NEW_PROJECT_TYPE ""

#==============================================================================
# Utility Functions
#==============================================================================

function log_info
    echo "INFO: $argv"
end

function log_success
    echo "✓ $argv"
end

function log_error
    echo "ERROR: $argv" >&2
end

function log_warning
    echo "WARNING: $argv" >&2
end

# Cleanup function for temporary files
function cleanup --on-process-exit
    rm -f /tmp/agent_update_*_$fish_pid
    rm -f /tmp/manual_additions_$fish_pid
end

#==============================================================================
# Validation Functions
#==============================================================================

function validate_environment
    # Check if we have a current branch/feature (git or non-git)
    if test -z "$CURRENT_BRANCH"
        log_error "Unable to determine current feature"
        if test "$HAS_GIT" = "true"
            log_info "Make sure you're on a feature branch"
        else
            log_info "Set SPECIFY_FEATURE environment variable or create a feature first"
        end
        exit 1
    end
    
    # Check if plan.md exists
    if not test -f "$NEW_PLAN"
        log_error "No plan.md found at $NEW_PLAN"
        log_info "Make sure you're working on a feature with a corresponding spec directory"
        if test "$HAS_GIT" != "true"
            log_info "Use: export SPECIFY_FEATURE=your-feature-name or create a new feature first"
        end
        exit 1
    end
    
    # Check if template exists (needed for new files)
    if not test -f "$TEMPLATE_FILE"
        log_warning "Template file not found at $TEMPLATE_FILE"
        log_warning "Creating new agent files will fail"
    end
end

#==============================================================================
# Plan Parsing Functions
#==============================================================================

function extract_plan_field
    set -l field_pattern $argv[1]
    set -l plan_file $argv[2]
    
    grep "^\*\*$field_pattern\*\*: " "$plan_file" 2>/dev/null | \
        head -1 | \
        sed "s|^\*\*$field_pattern\*\*: ||" | \
        string trim | \
        grep -v "NEEDS CLARIFICATION" | \
        grep -v "^N/A\$"; or echo ""
end

function parse_plan_data
    set -l plan_file $argv[1]
    
    if not test -f "$plan_file"
        log_error "Plan file not found: $plan_file"
        return 1
    end
    
    if not test -r "$plan_file"
        log_error "Plan file is not readable: $plan_file"
        return 1
    end
    
    log_info "Parsing plan data from $plan_file"
    
    set -g NEW_LANG (extract_plan_field "Language/Version" "$plan_file")
    set -g NEW_FRAMEWORK (extract_plan_field "Primary Dependencies" "$plan_file")
    set -g NEW_DB (extract_plan_field "Storage" "$plan_file")
    set -g NEW_PROJECT_TYPE (extract_plan_field "Project Type" "$plan_file")
    
    # Log what we found
    if test -n "$NEW_LANG"
        log_info "Found language: $NEW_LANG"
    else
        log_warning "No language information found in plan"
    end
    
    if test -n "$NEW_FRAMEWORK"
        log_info "Found framework: $NEW_FRAMEWORK"
    end
    
    if test -n "$NEW_DB"; and test "$NEW_DB" != "N/A"
        log_info "Found database: $NEW_DB"
    end
    
    if test -n "$NEW_PROJECT_TYPE"
        log_info "Found project type: $NEW_PROJECT_TYPE"
    end
end

function format_technology_stack
    set -l lang $argv[1]
    set -l framework $argv[2]
    set -l parts
    
    # Add non-empty parts
    if test -n "$lang"; and test "$lang" != "NEEDS CLARIFICATION"
        set -a parts "$lang"
    end
    if test -n "$framework"; and test "$framework" != "NEEDS CLARIFICATION"; and test "$framework" != "N/A"
        set -a parts "$framework"
    end
    
    # Join with proper formatting
    if test (count $parts) -eq 0
        echo ""
    else if test (count $parts) -eq 1
        echo "$parts[1]"
    else
        # Join multiple parts with " + "
        set -l result "$parts[1]"
        for i in (seq 2 (count $parts))
            set result "$result + $parts[$i]"
        end
        echo "$result"
    end
end

#==============================================================================
# Template and Content Generation Functions
#==============================================================================

function get_project_structure
    set -l project_type $argv[1]
    
    if string match -q '*web*' "$project_type"
        echo "backend/\\nfrontend/\\ntests/"
    else
        echo "src/\\ntests/"
    end
end

function get_commands_for_language
    set -l lang $argv[1]
    
    switch "$lang"
        case '*Python*'
            echo "cd src && pytest && ruff check ."
        case '*Rust*'
            echo "cargo test && cargo clippy"
        case '*JavaScript*' '*TypeScript*'
            echo "npm test && npm run lint"
        case '*'
            echo "# Add commands for $lang"
    end
end

function get_language_conventions
    set -l lang $argv[1]
    echo "$lang: Follow standard conventions"
end

function create_new_agent_file
    set -l target_file $argv[1]
    set -l temp_file $argv[2]
    set -l project_name $argv[3]
    set -l current_date $argv[4]
    
    if not test -f "$TEMPLATE_FILE"
        log_error "Template not found at $TEMPLATE_FILE"
        return 1
    end
    
    if not test -r "$TEMPLATE_FILE"
        log_error "Template file is not readable: $TEMPLATE_FILE"
        return 1
    end
    
    log_info "Creating new agent context file from template..."
    
    if not cp "$TEMPLATE_FILE" "$temp_file"
        log_error "Failed to copy template file"
        return 1
    end
    
    # Replace template placeholders
    set -l project_structure (get_project_structure "$NEW_PROJECT_TYPE")
    set -l commands (get_commands_for_language "$NEW_LANG")
    set -l language_conventions (get_language_conventions "$NEW_LANG")
    
    # Escape special characters for sed
    set -l escaped_lang (printf '%s\n' "$NEW_LANG" | sed 's/[\[\.*^$()+{}|]/\\&/g')
    set -l escaped_framework (printf '%s\n' "$NEW_FRAMEWORK" | sed 's/[\[\.*^$()+{}|]/\\&/g')
    set -l escaped_branch (printf '%s\n' "$CURRENT_BRANCH" | sed 's/[\[\.*^$()+{}|]/\\&/g')
    
    # Build technology stack and recent change strings conditionally
    set -l tech_stack
    if test -n "$escaped_lang"; and test -n "$escaped_framework"
        set tech_stack "- $escaped_lang + $escaped_framework ($escaped_branch)"
    else if test -n "$escaped_lang"
        set tech_stack "- $escaped_lang ($escaped_branch)"
    else if test -n "$escaped_framework"
        set tech_stack "- $escaped_framework ($escaped_branch)"
    else
        set tech_stack "- ($escaped_branch)"
    end

    set -l recent_change
    if test -n "$escaped_lang"; and test -n "$escaped_framework"
        set recent_change "- $escaped_branch: Added $escaped_lang + $escaped_framework"
    else if test -n "$escaped_lang"
        set recent_change "- $escaped_branch: Added $escaped_lang"
    else if test -n "$escaped_framework"
        set recent_change "- $escaped_branch: Added $escaped_framework"
    else
        set recent_change "- $escaped_branch: Added"
    end

    # Perform substitutions
    sed -i.bak -e "s|\[PROJECT NAME\]|$project_name|" \
        -e "s|\[DATE\]|$current_date|" \
        -e "s|\[EXTRACTED FROM ALL PLAN.MD FILES\]|$tech_stack|" \
        -e "s|\[ACTUAL STRUCTURE FROM PLANS\]|$project_structure|g" \
        -e "s|\[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES\]|$commands|" \
        -e "s|\[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE\]|$language_conventions|" \
        -e "s|\[LAST 3 FEATURES AND WHAT THEY ADDED\]|$recent_change|" \
        "$temp_file"
    
    # Convert \n sequences to actual newlines
    set -l newline (printf '\n')
    sed -i.bak2 "s/\\\\n/$newline/g" "$temp_file"
    
    # Clean up backup files
    rm -f "$temp_file.bak" "$temp_file.bak2"
    
    return 0
end

function update_existing_agent_file
    set -l target_file $argv[1]
    set -l current_date $argv[2]
    
    log_info "Updating existing agent context file..."
    
    # Use a single temporary file for atomic update
    set -l temp_file (mktemp); or begin
        log_error "Failed to create temporary file"
        return 1
    end
    
    # Process the file in one pass
    set -l tech_stack (format_technology_stack "$NEW_LANG" "$NEW_FRAMEWORK")
    set -l new_tech_entries
    set -l new_change_entry ""
    
    # Prepare new technology entries
    if test -n "$tech_stack"; and not grep -q "$tech_stack" "$target_file"
        set -a new_tech_entries "- $tech_stack ($CURRENT_BRANCH)"
    end
    
    if test -n "$NEW_DB"; and test "$NEW_DB" != "N/A"; and test "$NEW_DB" != "NEEDS CLARIFICATION"; and not grep -q "$NEW_DB" "$target_file"
        set -a new_tech_entries "- $NEW_DB ($CURRENT_BRANCH)"
    end
    
    # Prepare new change entry
    if test -n "$tech_stack"
        set new_change_entry "- $CURRENT_BRANCH: Added $tech_stack"
    else if test -n "$NEW_DB"; and test "$NEW_DB" != "N/A"; and test "$NEW_DB" != "NEEDS CLARIFICATION"
        set new_change_entry "- $CURRENT_BRANCH: Added $NEW_DB"
    end
    
    # Process file line by line
    set -l in_tech_section false
    set -l in_changes_section false
    set -l tech_entries_added false
    set -l changes_entries_added false
    set -l existing_changes_count 0
    
    while read -l line
        # Handle Active Technologies section
        if test "$line" = "## Active Technologies"
            echo "$line" >> "$temp_file"
            set in_tech_section true
            continue
        else if test $in_tech_section = true; and string match -qr '^##[[:space:]]' "$line"
            # Add new tech entries before closing the section
            if test $tech_entries_added = false; and test (count $new_tech_entries) -gt 0
                printf '%s\n' $new_tech_entries >> "$temp_file"
                set tech_entries_added true
            end
            echo "$line" >> "$temp_file"
            set in_tech_section false
            continue
        else if test $in_tech_section = true; and test -z "$line"
            # Add new tech entries before empty line in tech section
            if test $tech_entries_added = false; and test (count $new_tech_entries) -gt 0
                printf '%s\n' $new_tech_entries >> "$temp_file"
                set tech_entries_added true
            end
            echo "$line" >> "$temp_file"
            continue
        end
        
        # Handle Recent Changes section
        if test "$line" = "## Recent Changes"
            echo "$line" >> "$temp_file"
            # Add new change entry right after the heading
            if test -n "$new_change_entry"
                echo "$new_change_entry" >> "$temp_file"
            end
            set in_changes_section true
            set changes_entries_added true
            continue
        else if test $in_changes_section = true; and string match -qr '^##[[:space:]]' "$line"
            echo "$line" >> "$temp_file"
            set in_changes_section false
            continue
        else if test $in_changes_section = true; and string match -q '- *' "$line"
            # Keep only first 2 existing changes
            if test $existing_changes_count -lt 2
                echo "$line" >> "$temp_file"
                set existing_changes_count (math $existing_changes_count + 1)
            end
            continue
        end
        
        # Update timestamp
        if string match -qr '\*\*Last updated\*\*:.*[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' "$line"
            echo "$line" | sed "s/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/$current_date/" >> "$temp_file"
        else
            echo "$line" >> "$temp_file"
        end
    end < "$target_file"
    
    # Post-loop check: if we're still in the Active Technologies section and haven't added new entries
    if test $in_tech_section = true; and test $tech_entries_added = false; and test (count $new_tech_entries) -gt 0
        printf '%s\n' $new_tech_entries >> "$temp_file"
    end
    
    # Move temp file to target atomically
    if not mv "$temp_file" "$target_file"
        log_error "Failed to update target file"
        rm -f "$temp_file"
        return 1
    end
    
    return 0
end

#==============================================================================
# Main Agent File Update Function
#==============================================================================

function update_agent_file
    set -l target_file $argv[1]
    set -l agent_name $argv[2]
    
    if test -z "$target_file"; or test -z "$agent_name"
        log_error "update_agent_file requires target_file and agent_name parameters"
        return 1
    end
    
    log_info "Updating $agent_name context file: $target_file"
    
    set -l project_name (basename "$REPO_ROOT")
    set -l current_date (date +%Y-%m-%d)
    
    # Create directory if it doesn't exist
    set -l target_dir (dirname "$target_file")
    if not test -d "$target_dir"
        if not mkdir -p "$target_dir"
            log_error "Failed to create directory: $target_dir"
            return 1
        end
    end
    
    if not test -f "$target_file"
        # Create new file from template
        set -l temp_file (mktemp); or begin
            log_error "Failed to create temporary file"
            return 1
        end
        
        if create_new_agent_file "$target_file" "$temp_file" "$project_name" "$current_date"
            if mv "$temp_file" "$target_file"
                log_success "Created new $agent_name context file"
            else
                log_error "Failed to move temporary file to $target_file"
                rm -f "$temp_file"
                return 1
            end
        else
            log_error "Failed to create new agent file"
            rm -f "$temp_file"
            return 1
        end
    else
        # Update existing file
        if not test -r "$target_file"
            log_error "Cannot read existing file: $target_file"
            return 1
        end
        
        if not test -w "$target_file"
            log_error "Cannot write to existing file: $target_file"
            return 1
        end
        
        if update_existing_agent_file "$target_file" "$current_date"
            log_success "Updated existing $agent_name context file"
        else
            log_error "Failed to update existing agent file"
            return 1
        end
    end
    
    return 0
end

#==============================================================================
# Agent Selection and Processing
#==============================================================================

function update_specific_agent
    set -l agent_type $argv[1]
    
    switch "$agent_type"
        case claude
            update_agent_file "$CLAUDE_FILE" "Claude Code"
        case gemini
            update_agent_file "$GEMINI_FILE" "Gemini CLI"
        case copilot
            update_agent_file "$COPILOT_FILE" "GitHub Copilot"
        case cursor
            update_agent_file "$CURSOR_FILE" "Cursor IDE"
        case qwen
            update_agent_file "$QWEN_FILE" "Qwen Code"
        case opencode
            update_agent_file "$AGENTS_FILE" "opencode"
        case codex
            update_agent_file "$AGENTS_FILE" "Codex CLI"
        case windsurf
            update_agent_file "$WINDSURF_FILE" "Windsurf"
        case kilocode
            update_agent_file "$KILOCODE_FILE" "Kilo Code"
        case auggie
            update_agent_file "$AUGGIE_FILE" "Auggie CLI"
        case roo
            update_agent_file "$ROO_FILE" "Roo Code"
        case '*'
            log_error "Unknown agent type '$agent_type'"
            log_error "Expected: claude|gemini|copilot|cursor|qwen|opencode|codex|windsurf|kilocode|auggie|roo"
            exit 1
    end
end

function update_all_existing_agents
    set -l found_agent false
    
    # Check each possible agent file and update if it exists
    if test -f "$CLAUDE_FILE"
        update_agent_file "$CLAUDE_FILE" "Claude Code"
        set found_agent true
    end
    
    if test -f "$GEMINI_FILE"
        update_agent_file "$GEMINI_FILE" "Gemini CLI"
        set found_agent true
    end
    
    if test -f "$COPILOT_FILE"
        update_agent_file "$COPILOT_FILE" "GitHub Copilot"
        set found_agent true
    end
    
    if test -f "$CURSOR_FILE"
        update_agent_file "$CURSOR_FILE" "Cursor IDE"
        set found_agent true
    end
    
    if test -f "$QWEN_FILE"
        update_agent_file "$QWEN_FILE" "Qwen Code"
        set found_agent true
    end
    
    if test -f "$AGENTS_FILE"
        update_agent_file "$AGENTS_FILE" "Codex/opencode"
        set found_agent true
    end
    
    if test -f "$WINDSURF_FILE"
        update_agent_file "$WINDSURF_FILE" "Windsurf"
        set found_agent true
    end
    
    if test -f "$KILOCODE_FILE"
        update_agent_file "$KILOCODE_FILE" "Kilo Code"
        set found_agent true
    end

    if test -f "$AUGGIE_FILE"
        update_agent_file "$AUGGIE_FILE" "Auggie CLI"
        set found_agent true
    end
    
    if test -f "$ROO_FILE"
        update_agent_file "$ROO_FILE" "Roo Code"
        set found_agent true
    end
    
    # If no agent files exist, create a default Claude file
    if test "$found_agent" = false
        log_info "No existing agent files found, creating default Claude file..."
        update_agent_file "$CLAUDE_FILE" "Claude Code"
    end
end

function print_summary
    echo
    log_info "Summary of changes:"
    
    if test -n "$NEW_LANG"
        echo "  - Added language: $NEW_LANG"
    end
    
    if test -n "$NEW_FRAMEWORK"
        echo "  - Added framework: $NEW_FRAMEWORK"
    end
    
    if test -n "$NEW_DB"; and test "$NEW_DB" != "N/A"
        echo "  - Added database: $NEW_DB"
    end
    
    echo
    log_info "Usage: "(status filename)" [claude|gemini|copilot|cursor|qwen|opencode|codex|windsurf|kilocode|auggie|roo]"
end

#==============================================================================
# Main Execution
#==============================================================================

function main
    # Validate environment before proceeding
    validate_environment
    
    log_info "=== Updating agent context files for feature $CURRENT_BRANCH ==="
    
    # Parse the plan file to extract project information
    if not parse_plan_data "$NEW_PLAN"
        log_error "Failed to parse plan data"
        exit 1
    end
    
    # Process based on agent type argument
    set -l success true
    
    if test -z "$AGENT_TYPE"
        # No specific agent provided - update all existing agent files
        log_info "No agent specified, updating all existing agent files..."
        if not update_all_existing_agents
            set success false
        end
    else
        # Specific agent provided - update only that agent
        log_info "Updating specific agent: $AGENT_TYPE"
        if not update_specific_agent "$AGENT_TYPE"
            set success false
        end
    end
    
    # Print summary
    print_summary
    
    if test "$success" = true
        log_success "Agent context update completed successfully"
        exit 0
    else
        log_error "Agent context update completed with errors"
        exit 1
    end
end

# Execute main function
main $argv
