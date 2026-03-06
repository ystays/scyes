import logging
from typing import AsyncIterator, Any

from discord.ext import commands
from discord import Message, Intents
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, AIMessageChunk
from dotenv import load_dotenv

from config import app_config
from llm.agent import astream_agent
from llm.llm import astream
from observability.otel import configure_otel, get_tracer


intents = Intents.default()
intents.message_content = True

load_dotenv()

bot = commands.Bot(command_prefix='>', intents=intents)


configure_otel()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

tracer = get_tracer()

@bot.before_invoke
async def track_command(ctx: commands.Context) -> None:
    command_name = ctx.command.qualified_name if ctx.command else "unknown"
    with tracer.start_as_current_span("discord.command") as span:
        span.set_attribute("discord.command", command_name)
        span.set_attribute("discord.user_id", str(ctx.author.id))
        span.set_attribute("discord.channel_id", str(ctx.channel.id))
        span.set_attribute("discord.guild_id", str(ctx.guild.id) if ctx.guild else "dm")
        logger.info(
            "Discord command called",
            extra={
                "command": command_name,
                "user_id": str(ctx.author.id),
                "channel_id": str(ctx.channel.id),
                "guild_id": str(ctx.guild.id) if ctx.guild else "dm",
            },
        )


@bot.command()
async def ping(ctx):
    """Responds with pong"""
    await ctx.send('pong')

@bot.command()
async def add(ctx, left: int, right: int):
    """Adds two numbers together"""
    await ctx.send(left + right)

@bot.command()
async def llm(ctx: commands.Context, *, input: str):
    """Chat with 4B model (faster responses)"""
    message: Message = await ctx.send("thinking...")
    
    msg_history: list[BaseMessage] = [AIMessage(content=msg.content) if msg.author.bot else HumanMessage(content=msg.author.name + ": " + msg.content) async for msg in message.channel.history(limit=8)]

    buffer = ""
    msg_history.reverse()
    response: AsyncIterator[AIMessageChunk] = astream(input, msg_history[:-2])
    
    async for chunk in response:
        buffer += chunk.content

        # If LLM output is too long, just truncate and exit for now
        if len(buffer) > 2000:
            break

        # Periodically update message (e.g., every 5 chunks to reduce API load)
        if len(buffer) % 5 == 0:
            await message.edit(content=buffer + "...")
            
    # 4. Final update
    await message.edit(content=buffer)

@bot.command()
async def llma(ctx: commands.Context, *, input: str):
    """Chat with agent (tool calls, slower responses)"""
    message: Message = await ctx.send("thinking...")
    
    msg_history: list[BaseMessage] = [AIMessage(content=msg.content) if msg.author.bot else HumanMessage(content=msg.author.name + ": " + msg.content) async for msg in message.channel.history(limit=8)]

    buffer = ""
    msg_history.reverse()
    response: AsyncIterator[dict[str, Any] | Any] = astream_agent(input, msg_history[:-2])
    
    async for token, metadata in response:
        if not isinstance(token, AIMessageChunk) or len(token.content_blocks) == 0 or token.content_blocks[-1]["type"] != "text":
            continue

        buffer += token.content_blocks[0]["text"]

        # If LLM output is too long, just truncate and exit for now
        if len(buffer) > 2000:
            break

        # Periodically update message (e.g., every 5 chunks to reduce API load)
        if len(buffer) % 5 == 0:
            await message.edit(content=buffer + "...")

    # Final update
    await message.edit(content=buffer)

bot.run(app_config.discord_token)
