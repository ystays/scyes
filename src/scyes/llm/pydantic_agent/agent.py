"""
Pydantic AI deep agent with todos and a virtual filesystem.

Storage is pluggable via FilesystemBackend — swap in postgres (or any other
backend) by implementing that protocol and passing it to pyd_agent.
"""

from __future__ import annotations

import os
from typing import Any, Callable, Sequence

from pydantic_ai import Agent
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.capabilities.hooks import BeforeToolExecuteHookFunc
from pydantic_ai.mcp import MCPServer
from pydantic_ai.models import Model
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from scyes.config import app_config

from scyes.llm.google import GEMINI_3_1_FLASH_LITE, google_model
from scyes.llm.pydantic_agent.backends import InMemoryBackend
from scyes.llm.pydantic_agent.deps import AgentDeps, FilesystemBackend
from scyes.llm.pydantic_agent.openai_codex import DEFAULT_CODEX_MODEL, ChatGPTCodexModel
from scyes.llm.pydantic_agent.tools import bash, edit_file, ls, read_file, write_file

_SYSTEM_PROMPT = """\
You are a capable deep agent. You can:
- Plan tasks by writing and updating TODOS.md with write_file / read_file / edit_file
- Read, write, list, and edit other files in a persistent virtual filesystem
"""


def _make_fs_factory() -> Callable[[str], FilesystemBackend]:
    store: dict[str, InMemoryBackend] = {}

    def factory(user_id: str) -> FilesystemBackend:
        if user_id not in store:
            store[user_id] = InMemoryBackend()
        return store[user_id]

    return factory


def create_pyd_agent(
    model: Model,
    *,
    tools: Sequence[Any] | None = None,
    instructions: str = _SYSTEM_PROMPT,
    filesystem: Callable[[str], FilesystemBackend] | None = None,
    capabilities: Sequence[AbstractCapability] | None = None,
    mcp_servers: Sequence[MCPServer] | None = None,
    before_tool_call: BeforeToolExecuteHookFunc | None = None,
) -> Agent:
    # Keep the filesystem factory parameter for callers that construct deps externally.
    _ = filesystem or _make_fs_factory()

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


def _default_model() -> Model:
    if os.environ.get("PYD_AGENT_PROVIDER") in {"chatgpt-plus", "openai-codex"}:
        return ChatGPTCodexModel(DEFAULT_CODEX_MODEL)
    return GoogleModel(GEMINI_3_1_FLASH_LITE, provider=GoogleProvider(api_key=app_config.google_api_key))


# Top-level instance for the pydantic-ai CLI and Discord bot:
#   uv run python -m pydantic_ai -a "scyes.llm.pydantic_agent.agent:agent"
# Set PYD_AGENT_PROVIDER=chatgpt-plus to use ChatGPT Plus/Pro Codex subscription auth.
agent = create_pyd_agent(_default_model())
