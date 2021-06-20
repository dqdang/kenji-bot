import dbhandler as db
import discord
import json
import os
import urllib.request

DISCORD_BOT_TOKEN = os.environ['DISCORD_BOT_TOKEN']
GUILD = os.environ['GUILD']
CHANNEL_NAME = os.environ['CHANNEL_NAME']
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']

server_channels = {}  # Server channel cache

client = discord.Client()


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
    api_key = GOOGLE_API_KEY

    base_video_url = 'https://www.youtube.com/watch?v='
    base_search_url = 'https://www.googleapis.com/youtube/v3/search?'
    channel_id = "UC4er8qDSU1Y2IaTkC9gS9wA"

    first_url = base_search_url + \
        'key={}&channelId={}&part=snippet,id&order=date&maxResults=25'.format(
            api_key, channel_id)

    video_links = []
    url = first_url
    while True:
        inp = urllib.request.urlopen(url)
        resp = json.load(inp)

        for i in resp['items']:
            if i['id']['kind'] == "youtube#video":
                video_links.append(base_video_url + i['id']['videoId'])

        try:
            next_page_token = resp['nextPageToken']
            url = first_url + '&pageToken={}'.format(next_page_token)
        except:
            break
    return video_links[0]  # return first link (latest)


async def get_kenji_videos(server):
    await client.wait_until_ready()
    counter = 0
    channel = find_channel(server)
    while True:
        url = detect_kenji_videos()
        if url and not db.url_exists(url):
            await channel.send(url)
            db.insert_url(1, url)


@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )


client.loop.create_task(get_kenji_videos(GUILD))
client.run(DISCORD_BOT_TOKEN)
