"""
Module: reference_resolver.py
Vai trò: Tự động thay thế các biến giữ chỗ (dạng {{state.xxx}}) bằng dữ liệu thực tế trước khi gọi Tool.
"""

import re
from typing import Any
from app.schemas.state import RunState


REFERENCE_PATTERN = re.compile(r"^\{\{([^}]+)\}\}$")


def _lookup_state(path: str, state: RunState) -> Any:
    """Tìm và lấy giá trị bên trong state theo đường dẫn (ví dụ: 'extraction.summary')."""
    value: Any = state
    for part in path.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = getattr(value, part, None)
        if value is None:
            break
    return value


def resolve_value(value: Any, state: RunState) -> Any:
    """Quét và thay thế các biến giữ chỗ {{state.xxx}} trong chuỗi, danh sách hoặc từ điển."""
    if isinstance(value, str):
        match = REFERENCE_PATTERN.match(value.strip())
        if match:
            reference = match.group(1).strip()
            if reference.startswith("state."):
                return _lookup_state(reference.removeprefix("state."), state)
        return value

    if isinstance(value, list):
        return [resolve_value(item, state) for item in value]

    if isinstance(value, dict):
        return {key: resolve_value(item, state) for key, item in value.items()}

    return value


def resolve_arguments(arguments: dict[str, Any], state: RunState) -> dict[str, Any]:
    """Cập nhật toàn bộ tham số của Tool bằng dữ liệu thực tế lấy từ state."""
    resolved = resolve_value(arguments, state)
    return resolved if isinstance(resolved, dict) else {}


if __name__ == "__main__":
    from app.schemas.extraction import MeetingExtraction

    demo_state = RunState(
        session_id="session_123",
        user_request="Gửi báo cáo qua email",
        report_path="/reports/summary.pdf",
        extraction=MeetingExtraction(summary="Nội dung tóm tắt cuộc họp"),
        tool_results={"calendar_lookup": {"available": True, "free_slot": "14:00"}},
    )

    demo_args = {
        "session": "{{state.session_id}}",
        "attachment": "{{state.report_path}}",
        "summary": "{{state.extraction.summary}}",
        "slot": "{{state.tool_results.calendar_lookup.free_slot}}",
        "static_text": "Không thay đổi",
    }

    resolved = resolve_arguments(demo_args, demo_state)
    import json
    print(json.dumps(resolved, ensure_ascii=False, indent=2))