"""
Tests for MCP tools in lineage module.
"""

import pytest
from pathlib import Path
import os


class TestDepGraphAnalyzeTool:
    """Test dep_graph_analyze MCP tool."""

    @pytest.mark.asyncio
    async def test_analyze_no_specs_dir(self, temp_dir):
        """Test analyze when specs directory doesn't exist."""
        # Import here to avoid dependency issues if surrealdb not installed
        try:
            from spectrena.lineage.db import create_mcp_server
        except ImportError:
            pytest.skip("MCP dependencies not installed")

        os.chdir(temp_dir)

        mcp = create_mcp_server()
        # Get the tool function
        tool_func = None
        for tool in mcp.list_tools():
            if tool.name == "dep_graph_analyze":
                tool_func = tool.fn
                break

        assert tool_func is not None, "dep_graph_analyze tool not found"

        result = await tool_func()

        assert "specs" in result
        assert result["specs"] == []
        assert "instruction" in result
        assert "No specs directory" in result["instruction"]

    @pytest.mark.asyncio
    async def test_analyze_with_specs(self, temp_dir):
        """Test analyze with actual specs."""
        try:
            from spectrena.lineage.db import create_mcp_server
        except ImportError:
            pytest.skip("MCP dependencies not installed")

        os.chdir(temp_dir)

        # Create specs directory with some specs
        specs_dir = temp_dir / "specs"
        specs_dir.mkdir()

        # Create spec 1
        spec1_dir = specs_dir / "CORE-001-user-auth"
        spec1_dir.mkdir()
        (spec1_dir / "spec.md").write_text("""# User Authentication

Implements OAuth2 authentication for the application.

## Requirements
- OAuth2 provider integration
- Token management
- User session handling
""")

        # Create spec 2
        spec2_dir = specs_dir / "CORE-002-data-sync"
        spec2_dir.mkdir()
        (spec2_dir / "spec.md").write_text("""# Data Synchronization

Requires user authentication to sync data securely.
Depends on CORE-001 for auth tokens.

## Requirements
- Real-time sync
- Conflict resolution
""")

        mcp = create_mcp_server()
        tool_func = None
        for tool in mcp.list_tools():
            if tool.name == "dep_graph_analyze":
                tool_func = tool.fn
                break

        result = await tool_func()

        assert "specs" in result
        assert len(result["specs"]) == 2

        # Check spec IDs
        spec_ids = [s["id"] for s in result["specs"]]
        assert "CORE-001-user-auth" in spec_ids
        assert "CORE-002-data-sync" in spec_ids

        # Check content is truncated
        for spec in result["specs"]:
            assert len(spec["content"]) <= 1000

    @pytest.mark.asyncio
    async def test_analyze_skips_non_dirs(self, temp_dir):
        """Test analyze skips files and only processes directories."""
        try:
            from spectrena.lineage.db import create_mcp_server
        except ImportError:
            pytest.skip("MCP dependencies not installed")

        os.chdir(temp_dir)

        specs_dir = temp_dir / "specs"
        specs_dir.mkdir()

        # Create a file (not a directory)
        (specs_dir / "README.md").write_text("This is not a spec")

        # Create a directory without spec.md
        (specs_dir / "incomplete").mkdir()

        # Create a valid spec
        spec_dir = specs_dir / "SPEC-001"
        spec_dir.mkdir()
        (spec_dir / "spec.md").write_text("# Valid Spec")

        mcp = create_mcp_server()
        tool_func = None
        for tool in mcp.list_tools():
            if tool.name == "dep_graph_analyze":
                tool_func = tool.fn
                break

        result = await tool_func()

        # Should only find the one valid spec
        assert len(result["specs"]) == 1
        assert result["specs"][0]["id"] == "SPEC-001"


class TestDepGraphSaveTool:
    """Test dep_graph_save MCP tool."""

    @pytest.mark.asyncio
    async def test_save_simple_graph(self, temp_dir):
        """Test saving a simple dependency graph."""
        try:
            from spectrena.lineage.db import create_mcp_server
        except ImportError:
            pytest.skip("MCP dependencies not installed")

        os.chdir(temp_dir)

        mcp = create_mcp_server()
        tool_func = None
        for tool in mcp.list_tools():
            if tool.name == "dep_graph_save":
                tool_func = tool.fn
                break

        assert tool_func is not None, "dep_graph_save tool not found"

        graph = """graph TD
    CORE-001
    CORE-002 --> CORE-001
"""

        result = await tool_func(graph)

        assert result["status"] == "saved"
        assert result["edge_count"] == 1

        # Verify file was created
        deps_file = temp_dir / "deps.mermaid"
        assert deps_file.exists()

        content = deps_file.read_text()
        assert "graph TD" in content
        assert "CORE-002 --> CORE-001" in content

    @pytest.mark.asyncio
    async def test_save_graph_without_header(self, temp_dir):
        """Test saving graph without 'graph TD' header."""
        try:
            from spectrena.lineage.db import create_mcp_server
        except ImportError:
            pytest.skip("MCP dependencies not installed")

        os.chdir(temp_dir)

        mcp = create_mcp_server()
        tool_func = None
        for tool in mcp.list_tools():
            if tool.name == "dep_graph_save":
                tool_func = tool.fn
                break

        # Graph without header
        graph = """CORE-001
CORE-002 --> CORE-001"""

        result = await tool_func(graph)

        # Should auto-add header
        deps_file = temp_dir / "deps.mermaid"
        content = deps_file.read_text()
        assert content.startswith("graph TD\n")

    @pytest.mark.asyncio
    async def test_save_complex_graph(self, temp_dir):
        """Test saving complex multi-level graph."""
        try:
            from spectrena.lineage.db import create_mcp_server
        except ImportError:
            pytest.skip("MCP dependencies not installed")

        os.chdir(temp_dir)

        mcp = create_mcp_server()
        tool_func = None
        for tool in mcp.list_tools():
            if tool.name == "dep_graph_save":
                tool_func = tool.fn
                break

        graph = """graph TD
    CORE-001-user-auth
    CORE-002-data-sync --> CORE-001-user-auth
    API-001-rest-endpoints --> CORE-001-user-auth
    API-002-webhooks --> API-001-rest-endpoints
    UI-001-dashboard --> API-001-rest-endpoints
    UI-001-dashboard --> CORE-002-data-sync
"""

        result = await tool_func(graph)

        assert result["status"] == "saved"
        assert result["edge_count"] == 5

        # Verify file content
        deps_file = temp_dir / "deps.mermaid"
        content = deps_file.read_text()
        assert "CORE-001-user-auth" in content
        assert "UI-001-dashboard --> API-001-rest-endpoints" in content
        assert "UI-001-dashboard --> CORE-002-data-sync" in content

    @pytest.mark.asyncio
    async def test_save_overwrites_existing(self, temp_dir):
        """Test that saving overwrites existing deps.mermaid."""
        try:
            from spectrena.lineage.db import create_mcp_server
        except ImportError:
            pytest.skip("MCP dependencies not installed")

        os.chdir(temp_dir)

        # Create existing file
        deps_file = temp_dir / "deps.mermaid"
        deps_file.write_text("graph TD\nOLD-SPEC\n")

        mcp = create_mcp_server()
        tool_func = None
        for tool in mcp.list_tools():
            if tool.name == "dep_graph_save":
                tool_func = tool.fn
                break

        # Save new graph
        new_graph = """graph TD
    NEW-SPEC-001
    NEW-SPEC-002 --> NEW-SPEC-001
"""

        result = await tool_func(new_graph)

        # Verify old content is gone
        content = deps_file.read_text()
        assert "OLD-SPEC" not in content
        assert "NEW-SPEC-001" in content
        assert "NEW-SPEC-002" in content


class TestMCPToolIntegration:
    """Integration tests for MCP tools workflow."""

    @pytest.mark.asyncio
    async def test_analyze_then_save_workflow(self, temp_dir):
        """Test complete workflow: analyze specs, then save graph."""
        try:
            from spectrena.lineage.db import create_mcp_server
            from spectrena.worktrees import parse_mermaid_deps
        except ImportError:
            pytest.skip("MCP dependencies not installed")

        os.chdir(temp_dir)

        # Create some specs
        specs_dir = temp_dir / "specs"
        specs_dir.mkdir()

        for spec_id in ["CORE-001", "CORE-002", "API-001"]:
            spec_dir = specs_dir / spec_id
            spec_dir.mkdir()
            (spec_dir / "spec.md").write_text(f"# {spec_id}\n\nSome content.")

        # Step 1: Analyze
        mcp = create_mcp_server()
        analyze_func = None
        save_func = None

        for tool in mcp.list_tools():
            if tool.name == "dep_graph_analyze":
                analyze_func = tool.fn
            elif tool.name == "dep_graph_save":
                save_func = tool.fn

        assert analyze_func is not None
        assert save_func is not None

        analyze_result = await analyze_func()
        assert len(analyze_result["specs"]) == 3

        # Step 2: Create graph (simulating Claude's analysis)
        graph = """graph TD
    CORE-001
    CORE-002 --> CORE-001
    API-001 --> CORE-001
"""

        # Step 3: Save
        save_result = await save_func(graph)
        assert save_result["status"] == "saved"
        assert save_result["edge_count"] == 2

        # Step 4: Verify saved graph can be parsed
        deps_file = temp_dir / "deps.mermaid"
        deps = parse_mermaid_deps(deps_file)

        assert "CORE-001" in deps
        assert "CORE-002" in deps
        assert "API-001" in deps
        assert deps["CORE-002"] == ["CORE-001"]
        assert deps["API-001"] == ["CORE-001"]


class TestOtherMCPTools:
    """Test other existing MCP tools."""

    @pytest.mark.asyncio
    async def test_phase_get_tool_exists(self):
        """Test that phase_get MCP tool is registered."""
        try:
            from spectrena.lineage.db import create_mcp_server
        except ImportError:
            pytest.skip("MCP dependencies not installed")

        mcp = create_mcp_server()
        tool_names = [tool.name for tool in mcp.list_tools()]

        assert "phase_get" in tool_names

    @pytest.mark.asyncio
    async def test_task_start_tool_exists(self):
        """Test that task_start MCP tool is registered."""
        try:
            from spectrena.lineage.db import create_mcp_server
        except ImportError:
            pytest.skip("MCP dependencies not installed")

        mcp = create_mcp_server()
        tool_names = [tool.name for tool in mcp.list_tools()]

        assert "task_start" in tool_names

    @pytest.mark.asyncio
    async def test_all_expected_tools_registered(self):
        """Test that all expected MCP tools are registered."""
        try:
            from spectrena.lineage.db import create_mcp_server
        except ImportError:
            pytest.skip("MCP dependencies not installed")

        mcp = create_mcp_server()
        tool_names = [tool.name for tool in mcp.list_tools()]

        expected_tools = [
            "phase_get",
            "task_start",
            "task_complete",
            "task_context",
            "record_change",
            "impact_analysis",
            "ready_specs",
            "velocity",
            "dep_graph_analyze",
            "dep_graph_save",
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names, f"Tool {tool_name} not found"
