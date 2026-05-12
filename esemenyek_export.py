import os
import json
from datetime import datetime, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 🔐 Hitelesítés
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "credentials.json")
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CALENDAR_ID = "ungitomi27@gmail.com"

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("calendar", "v3", credentials=credentials)

# 📅 Események lekérése
def get_upcoming_events(max_events=30):
    now = datetime.now(timezone.utc).isoformat()
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=now,
        maxResults=max_events,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = events_result.get("items", [])
    return events

# 💾 JSON fájlba írás
def save_events_to_json(events, filename=os.path.join(BASE_DIR, "esemenyek_export.json")):

    event_list = []

    for event in events:
        event_info = {
            "cim": event.get("summary", "Névtelen esemény"),
            "kezdes": event["start"].get("dateTime", event["start"].get("date")),
            "vege": event["end"].get("dateTime", event["end"].get("date")),
            "helyszin": event.get("location", "")
        }
        event_list.append(event_info)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(event_list, f, ensure_ascii=False, indent=4)

    print(f"{len(event_list)} esemény mentve a '{filename}' fájlba.")

# 🔄 Futtatás
events = get_upcoming_events(max_events=30)
save_events_to_json(events)
