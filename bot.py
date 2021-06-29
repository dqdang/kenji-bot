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
url_regex = "(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"
pattern = re.compile(url_regex)
client = discord.Client()

current_video = ""

queries = ["-kenji", "-crimes", "-bonk", "-pats"]
seen = set()


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
    channel = "https://www.youtube.com/channel/UC4er8qDSU1Y2IaTkC9gS9wA/videos"

    resp = requests.get(channel)
    soup = BeautifulSoup(resp.text, "lxml")
    data = soup.find_all("script")
    url = None

    for point in data:
        try:
            pattern = re.compile("var ytInitialData = (.*?);")
            m = pattern.match(point.string)
            if m:
                channel_info = json.loads(m.groups()[0])
                latest_video_watch_id = channel_info["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][1]["tabRenderer"]["content"][
                    "sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"][0]["gridRenderer"]["items"][0]["gridVideoRenderer"]["videoId"]
                # x.contents.twoColumnBrowseResultsRenderer.tabs[1].tabRenderer.content.sectionListRenderer.contents[0].itemSectionRenderer.contents[0].gridRenderer.items[0].gridVideoRenderer.videoId
                url = "https://www.youtube.com/watch?v=" + latest_video_watch_id
                break
        except Exception as e:
            continue

    return url

@client.event
async def on_message(message):
    global queries
    global current_video
    global pattern
    if message.author == client.user or pattern.match(message.content):
        return

    if message.content in queries:
        print("Request to send most recent video received.")
        url = current_video
        await message.channel.send(url)


async def get_kenji_videos(server):
    global current_video
    global seen
    await client.wait_until_ready()
    channel = find_channel(server)
    cur_time = time.time()
    found_time = cur_time - 5
    while True:
        wait_duration = cur_time - found_time
        cur_time = time.time()
        if wait_duration >= 5:
            url = detect_kenji_videos()
            found_time = time.time()
            print(url)
            print(seen)
            print("Current Video: {}".format(current_video))
        else:
            url = None
        if url and current_video != url and current_video not in seen:
            print("New video found! Updating database.")
            await channel.send(url)
            print(db.insert_url(1, url))
            print(db.get_table("Seen", "url"))
            current_video = url
            seen.add(current_video)
        await asyncio.sleep(1)


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
seen.add(current_video)
client.loop.create_task(get_kenji_videos(GUILD))
try:
    client.run(DISCORD_BOT_TOKEN)
finally:
    if not db.id_exists(1).url != current_video:
        db.change_url(1, current_video)
