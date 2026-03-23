from langchain.tools import tool
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

from config import app_config

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_service():
    creds = service_account.Credentials.from_service_account_file(
        app_config.google_service_account_key_file, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds)


@tool
def list_calendar_events(days: int = 7) -> str:
    """List upcoming Google Calendar events for the next N days (default 7)."""
    service = _get_service()
    now = datetime.datetime.utcnow().isoformat() + "Z"
    end = (datetime.datetime.utcnow() + datetime.timedelta(days=days)).isoformat() + "Z"

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            timeMax=end,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    if not events:
        return "No upcoming events found."

    lines = []
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        lines.append(f"- {start}: {e['summary']}")
    return "\n".join(lines)


@tool
def create_calendar_event(
    summary: str,
    start: str,
    end: str,
    description: str = "",
    location: str = "",
) -> str:
    """Create a Google Calendar event.

    Args:
        summary: Title of the event.
        start: Start datetime in ISO 8601 format (e.g. '2026-03-10T14:00:00+01:00').
        end: End datetime in ISO 8601 format (e.g. '2026-03-10T15:00:00+01:00').
        description: Optional event description.
        location: Optional event location.
    """
    service = _get_service()
    event = {
        "summary": summary,
        "start": {"dateTime": start},
        "end": {"dateTime": end},
    }
    if description:
        event["description"] = description
    if location:
        event["location"] = location

    created = service.events().insert(calendarId="primary", body=event).execute()
    return f"Event created: {created.get('summary')} (id: {created.get('id')})"
