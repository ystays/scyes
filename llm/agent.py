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
from integrations.giphy import giphy
from integrations.mcp import HA_MCP_CONFIG
from integrations.msg_scheduler import create_msg_scheduler_tool

# from llm.model_router import get_model
from llm.google import google_model

from observability.langfuse import langfuse  # noqa F401
from langfuse.langchain import CallbackHandler

# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()

_system_prompt = SystemMessage(
    content=[
        {
            "type": "text",
            "text": f"You're a chatbot. Please keep your responses concise, specifically to below 300 words. Today is {datetime.today().strftime('%Y-%m-%d')}. The current time is {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')} UTC. When scheduling messages, always convert times to ISO 8601 UTC format before calling msg_scheduler.",
        }
    ]
)


def invoke_agent(message: str) -> str:
    """Handle llm command by invoking the LLM."""
    try:
        agent = create_agent(
            google_model,
            system_prompt=_system_prompt,
            tools=[
                tavily_search,
                wikipedia,
                giphy,
            ],
        )
        response = agent.invoke(message, config={"callbacks": [langfuse_handler]})
        content = response.content
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
    messages = [
        # *msg_history,  # remove history to reduce context size
        HumanMessage(content=input),
    ]

    try:
        mcp_client = MultiServerMCPClient(HA_MCP_CONFIG)
        tools = (
            [
                tavily_search,
                wikipedia,
                giphy,
            ]
            + [create_msg_scheduler_tool(bot, channel_id, scheduler)]
            + await mcp_client.get_tools()
        )
        agent = create_agent(google_model, system_prompt=_system_prompt, tools=tools)
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
