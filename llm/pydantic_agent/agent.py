"""
Pydantic AI deep agent with todos and a virtual filesystem.

Storage is pluggable via FilesystemBackend and MessageBackend protocols —
swap in postgres (or any other backend) by implementing those two protocols
and passing them to PydanticDeepAgent().
"""

from __future__ import annotations

from typing import AsyncIterator, Callable

from pydantic_ai import Agent

from llm.pydantic_agent.deps import (
    AgentDeps,
    FilesystemBackend,
    InMemoryBackend,
    InMemoryMessageBackend,
    MessageBackend,
)

_SYSTEM_PROMPT = """\
You are a capable deep agent. You can:
- Plan tasks by writing and updating TODOS.md with write_file / read_file / edit_file
- Read, write, list, and edit other files in a persistent virtual filesystem

Always start by writing a plan to TODOS.md before acting on a multi-step task.
"""

agent: Agent[AgentDeps, str] = Agent(
    "google-gla:gemini-2.5-flash",
    deps_type=AgentDeps,
    system_prompt=_SYSTEM_PROMPT,
)


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
        fs_factory: Callable[[str], FilesystemBackend] | None = None,
    ) -> None:
        self._message_store = messages or InMemoryMessageBackend()
        self._fs_factory = fs_factory or _make_fs_factory()

    @classmethod
    async def create(
        cls,
        *,
        messages: MessageBackend | None = None,
        fs_factory: Callable[[str], FilesystemBackend] | None = None,
    ) -> "PydanticDeepAgent":
        return cls(messages=messages, fs_factory=fs_factory)

    async def astream(
        self, message: str, user_id: str = "default"
    ) -> AsyncIterator[str]:
        history = await self._message_store.load(user_id)
        deps = AgentDeps(
            fs=self._fs_factory(user_id),
            user_id=user_id
        )

        async with agent.run_stream(
            message, deps=deps, message_history=history
        ) as result:
            async for chunk in result.stream_text(delta=True):
                yield chunk
            new_messages = result.new_messages()
        await self._message_store.save(user_id, history + new_messages)

    async def close(self) -> None:
        pass
