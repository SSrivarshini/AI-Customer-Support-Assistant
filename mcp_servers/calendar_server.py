"""MCP server: Google Calendar availability + appointment booking."""
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("calendar")

TZ = ZoneInfo(os.getenv("TIMEZONE", "Asia/Kolkata"))
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
WORK_START, WORK_END = 10, 17  # support hours, 10:00-17:00
SLOT_MINUTES = 30
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _service():
    creds = service_account.Credentials.from_service_account_file(
        os.environ["GOOGLE_SERVICE_ACCOUNT_FILE"], scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _day_bounds(day: str):
    d = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=TZ)
    return d.replace(hour=WORK_START), d.replace(hour=WORK_END)


@mcp.tool()
def check_availability(date: str) -> dict:
    """List free 30-minute support slots for a date (format YYYY-MM-DD)."""
    start, end = _day_bounds(date)
    body = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "timeZone": str(TZ),
        "items": [{"id": CALENDAR_ID}],
    }
    busy = _service().freebusy().query(body=body).execute()["calendars"][CALENDAR_ID]["busy"]
    busy = [
        (datetime.fromisoformat(b["start"]).astimezone(TZ), datetime.fromisoformat(b["end"]).astimezone(TZ))
        for b in busy
    ]
    slots, cur = [], start
    while cur + timedelta(minutes=SLOT_MINUTES) <= end:
        nxt = cur + timedelta(minutes=SLOT_MINUTES)
        if not any(cur < b_end and nxt > b_start for b_start, b_end in busy):
            slots.append(cur.strftime("%H:%M"))
        cur = nxt
    return {"date": date, "free_slots": slots}


@mcp.tool()
def book_appointment(customer_name: str, date: str, time: str, reason: str) -> dict:
    """Book a 30-minute support appointment. date=YYYY-MM-DD, time=HH:MM (24h)."""
    start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
    end = start + timedelta(minutes=SLOT_MINUTES)

    free = check_availability(date)["free_slots"]
    if time not in free:
        return {"booked": False, "message": f"{time} on {date} is not available.", "free_slots": free}

    event = {
        "summary": f"Support appointment - {customer_name}",
        "description": reason,
        "start": {"dateTime": start.isoformat(), "timeZone": str(TZ)},
        "end": {"dateTime": end.isoformat(), "timeZone": str(TZ)},
    }
    created = _service().events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return {
        "booked": True,
        "event_id": created["id"],
        "customer_name": customer_name,
        "date": date,
        "time": time,
        "duration_minutes": SLOT_MINUTES,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
