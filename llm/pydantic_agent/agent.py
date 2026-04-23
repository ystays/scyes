"""
Pydantic AI deep agent with todos and a virtual filesystem.

Storage is pluggable via FilesystemBackend — swap in postgres (or any other
backend) by implementing that protocol and passing it to pyd_agent.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Callable, Sequence

from pydantic_ai import Agent
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.capabilities.hooks import BeforeToolExecuteHookFunc
from pydantic_ai.mcp import MCPServer
from pydantic_ai.models.google import GoogleModel

from llm.google import GEMINI_3_1_FLASH_LITE
from llm.pydantic_agent.backends import InMemoryBackend
from llm.pydantic_agent.backends.session_manager import SessionManager
from llm.pydantic_agent.deps import AgentDeps, FilesystemBackend
from llm.pydantic_agent.tools import bash, edit_file, ls, read_file, write_file

_SYSTEM_PROMPT = """\
You are a capable deep agent. You can:
- Plan tasks by writing and updating TODOS.md with write_file / read_file / edit_file
- Read, write, list, and edit other files in a persistent virtual filesystem

Always start by writing a plan to TODOS.md before acting on a multi-step task.
"""


def _make_fs_factory() -> Callable[[str], FilesystemBackend]:
    store: dict[str, InMemoryBackend] = {}

    def factory(user_id: str) -> FilesystemBackend:
        if user_id not in store:
            store[user_id] = InMemoryBackend()
        return store[user_id]

    return factory


def create_pyd_agent(
    model: GoogleModel,
    *,
    tools: Sequence[Any] | None = None,
    instructions: str = _SYSTEM_PROMPT,
    filesystem: Callable[[str], FilesystemBackend] | None = None,
    capabilities: Sequence[AbstractCapability] | None = None,
    mcp_servers: Sequence[MCPServer] | None = None,
    before_tool_call: BeforeToolExecuteHookFunc | None = None,
) -> Agent:
    fs_factory = filesystem or _make_fs_factory()

    # Core filesystem + shell tools, plus any caller-supplied extras
    core_tools: list[Any] = [ls, read_file, bash, edit_file, write_file, *(tools or [])]

    # Build capabilities and hooks
    all_capabilities: list[AbstractCapability] = list(capabilities or [])

    return Agent(
        model=model,
        instructions=instructions,
        tools=core_tools,
        mcp_servers=list(mcp_servers) if mcp_servers else None,
        capabilities=all_capabilities,
        deps_type=AgentDeps,
    )


# Top-level instance for the pydantic-ai CLI:
#   uv run python -m pydantic_ai -a "llm.pydantic_agent.agent:agent"
agent = create_pyd_agent(GoogleModel(GEMINI_3_1_FLASH_LITE))
