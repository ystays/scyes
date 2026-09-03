"""ChatGPT Plus/Pro (OpenAI Codex subscription) support for pydantic-agent.

Credentials are stored in ``~/.pi/agent/auth.json`` under the
``openai-codex`` key, can be created with the device-code flow, and are refreshed
before model requests.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator

import httpx
from openai import AsyncOpenAI
from pydantic_ai.models import Model, ModelRequestParameters, StreamedResponse
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import RequestUsage
from pydantic_ai.messages import ModelMessage, ModelResponse

CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
AUTH_BASE_URL = "https://auth.openai.com"
TOKEN_URL = f"{AUTH_BASE_URL}/oauth/token"
DEVICE_USER_CODE_URL = f"{AUTH_BASE_URL}/api/accounts/deviceauth/usercode"
DEVICE_TOKEN_URL = f"{AUTH_BASE_URL}/api/accounts/deviceauth/token"
DEVICE_VERIFICATION_URI = f"{AUTH_BASE_URL}/codex/device"
DEVICE_REDIRECT_URI = f"{AUTH_BASE_URL}/deviceauth/callback"
DEVICE_CODE_TIMEOUT_SECONDS = 15 * 60
JWT_CLAIM_PATH = "https://api.openai.com/auth"
DEFAULT_AUTH_PATH = Path.home() / ".pi" / "agent" / "auth.json"
DEFAULT_CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"
DEFAULT_CODEX_MODEL = "gpt-5.5"


@dataclass(slots=True)
class OpenAICodexCredential:
    access: str
    refresh: str
    expires: int
    account_id: str

    def to_auth_json(self) -> dict[str, Any]:
        return {
            "type": "oauth",
            "access": self.access,
            "refresh": self.refresh,
            "expires": self.expires,
            "accountId": self.account_id,
        }


def _auth_path() -> Path:
    return Path(os.environ.get("PI_CODEX_AUTH_PATH", DEFAULT_AUTH_PATH)).expanduser()


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT access token")
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


def _account_id_from_access_token(access_token: str) -> str:
    payload = _decode_jwt_payload(access_token)
    account_id = payload.get(JWT_CLAIM_PATH, {}).get("chatgpt_account_id")
    if not account_id:
        raise ValueError("Could not extract chatgpt_account_id from OpenAI Codex token")
    return account_id


def _credential_from_token_response(data: dict[str, Any]) -> OpenAICodexCredential:
    access = data.get("access_token")
    refresh = data.get("refresh_token")
    expires_in = data.get("expires_in")
    if not access or not refresh or not isinstance(expires_in, int):
        raise RuntimeError(f"OpenAI Codex token response missing fields: {data}")
    return OpenAICodexCredential(
        access=access,
        refresh=refresh,
        expires=int(time.time() * 1000) + expires_in * 1000,
        account_id=_account_id_from_access_token(access),
    )


class OpenAICodexAuthStore:
    """Read/write Pi-compatible ``auth.json`` credentials for openai-codex."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _auth_path()

    def load(self) -> OpenAICodexCredential | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text())
        raw = data.get("openai-codex")
        if not isinstance(raw, dict) or raw.get("type") != "oauth":
            return None
        access = raw.get("access")
        refresh = raw.get("refresh")
        expires = raw.get("expires")
        account_id = raw.get("accountId") or raw.get("account_id")
        if not access or not refresh or not isinstance(expires, int):
            return None
        if not account_id:
            account_id = _account_id_from_access_token(access)
        return OpenAICodexCredential(access=access, refresh=refresh, expires=expires, account_id=account_id)

    def save(self, credential: OpenAICodexCredential) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        data: dict[str, Any] = {}
        if self.path.exists():
            data = json.loads(self.path.read_text())
        data["openai-codex"] = credential.to_auth_json()
        self.path.write_text(json.dumps(data, indent=2))
        self.path.chmod(0o600)


async def refresh_openai_codex_credential(refresh_token: str) -> OpenAICodexCredential:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": CLIENT_ID,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if response.status_code >= 400:
        raise RuntimeError(f"OpenAI Codex token refresh failed ({response.status_code}): {response.text}")
    return _credential_from_token_response(response.json())


async def login_openai_codex_device_code(store: OpenAICodexAuthStore | None = None) -> OpenAICodexCredential:
    """Run the headless device-code flow and persist a Pi-compatible credential."""
    store = store or OpenAICodexAuthStore()
    async with httpx.AsyncClient(timeout=30) as client:
        start = await client.post(
            DEVICE_USER_CODE_URL,
            json={"client_id": CLIENT_ID},
            headers={"Content-Type": "application/json"},
        )
        if start.status_code >= 400:
            raise RuntimeError(f"OpenAI Codex device-code request failed ({start.status_code}): {start.text}")
        device = start.json()
        device_auth_id = device.get("device_auth_id")
        user_code = device.get("user_code")
        interval = int(device.get("interval", 5))
        if not device_auth_id or not user_code:
            raise RuntimeError(f"Invalid OpenAI Codex device-code response: {device}")

        print(f"Open {DEVICE_VERIFICATION_URI} and enter code: {user_code}")
        deadline = time.monotonic() + DEVICE_CODE_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            await asyncio.sleep(interval)
            poll = await client.post(
                DEVICE_TOKEN_URL,
                json={"device_auth_id": device_auth_id, "user_code": user_code},
                headers={"Content-Type": "application/json"},
            )
            if poll.status_code == 200:
                payload = poll.json()
                authorization_code = payload.get("authorization_code")
                code_verifier = payload.get("code_verifier")
                if not authorization_code or not code_verifier:
                    raise RuntimeError(f"Invalid OpenAI Codex device auth response: {payload}")
                token = await client.post(
                    TOKEN_URL,
                    data={
                        "grant_type": "authorization_code",
                        "client_id": CLIENT_ID,
                        "code": authorization_code,
                        "code_verifier": code_verifier,
                        "redirect_uri": DEVICE_REDIRECT_URI,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                if token.status_code >= 400:
                    raise RuntimeError(f"OpenAI Codex token exchange failed ({token.status_code}): {token.text}")
                credential = _credential_from_token_response(token.json())
                store.save(credential)
                return credential

            if poll.status_code in {403, 404}:
                continue
            try:
                error = poll.json().get("error")
                code = error.get("code") if isinstance(error, dict) else error
            except Exception:
                code = None
            if code in {"deviceauth_authorization_pending", "authorization_pending"}:
                continue
            if code == "slow_down":
                interval += 5
                continue
            raise RuntimeError(f"OpenAI Codex device auth failed ({poll.status_code}): {poll.text}")

    raise TimeoutError("OpenAI Codex device-code login timed out")


class ChatGPTCodexModel(Model):
    """Pydantic AI model backed by a ChatGPT Plus/Pro Codex subscription."""

    def __init__(
        self,
        model_name: str = DEFAULT_CODEX_MODEL,
        *,
        store: OpenAICodexAuthStore | None = None,
        base_url: str = DEFAULT_CODEX_BASE_URL,
    ) -> None:
        super().__init__()
        self._model_name = model_name
        self._store = store or OpenAICodexAuthStore()
        self._base_url = base_url
        self._credential: OpenAICodexCredential | None = None
        self._delegate: OpenAIResponsesModel | None = None
        self._lock = asyncio.Lock()

    @property
    def model_name(self) -> str:
        return self._model_name

    async def _get_credential(self) -> OpenAICodexCredential:
        async with self._lock:
            credential = self._credential or self._store.load()
            if credential is None:
                raise RuntimeError(
                    "Missing ChatGPT Plus/Pro credentials. Run `pyd-agent --login-openai-codex` "
                    "or log in with Pi using `/login` and select ChatGPT Plus/Pro."
                )
            # Refresh one minute early.
            if credential.expires <= int(time.time() * 1000) + 60_000:
                credential = await refresh_openai_codex_credential(credential.refresh)
                self._store.save(credential)
            if self._credential != credential:
                self._credential = credential
                self._delegate = None
            return credential

    async def _get_delegate(self) -> OpenAIResponsesModel:
        credential = await self._get_credential()
        if self._delegate is None:
            client = AsyncOpenAI(
                api_key=credential.access,
                base_url=self._base_url,
                default_headers={
                    "chatgpt-account-id": credential.account_id,
                    "originator": "scyes-pydantic-agent",
                    "OpenAI-Beta": "responses=experimental",
                },
                max_retries=0,
            )
            self._delegate = OpenAIResponsesModel(
                self._model_name, provider=OpenAIProvider(openai_client=client)
            )
        return self._delegate

    def _codex_model_settings(self, model_settings: Any) -> dict[str, Any]:
        settings = dict(model_settings or {})
        # ChatGPT/Codex subscription backend rejects the OpenAI default/omitted
        # value and requires store=false explicitly.
        settings["openai_store"] = False
        return settings

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: Any,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        return await (await self._get_delegate()).request(
            messages, self._codex_model_settings(model_settings), model_request_parameters
        )

    async def count_tokens(
        self,
        messages: list[ModelMessage],
        model_settings: Any,
        model_request_parameters: ModelRequestParameters,
    ) -> RequestUsage:
        return await (await self._get_delegate()).count_tokens(
            messages, self._codex_model_settings(model_settings), model_request_parameters
        )

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: Any,
        model_request_parameters: ModelRequestParameters,
        run_context: Any | None = None,
    ) -> AsyncIterator[StreamedResponse]:
        async with (await self._get_delegate()).request_stream(
            messages, self._codex_model_settings(model_settings), model_request_parameters, run_context
        ) as response:
            yield response
