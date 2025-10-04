import discord
from discord.ext import commands, tasks
import json
from urllib.request import urlopen, urlretrieve
import os
import tempfile
from datetime import datetime
from typing import Optional
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot configuration from environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID_STR = os.getenv('CHANNEL_ID')

# Validate required environment variables
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables. Please check your .env file.")
if not CHANNEL_ID_STR:
    raise ValueError("CHANNEL_ID not found in environment variables. Please check your .env file.")

CHANNEL_ID = int(CHANNEL_ID_STR)

# Create bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Store last posted radio IDs to avoid duplicates
posted_radios = set()

def get_team_radio_data(session_key="latest", driver_number=None):
    """Fetch team radio data from OpenF1 API"""
    try:
        url = f"https://api.openf1.org/v1/team_radio?session_key={session_key}"
        if driver_number:
            url += f"&driver_number={driver_number}"
        
        response = urlopen(url)
        data = json.loads(response.read().decode('utf-8'))
        return data
    except Exception as e:
        print(f"Error fetching team radio data: {e}")
        return []

async def download_mp3_file(recording_url, driver_number, date):
    """Download MP3 file directly without conversion"""
    try:
        # Create a temporary directory for processing
        temp_dir = tempfile.mkdtemp()
        
        # Generate safe filename
        safe_date = date.replace(':', '-').replace('+', '_').replace('T', '_')
        mp3_filename = f"radio_driver_{driver_number}_{safe_date}.mp3"
        
        mp3_path = os.path.join(temp_dir, mp3_filename)
        
        # Download the MP3 file
        print(f"Downloading MP3 from: {recording_url}")
        try:
            urlretrieve(recording_url, mp3_path)
        except Exception as e:
            print(f"Failed to download MP3 file: {e}")
            return None, temp_dir
        
        # Verify download
        if not os.path.exists(mp3_path) or os.path.getsize(mp3_path) < 1000:
            print("Downloaded MP3 file is too small or doesn't exist")
            return None, temp_dir
        
        print(f"Successfully downloaded MP3: {mp3_filename} ({os.path.getsize(mp3_path)} bytes)")
        return mp3_path, temp_dir
            
    except Exception as e:
        print(f"Error downloading MP3: {e}")
        return None, temp_dir

def cleanup_temp_files(temp_dir):
    """Clean up temporary files"""
    if temp_dir:
        try:
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"Error cleaning up temp files: {e}")

def create_radio_embed(radio_data, include_audio_link=True):
    """Create a Discord embed for team radio data"""
    embed = discord.Embed(
        title="🏁 F1 Team Radio",
        color=0xFF0000  # F1 red color
    )
    
    # Parse the date
    date_str = radio_data['date']
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        formatted_date = date_str
    
    embed.add_field(name="Driver Number", value=f"#{radio_data['driver_number']}", inline=True)
    embed.add_field(name="Date", value=formatted_date, inline=True)
    embed.add_field(name="Session", value=radio_data['session_key'], inline=True)
    embed.add_field(name="Meeting", value=radio_data['meeting_key'], inline=True)
    
    # Add audio link only if requested (for fallback)
    if include_audio_link and radio_data['recording_url']:
        embed.add_field(name="🎧 Original MP3 Link", value=f"[MP3 Link]({radio_data['recording_url']})", inline=False)
    
    embed.set_footer(text="OpenF1 API • F1 Team Radio Bot • Direct MP3 Upload")
    
    return embed

async def send_radio_with_audio(channel_or_ctx, radio_data, is_ctx=False):
    """Send radio data with MP3 file (no conversion needed)"""
    embed = create_radio_embed(radio_data, include_audio_link=False)
    
    # Send the embed first
    await channel_or_ctx.send(embed=embed)
    
    # Try to download MP3 file
    if radio_data['recording_url']:
        if is_ctx:
            await channel_or_ctx.send("📥 Downloading audio file...")
        
        mp3_path, temp_dir = await download_mp3_file(
            radio_data['recording_url'], 
            radio_data['driver_number'], 
            radio_data['date']
        )
        
        try:
            if mp3_path and os.path.exists(mp3_path):
                # Check file size (Discord has 25MB limit for regular users)
                file_size = os.path.getsize(mp3_path)
                if file_size > 25 * 1024 * 1024:  # 25MB
                    await channel_or_ctx.send(f"⚠️ **File Too Large**: Audio file ({file_size // (1024*1024)}MB) exceeds Discord's limit. Use the MP3 link: {radio_data['recording_url']}")
                else:
                    # Send the MP3 file directly
                    with open(mp3_path, 'rb') as audio_file:
                        discord_file = discord.File(audio_file, filename=f"radio_driver_{radio_data['driver_number']}.mp3")
                        await channel_or_ctx.send(file=discord_file)
            else:
                # Fallback to link if download failed
                await channel_or_ctx.send(f"⚠️ **Download Failed**: Could not download audio. Use the MP3 link: {radio_data['recording_url']}")
        finally:
            # Clean up temp files
            cleanup_temp_files(temp_dir)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print('Bot is ready to fetch F1 team radio data')
    print('Audio files will be uploaded as MP3 (no conversion required)')
    # Start the background task to check for new radio messages
    check_new_radios.start()

@bot.command(name='radio')
async def get_radio(ctx, driver_number: Optional[int] = None, session_key: str = "latest"):
    """Get team radio for a specific driver or all drivers"""
    await ctx.send("🔍 Fetching F1 team radio data...")
    
    radio_data = get_team_radio_data(session_key, driver_number)
    
    if not radio_data:
        await ctx.send("❌ No team radio data found for the specified parameters.")
        return
    
    # Limit to 3 most recent entries to avoid spam
    radio_data = sorted(radio_data, key=lambda x: x['date'], reverse=True)[:3]
    
    for radio in radio_data:
        await send_radio_with_audio(ctx, radio, is_ctx=True)

@bot.command(name='latest_radio')
async def latest_radio(ctx):
    """Get the most recent team radio from the latest session"""
    await ctx.send("🔍 Fetching latest F1 team radio...")
    
    radio_data = get_team_radio_data("latest")
    
    if not radio_data:
        await ctx.send("❌ No recent team radio data found.")
        return
    
    # Get the most recent radio
    latest_radio = sorted(radio_data, key=lambda x: x['date'], reverse=True)[0]
    await send_radio_with_audio(ctx, latest_radio, is_ctx=True)

@bot.command(name='driver_radio')
async def driver_radio(ctx, driver_number: int):
    """Get team radio for a specific driver from the latest session"""
    await ctx.send(f"🔍 Fetching team radio for driver #{driver_number}...")
    
    radio_data = get_team_radio_data("latest", driver_number)
    
    if not radio_data:
        await ctx.send(f"❌ No team radio found for driver #{driver_number}.")
        return
    
    # Show radios for this driver (limit to 5)
    radio_data = sorted(radio_data, key=lambda x: x['date'], reverse=True)[:5]
    
    for radio in radio_data:
        await send_radio_with_audio(ctx, radio, is_ctx=True)

@tasks.loop(minutes=2)  # Check every 2 minutes
async def check_new_radios():
    """Background task to check for new team radio messages"""
    try:
        channel = bot.get_channel(CHANNEL_ID)
        if not channel or not hasattr(channel, 'send'):
            return
        
        radio_data = get_team_radio_data("latest")
        
        if not radio_data:
            return
        
        # Check for new radios (ones we haven't posted yet)
        new_radios = []
        for radio in radio_data:
            radio_id = f"{radio['session_key']}_{radio['driver_number']}_{radio['date']}"
            if radio_id not in posted_radios:
                new_radios.append(radio)
                posted_radios.add(radio_id)
        
        # Sort by date and post new ones
        new_radios = sorted(new_radios, key=lambda x: x['date'])
        
        for radio in new_radios:
            try:
                await channel.send("🆕 **New Team Radio!**")
                await send_radio_with_audio(channel, radio, is_ctx=False)
            except Exception as e:
                print(f"Error sending radio to channel: {e}")
                # Fallback to embed only
                embed = create_radio_embed(radio, include_audio_link=True)
                await channel.send("🆕 **New Team Radio!**", embed=embed)
            
    except Exception as e:
        print(f"Error in background task: {e}")

@check_new_radios.before_loop
async def before_check_new_radios():
    await bot.wait_until_ready()

@bot.command(name='test_audio')
async def test_audio(ctx):
    """Test audio upload with a sample URL"""
    await ctx.send("🧪 Testing audio upload...")
    
    # Use a sample URL from the example you provided
    test_url = "https://livetiming.formula1.com/static/2025/2025-10-05_Singapore_Grand_Prix/2025-10-03_Practice_2/TeamRadio/LIALAW01_30_20251003_210721.mp3"
    test_radio = {
        "driver_number": 30,
        "date": "2025-10-03T13:07:24.559000+00:00",
        "recording_url": test_url,
        "session_key": 9890,
        "meeting_key": 1270
    }
    
    await send_radio_with_audio(ctx, test_radio, is_ctx=True)

@bot.command(name='help_radio')
async def help_radio(ctx):
    """Show available commands"""
    embed = discord.Embed(
        title="🏁 F1 Team Radio Bot Commands",
        description="Available commands for fetching F1 team radio data",
        color=0xFF0000
    )
    
    embed.add_field(
        name="!radio [driver_number] [session_key]",
        value="Get team radio data. Both parameters are optional.\nExample: `!radio 44 latest`",
        inline=False
    )
    
    embed.add_field(
        name="!latest_radio",
        value="Get the most recent team radio from the latest session",
        inline=False
    )
    
    embed.add_field(
        name="!driver_radio <driver_number>",
        value="Get all team radio for a specific driver from latest session\nExample: `!driver_radio 44`",
        inline=False
    )
    
    embed.add_field(
        name="!test_audio",
        value="Test audio upload with a sample F1 team radio file",
        inline=False
    )
    
    embed.add_field(
        name="Auto-posting",
        value="The bot automatically posts new team radio messages every 2 minutes",
        inline=False
    )
    
    embed.add_field(
        name="🎵 Audio Features",
        value="• Uploads MP3 files directly to Discord\n• No conversion required\n• Fallback to MP3 links if upload fails",
        inline=False
    )
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    # Run the bot
    bot.run(DISCORD_TOKEN)