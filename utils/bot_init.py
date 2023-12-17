import discord
from discord.ext import commands

def bot_initialization() :
    intents = discord.Intents.default()
    intents.guilds = True
    intents.messages = True
    intents.guild_messages = True
    intents.message_content = True
    intents.messages = True  # This enables the message content intent

    bot = commands.Bot(command_prefix="!", intents=intents)

    return bot