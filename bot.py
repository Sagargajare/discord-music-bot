
import os
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import asyncio
import urllib.request
import re
import discord
import youtube_dl
import time
from discord.ext import commands

prifix = ";"

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    # bind to ipv4 since ipv6 addresses cause issues sometimes
    'source_address': '0.0.0.0'
}

chrome_options = Options()

chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument('--lang=en_US')
chrome_options.add_argument("--disable-gpu")
chrome_options.headless = True
chrome_options.add_argument(
    "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36")

chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
def get_source(query):
    driver = webdriver.Chrome(
        executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options)
    driver.get(f"https://music.youtube.com/search?q={query}")
    time.sleep(3)

    return driver.page_source
 
   
def search_youtube(query):
    query = query.replace(' ', '+')

    html = get_source(query)
    video_ids = re.findall(r"watch\?v=(\S{11})", html)
    if(len(video_ids) == 0):
        return None
    url = f"https://music.youtube.com/watch?v={video_ids[0]}"
    return url


ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @commands.command()
    # async def help(self, ctx):
    #     embed = discord.Embed(
    #         title="Help",
    #         description="Help us to improve. report issues to admins",
    #         color=discord.Color.blue())

    #     embed.add_field(name=f"*{prifix}join*",
    #                     value="To Join Voice Channel", inline=False)
    #     embed.add_field(name=f"*{prifix}play <query>*",
    #                     value="To search and play song", inline=False)
    #     embed.add_field(name=f"*{prifix}stop*",
    #                     value="To Stop the song and leave channnel", inline=False)
    #     await ctx.send(embed=embed)
    @commands.command()
    async def join(self, ctx):
        """Joins a voice channel"""
        if(type(ctx.author.voice) == type(None)):
            await ctx.send('```Join Voice Channel And Try Again```')
            return
        channel = ctx.author.voice.channel
        await ctx.send(f'```Joined {channel} Voice Channel```')
        print(channel)
        await channel.connect()

    @commands.command()
    async def play(self, ctx, *, query=None):
        """play <query> """
        if(query == None):
            await ctx.send('```Please Provide Valid correct input```')
            return
        url = search_youtube(query)
        if(url == None):
            await ctx.send('```Your Music Sense Sucks !```')
            return
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(
                'Player error: %s' % e) if e else None)

        await ctx.send('```Now playing: {}```'.format(player.title))

    @commands.command()
    async def yt(self, ctx, *, url):
        """Plays from a url """

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print(
                'Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.title))

    @commands.command()
    async def stream(self, ctx, *, url):
        """Streams from a url (same as yt, but doesn't predownload)"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(
                'Player error: %s' % e) if e else None)

        await ctx.send('```Now playing: {}```'.format(player.title))

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("```Not connected to a voice channel```")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Changed volume to {}%".format(volume))

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()

    @play.before_invoke
    @yt.before_invoke
    @stream.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("```You are not connected to a voice channel.```")
                raise commands.CommandError(
                    "Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


bot = commands.Bot(command_prefix=commands.when_mentioned_or(prifix),
                   description='CSI DYPIEMR')


@bot.event
async def on_ready():
    print('Logged in as {0} ({0.id})'.format(bot.user))
    print('------')


bot.add_cog(Music(bot))
token = os.getenv('TOKEN')
bot.run(token)
