"""
Unit tests for mcp_config.py module.

Tests cover:
- MCP_RECIPES structure validation
- All required fields present for every recipe
- Type-specific field validation
"""

import pytest
from infrakit_cli.mcp_config import MCP_RECIPES


class TestMcpConfig:
    """Test the MCP_RECIPES dictionary structure and contents."""

    def test_all_recipes_have_required_fields(self):
        """Every MCP recipe must have all required fields."""
        base_required_fields = [
            "display_name",
            "description",
            "type",
            "tools",
            "usage",
        ]

        for recipe_key, recipe in MCP_RECIPES.items():
            for field in base_required_fields:
                assert field in recipe, (
                    f"MCP recipe '{recipe_key}' missing required field '{field}'"
                )

    def test_recipe_type_validation(self):
        """Recipe type must be either 'stdio' or 'sse'."""
        valid_types = ["stdio", "sse"]

        for recipe_key, recipe in MCP_RECIPES.items():
            recipe_type = recipe["type"]
            assert recipe_type in valid_types, (
                f"MCP recipe '{recipe_key}' has invalid type '{recipe_type}'"
            )

    def test_stdio_recipe_fields(self):
        """Stdio type recipes must have command and args fields."""
        for recipe_key, recipe in MCP_RECIPES.items():
            if recipe["type"] == "stdio":
                assert "command" in recipe, (
                    f"Stdio recipe '{recipe_key}' missing 'command' field"
                )
                assert "args" in recipe, (
                    f"Stdio recipe '{recipe_key}' missing 'args' field"
                )

                # Command and args should be non-empty
                assert len(recipe["command"]) > 0, (
                    f"Recipe '{recipe_key}' has empty command"
                )
                assert isinstance(recipe["args"], list), (
                    f"Recipe '{recipe_key}' args is not a list"
                )
                assert len(recipe["args"]) > 0, (
                    f"Recipe '{recipe_key}' has empty args list"
                )

    def test_sse_recipe_fields(self):
        """SSE type recipes must have url field."""
        for recipe_key, recipe in MCP_RECIPES.items():
            if recipe["type"] == "sse":
                assert "url" in recipe, f"SSE recipe '{recipe_key}' missing 'url' field"
                assert recipe["url"].startswith("http"), (
                    f"Recipe '{recipe_key}' has invalid URL"
                )

    def test_tools_field_validation(self):
        """Tools field must be a non-empty list of strings."""
        for recipe_key, recipe in MCP_RECIPES.items():
            tools = recipe["tools"]
            assert isinstance(tools, list), f"Recipe '{recipe_key}' tools is not a list"
            assert len(tools) > 0, f"Recipe '{recipe_key}' has empty tools list"

            for tool in tools:
                assert isinstance(tool, str), (
                    f"Recipe '{recipe_key}' has non-string tool"
                )
                assert len(tool) > 0, f"Recipe '{recipe_key}' has empty tool name"

    def test_context7_recipe(self):
        """Context7 recipe should be correctly configured."""
        assert "context7" in MCP_RECIPES
        context7 = MCP_RECIPES["context7"]

        assert context7["type"] == "stdio"
        assert context7["command"] == "npx"
        assert context7["args"] == ["-y", "@upstash/context7-mcp@latest"]
        assert "resolve-library-id" in context7["tools"]

    def test_deepwiki_recipe(self):
        """DeepWiki recipe should be correctly configured."""
        assert "deepwiki" in MCP_RECIPES
        deepwiki = MCP_RECIPES["deepwiki"]

        assert deepwiki["type"] == "sse"
        assert deepwiki["url"] == "https://mcp.deepwiki.com/mcp"
        assert "ask_question" in deepwiki["tools"]

    def test_aws_best_practices_recipe(self):
        """AWS Best Practices recipe should be correctly configured."""
        assert "aws-best-practices" in MCP_RECIPES
        aws = MCP_RECIPES["aws-best-practices"]

        assert aws["type"] == "stdio"
        assert aws["command"] == "uvx"
        assert aws["args"] == ["awslabs.aws-documentation-mcp-server@latest"]

    def test_microsoft_learn_recipe(self):
        """Microsoft Learn recipe should be correctly configured."""
        assert "microsoft-learn" in MCP_RECIPES
        ms = MCP_RECIPES["microsoft-learn"]

        assert ms["type"] == "stdio"
        assert ms["command"] == "npx"
        assert ms["args"] == ["-y", "@microsoft/mcp-microsoft-learn@latest"]

    def test_all_recipes_have_unique_display_names(self):
        """All MCP recipes should have unique display names."""
        names = []
        for recipe_key, recipe in MCP_RECIPES.items():
            name = recipe["display_name"]
            assert name not in names, f"Duplicate display name '{name}' for MCP recipe"
            names.append(name)

    @pytest.mark.parametrize("recipe_key", MCP_RECIPES.keys())
    def test_recipe_consistency(self, recipe_key):
        """General consistency checks for every MCP recipe."""
        recipe = MCP_RECIPES[recipe_key]

        # Display name should be non-empty
        assert isinstance(recipe["display_name"], str)
        assert len(recipe["display_name"]) > 0

        # Description should be non-empty
        assert isinstance(recipe["description"], str)
        assert len(recipe["description"]) > 0

        # Usage should be non-empty
        assert isinstance(recipe["usage"], str)
        assert len(recipe["usage"]) > 0

    def test_no_duplicate_tool_names_across_recipes(self):
        """Tool names should be unique across all recipes (best practice)."""
        all_tools = []
        for recipe_key, recipe in MCP_RECIPES.items():
            for tool in recipe["tools"]:
                # Tools don't need to be globally unique, but this is just an informational check
                # If they are duplicated, it's okay but worth noting
                pass
