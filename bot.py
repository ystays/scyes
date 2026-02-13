from discord.ext import commands
from discord import Message, Intents
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
import os
from llm.agent import stream_agent
from llm.llm import stream
from langchain_core.messages import AIMessageChunk
from typing import Iterator, Any

intents = Intents.default()
intents.message_content = True

load_dotenv()

bot = commands.Bot(command_prefix='>', intents=intents)

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.command()
async def add(ctx, left: int, right: int):
    """Adds two numbers together."""
    await ctx.send(left + right)

@bot.command()
async def help(ctx):
    await ctx.send("Use >llm to chat with 4B model (faster responses), use >llma to chat with agent (tool calls, slower responses)")

@bot.command()
async def llm(ctx: commands.Context, *, input: str):
    message: Message = await ctx.send("thinking...")
    
    msg_history: list[BaseMessage] = [AIMessage(content=msg.content) if msg.author.bot else HumanMessage(content=msg.author.name + ": " + msg.content) async for msg in message.channel.history(limit=8)]

    buffer = ""
    msg_history.reverse()
    response: Iterator[AIMessageChunk] = stream(input, msg_history[:-2])
    
    for chunk in response:
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
    message: Message = await ctx.send("thinking...")
    
    msg_history: list[BaseMessage] = [AIMessage(content=msg.content) if msg.author.bot else HumanMessage(content=msg.author.name + ": " + msg.content) async for msg in message.channel.history(limit=8)]

    buffer = ""
    msg_history.reverse()
    response: Iterator[dict[str, Any] | Any] = stream_agent(input, msg_history[:-2])
    
    for token, metadata in response:
        if len(token.content_blocks) == 0 or token.content_blocks[-1]["type"] != "text":
            continue

        buffer += token.content_blocks[0]["text"]

        # If LLM output is too long, just truncate and exit for now
        if len(buffer) > 2000:
            break

        # Periodically update message (e.g., every 5 chunks to reduce API load)
        if len(buffer) % 5 == 0:
            await message.edit(content=buffer + "...")
            
    # 4. Final update
    await message.edit(content=buffer)

bot.run(os.getenv("DISCORD_TOKEN"))