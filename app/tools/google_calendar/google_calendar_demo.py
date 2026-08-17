from __future__ import annotations

import argparse
import sys
import unicodedata
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token_calendar.json"
DEFAULT_TIMEZONE = "Asia/Bangkok"
PRIMARY_CALENDAR_ID = "primary"


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")


def safe_text(value: object) -> str:
    text = str(value)
    text = text.replace("Đ", "D").replace("đ", "d")
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


def safe_print(value: object = "") -> None:
    print(safe_text(value))


def build_calendar_service():
    credentials = get_calendar_credentials()
    return build("calendar", "v3", credentials=credentials)


def get_calendar_credentials() -> Credentials:
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(f"Không tìm thấy file credentials: {CREDENTIALS_FILE}")

    credentials = None
    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
        credentials = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")

    return credentials


def parse_target_date(date_text: str | None, timezone_name: str) -> date:
    timezone = ZoneInfo(timezone_name)
    if not date_text:
        return datetime.now(timezone).date()

    return datetime.strptime(date_text, "%Y-%m-%d").date()


def get_calendars(service, max_results: int = 10) -> list[dict[str, Any]]:
    result = service.calendarList().list(maxResults=max_results).execute()
    return result.get("items", [])


def get_events_for_day(
    service,
    target_date: date,
    timezone_name: str,
    calendar_id: str = PRIMARY_CALENDAR_ID,
) -> list[dict[str, Any]]:
    timezone = ZoneInfo(timezone_name)
    start_of_day = datetime.combine(target_date, time.min, tzinfo=timezone)
    start_of_next_day = start_of_day + timedelta(days=1)

    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=start_of_day.isoformat(),
            timeMax=start_of_next_day.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return events_result.get("items", [])


def print_calendars(calendars: list[dict[str, Any]]) -> None:
    safe_print("Kết nối Google Calendar thành công.")
    safe_print(f"Số calendar lấy được: {len(calendars)}")

    for calendar in calendars:
        summary = calendar.get("summary", "(Không có tên)")
        calendar_id = calendar.get("id", "(Không có id)")
        safe_print(f"- {summary}: {calendar_id}")


def print_events(events: list[dict[str, Any]], target_date: date, timezone_name: str) -> None:
    safe_print(f"\nSự kiện trong primary calendar ngày {target_date.isoformat()} ({timezone_name}):")
    safe_print(f"Số event: {len(events)}")

    if not events:
        safe_print("- Không có sự kiện.")
        return

    for event in events:
        start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
        end = event.get("end", {}).get("dateTime") or event.get("end", {}).get("date")
        summary = event.get("summary", "(Không có tiêu đề)")
        safe_print(f"- {start} -> {end}: {summary}")


def check_calendar_access(date_text: str | None = None, timezone_name: str = DEFAULT_TIMEZONE) -> None:
    service = build_calendar_service()
    target_date = parse_target_date(date_text, timezone_name)
    calendars = get_calendars(service)
    events = get_events_for_day(service, target_date, timezone_name)

    print_calendars(calendars)
    print_events(events, target_date, timezone_name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Kiểm tra Google Calendar theo ngày.")
    parser.add_argument(
        "--date",
        help="Ngày cần kiểm tra, định dạng YYYY-MM-DD. Bỏ trống để dùng ngày hôm nay.",
    )
    parser.add_argument(
        "--timezone",
        default=DEFAULT_TIMEZONE,
        help=f"Timezone dùng để tính ngày, mặc định là {DEFAULT_TIMEZONE}.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    configure_stdout()
    args = parse_args()
    check_calendar_access(date_text=args.date, timezone_name=args.timezone)
