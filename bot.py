import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from llm.model import invoke, stream
from langchain_core.messages import AIMessageChunk
from typing import Iterator

intents = discord.Intents.default()
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
async def llm(ctx, *, input: str):
    message = await ctx.send("Thinking...")
    
    buffer = ""
    response: Iterator[AIMessageChunk] = stream(input)
    
    for chunk in response:
        buffer += chunk.content
        
        # Periodically update message (e.g., every 5 chunks to reduce API load)
        if len(buffer) % 5 == 0:
            await message.edit(content=buffer + "...")
            
    # 4. Final update
    await message.edit(content=buffer)


bot.run(os.getenv("DISCORD_TOKEN"))