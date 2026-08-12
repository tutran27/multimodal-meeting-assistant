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