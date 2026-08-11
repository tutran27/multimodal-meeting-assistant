from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.core.prompts import PLANNER_PROMPT
from app.schemas.plan import ExecutionPlan
from app.schemas.state import RunState
from app.services.llm_service import get_llm


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

    prompt = f"{PLANNER_PROMPT}\n\nCONTEXT:\n{context}"

    structured_llm = get_llm().with_structured_output(ExecutionPlan)
    plan = structured_llm.invoke(prompt)
    return plan


if __name__ == "__main__":
    from app.schemas.extraction import MeetingExtraction

    demo = RunState(
        session_id="demo",
        user_request="Kiểm tra lịch, tìm đối tác, tạo PDF và email draft",
        extraction=MeetingExtraction.model_validate({
  "summary": "Cuộc họp bắt đầu lúc 9:00 với Nam (PM), Minh (Sales), Lan (Tech Lead) và Hoàng đại diện ABC Corporation. Lan trình bày quyết định sử dụng thư viện ReportLab để xuất báo cáo PDF và sẽ hoàn thành bản POC trước thứ Tư. Minh sẽ hoàn thiện file báo giá chi tiết và gửi cho Hoàng trước 17:00 thứ Sáu (2026-08-15). Hoàng đặt câu hỏi về việc áp dụng chiết khấu 5% đồng thời với ưu đãi hỗ trợ kỹ thuật. Hai bên thống nhất ký MOU hợp tác giai đoạn 1 trong tháng 8.",
  "participants": [
    "Nam",
    "Minh",
    "Lan",
    "Hoàng"
  ],
  "organizations": [
    "ABC Corporation"
  ],
  "decisions": [
    "Hai bên thống nhất ký MOU hợp tác giai đoạn 1 trong tháng 8."
  ],
  "action_items": [
    {
      "action_id": "ACTION_001",
      "description": "Hoàn thành bản POC trước thứ Tư",
      "owner": "Lan",
      "deadline": None,
      "priority": "medium",
      "duration_minutes": None,
      "evidence_ids": [
        "AUDIO_001"
      ],
      "status": "unverified"
    },
    {
      "action_id": "ACTION_002",
      "description": "Hoàn thiện file báo giá chi tiết và gửi cho anh Hoàng trước 17:00 thứ Sáu (2026-08-15)",
      "owner": "Minh",
      "deadline": "2026-08-15",
      "priority": "medium",
      "duration_minutes": None,
      "evidence_ids": [
        "SCRIPT_002"
      ],
      "status": "unverified"
    }
  ],
  "unresolved_questions": [
    "Chiết khấu 5% cho hợp đồng năm có áp dụng đồng thời với ưu đãi hỗ trợ kỹ thuật không?"
  ]
}),
    )

    result = create_plan(demo)
    print(result.model_dump_json(indent=2))