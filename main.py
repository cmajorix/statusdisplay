import discord
from dotenv import load_dotenv
import os

intents = discord.Intents.default()
intents.presences = True
intents.members = True

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_presence_update(before: discord.Member, after: discord.Member):

    games = []
    for activity in after.activities:
        if activity.type == discord.ActivityType.playing or isinstance(activity, discord.Game):
            games.append(activity)

    if not games:
        print("Game not found")
        return

    game_title = games[0].name

    print(f"User is playing {game_title}")

client.run(token)
