# Test suite for scripts/fish/check-prerequisites.fish
# Tests argument parsing and help functionality
# Note: Full script execution tests removed due to execution context limitations

@echo === Loading test helpers ===

source (status dirname)/helpers.fish
set -l project_root (test_project_root)

@echo === Testing argument parsing and help ===

@test "check-prerequisites: --help shows usage" (fish $project_root/scripts/fish/check-prerequisites.fish --help 2>&1 | grep -q "Usage"; echo $status) -eq 0

@test "check-prerequisites: -h shows usage" (fish $project_root/scripts/fish/check-prerequisites.fish -h 2>&1 | grep -q "Usage"; echo $status) -eq 0

@test "check-prerequisites: help mentions --json" (fish $project_root/scripts/fish/check-prerequisites.fish --help 2>&1 | grep -q "json"; echo $status) -eq 0

@test "check-prerequisites: help mentions --require-tasks" (fish $project_root/scripts/fish/check-prerequisites.fish --help 2>&1 | grep -q "require-tasks"; echo $status) -eq 0

@test "check-prerequisites: help mentions --include-tasks" (fish $project_root/scripts/fish/check-prerequisites.fish --help 2>&1 | grep -q "include-tasks"; echo $status) -eq 0

@test "check-prerequisites: help mentions --paths-only" (fish $project_root/scripts/fish/check-prerequisites.fish --help 2>&1 | grep -q "paths-only"; echo $status) -eq 0

@test "check-prerequisites: help exits successfully" (fish $project_root/scripts/fish/check-prerequisites.fish --help >/dev/null 2>&1; echo $status) -eq 0

# Note: Full integration tests for this script require it to be run from within
# a properly configured repository. See test/integration.test.fish for end-to-end tests.