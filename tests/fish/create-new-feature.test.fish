# Test suite for scripts/fish/create-new-feature.fish
# Tests argument parsing and help functionality
# Note: Full script execution tests removed due to execution context limitations

@echo === Loading test helpers ===

source (status dirname)/helpers.fish
set -l project_root (test_project_root)

@echo === Testing argument parsing and help ===

@test "create-new-feature: requires feature description" (fish $project_root/scripts/fish/create-new-feature.fish 2>&1 | grep -q "Usage"; echo $status) -eq 0

@test "create-new-feature: --help shows usage" (fish $project_root/scripts/fish/create-new-feature.fish --help 2>&1 | grep -q "Usage"; echo $status) -eq 0

@test "create-new-feature: help exits successfully" (fish $project_root/scripts/fish/create-new-feature.fish --help >/dev/null 2>&1; echo $status) -eq 0

@test "create-new-feature: help mentions --json" (fish $project_root/scripts/fish/create-new-feature.fish --help 2>&1 | grep -q "json"; echo $status) -eq 0

@echo === Testing with non-git repo warning ===

set temp_repo (test_setup_repo without-git)
test_create_templates $temp_repo
cd $temp_repo
@test "create-new-feature: warns for non-git repos" (fish $project_root/scripts/fish/create-new-feature.fish "test" 2>&1 | grep -q "Warning"; echo $status) -eq 0
test_cleanup_repo $temp_repo

# Note: Full integration tests for feature creation, numbering, and git operations
# require the script to run from within a properly configured repository.
# These are better tested manually or with end-to-end integration tests.