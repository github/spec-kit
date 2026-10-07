"""Reproduction tests for Junie token mangling bug."""
from specify_cli.integrations import get_integration

def test_junie_token_mangling_reproduction():
    """Reproduce the token mangling and false positive detection issues."""
    junie = get_integration("junie")

    # Case 1: $ARGUMENTS should be exactly matched and replaced by $prompt
    content = "Run with $ARGUMENTS"
    updated = junie.post_process_command_content(content)
    assert "$prompt" in updated
    assert "allowPromptArgument: true" in updated

    # Case 2: $ARGUMENTS_SUFFIX should NOT be replaced by $prompt_SUFFIX
    # Currently it is mangled.
    content = "Variable: $ARGUMENTS_SUFFIX"
    updated = junie.post_process_command_content(content)
    # EXPECTED: $$ARGUMENTS_SUFFIX (escaped)
    assert "$$ARGUMENTS_SUFFIX" in updated
    assert "$prompt" not in updated

    # Case 3: $prompt (original) should be escaped to $$prompt
    # Currently it is NOT escaped.
    content = "Reserved: $prompt"
    updated = junie.post_process_command_content(content)
    # EXPECTED: $$prompt
    assert "$$prompt" in updated

    # Case 4: has_arguments false positive
    # Currently '$ARGUMENTS' in content returns True for '$ARGUMENTS_SUFFIX'
    content = "Only $ARGUMENTS_SUFFIX here"
    updated = junie.post_process_command_content(content)
    # EXPECTED: allowPromptArgument: false
    assert "allowPromptArgument: false" in updated

def test_transform_body_variables_direct():
    """Directly test _transform_body_variables with various tokens."""
    junie = get_integration("junie")

    # Desired behavior:
    assert junie._transform_body_variables("$ARGUMENTS") == "$prompt"
    assert junie._transform_body_variables("$ARGUMENTS_SUFFIX") == "$$ARGUMENTS_SUFFIX"
    assert junie._transform_body_variables("$prompt") == "$$prompt"
    assert junie._transform_body_variables("$foo") == "$$foo"

def test_malformed_frontmatter_short_circuit():
    """Verify that malformed frontmatter short-circuits the pipeline."""
    junie = get_integration("junie")

    # Input starts with --- but has no closing ---
    content = "---\n$ARGUMENTS"
    updated = junie.post_process_command_content(content)

    # It should be returned unchanged
    assert updated == content

    # Case with spaces after dashes
    content = "--- \n$ARGUMENTS"
    updated = junie.post_process_command_content(content)
    assert updated == content
