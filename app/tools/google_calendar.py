"""
Module: google_calendar.py
Vai trò: Quản lý tích hợp Google Calendar API — tra cứu lịch rảnh và tạo sự kiện lịch.

Mô tả chi tiết:
- Kết nối với Google Calendar API qua `GoogleOAuthService` để tương tác với lịch làm việc của người dùng.
- Tra cứu lịch bận/rảnh (`calendar_freebusy`) trong khoảng thời gian chỉ định và tự động gợi ý các khung giờ rảnh (candidate slots) phù hợp trong giờ làm việc.
- Tạo sự kiện mới (`calendar_create_event`) trên Google Calendar với đầy đủ thông tin: tiêu đề, mô tả, thời gian bắt đầu/kết thúc và danh sách người tham dự.
"""

import logging
from typing import Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.core.exceptions import ConfigurationError, ToolExecutionError
from app.services.oauth_service import GoogleOAuthService

logger = logging.getLogger(__name__)


def _normalize_attendees(attendees: list[Any] | None) -> list[dict[str, str]]:
    """Chuẩn hóa danh sách người tham gia sang định dạng Google Calendar API."""
    if not attendees:
        return []

    valid_attendees: list[dict[str, str]] = []
    seen: set[str] = set()

    for item in attendees:
        if not item:
            continue
        email: str | None = None
        display_name: str | None = None

        if isinstance(item, dict):
            email = item.get("email")
            display_name = item.get("displayName") or item.get("name")
        elif isinstance(item, str):
            item_str = item.strip()
            if "@" in item_str:
                email = item_str
            else:
                display_name = item_str

        if email and email.lower() not in seen:
            seen.add(email.lower())
            entry: dict[str, str] = {"email": email}
            if display_name:
                entry["displayName"] = display_name
            valid_attendees.append(entry)

    return valid_attendees

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


def calendar_freebusy(
    time_min: str | None = None,
    time_max: str | None = None,
    duration_minutes: int = 60,
    **kwargs: Any,
) -> dict:
    """Tra cứu khoảng thời gian bận/rảnh trên Google Calendar."""
    # Hỗ trợ linh hoạt cả time_min/time_max, start/end, start_time/end_time
    time_min = time_min or kwargs.get("start") or kwargs.get("start_time") or kwargs.get("timeMin")
    time_max = time_max or kwargs.get("end") or kwargs.get("end_time") or kwargs.get("timeMax")
    duration_minutes = int(kwargs.get("duration") or duration_minutes or 60)

    if not time_min or not time_max:
        raise ValueError(f"Missing time range for calendar_freebusy: time_min={time_min}, time_max={time_max}")

    logger.info(f"📅 [CALENDAR FREEBUSY START] Looking up free slots from {time_min} to {time_max} (duration={duration_minutes}m)")
    if not settings.google_enabled:
        logger.warning("📅 [CALENDAR FREEBUSY] GOOGLE_ENABLED=false: returning mock/empty result")
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
        candidate_slots = _find_free_slots(start, end, busy, duration_minutes)

        logger.info(f"📅 [CALENDAR FREEBUSY DONE] Found {len(busy)} busy ranges, generated {len(candidate_slots)} candidate free slots")
        return {
            "busy": busy,
            "candidate_slots": candidate_slots,
        }
    except Exception as exc:
        logger.error(f"📅 [CALENDAR FREEBUSY ERROR] Lookup failed: {exc}")
        raise ToolExecutionError(f"Calendar free/busy failed: {exc}") from exc


def calendar_create_event(
    title: str | None = None,
    start: str | None = None,
    end: str | None = None,
    attendees: list[str] | None = None,
    description: str = "",
    **kwargs: Any,
) -> dict:
    """Tạo sự kiện mới trên Google Calendar."""
    # Hỗ trợ linh hoạt các biến thể tham số từ LLM Planner
    title = title or kwargs.get("summary") or kwargs.get("name") or "Cuộc họp"
    start = start or kwargs.get("start_time") or kwargs.get("time_min") or kwargs.get("timeMin")
    end = end or kwargs.get("end_time") or kwargs.get("time_max") or kwargs.get("timeMax")
    attendees = attendees or kwargs.get("participants") or kwargs.get("emails") or []
    description = description or kwargs.get("details") or ""

    if not start or not end:
        raise ValueError(f"Missing start/end time for calendar_create_event: start={start}, end={end}")

    logger.info(f"📅 [CALENDAR CREATE EVENT START] Creating event '{title}' ({start} -> {end}) for attendees: {attendees}")
    if not settings.google_enabled:
        logger.warning("📅 [CALENDAR CREATE EVENT] GOOGLE_ENABLED=false")
        raise ConfigurationError("GOOGLE_ENABLED=false")

    try:
        service = GoogleOAuthService().build_calendar_service()
        valid_attendees = _normalize_attendees(attendees)
        body: dict[str, Any] = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start, "timeZone": settings.timezone},
            "end": {"dateTime": end, "timeZone": settings.timezone},
        }
        if valid_attendees:
            body["attendees"] = valid_attendees

        # Nếu có người tham dự, gửi email thư mời ("all") để sự kiện tự đồng bộ vào Calendar của họ; nếu là task cá nhân thì ghi âm thầm ("none")
        send_updates = kwargs.get("send_updates") or kwargs.get("sendUpdates") or ("all" if valid_attendees else "none")

        event = service.events().insert(
            calendarId=settings.google_calendar_id,
            body=body,
            sendUpdates=send_updates,
        ).execute()

        event_id = event.get("id")
        html_link = event.get("htmlLink")
        logger.info(f"📅 [CALENDAR CREATE EVENT DONE] Created event ID={event_id} Link={html_link} (sendUpdates={send_updates})")
        return {"event_id": event_id, "html_link": html_link, "attendees": valid_attendees}
    except Exception as exc:
        logger.error(f"📅 [CALENDAR CREATE EVENT ERROR] Failed to create event '{title}': {exc}")
        raise ToolExecutionError(f"Create calendar event failed: {exc}") from exc


if __name__ == "__main__":
    now = datetime.now(ZoneInfo(settings.timezone)).replace(minute=0, second=0, microsecond=0)
    result = calendar_freebusy(
        now.isoformat(),
        (now + timedelta(days=3)).isoformat(),
        duration_minutes=60,
    )
    print(result)