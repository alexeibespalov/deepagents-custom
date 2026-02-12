import json
from contextlib import asynccontextmanager

import pytest


@pytest.mark.asyncio
async def test_open_mcp_toolset_exposes_tools_and_can_invoke(tmp_path, monkeypatch) -> None:
    """Smoke test MCP tool loading without spawning real processes.

    We monkeypatch the MCP SDK's transport + session objects so we can validate:
    - `.mcp.json` parsing and tool naming
    - schema wiring into a LangChain StructuredTool
    - tool invocation routes to `session.call_tool`
    """

    # Write a minimal .mcp.json that would normally use stdio.
    (tmp_path / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "tavily": {
                        "command": "npx",
                        "args": ["-y", "mcp-remote", "https://example.com"],
                        "env": {},
                    }
                }
            }
        )
    )

    import mcp.types as mt
    import mcp.client.session as mcs
    import mcp.client.stdio as stdio

    @asynccontextmanager
    async def _fake_stdio_client(_params, _errlog=None):
        yield object(), object()

    class FakeSession:
        def __init__(self) -> None:
            self.initialized = False
            self.calls: list[tuple[str, dict]] = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, _exc_type, _exc, _tb):
            return False

        async def initialize(self) -> None:
            self.initialized = True

        async def list_tools(self):
            return mt.ListToolsResult(
                tools=[
                    mt.Tool(
                        name="search",
                        description="Search something",
                        inputSchema={
                            "type": "object",
                            "properties": {"q": {"type": "string"}},
                            "required": ["q"],
                        },
                    )
                ]
            )

        async def call_tool(self, name: str, args: dict):
            self.calls.append((name, args))
            return mt.CallToolResult(
                content=[mt.TextContent(type="text", text="ok")],
                structuredContent=None,
                isError=False,
            )

    # Patch the MCP SDK pieces that open_mcp_toolset relies on.
    monkeypatch.setattr(stdio, "stdio_client", _fake_stdio_client)

    def _fake_client_session(_read, _write):
        return FakeSession()

    monkeypatch.setattr(mcs, "ClientSession", _fake_client_session)

    from deepagents_cli.mcp_tools import open_mcp_toolset

    async with open_mcp_toolset(tmp_path) as toolset:
        assert toolset.errors == []
        assert toolset.config_path == tmp_path / ".mcp.json"
        assert len(toolset.tools) == 1

        tool = toolset.tools[0]
        assert tool.name == "tavily__search"
        assert "[MCP:tavily]" in tool.description

        out = await tool.ainvoke({"q": "hello"})
        assert out == "ok"
