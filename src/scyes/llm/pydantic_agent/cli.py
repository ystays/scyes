"""CLI entry point for the pydantic-ai deep agent.

Usage:
    pyd-agent                          # local home-directory backend, new session
    pyd-agent --dir ./agent_workspace  # persist files to a local directory
    pyd-agent --memory                 # use an in-memory backend
    pyd-agent --session <id>           # resume a previous session
    pyd-agent --list-sessions          # show saved sessions
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from getpass import getuser
from pathlib import Path

from pydantic_ai.models.google import GoogleModel

from scyes.llm.google import GEMINI_3_1_FLASH_LITE
from scyes.llm.pydantic_agent.agent import create_pyd_agent
from scyes.llm.pydantic_agent.backends import InMemoryBackend, LocalDirBackend, SessionManager
from scyes.llm.pydantic_agent.deps import AgentDeps
from scyes.llm.pydantic_agent.openai_codex import DEFAULT_CODEX_MODEL, ChatGPTCodexModel, login_openai_codex_device_code


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="pyd-agent",
        description="Interactive deep agent with filesystem tools.",
    )
    p.add_argument("--dir", metavar="PATH", help="Persist agent files in this directory (default: home directory)")
    p.add_argument("--memory", action="store_true", help="Use a temporary in-memory filesystem instead of local files")
    p.add_argument("--provider", choices=["google", "chatgpt-plus"], default="google", help="Model provider")
    p.add_argument("--model", default=None, help="Model ID (Gemini by default, GPT Codex for chatgpt-plus)")
    p.add_argument("--login-openai-codex", action="store_true", help="Log in to ChatGPT Plus/Pro via OpenAI Codex device-code flow and exit")
    p.add_argument("--user", default=getuser(), help="User ID (default: current OS user)")
    p.add_argument("--session", metavar="ID", help="Resume an existing session by ID")
    p.add_argument("--list-sessions", action="store_true", help="List saved sessions and exit")
    args = p.parse_args()
    if args.memory and args.dir:
        p.error("--memory cannot be used with --dir")
    return args


async def _run(args: argparse.Namespace) -> None:
    if args.login_openai_codex:
        await login_openai_codex_device_code()
        print("Saved OpenAI Codex credentials.")
        return

    if args.memory:
        fs = InMemoryBackend()
    else:
        fs = LocalDirBackend(args.dir or Path.home())
    sm = SessionManager(fs)

    if args.list_sessions:
        sessions = await sm.list_sessions(args.user)
        if not sessions:
            print("No sessions found.")
        for s in sessions:
            print(f"  {s.session_id}  (created {s.created_at})")
        return

    if args.session:
        session_id = args.session
        history = await sm.load_messages(session_id)
        print(f"Resumed session {session_id} ({len(history)} messages)")
    else:
        session_id = await sm.create_session(args.user)
        history = []
        print(f"New session {session_id}")

    if args.provider == "chatgpt-plus":
        model = ChatGPTCodexModel(args.model or DEFAULT_CODEX_MODEL)
    else:
        model = GoogleModel(args.model or GEMINI_3_1_FLASH_LITE)

    agent = create_pyd_agent(model)
    deps = AgentDeps(fs=fs, user_id=args.user, session_id=session_id)

    print("Type your message (Ctrl-D or 'exit' to quit).\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input or user_input.lower() in {"exit", "quit"}:
            break

        print("Agent: ", end="", flush=True)
        async with agent.run_stream(user_input, deps=deps, message_history=history) as result:
            async for chunk in result.stream_text(delta=True):
                print(chunk, end="", flush=True)
            print()
            history = result.all_messages()

        await sm.save_messages(session_id, history)


def main() -> None:
    args = _parse_args()
    try:
        asyncio.run(_run(args))
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
