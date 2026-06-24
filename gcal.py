import os
import datetime
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load config
with open("settings.cfg") as settings_file:
    config = json.load(settings_file)

# Google OAuth stuff
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
creds = None
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
    with open("token.json", "w") as token:
        token.write(creds.to_json())

def get_sorted_events() -> list:
    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
        tomorrow = (
            datetime.datetime.combine(
                datetime.datetime.today().date() + datetime.timedelta(days=1),
                datetime.time.min
            )
            .astimezone(datetime.timezone.utc)
        )

        all_day_events = []
        timed_events = []

        for calendarId in config["calendar_ids"]:
            events_result = (
                service.events()
                .list(
                    calendarId=calendarId,
                    timeMin=now,
                    maxResults=10,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            if events:
                for event in events:
                    if event["start"].get("dateTime") and datetime.datetime.fromisoformat(event["start"].get("dateTime")) < tomorrow:
                        timed_events.append(event)
                    elif event["start"].get("date") and datetime.date.fromisoformat(event["start"].get("date")) < datetime.datetime.today().date() + datetime.timedelta(days=1):
                        all_day_events.append(event)

        timed_events.sort(key = lambda x: datetime.datetime.fromisoformat(x["start"]["dateTime"]))
        
        for event in timed_events:
            print(event["summary"])

        return timed_events

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []
    
if __name__ == "__main__":
    get_sorted_events()