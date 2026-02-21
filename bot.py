import time
from typing import Any, AsyncIterator

from discord import Intents, Message
from discord.ext import commands
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage

from config import app_config
from llm.agent import astream_agent
from llm.llm import astream
from observability.logging import configure_logging

intents = Intents.default()
intents.message_content = True

load_dotenv()

logger = configure_logging()

bot = commands.Bot(command_prefix='>', intents=intents)


@bot.event
async def on_ready():
    logger.info(
        "Bot connected",
        extra={"event": "bot_ready"},
    )


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    logger.exception(
        "Command failed",
        extra={
            "event": "command_error",
            "command": ctx.command.name if ctx.command else "unknown",
            "guild_id": str(ctx.guild.id) if ctx.guild else "dm",
            "channel_id": str(ctx.channel.id),
            "user_id": str(ctx.author.id),
        },
    )
    raise error


@bot.command()
async def ping(ctx):
    await ctx.send('pong')


@bot.command()
async def add(ctx, left: int, right: int):
    """Adds two numbers together."""
    await ctx.send(left + right)


@bot.command()
async def llm(ctx: commands.Context, *, input: str):
    """Chat with 4B model (faster responses)"""
    start = time.perf_counter()
    logger.info(
        "LLM command started",
        extra={
            "event": "command_start",
            "command": "llm",
            "guild_id": str(ctx.guild.id) if ctx.guild else "dm",
            "channel_id": str(ctx.channel.id),
            "user_id": str(ctx.author.id),
        },
    )

    message: Message = await ctx.send("thinking...")

    msg_history: list[BaseMessage] = [
        AIMessage(content=msg.content)
        if msg.author.bot
        else HumanMessage(content=msg.author.name + ": " + msg.content)
        async for msg in message.channel.history(limit=8)
    ]

    buffer = ""
    msg_history.reverse()
    response: AsyncIterator[AIMessageChunk] = astream(input, msg_history[:-2])

    async for chunk in response:
        buffer += chunk.content

        if len(buffer) > 2000:
            break

        if len(buffer) % 5 == 0:
            await message.edit(content=buffer + "...")

    await message.edit(content=buffer)

    logger.info(
        "LLM command completed",
        extra={
            "event": "command_complete",
            "command": "llm",
            "guild_id": str(ctx.guild.id) if ctx.guild else "dm",
            "channel_id": str(ctx.channel.id),
            "user_id": str(ctx.author.id),
            "latency_ms": int((time.perf_counter() - start) * 1000),
        },
    )


@bot.command()
async def llma(ctx: commands.Context, *, input: str):
    """Chat with agent (tool calls, slower responses)"""
    start = time.perf_counter()
    logger.info(
        "Agent command started",
        extra={
            "event": "command_start",
            "command": "llma",
            "guild_id": str(ctx.guild.id) if ctx.guild else "dm",
            "channel_id": str(ctx.channel.id),
            "user_id": str(ctx.author.id),
        },
    )

    message: Message = await ctx.send("thinking...")

    msg_history: list[BaseMessage] = [
        AIMessage(content=msg.content)
        if msg.author.bot
        else HumanMessage(content=msg.author.name + ": " + msg.content)
        async for msg in message.channel.history(limit=8)
    ]

    buffer = ""
    msg_history.reverse()
    response: AsyncIterator[dict[str, Any] | Any] = astream_agent(input, msg_history[:-2])

    async for token, _metadata in response:
        if len(token.content_blocks) == 0 or token.content_blocks[-1]["type"] != "text":
            continue

        buffer += token.content_blocks[0]["text"]

        if len(buffer) > 2000:
            break

        if len(buffer) % 5 == 0:
            await message.edit(content=buffer + "...")

    await message.edit(content=buffer)

    logger.info(
        "Agent command completed",
        extra={
            "event": "command_complete",
            "command": "llma",
            "guild_id": str(ctx.guild.id) if ctx.guild else "dm",
            "channel_id": str(ctx.channel.id),
            "user_id": str(ctx.author.id),
            "latency_ms": int((time.perf_counter() - start) * 1000),
        },
    )


bot.run(app_config.discord_token)
