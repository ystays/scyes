from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class FilesystemBackend(Protocol):
    async def ls(self, path: str) -> list[str]: ...
    async def read(self, path: str) -> str: ...
    async def write(self, path: str, content: str) -> None: ...
    async def edit(self, path: str, old: str, new: str) -> None: ...


@dataclass
class AgentDeps:
    fs: FilesystemBackend
    user_id: str
    session_id: str = ""
