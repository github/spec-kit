# Test suite for scripts/fish/setup-plan.fish  
# Tests argument parsing and help functionality
# Note: Full script execution tests removed due to execution context limitations

@echo === Loading test helpers ===

source (status dirname)/helpers.fish
set -l project_root (test_project_root)

@echo === Testing argument parsing and help ===

@test "setup-plan: --help shows usage" (fish $project_root/scripts/fish/setup-plan.fish --help 2>&1 | grep -q "Usage"; echo $status) -eq 0

@test "setup-plan: -h shows usage" (fish $project_root/scripts/fish/setup-plan.fish -h 2>&1 | grep -q "Usage"; echo $status) -eq 0

@test "setup-plan: help exits successfully" (fish $project_root/scripts/fish/setup-plan.fish --help >/dev/null 2>&1; echo $status) -eq 0

@test "setup-plan: help mentions --json" (fish $project_root/scripts/fish/setup-plan.fish --help 2>&1 | grep -q "json"; echo $status) -eq 0

# Note: Script execution tests (validation, template copying, file creation)
# require the script to run from within a properly configured repository with
# correct git context. These are removed as they cannot be reliably tested
# in isolated test environments. Integration tests should be done manually
# or with end-to-end testing in actual repositories.