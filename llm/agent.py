from typing import AsyncIterator, Any
from datetime import datetime

from langchain.agents import create_agent
from langchain_core.messages import (
    AIMessageChunk,
    SystemMessage,
    HumanMessage,
    BaseMessage,
)
from langchain_mcp_adapters.client import MultiServerMCPClient

from integrations.tavily import tavily_search
from integrations.wikipedia import wikipedia
from integrations.weather import weather
from integrations.klipy import gif_search
from integrations.webpage_reader import read_webpage
from integrations.python_repl import python_repl
from integrations.google_calendar import list_calendar_events
from integrations.mcp_tools import HA_MCP_CONFIG
from llm.model_router import get_model

from observability.langfuse import langfuse  # noqa F401
from langfuse.langchain import CallbackHandler

# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()

_system_prompt = SystemMessage(
    content=[
        {
            "type": "text",
            "text": f"You're a chatbot. Please keep your responses concise, specifically to below 300 words. Today is {datetime.today().strftime('%Y-%m-%d')}.",
        }
    ]
)


def invoke_agent(message: str) -> str:
    """Handle llm command by invoking the LLM."""
    try:
        agent = create_agent(
            get_model(message),
            system_prompt=_system_prompt,
            tools=[
                tavily_search,
                wikipedia,
                weather,
                gif_search,
                read_webpage,
                list_calendar_events,
            ],
        )
        response = agent.invoke(message, config={"callbacks": [langfuse_handler]})
        content = response.content
    except Exception as e:
        content = f"Error invoking LLM: {str(e)}"
    return content


async def astream_agent(
    input: str, msg_history: list[BaseMessage]
) -> AsyncIterator[dict[str, Any] | Any]:
    messages = [
        _system_prompt,
        # *msg_history,  # remove history to reduce context size
        HumanMessage(content=input),
    ]

    try:
        mcp_client = MultiServerMCPClient(HA_MCP_CONFIG)
        tools = [
            tavily_search,
            wikipedia,
            weather,
            gif_search,
            read_webpage,
            list_calendar_events,
        ] + await mcp_client.get_tools()
        agent = create_agent(get_model(input), system_prompt=_system_prompt, tools=tools)
        async for item in agent.astream(
            {"messages": messages},
            stream_mode="messages",
            config={"callbacks": [langfuse_handler]},
        ):
            yield item
    except Exception as e:
        import traceback

        traceback.print_exc()
        yield AIMessageChunk(content=f"Error streaming LLM response: {str(e)}"), {}
