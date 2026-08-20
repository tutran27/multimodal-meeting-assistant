"""
Module: google_calendar.py
Vai trò: Quản lý tích hợp Google Calendar API — tra cứu lịch rảnh và tạo sự kiện lịch.

Mô tả chi tiết:
- Kết nối với Google Calendar API qua `GoogleOAuthService` để tương tác với lịch làm việc của người dùng.
- Tra cứu lịch bận/rảnh (`calendar_freebusy`) trong khoảng thời gian chỉ định và tự động gợi ý các khung giờ rảnh (candidate slots) phù hợp trong giờ làm việc.
- Tạo sự kiện mới (`calendar_create_event`) trên Google Calendar với đầy đủ thông tin: tiêu đề, mô tả, thời gian bắt đầu/kết thúc và danh sách người tham dự.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.core.exceptions import ConfigurationError, ToolExecutionError
from app.services.oauth_service import GoogleOAuthService


def _parse_iso(value: str) -> datetime:
    """Parse chuỗi ISO 8601 sang datetime. Nếu thiếu timezone sẽ gán timezone mặc định của hệ thống."""
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(settings.timezone))
    return dt


def _find_free_slots(
    start: datetime,
    end: datetime,
    busy: list[dict],
    duration_minutes: int,
    workday_start: int = 8,
    workday_end: int = 18,
) -> list[dict]:
    """Tìm danh sách các khoảng thời gian rảnh (slots) phù hợp trong giờ làm việc."""
    duration = timedelta(minutes=duration_minutes)
    busy_ranges = sorted(
        [(_parse_iso(item["start"]), _parse_iso(item["end"])) for item in busy],
        key=lambda item: item[0],
    )

    slots: list[dict] = []
    current_day = start.date()

    while current_day <= end.date():
        day_start = datetime.combine(current_day, datetime.min.time(), tzinfo=start.tzinfo).replace(hour=workday_start)
        day_end = day_start.replace(hour=workday_end)

        cursor = max(day_start, start)
        day_limit = min(day_end, end)

        while cursor + duration <= day_limit:
            candidate_end = cursor + duration
            has_conflict = any(
                cursor < busy_end and candidate_end > busy_start
                for busy_start, busy_end in busy_ranges
            )

            if not has_conflict:
                slots.append({"start": cursor.isoformat(), "end": candidate_end.isoformat()})
                if len(slots) >= 5:
                    return slots

            cursor += timedelta(minutes=30)

        current_day += timedelta(days=1)

    return slots


def calendar_freebusy(time_min: str, time_max: str, duration_minutes: int = 60) -> dict:
    """Tra cứu khoảng thời gian bận/rảnh trên Google Calendar."""
    if not settings.google_enabled:
        raise ConfigurationError("GOOGLE_ENABLED=false")

    try:
        service = GoogleOAuthService().build_calendar_service()
        response = service.freebusy().query(body={
            "timeMin": time_min,
            "timeMax": time_max,
            "timeZone": settings.timezone,
            "items": [{"id": settings.google_calendar_id}],
        }).execute()

        busy = response.get("calendars", {}).get(settings.google_calendar_id, {}).get("busy", [])
        start = _parse_iso(time_min)
        end = _parse_iso(time_max)

        return {
            "busy": busy,
            "candidate_slots": _find_free_slots(start, end, busy, duration_minutes),
        }
    except Exception as exc:
        raise ToolExecutionError(f"Calendar free/busy failed: {exc}") from exc


def calendar_create_event(
    title: str,
    start: str,
    end: str,
    attendees: list[str] | None = None,
    description: str = "",
) -> dict:
    """Tạo sự kiện mới trên Google Calendar."""
    if not settings.google_enabled:
        raise ConfigurationError("GOOGLE_ENABLED=false")

    try:
        service = GoogleOAuthService().build_calendar_service()
        body = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start, "timeZone": settings.timezone},
            "end": {"dateTime": end, "timeZone": settings.timezone},
            "attendees": [{"email": email} for email in (attendees or [])],
        }

        event = service.events().insert(
            calendarId=settings.google_calendar_id,
            body=body,
            sendUpdates="none",
        ).execute()

        return {"event_id": event.get("id"), "html_link": event.get("htmlLink")}
    except Exception as exc:
        raise ToolExecutionError(f"Create calendar event failed: {exc}") from exc


if __name__ == "__main__":
    now = datetime.now(ZoneInfo(settings.timezone)).replace(minute=0, second=0, microsecond=0)
    result = calendar_freebusy(
        now.isoformat(),
        (now + timedelta(days=3)).isoformat(),
        duration_minutes=60,
    )
    print(result)