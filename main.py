import discord

from dotenv import load_dotenv
import sys
import os
import argparse
import io
import json
from typing import Optional
import datetime

from PIL import Image, ImageDraw, ImageFont, ImageText
import requests

if sys.platform == "linux":
    from inky.auto import auto

    display = auto()
else:
    print("Not running on Linux. Inky display integration disabled.")
    display = None

import gcal

# Devmode parsing
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dev", action="store_true")

args = parser.parse_args()
devmode = args.dev

# Create Discord bot
intents = discord.Intents.default()
intents.presences = True
intents.members = True

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

client = discord.Client(intents=intents)

# Load config
with open("settings.cfg") as settings_file:
    config = json.load(settings_file)


# Function to show the screen, depending on if Inky is imported (not possible if debugging on Windows)
def render(img: Image.Image, display):
    if sys.platform == "linux":
        display.set_image(img)
        display.show()
    else:
        img.show()


async def draw_screen(after: Optional[discord.Member]):
    # Discord stuff
    img = Image.new("RGB", (600, 448), "white")
    draw = ImageDraw.Draw(img)

    if after is not None:
        games = []
        for activity in after.activities:
            if activity.type == discord.ActivityType.playing or isinstance(
                activity, discord.Game
            ):
                games.append(activity)

        if not games:
            print("Game not found")
            draw.rectangle([0, 348, 600, 448], fill="gray")
            draw.text(
                (300, 398),
                "No game active",
                "white",
                ImageFont.load_default(size=70),
                anchor="mm",
            )

        else:
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
                    logo_img = logo_img.resize((100, 100))
                else:
                    print("Error", r.status_code)

            draw.rectangle([0, 348, 600, 448], fill="orange")
            if logo_img is not None:
                img.paste(logo_img, (0, 348))
            game_title_text = ImageText.Text(
                game_title, ImageFont.load_default(size=60)
            )
            if game_title_text.get_length() > 490:
                title_len = len(game_title_text.text)
                for i in range(title_len, 0, -1):
                    game_title_text.text = game_title[:i] + "..."
                    if game_title_text.get_length() <= 490:
                        break

            draw.text((110, 398), game_title_text, "white", anchor="lm")

    events = gcal.get_sorted_events()

    if events:
        draw.line((390, 0, 390, 348), fill="gray", width=2)

        main_event_text = ImageText.Text(
            events[0]["summary"], ImageFont.load_default(size=60)
        )
        if main_event_text.get_length() > 380:  # shrink font
            main_event_text.font = ImageFont.load_default(size=40)
        if main_event_text.get_length() > 380:  # cut it off
            for i in range(len(events[0]["summary"]), 0, -1):
                main_event_text.text = events[0]["summary"][:i] + "..."
                if main_event_text.get_length() <= 380:
                    break

        main_event_start = ImageText.Text(
            datetime.datetime.fromisoformat(
                events[0]["start"].get("dateTime")
            ).strftime("%H:%M"),
            ImageFont.load_default(size=30),
        )
        main_event_end = ImageText.Text(
            "- "
            + datetime.datetime.fromisoformat(
                events[0]["end"].get("dateTime")
            ).strftime("%H:%M"),
            ImageFont.load_default(size=30),
        )

        cal_logo = Image.open("assets/calendar.png")

        for event in events[1:5]:
            pass

        draw.text((195, 50), main_event_text, "black", anchor="mm")
        draw.text((340, 200), main_event_start, "black", anchor="rm")
        draw.text((340, 250), main_event_end, "black", anchor="rm")
        img.paste(cal_logo, (50, 175, 150, 275))

    else:
        draw.text(
            (300, 174),
            "No events today",
            "black",
            anchor="mm",
            font=ImageFont.load_default(size=70),
        )

    render(img, display)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    await draw_screen(after)


client.run(token)
