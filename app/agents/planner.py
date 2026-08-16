"""
Module: planner.py
Vai trò: Planning Agent chịu trách nhiệm lập kế hoạch thực thi các bước hành động (ExecutionPlan) dựa trên yêu cầu người dùng và thông tin đã trích xuất.

Mô tả chi tiết:
- Tổng hợp ngữ cảnh từ trạng thái thực thi hiện tại: yêu cầu của người dùng (`user_request`), tóm tắt cuộc họp (`summary`), các đối tác/tổ chức liên quan (`organizations`), danh sách hành động cần làm (`action_items`), thời gian hiện tại và múi giờ hệ thống.
- Sử dụng LLM và Prompt lập kế hoạch (`PLANNER_PROMPT`) để phân tích và sinh ra danh sách các bước thực thi (`ExecutionStep`).
- Mỗi bước thực thi xác định rõ: mục tiêu (`objective`), công cụ cần gọi (`tool_name`), tham số truyền vào (`arguments`), và danh sách các bước phụ thuộc (`depends_on`).
- Cung cấp khối `__main__` để kiểm thử tạo và xuất kế hoạch thực thi ra tệp JSON cục bộ.
"""

import json
import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.core.prompts import PLANNER_PROMPT
from app.schemas.plan import ExecutionPlan
from app.schemas.state import RunState
from app.services.llm_service import get_llm


def _extract_json_object(text: str) -> dict[str, Any]:
    """Lấy JSON object từ response content của LLM."""
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"LLM không trả về JSON object hợp lệ: {text}")
    return json.loads(match.group(0))


def create_plan(state: RunState) -> ExecutionPlan:
    context = {
        "request": state.user_request,
        "summary": state.extraction.summary,
        "organizations": state.extraction.organizations,
        "action_items": [item.model_dump(mode="json") for item in state.extraction.action_items],
        "current_time": datetime.now(ZoneInfo(settings.timezone)).isoformat(),
        "timezone": settings.timezone,
        "default_boss_email": settings.default_boss_email,
    }

    prompt = (
        f"{PLANNER_PROMPT}\n\n"
        f"CONTEXT:\n{context}\n\n"
        "Chỉ trả về duy nhất một JSON object cho ExecutionPlan (không dùng markdown backticks, không giải thích).\n"
        "Cấu trúc JSON: {\"steps\": [ {\"step_id\": \"step1\", \"objective\": \"...\", \"tool_name\": \"...\", \"arguments\": {...}, \"depends_on\": []} ]}"
    )

    response = get_llm().invoke(prompt)
    payload = _extract_json_object(response.content)
    return ExecutionPlan.model_validate(payload)


if __name__ == "__main__":
    from pathlib import Path
    from app.schemas.extraction import MeetingExtraction

    extractor_file = Path("outputs/step/extractor.json")
    with open(extractor_file, "r", encoding="utf-8") as f:
        raw_extraction = json.load(f)

    demo = RunState(
        session_id="demo",
        user_request="Kiểm tra lịch, tìm đối tác, tạo PDF và email draft",
        extraction=MeetingExtraction.model_validate(raw_extraction),
    )

    result = create_plan(demo)
    print(result.model_dump_json(indent=2))

    output_plan_file = Path("outputs/step/planner.json")
    with open(output_plan_file, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)

    print(f"Đã lưu ExecutionPlan vào {output_plan_file}")