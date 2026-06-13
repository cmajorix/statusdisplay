import discord

from dotenv import load_dotenv
import os
import argparse
import io
import datetime as dt

# from inky.auto import auto
from PIL import Image, ImageDraw, ImageFont
import requests


parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dev", action="store_true")

args = parser.parse_args()
devmode = args.dev

intents = discord.Intents.default()
intents.presences = True
intents.members = True

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

client = discord.Client(intents=intents)


async def render_screen(after: discord.Member):
    games = []
    for activity in after.activities:
        if activity.type == discord.ActivityType.playing or isinstance(
            activity, discord.Game
        ):
            games.append(activity)

    if not games:
        print("Game not found")
        return

    game_title = games[0].name
    game_logo_url = games[0].small_image_url
    print(f"User is playing {game_title}")
    if game_logo_url is None:
        game_asset = await client.fetch_application(games[0].application_id)
        game_logo_url = game_asset.icon.url

    logo_img = None
    if game_logo_url is not None:
        r = requests.get(game_logo_url, stream=True)
        if r.status_code == 200:
            logo_img = Image.open(io.BytesIO(r.content))
        else:
            print("Error", r.status_code)

    img = Image.new("RGB", (600, 448), "white")
    draw = ImageDraw.Draw(img)

    logo_img = logo_img.resize((100, 100))
    draw.rectangle([0, 348, 600, 448], fill="orange")
    if logo_img is not None:
        # draw.bitmap((0, 348), logo_img)
        img.paste(logo_img, (0, 348))
    draw.text((100, 348), game_title, "white", ImageFont.load_default())
    img.save(f"gametest{dt.datetime.today().strftime('%Y%m%d%H%M%S')}.png")


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    await render_screen(after)


client.run(token)
