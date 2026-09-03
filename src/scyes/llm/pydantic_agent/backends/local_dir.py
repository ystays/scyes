from pathlib import Path


class LocalDirBackend:
    """Reads and writes real files inside a given root directory."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root).expanduser().resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        raw = Path(path).expanduser()
        resolved = raw.resolve() if raw.is_absolute() else (self._root / raw).resolve()
        if not resolved.is_relative_to(self._root):
            raise PermissionError(f"Path escapes agent dir: {path}")
        return resolved

    async def ls(self, path: str = "") -> list[str]:
        target = self._resolve(path) if path else self._root
        if not target.exists():
            return []
        if target.is_file():
            return [target.name]
        return sorted(
            (str(p.relative_to(self._root)) for p in target.iterdir()),
            key=lambda s: (not Path(s).is_dir(), s),
        )

    async def read(self, path: str) -> str:
        p = self._resolve(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return p.read_text(errors="replace")

    async def write(self, path: str, content: str) -> None:
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    async def edit(self, path: str, old: str, new: str) -> None:
        p = self._resolve(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        text = p.read_text(errors="replace")
        if old not in text:
            raise ValueError(f"String not found in {path}: {old!r}")
        p.write_text(text.replace(old, new, 1))
