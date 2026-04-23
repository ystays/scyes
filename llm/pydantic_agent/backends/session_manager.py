import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from llm.pydantic_agent.deps import FilesystemBackend

_SESSIONS_DIR = ".sessions"


@dataclass
class SessionMeta:
    session_id: str
    user_id: str
    created_at: str  # ISO format


class SessionManager:
    def __init__(self, fs: FilesystemBackend) -> None:
        self._fs = fs

    async def create_session(self, user_id: str) -> str:
        session_id = str(uuid.uuid4())
        meta = SessionMeta(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        await self._fs.write(f"{_SESSIONS_DIR}/{session_id}/meta.json", json.dumps(asdict(meta)))
        await self._fs.write(f"{_SESSIONS_DIR}/{session_id}/messages.json", "[]")
        return session_id

    async def list_sessions(self, user_id: str) -> list[SessionMeta]:
        try:
            entries = await self._fs.ls(_SESSIONS_DIR)
        except FileNotFoundError:
            return []
        sessions = []
        for entry in entries:
            try:
                raw = await self._fs.read(f"{entry}/meta.json")
                data = json.loads(raw)
                if data.get("user_id") == user_id:
                    sessions.append(SessionMeta(**data))
            except (FileNotFoundError, KeyError):
                continue
        return sessions

    async def load_messages(self, session_id: str) -> list[ModelMessage]:
        try:
            raw = await self._fs.read(f"{_SESSIONS_DIR}/{session_id}/messages.json")
            return ModelMessagesTypeAdapter.validate_json(raw)
        except FileNotFoundError:
            return []

    async def save_messages(self, session_id: str, messages: list[ModelMessage]) -> None:
        data = ModelMessagesTypeAdapter.dump_json(messages).decode()
        await self._fs.write(f"{_SESSIONS_DIR}/{session_id}/messages.json", data)
