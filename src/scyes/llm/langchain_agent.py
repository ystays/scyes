from typing import AsyncIterator, Any, Callable
from datetime import datetime
import logging

import discord
from langchain.agents import create_agent
from langchain_core.messages import (
    AIMessageChunk,
    SystemMessage,
    HumanMessage,
    BaseMessage,
)
from langchain_mcp_adapters.client import MultiServerMCPClient

from scyes.integrations.tavily import tavily_search
from scyes.integrations.wikipedia import wikipedia
from scyes.integrations.giphy import giphy
from scyes.integrations.google_calendar import list_calendar_events, create_calendar_event
from scyes.integrations.mcp import HA_MCP_CONFIG
from scyes.integrations.msg_scheduler import create_msg_scheduler_tool
from scyes.integrations.buttons import create_buttons_tool

# from scyes.llm.model_router import get_model
from scyes.llm.google import langchain_fallback_models, is_unavailable

from scyes.observability.langfuse import langfuse  # noqa F401
from langfuse.langchain import CallbackHandler

# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()

logger = logging.getLogger(__name__)


async def stream_agent_to_message(message, send_fn, input, msg_history, bot, channel_id, scheduler):
    buffer = ""
    chunk_count = 0
    async for token, metadata in astream_agent(input, msg_history, bot, channel_id, scheduler):
        if (
            not isinstance(token, AIMessageChunk)
            or len(token.content_blocks) == 0
            or token.content_blocks[0]["type"] != "text"
        ):
            continue

        buffer += token.content_blocks[0]["text"]
        chunk_count += 1

        if len(buffer) > 2000:
            await message.edit(content=buffer[:2000])
            buffer = buffer[2000:]
            chunk_count = 0
            message = await send_fn(buffer + "...")
            continue

        if chunk_count % 2 == 0:
            await message.edit(content=buffer + "...")

    await message.edit(content=buffer)


def make_button_callback(bot, channel_id: int, scheduler) -> Callable:
    async def on_click(interaction: discord.Interaction, value: str):
        await interaction.response.defer()
        channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
        message = await channel.send("thinking...")
        await stream_agent_to_message(message, channel.send, value, [], bot, channel_id, scheduler)

    return on_click


async def ainvoke_agent(message: str) -> str:
    """Handle llm command by invoking the LLM asynchronously."""
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
        response = await agent.ainvoke({"messages": [HumanMessage(content=message)]}, config={"callbacks": [langfuse_handler]})
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
        *msg_history,  # remove history to reduce context size
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
            ]
            + [create_msg_scheduler_tool(bot, channel_id, scheduler)]
            + [create_buttons_tool(bot, channel_id, make_button_callback(bot, channel_id, scheduler))]
            + mcp_tools
        )

        last_err = None
        for model in langchain_fallback_models:
            try:
                agent = create_agent(model, system_prompt=system_prompt, tools=tools)
                async for item in agent.astream(
                    {"messages": messages},
                    stream_mode="messages",
                    config={"callbacks": [langfuse_handler]},
                ):
                    yield item
                return
            except Exception as e:
                if is_unavailable(e):
                    logger.warning(f"Model {model.model} unavailable, trying fallback: {e}")
                    last_err = e
                    continue
                raise

        yield AIMessageChunk(content=f"Error streaming LLM response: {str(last_err)}"), {}
    except Exception as e:
        yield AIMessageChunk(content=f"Error streaming LLM response: {str(e)}"), {}
