"""Real stdio MCP handshake and protocol-purity integration test."""

import asyncio
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters, stdio_client

_READ_TIMEOUT_SECONDS = 10
_TEST_TIMEOUT_SECONDS = 30


def test_real_stdio_server_initializes_discovers_and_calls_first_class_tools():
    async def exercise() -> None:
        repo_root = Path(__file__).resolve().parents[3]
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-c", "from specify_cli import main; main()", "mcp"],
            cwd=repo_root,
        )

        async with asyncio.timeout(_TEST_TIMEOUT_SECONDS):
            with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errlog:
                async with (
                    stdio_client(parameters, errlog=errlog) as (read, write),
                    ClientSession(
                        read,
                        write,
                        read_timeout_seconds=_READ_TIMEOUT_SECONDS,
                    ) as session,
                ):
                    initialized = await session.initialize()
                    tools = await session.list_tools()
                    listed = await session.call_tool("specify_list_commands", {})
                    version = await session.call_tool("specify_version", {})
                    artifacts = await session.call_tool("specify_artifact_list", {})
                    artifact_failure = await session.call_tool(
                        "specify_artifact_list",
                        {"project_directory": str(repo_root / "tests")},
                    )
                    ran = await session.call_tool(
                        "specify_run_command",
                        {"command": "version"},
                    )
                    unavailable = await session.call_tool(
                        "specify_describe_command",
                        {"command": "artifact.list"},
                    )
                errlog.seek(0)
                stderr = errlog.read()

        assert initialized.server_info.name == "specify"
        assert [tool.name for tool in tools.tools] == [
            "specify_list_commands",
            "specify_describe_command",
            "specify_run_command",
            "specify_version",
            "specify_artifact_list",
        ]
        assert listed.structured_content["commands"][0]["command"] == "version"
        assert set(version.structured_content) == {
            "cli_version",
            "runtime",
            "system",
            "features",
        }
        assert version.is_error is False
        assert artifacts.is_error is False
        assert isinstance(artifacts.structured_content["rows"], list)
        assert artifacts.structured_content["rows"]
        assert artifact_failure.is_error is True
        assert artifact_failure.structured_content == {
            "error": {
                "code": "not_a_spec_kit_project",
                "message": "not a Spec Kit project: no .specify/ directory found",
                "details": {"project_directory": str(repo_root / "tests")},
                "retryable": False,
            }
        }
        assert set(ran.structured_content) == {
            "cli_version",
            "runtime",
            "system",
            "features",
        }
        assert ran.is_error is False
        assert unavailable.is_error is True
        assert unavailable.structured_content == {
            "error": {
                "code": "unavailable_command",
                "message": (
                    "Command 'artifact.list' is not available through the "
                    "experimental Spec Kit MCP server."
                ),
                "details": {
                    "command": "artifact.list",
                    "available_commands": ["version"],
                },
            }
        }
        assert unavailable.content[0].text.startswith("unavailable_command:")
        assert stderr == ""

    asyncio.run(exercise())
