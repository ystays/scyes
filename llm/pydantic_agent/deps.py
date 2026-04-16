from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class FilesystemBackend(Protocol):
    async def ls(self, path: str) -> list[str]: ...
    async def read(self, path: str) -> str: ...
    async def write(self, path: str, content: str) -> None: ...
    async def edit(self, path: str, old: str, new: str) -> None: ...


class InMemoryBackend:
    def __init__(self) -> None:
        self._files: dict[str, str] = {}

    async def ls(self, path: str) -> list[str]:
        prefix = path.rstrip("/") + "/"
        if path in ("", "/"):
            return list(self._files)
        return [k for k in self._files if k.startswith(prefix)]

    async def read(self, path: str) -> str:
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
        return self._files[path]

    async def write(self, path: str, content: str) -> None:
        self._files[path] = content

    async def edit(self, path: str, old: str, new: str) -> None:
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
        if old not in self._files[path]:
            raise ValueError(f"String not found in {path}: {old!r}")
        self._files[path] = self._files[path].replace(old, new, 1)


@dataclass
class AgentDeps:
    fs: FilesystemBackend
    user_id: str
