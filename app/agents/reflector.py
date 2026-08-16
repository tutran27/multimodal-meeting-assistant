"""
Module: reflector.py
Vai trò: Reflection Agent chịu trách nhiệm đánh giá, phản tư và kiểm tra chất lượng kết quả thực thi so với yêu cầu ban đầu.

Mô tả chi tiết:
- Tổng hợp toàn bộ ngữ cảnh thực thi: yêu cầu người dùng, thông tin trích xuất, kế hoạch thực thi, kết quả trả về từ các công cụ (tool results), đường dẫn báo cáo PDF và ID bản thảo email.
- Sử dụng mô hình LLM với đầu ra có cấu trúc (`ReflectionResult`) để đánh giá mức độ hoàn thành nhiệm vụ (`completed`), độ tin cậy (`confidence`), và phát hiện các điểm còn thiếu sót hoặc sai lệch.
- Đề xuất các điều chỉnh hoặc kích hoạt luồng lập lại kế hoạch (`replan`) nếu kết quả chưa đạt yêu cầu.
"""

from app.core.prompts import REFLECTION_PROMPT
from app.schemas.state import RunState
from app.schemas.validation import ReflectionResult
from app.services.llm_service import get_llm


def reflect(state: RunState) -> ReflectionResult:
    context = {
        "request": state.user_request,
        "extraction": state.extraction.model_dump(mode="json"), 
        "plan": [step.model_dump(mode="json") for step in state.plan],
        "tool_results": state.tool_results,
        "report_path": state.report_path,
        "email_draft_id": state.email_draft_id,
    }

    prompt = f"""{REFLECTION_PROMPT}\n\n
                CONTEXT:\n{context}\n
                Return the output in JSON format matching the schema."""

    structured_llm = get_llm().with_structured_output(ReflectionResult)
    return structured_llm.invoke(prompt)


if __name__ == "__main__":
    from app.schemas.extraction import ActionItem, MeetingExtraction

    demo = RunState(
        session_id="demo",
        user_request="Trích xuất việc cần làm",
        extraction=MeetingExtraction(
            action_items=[
                ActionItem(
                    action_id="ACTION_001",
                    description="Gửi báo giá",
                    evidence_ids=["SCRIPT_001"],
                )
            ]
        ),
    )

    result = reflect(demo)
    print(result.model_dump_json(indent=2))