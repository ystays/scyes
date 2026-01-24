import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from llm.model import invoke 

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
async def llm(ctx, *, message: str):
    await ctx.send(invoke(message))


bot.run(os.getenv("DISCORD_TOKEN"))