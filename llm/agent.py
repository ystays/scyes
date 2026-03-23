from typing import AsyncIterator, Any
from datetime import datetime
import traceback
import logging

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
from integrations.giphy import giphy
from integrations.google_calendar import list_calendar_events, create_calendar_event
from integrations.mcp import HA_MCP_CONFIG
from integrations.msg_scheduler import create_msg_scheduler_tool

# from llm.model_router import get_model
from llm.google import google_model

from observability.langfuse import langfuse  # noqa F401
from langfuse.langchain import CallbackHandler

# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()

logger = logging.getLogger(__name__)


def invoke_agent(message: str) -> str:
    """Handle llm command by invoking the LLM."""
    system_prompt = SystemMessage(
        content=[
            {
                "type": "text",
                "text": f"You're a chatbot. Please keep your responses concise, specifically to below 300 words. Today is {datetime.today().strftime('%Y-%m-%d')}. The current time is {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')} UTC. When scheduling messages, always convert times to ISO 8601 UTC format before calling msg_scheduler.",
            }
        ]
    )
    try:
        agent = create_agent(
            google_model,
            system_prompt=system_prompt,
            tools=[
                tavily_search,
                wikipedia,
                giphy,
                list_calendar_events,
                create_calendar_event,
            ],
        )
        response = agent.invoke({"messages": [HumanMessage(content=message)]}, config={"callbacks": [langfuse_handler]})
        content = response["messages"][-1].content
    except Exception as e:
        content = f"Error invoking LLM: {str(e)}"
    return content


async def astream_agent(
    input: str,
    msg_history: list[BaseMessage],
    bot=None,
    channel_id: int = 0,
    scheduler=None,
) -> AsyncIterator[dict[str, Any] | Any]:
    system_prompt = SystemMessage(
        content=[
            {
                "type": "text",
                "text": f"You're a chatbot. Please keep your responses concise, specifically to below 300 words. Today is {datetime.today().strftime('%Y-%m-%d')}. The current time is {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')} UTC. When scheduling messages, always convert times to ISO 8601 UTC format before calling msg_scheduler.",
            }
        ]
    )

    messages = [
        *msg_history,
        HumanMessage(content=input),
    ]

    try:
        mcp_client = MultiServerMCPClient(HA_MCP_CONFIG)
        try:
            mcp_tools = await mcp_client.get_tools()
        except Exception as mcp_err:
            logger.warning(f"MCP tools unavailable, skipping: {mcp_err}")
            mcp_tools = []

        tools = (
            [
                tavily_search,
                wikipedia,
                giphy,
                list_calendar_events,
            ]
            + [create_msg_scheduler_tool(bot, channel_id, scheduler)]
            + mcp_tools
        )
        agent = create_agent(google_model, system_prompt=system_prompt, tools=tools)
        async for item in agent.astream(
            {"messages": messages},
            stream_mode="messages",
            config={"callbacks": [langfuse_handler]},
        ):
            yield item
    except Exception as e:
        traceback.print_exc()
        yield AIMessageChunk(content=f"Error streaming LLM response: {str(e)}"), {}
