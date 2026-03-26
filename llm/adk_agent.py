import logging
import os
import uuid
from datetime import datetime, timezone
from typing import AsyncIterator

import wikipedia as wiki_api
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from config import app_config
from integrations.tavily import tavily_search
from integrations.giphy import giphy
from integrations.wikipedia import wikipedia

logger = logging.getLogger(__name__)

# Set API key for ADK
os.environ.setdefault("GOOGLE_API_KEY", app_config.google_api_key)

APP_NAME = "scyes"
_session_service = InMemorySessionService()


# --- Tools ---
def get_current_datetime() -> dict:
    """Returns the current date and time in UTC."""
    now = datetime.now(timezone.utc)
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time_utc": now.strftime("%Y-%m-%dT%H:%M:%S"),
    }

def search_web(query: str) -> str:
    """Search the web for current information using Tavily."""
    return tavily_search.run(query)

def search_wikipedia(query: str) -> str:
    """Search Wikipedia for general knowledge about a topic."""
    return wikipedia.run(query)

def search_giphy(query: str) -> str:
    """Search Giphy for a relevant GIF URL."""
    return giphy.run(query)


_agent = Agent(
    name="scyes_agent",
    model="gemini-2.5-flash",
    description="A helpful Discord chatbot assistant.",
    instruction=(
        "You're a helpful chatbot. Keep responses concise (under 300 words). "
        "Use tools when you need current information or to answer factual questions."
    ),
    tools=[
        get_current_datetime,
        search_web,
        search_wikipedia,
        search_giphy
    ],
)

# --- Runner helpers ---
def _make_runner() -> Runner:
    return Runner(
        agent=_agent,
        app_name=APP_NAME,
        session_service=_session_service,
    )


async def ainvoke_adk_agent(message: str) -> str:
    """Invoke the ADK agent asynchronously and return the final response."""
    return await _invoke_async(message)


async def _invoke_async(message: str) -> str:
    user_id = "discord_user"
    session_id = str(uuid.uuid4())

    await _session_service.create_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )

    runner = _make_runner()
    user_message = Content(role="user", parts=[Part(text=message)])

    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=user_message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            return event.content.parts[0].text

    return "No response generated."


async def astream_adk_agent(message: str) -> AsyncIterator[str]:
    """Stream the ADK agent's final response text."""
    user_id = "discord_user"
    session_id = str(uuid.uuid4())

    await _session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )

    runner = _make_runner()
    user_message = Content(role="user", parts=[Part(text=message)])

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            yield event.content.parts[0].text
