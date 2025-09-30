# Test Helper Functions for Fishtape
# Shared utilities for testing fish scripts

# Get the project root directory
function test_project_root
    cd (status dirname)/../..
    pwd
end

# Create a temporary test repository with optional git initialization
function test_setup_repo
    set -l use_git $argv[1]
    set -l temp_dir (mktemp -d)
    
    if test "$use_git" = "with-git"
        git -C $temp_dir init -q
        git -C $temp_dir config user.name "Test User"
        git -C $temp_dir config user.email "test@example.com"
        git -C $temp_dir commit --allow-empty -m "Initial commit" -q
    end
    
    # Create .specify directory structure
    mkdir -p $temp_dir/.specify/templates
    mkdir -p $temp_dir/specs
    
    echo $temp_dir
end

# Clean up a test repository
function test_cleanup_repo
    set -l repo_dir $argv[1]
    if test -d "$repo_dir"
        rm -rf "$repo_dir"
    end
end

# Create mock feature directories
# Usage: test_create_features REPO_DIR 001 002 005
function test_create_features
    set -l repo_dir $argv[1]
    set -l feature_nums $argv[2..-1]
    
    for num in $feature_nums
        set -l feature_dir "$repo_dir/specs/$num-test-feature"
        mkdir -p "$feature_dir"
        
        # Create spec.md
        echo "# Feature $num" > "$feature_dir/spec.md"
        echo "Test feature specification." >> "$feature_dir/spec.md"
        
        # Create plan.md
        echo "# Implementation Plan" > "$feature_dir/plan.md"
        echo "" >> "$feature_dir/plan.md"
        echo "**Language/Version**: Python 3.9" >> "$feature_dir/plan.md"
        echo "**Primary Dependencies**: FastAPI" >> "$feature_dir/plan.md"
        echo "**Storage**: PostgreSQL" >> "$feature_dir/plan.md"
        echo "**Project Type**: Web API" >> "$feature_dir/plan.md"
    end
end

# Create template files in test repository
function test_create_templates
    set -l repo_dir $argv[1]
    set -l templates_dir "$repo_dir/.specify/templates"
    
    mkdir -p "$templates_dir"
    
    # Create spec-template.md
    echo "# Feature Specification" > "$templates_dir/spec-template.md"
    echo "" >> "$templates_dir/spec-template.md"
    echo "## Overview" >> "$templates_dir/spec-template.md"
    echo "[Describe the feature]" >> "$templates_dir/spec-template.md"
    
    # Create plan-template.md
    echo "# Implementation Plan" > "$templates_dir/plan-template.md"
    echo "" >> "$templates_dir/plan-template.md"
    echo "**Language/Version**: NEEDS CLARIFICATION" >> "$templates_dir/plan-template.md"
    echo "**Primary Dependencies**: NEEDS CLARIFICATION" >> "$templates_dir/plan-template.md"
    echo "**Storage**: N/A" >> "$templates_dir/plan-template.md"
    echo "**Project Type**: NEEDS CLARIFICATION" >> "$templates_dir/plan-template.md"
    
    # Create agent-file-template.md
    echo "# Agent Context for [PROJECT NAME]" > "$templates_dir/agent-file-template.md"
    echo "" >> "$templates_dir/agent-file-template.md"
    echo "**Last updated**: [DATE]" >> "$templates_dir/agent-file-template.md"
    echo "" >> "$templates_dir/agent-file-template.md"
    echo "## Active Technologies" >> "$templates_dir/agent-file-template.md"
    echo "[EXTRACTED FROM ALL PLAN.MD FILES]" >> "$templates_dir/agent-file-template.md"
end

# Create a plan.md file with specific content
# Usage: test_create_plan FILE_PATH "Python 3.9" "FastAPI" "PostgreSQL" "Web API"
function test_create_plan
    set -l path $argv[1]
    set -l lang $argv[2]
    set -l framework $argv[3]
    set -l db $argv[4]
    set -l type $argv[5]
    
    mkdir -p (dirname "$path")
    
    echo "# Implementation Plan" > "$path"
    echo "" >> "$path"
    echo "**Language/Version**: $lang" >> "$path"
    echo "**Primary Dependencies**: $framework" >> "$path"
    echo "**Storage**: $db" >> "$path"
    echo "**Project Type**: $type" >> "$path"
    echo "" >> "$path"
    echo "## Overview" >> "$path"
    echo "Test implementation plan." >> "$path"
end

# Assert that output contains a string
function test_assert_contains
    set -l output $argv[1]
    set -l expected $argv[2]
    
    echo "$output" | grep -q "$expected"
end

# Assert that a file exists
function test_assert_file_exists
    set -l file_path $argv[1]
    test -f "$file_path"
end

# Assert that a directory exists
function test_assert_dir_exists
    set -l dir_path $argv[1]
    test -d "$dir_path"
end

# Assert that output is valid JSON
function test_assert_json_valid
    set -l output $argv[1]
    echo "$output" | python3 -m json.tool >/dev/null 2>&1
end

# Get a temporary file
function test_temp_file
    mktemp
end

# Get a temporary directory
function test_temp_dir
    mktemp -d
end

# Run a fish script from the project
# Usage: test_run_script script-name.fish --arg1 --arg2
function test_run_script
    set -l project_root (test_project_root)
    set -l script_name $argv[1]
    set -l script_args $argv[2..-1]
    
    fish "$project_root/scripts/fish/$script_name" $script_args
end
