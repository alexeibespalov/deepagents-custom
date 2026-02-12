"""MCP server integration for the Deep Agents CLI.

This module loads MCP server definitions from `.mcp.json`, connects to those
servers, and exposes each MCP tool as a LangChain `StructuredTool` so it can be
used by the deep agent.

We intentionally keep this isolated from the Textual UI so both interactive and
non-interactive entrypoints can reuse it.
"""

from __future__ import annotations

import json
import shlex
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_core.tools.base import ToolException
from langchain_core.tools.structured import StructuredTool


@dataclass(frozen=True, slots=True)
class McpToolset:
    """Connected MCP toolset for the duration of a CLI session."""

    tools: list[StructuredTool]
    config_path: Path | None
    errors: list[str]


def find_mcp_config_path(start_path: Path) -> Path | None:
    """Search upward from `start_path` for `.mcp.json`.

    Args:
        start_path: Directory to start searching from.

    Returns:
        Path to the nearest `.mcp.json`, or `None` if not found.
    """

    start = start_path.resolve()
    for candidate_dir in (start, *start.parents):
        candidate = candidate_dir / ".mcp.json"
        if candidate.exists():
            return candidate
    return None


def extract_mcp_servers(data: object) -> dict[str, object]:
    """Extract MCP server definitions from supported config formats.

    Supports:
    - `{ "mcpServers": { ... } }`
    - `{ "servers": { ... } }`
    - simplified root map: `{ "server": { ... }, ... }`
    """
    if not isinstance(data, dict):
        return {}

    servers = data.get("mcpServers")
    if isinstance(servers, dict):
        return servers  # type: ignore[return-value]

    servers = data.get("servers")
    if isinstance(servers, dict):
        return servers  # type: ignore[return-value]

    meta_keys = {"$schema", "version", "inputs", "env"}
    candidate: dict[str, object] = {
        k: v for k, v in data.items() if isinstance(k, str) and k not in meta_keys
    }
    if not candidate or not all(isinstance(v, dict) for v in candidate.values()):
        return {}

    def _looks_like_server(cfg: dict[str, object]) -> bool:
        return any(key in cfg for key in ("command", "url", "type"))

    if all(_looks_like_server(v) for v in candidate.values() if isinstance(v, dict)):
        return candidate

    return {}


def _format_call_tool_result(result: Any) -> str:
    """Convert an MCP `CallToolResult` into a human-readable string."""
    # We intentionally avoid importing mcp.types at module import time in case
    # the dependency graph changes; we rely on duck-typing.
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return json.dumps(structured, indent=2, ensure_ascii=False)

    content = getattr(result, "content", None)
    if not content:
        return ""

    parts: list[str] = []
    for block in content:
        block_type = getattr(block, "type", None)
        if block_type == "text":
            parts.append(str(getattr(block, "text", "")))
        else:
            # Fall back to a best-effort JSON-ish representation.
            if hasattr(block, "model_dump_json"):
                parts.append(block.model_dump_json())
            else:
                parts.append(repr(block))
    return "\n".join(p for p in parts if p)


def _normalize_stdio_command(raw_command: object, raw_args: object) -> tuple[str, list[str]]:
    """Normalize stdio `command` + `args`.

    Some configs put everything in `command` (shell-like string). We accept
    that for convenience but normalize to `command` executable + `args` list.
    """
    command = raw_command if isinstance(raw_command, str) else ""
    args = raw_args if isinstance(raw_args, list) else []
    args = [str(a) for a in args]

    if command and args:
        return command, args

    if command and not args and any(ch.isspace() for ch in command):
        split = shlex.split(command)
        if split:
            return split[0], split[1:]

    return command, args


@asynccontextmanager
async def open_mcp_toolset(start_path: Path) -> AsyncIterator[McpToolset]:
    """Open MCP servers from `.mcp.json` and expose tools for the agent.

    Args:
        start_path: Directory to search upward from for `.mcp.json`.

    Yields:
        `McpToolset` containing LangChain tools and any load errors.
    """
    config_path = find_mcp_config_path(start_path)
    if not config_path:
        yield McpToolset(tools=[], config_path=None, errors=[])
        return

    errors: list[str] = []
    try:
        data = json.loads(config_path.read_text())
    except Exception as e:  # noqa: BLE001
        yield McpToolset(
            tools=[],
            config_path=config_path,
            errors=[f"Failed to read {config_path}: {type(e).__name__}: {e}"],
        )
        return

    servers = extract_mcp_servers(data)
    if not servers:
        yield McpToolset(
            tools=[],
            config_path=config_path,
            errors=[
                f"No MCP servers configured in {config_path}. "
                "Expected a top-level 'mcpServers'/'servers' object or a simplified server map."
            ],
        )
        return

    # Lazy imports: mcp is an optional-ish integration and we want fast startup.
    from mcp.client.session import ClientSession  # noqa: PLC0415
    from mcp.client.sse import sse_client  # noqa: PLC0415
    from mcp.client.stdio import StdioServerParameters, stdio_client  # noqa: PLC0415
    from mcp.client.streamable_http import streamable_http_client  # noqa: PLC0415

    async with AsyncExitStack() as stack:
        tools: list[StructuredTool] = []

        for server_name, cfg_obj in sorted(servers.items(), key=lambda kv: kv[0]):
            if not isinstance(cfg_obj, dict):
                errors.append(f"MCP server '{server_name}' config must be an object.")
                continue

            cfg: dict[str, Any] = cfg_obj
            server_type = cfg.get("type")
            env = cfg.get("env")
            env_dict = env if isinstance(env, dict) else None

            try:
                if "command" in cfg:
                    command, args = _normalize_stdio_command(cfg.get("command"), cfg.get("args"))
                    if not command:
                        raise ValueError("Missing 'command' for stdio MCP server")
                    params = StdioServerParameters(
                        command=command,
                        args=args,
                        env={str(k): str(v) for k, v in (env_dict or {}).items()} or None,
                        cwd=str(start_path),
                    )
                    read, write = await stack.enter_async_context(stdio_client(params))
                elif "url" in cfg:
                    url = cfg.get("url")
                    if not isinstance(url, str) or not url:
                        raise ValueError("Missing 'url' for HTTP/SSE MCP server")

                    headers = cfg.get("headers")
                    headers_dict = headers if isinstance(headers, dict) else None
                    headers_typed = (
                        {str(k): v for k, v in headers_dict.items()} if headers_dict else None
                    )

                    if server_type == "sse":
                        read, write = await stack.enter_async_context(
                            sse_client(url, headers=headers_typed)
                        )
                    else:
                        # Default for `type: http` (and omitted): streamable HTTP.
                        read, write, _get_session_id = await stack.enter_async_context(
                            streamable_http_client(url)
                        )
                else:
                    raise ValueError("Expected either 'command' or 'url' in MCP server config")

                session = await stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                listed = await session.list_tools()

                for mcp_tool in listed.tools:
                    # Always namespace to avoid collisions with built-in tools.
                    tool_name = f"{server_name}__{mcp_tool.name}"
                    description = mcp_tool.description or mcp_tool.title or ""
                    if description:
                        description = f"[MCP:{server_name}] {description}"
                    else:
                        description = f"[MCP:{server_name}]"

                    input_schema = mcp_tool.inputSchema or {
                        "type": "object",
                        "properties": {},
                    }

                    async def _call_mcp_tool(
                        *,
                        _session: Any = session,
                        _mcp_tool_name: str = mcp_tool.name,
                        **kwargs: Any,
                    ) -> str:
                        result = await _session.call_tool(_mcp_tool_name, kwargs)
                        if getattr(result, "isError", False):
                            msg = _format_call_tool_result(result) or "MCP tool call failed"
                            raise ToolException(msg)
                        return _format_call_tool_result(result)

                    tools.append(
                        StructuredTool.from_function(
                            coroutine=_call_mcp_tool,
                            name=tool_name,
                            description=description,
                            args_schema=input_schema,
                            metadata={
                                "source": "mcp",
                                "mcp_server": server_name,
                                "mcp_tool": mcp_tool.name,
                                "mcp_transport": "stdio" if "command" in cfg else "http",
                            },
                        )
                    )

            except Exception as e:  # noqa: BLE001
                errors.append(
                    f"Failed to connect MCP server '{server_name}': {type(e).__name__}: {e}"
                )
                continue

        yield McpToolset(tools=tools, config_path=config_path, errors=errors)
