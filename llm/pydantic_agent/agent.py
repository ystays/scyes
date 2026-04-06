"""
Pydantic AI deep agent with todos and a virtual filesystem.

Storage is pluggable via FilesystemBackend and MessageBackend protocols —
swap in postgres (or any other backend) by implementing those two protocols
and passing them to PydanticDeepAgent().
"""

from __future__ import annotations

from typing import AsyncIterator, Callable, Sequence

from pydantic_ai import Agent
from pydantic_ai.capabilities import AbstractCapability, Hooks
from pydantic_ai.capabilities.hooks import BeforeToolExecuteHookFunc

from llm.pydantic_agent.deps import (
    AgentDeps,
    FilesystemBackend,
    InMemoryBackend,
    InMemoryMessageBackend,
    MessageBackend,
)
from llm.pydantic_agent.tools import ALL_TOOLS

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


class PydanticDeepAgent:
    def __init__(
        self,
        *,
        messages: MessageBackend | None = None,
        filesystem: Callable[[str], FilesystemBackend] | None = None,
        capabilities: Sequence[AbstractCapability] | None = None,
        before_tool_call: BeforeToolExecuteHookFunc | None = None,
    ) -> None:
        self._message_store = messages or InMemoryMessageBackend()
        self._filesystem = filesystem or _make_fs_factory()

        all_capabilities: list[AbstractCapability] = list(capabilities or [])
        if before_tool_call is not None:
            hooks = Hooks()
            hooks.on.before_tool_execute(before_tool_call)
            all_capabilities.append(hooks)

        self._agent: Agent[AgentDeps, str] = Agent(
            "google-gla:gemini-2.5-flash",
            deps_type=AgentDeps,
            system_prompt=_SYSTEM_PROMPT,
            capabilities=all_capabilities or None,
        )
        for tool_fn in ALL_TOOLS:
            self._agent.tool(tool_fn)

    async def ainvoke(self, message: str, user_id: str = "default") -> str:
        history = await self._message_store.load(user_id)
        deps = AgentDeps(fs=self._filesystem(user_id), user_id=user_id)

        result = await self._agent.run(message, deps=deps, message_history=history)
        await self._message_store.save(user_id, history + result.new_messages())

        return result.output

    async def astream(
        self, message: str, user_id: str = "default"
    ) -> AsyncIterator[str]:
        history = await self._message_store.load(user_id)
        deps = AgentDeps(fs=self._filesystem(user_id), user_id=user_id)

        async with self._agent.run_stream(
            message, deps=deps, message_history=history
        ) as result:
            async for chunk in result.stream_text(delta=True):
                yield chunk
            new_messages = result.new_messages()
        await self._message_store.save(user_id, history + new_messages)

    async def close(self) -> None:
        pass


def create_pydantic_agent(
    *,
    messages: MessageBackend | None = None,
    filesystem: Callable[[str], FilesystemBackend] | None = None,
    capabilities: Sequence[AbstractCapability] | None = None,
    before_tool_call: BeforeToolExecuteHookFunc | None = None,
) -> PydanticDeepAgent:
    return PydanticDeepAgent(
        messages=messages,
        filesystem=filesystem,
        capabilities=capabilities,
        before_tool_call=before_tool_call,
    )
