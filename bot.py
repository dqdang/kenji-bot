import asyncio
from bs4 import BeautifulSoup
import dbhandler as db
import discord
import json
import os
import requests
import re
import time


DISCORD_BOT_TOKEN = os.environ['DISCORD_BOT_TOKEN']
GUILD = os.environ['GUILD']
CHANNEL_NAME = os.environ['CHANNEL_NAME']

server_channels = {}  # Server channel cache

client = discord.Client()

current_video = ""

queries = ["-kenji", "-crimes", "-bonk", "-pats"]


def find_channel(server, refresh=False):
    """
    Find and return the channel to log the voice events to.
    :param server: The server to find the channel for.
    :param refresh: Whether to refresh the channel cache for this server.
    """
    if not refresh and server in server_channels:
        return server_channels[server]

    for channel in client.get_all_channels():
        if channel.guild.name == server and channel.name == CHANNEL_NAME:
            print("%s: refreshed destination log channel" % server)
            server_channels[server] = channel
            return channel

    return None


def detect_kenji_videos():
    global current_video

    channel = 'https://www.youtube.com/channel/UC4er8qDSU1Y2IaTkC9gS9wA/videos'

    resp = requests.get(channel)
    soup = BeautifulSoup(resp.text, "lxml")
    data = soup.find_all("script")
    for point in data:
        try:
            pattern = re.compile("var ytInitialData = (.*?);")
            m = pattern.match(point.string)
            if m:
                break
        except Exception as e:
            continue
    channel_info = json.loads(m.groups()[0])
    latestVideoWatchId = channel_info["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][1]["tabRenderer"]["content"][
        "sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"][0]["gridRenderer"]["items"][0]["gridVideoRenderer"]["videoId"]
    # x.contents.twoColumnBrowseResultsRenderer.tabs[1].tabRenderer.content.sectionListRenderer.contents[0].itemSectionRenderer.contents[0].gridRenderer.items[0].gridVideoRenderer.videoId
    url = "https://www.youtube.com/watch?v=" + latestVideoWatchId
    return url


@client.event
async def on_message(message):
    global queries
    if message.author == client.user:
        return

    if message.content in queries:
        url = current_video
        await message.channel.send(url)


async def get_kenji_videos(server):
    global current_video
    await client.wait_until_ready()
    counter = 0
    channel = find_channel(server)
    while True:
        url = detect_kenji_videos()
        if url and current_video != url:
            print("New video found! Updating database.")
            await channel.send(url)
            print(db.insert_url(1, url))
            print(db.get_table("Seen", "url"))
            current_video = url
        await asyncio.sleep(1)
        time.sleep(10)


@client.event
async def on_ready():
    global current_video
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

current_video = db.id_exists(1).url
print("Current video: {}".format(db.id_exists(1).url))
client.loop.create_task(get_kenji_videos(GUILD))
try:
    client.run(DISCORD_BOT_TOKEN)
finally:
    if not db.id_exists(1).url != current_video:
        db.change_url(1, current_video)
