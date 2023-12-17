import asyncio
import yt_dlp
import os

from discord import FFmpegPCMAudio
from dotenv import load_dotenv
from collections import deque

from utils.bot_init import bot_initialization

# Variables load

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = bot_initialization()
music_queues = {}

# commands 

@bot.command(name='join')
async def join(ctx):
    if ctx.author.voice is not None:
        channel = ctx.message.author.voice.channel
        voice_client = ctx.message.guild.voice_client

        if not voice_client :
            await channel.connect()

        return ctx.message.guild.voice_client
    else:
        await ctx.send("✨ You need to be in a voice channel to use this command. 🧚")

@bot.command(name='leave')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")

@bot.command(name='play')
async def play(ctx, *, query=None):

    voice_client = await join(ctx)

    if not voice_client:
        await ctx.send("Error connecting to voice channel.")
        return

    if ctx.message.attachments:
        await handle_attachment(ctx, voice_client)
    elif query:
        await handle_youtube(ctx, voice_client, query)
    else:
        await ctx.send("✨ Please attach an MP3 file or provide a YouTube URL or song name. 🌟")

async def handle_attachment(ctx, voice_client):
    attachment = ctx.message.attachments[0]  # Get the first attachment
    if attachment.filename.endswith('.mp3'):
        track = create_track(attachment.url, attachment.filename, ctx.author.display_name)
        add_to_queue(ctx, track)
        await play_track_if_not_playing(ctx, voice_client, track['title'])
    else:
        await ctx.send("✨ Please attach an MP3 file. 🧚")  

async def handle_youtube(ctx, voice_client, query):
    ydl_opts = {
        'default_search': 'ytsearch',  # Enable searching by default
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # The query can be a URL or a search term
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                # Take the first result from a search
                track_info = info['entries'][0]
            else:
                # Direct URL, so just use the info
                track_info = info

            track = create_track(track_info['url'], track_info['title'], ctx.author.display_name)
            add_to_queue(ctx, track)
            await play_track_if_not_playing(ctx, voice_client, track['title'])
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")

def add_to_queue(ctx, track):
    guild_id = ctx.guild.id
    if guild_id not in music_queues:
        music_queues[guild_id] = deque()
    music_queues[guild_id].append(track)     

def create_track(url, title, requested_by):
    return {'url': url, 'title': title, 'requested_by': requested_by}       

async def play_track_if_not_playing(ctx, voice_client, track_title):
    if not voice_client.is_playing():
        await play_next_track(ctx)
    else:
        await ctx.send(f"✨ Added {track_title} to the queue. ✨")

async def play_next_track(ctx):
    guild_id = ctx.guild.id
    voice_client = ctx.message.guild.voice_client

    if guild_id in music_queues and len(music_queues[guild_id]) > 0:
        # Get the next track from the queue
        track = music_queues[guild_id].popleft()
        audio_source = FFmpegPCMAudio(track['url'], before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options='-bufsize 128M -vn')

        # Play the track and announce it
        voice_client.play(audio_source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_track(ctx), bot.loop))
        await ctx.send(f"✨ Playing {track['title']} by {track['requested_by']}. 🧚")

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

if __name__ == "__main__":

    @bot.event
    async def on_ready():
        print(f"{bot.user.name} has connected to Discord!")

    @bot.event
    async def on_command_error(ctx, error):
        await ctx.send(f'An error occurred: {str(error)}')

    bot.run(BOT_TOKEN)