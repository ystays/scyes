import logging
import os
import uuid
from datetime import datetime
from typing import AsyncIterator

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from scyes.config import app_config
from scyes.integrations.tavily import tavily_search
from scyes.integrations.giphy import giphy
from scyes.integrations.wikipedia import wikipedia

logger = logging.getLogger(__name__)

# Set API key for ADK
os.environ.setdefault("GOOGLE_API_KEY", app_config.google_api_key)

APP_NAME = "scyes"
_session_service = InMemorySessionService()


# --- Tools ---
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
        f"Today is {datetime.today().strftime('%Y-%m-%d')}. The current time is {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')} UTC. "
        "Use tools when you need current information or to answer factual questions."
    ),
    tools=[
        search_web,
        search_wikipedia,
        search_giphy,
    ],
)

_runner = Runner(agent=_agent, app_name=APP_NAME, session_service=_session_service)


async def _run_events(message: str):
    session_id = str(uuid.uuid4())
    await _session_service.create_session(
        app_name=APP_NAME, user_id="discord_user", session_id=session_id
    )
    user_message = Content(role="user", parts=[Part(text=message)])
    result = None
    async for event in _runner.run_async(
        user_id="discord_user", session_id=session_id, new_message=user_message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            result = event.content.parts[0].text
    if result is not None:
        yield result


async def ainvoke_adk_agent(message: str) -> str:
    """Invoke the ADK agent asynchronously and return the final response."""
    async for text in _run_events(message):
        return text
    return "No response generated."


async def astream_adk_agent(message: str) -> AsyncIterator[str]:
    """Stream the ADK agent's final response text."""
    async for text in _run_events(message):
        yield text
