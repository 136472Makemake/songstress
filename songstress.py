import discord
import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio
import yt_dlp
from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.guild_messages = True
intents.message_content = True
intents.messages = True  # This enables the message content intent

bot = commands.Bot(command_prefix="!", intents=intents)

from collections import deque

# Dictionary where the key is the guild ID and the value is a queue of tracks
music_queues = {}



@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")


@bot.command(name='test')
async def test(ctx):
    await ctx.send("Test command received")


@bot.command(name='join')
async def join(ctx):
    print("test")
    if ctx.author.voice is not None:
        channel = ctx.message.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("You are not connected to a voice channel.")

@bot.command(name='leave')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")

async def play_next_track(ctx):
    guild_id = ctx.guild.id
    voice_client = ctx.message.guild.voice_client

    if guild_id in music_queues and len(music_queues[guild_id]) > 0:
        # Get the next track from the queue
        track = music_queues[guild_id].popleft()
        audio_source = FFmpegPCMAudio(track['url'], options='-bufsize 20M')

        # Play the track and announce it
        voice_client.play(audio_source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_track(ctx), bot.loop))
        await ctx.send(f"✨ Playing {track['title']} by {track['requested_by']}. 🧚")


@bot.command(name='play')
async def play(ctx, *, url=None):
    if not ctx.author.voice:
        await ctx.send("✨ You need to be in a voice channel to use this command. 🧚")
        return
    
    voice_client = await get_voice_client(ctx)

    if ctx.message.attachments:
        await handle_attachment(ctx, voice_client)
    elif url:
        await handle_youtube(ctx, voice_client, url)
    else:
        await ctx.send("✨ Please attach an MP3 file or provide a YouTube URL. 🌟")

async def get_voice_client(ctx):
    voice_client = ctx.message.guild.voice_client

    if voice_client is None:
        channel = ctx.author.voice.channel if ctx.author.voice else None
        if channel:
            await channel.connect()

    return ctx.message.guild.voice_client

async def handle_attachment(ctx, voice_client):
    attachment = ctx.message.attachments[0]  # Get the first attachment
    if attachment.filename.endswith('.mp3'):
        track = create_track(attachment.url, attachment.filename, ctx.author.display_name)
        add_to_queue(ctx, track)
        await play_track_if_not_playing(ctx, voice_client, track['title'])
    else:
        await ctx.send("✨ Please attach an MP3 file. 🧚")

async def handle_youtube(ctx, voice_client, url):
    ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '128',  # Lower quality might be more stable
    }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            track = create_track(info['url'], info['title'], ctx.author.display_name)
            add_to_queue(ctx, track)
            await play_track_if_not_playing(ctx, voice_client, track['title'])
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")

def create_track(url, title, requested_by):
    return {'url': url, 'title': title, 'requested_by': requested_by}

def add_to_queue(ctx, track):
    guild_id = ctx.guild.id
    if guild_id not in music_queues:
        music_queues[guild_id] = deque()
    music_queues[guild_id].append(track)

async def play_track_if_not_playing(ctx, voice_client, track_title):
    if not voice_client.is_playing():
        await play_next_track(ctx)
    else:
        await ctx.send(f"✨ Added {track_title} to the queue. ✨")

@bot.command(name='next')
async def next(ctx):
    guild_id = ctx.guild.id
    voice_client = ctx.message.guild.voice_client

    if guild_id in music_queues and voice_client.is_playing():
        voice_client.stop()  # This will stop the current track
        await play_next_track(ctx)  # Play the next track in the queue
    else:
        await ctx.send("✨ No track is currently playing. 🧚")


@bot.command(name='pause')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client

    if voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Audio paused.")
    else:
        await ctx.send("✨ No audio is playing. 🧚")

@bot.command(name='resume')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client

    if voice_client.is_paused():
        voice_client.resume()
        await ctx.send("✨ Audio resumed. 🧚")
    else:
        await ctx.send("✨ Audio is not paused. 🧚")

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f'An error occurred: {str(error)}')

bot.run(BOT_TOKEN)
