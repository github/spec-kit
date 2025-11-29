#!/usr/bin/env bash
# Manual test script to verify the newline conversion fix

set -e

echo "=== Testing Newline Conversion Fix ==="
echo ""

# Test 1: Demonstrate the problem with command substitution
echo "1. Testing command substitution (OLD - broken method):"
newline_old=$(printf '\n')
echo "   Length of newline variable: ${#newline_old}"
if [[ ${#newline_old} -eq 0 ]]; then
    echo "   ❌ PROBLEM: Variable is empty! Command substitution stripped the newline."
else
    echo "   ✓ Variable has content (length: ${#newline_old})"
fi
echo ""

# Test 2: Demonstrate the fix with printf -v
echo "2. Testing printf -v (NEW - fixed method):"
printf -v newline_new '\n'
echo "   Length of newline variable: ${#newline_new}"
if [[ ${#newline_new} -eq 1 ]]; then
    echo "   ✓ SUCCESS: Variable contains the newline character (length: 1)"
else
    echo "   ❌ PROBLEM: Variable length is ${#newline_new} (expected 1)"
fi
echo ""

# Test 3: Simulate the actual conversion
echo "3. Simulating actual \\\\n to newline conversion:"
test_content="backend/\\nfrontend/\\ntests/"

# OLD method (broken)
old_result="$test_content"
if [[ ${#newline_old} -eq 0 ]]; then
    # When newline is empty, sed would delete \\n sequences
    old_result=$(echo "$test_content" | sed 's/\\n//g')
    echo "   OLD method result: '$old_result'"
    echo "   ❌ All newlines were deleted!"
else
    old_result=$(echo "$test_content" | sed "s/\\\\n/${newline_old}/g")
    echo "   OLD method result: '$old_result'"
fi
echo "   Line count: $(echo "$old_result" | wc -l | tr -d ' ')"
echo ""

# NEW method (fixed)
new_result=$(echo "$test_content" | sed $'s/\\\\n/\\\n/g')
echo "   NEW method result:"
echo "$new_result" | while IFS= read -r line; do
    echo "     - $line"
done
echo "   Line count: $(echo "$new_result" | wc -l | tr -d ' ')"
echo ""

# Test 4: Verify the fix works in the actual script context
echo "4. Testing with actual script pattern:"
temp_file=$(mktemp)
echo "backend/\\nfrontend/\\ntests/" > "$temp_file"

# Use the fixed method
printf -v newline '\n'
sed -i.bak "s/\\\\n/${newline}/g" "$temp_file" 2>/dev/null || {
    # Fallback for macOS sed which may need different syntax
    sed -i.bak $'s/\\\\n/\\\n/g' "$temp_file"
}

echo "   File content after conversion:"
cat "$temp_file"
echo ""
echo "   Line count: $(wc -l < "$temp_file" | tr -d ' ')"
if [[ $(wc -l < "$temp_file" | tr -d ' ') -eq 3 ]]; then
    echo "   ✓ SUCCESS: File has 3 lines as expected!"
else
    echo "   ❌ PROBLEM: Expected 3 lines, got $(wc -l < "$temp_file" | tr -d ' ')"
fi

rm -f "$temp_file" "$temp_file.bak"

echo ""
echo "=== Test Complete ==="
echo ""
echo "Summary:"
echo "  - OLD method (command substitution): newline variable is empty"
echo "  - NEW method (printf -v): newline variable contains actual newline"
echo "  - Result: NEW method correctly converts \\\\n sequences to real newlines"
