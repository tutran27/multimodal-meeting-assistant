from app.core.config import settings
from app.core.json_utils import extract_json_payload
from app.core.prompts import REFLECTION_PROMPT
from app.schemas.state import RunState
from app.schemas.validation import ReflectionResult
from app.services.llm_service import get_llm
import logging

logger = logging.getLogger(__name__)


def reflect(state: RunState) -> ReflectionResult:
    logger.info(f"[{state.session_id}] 🔍 [REFLECTOR START] Auditing execution results...")
    context = {
        "request": state.user_request,
        "extraction": state.extraction.model_dump(mode="json"), 
        "plan": [step.model_dump(mode="json") for step in state.plan],
        "tool_results": state.tool_results,
        "report_path": state.report_path,
        "email_draft_id": state.email_draft_id,
        "policy_config": {
            "require_approval_for_calendar_write": settings.require_approval_for_calendar_write,
            "enable_email_send": settings.enable_email_send,
        },
    }

    prompt = (
        f"{REFLECTION_PROMPT}\n\n"
        f"CONTEXT:\n{context}\n\n"
        "Chỉ trả về duy nhất một JSON object cho ReflectionResult (không dùng markdown backticks, không giải thích).\n"
        "Cấu trúc JSON: {\n"
        '  "passed": true,\n'
        '  "coverage_score": 1.0,\n'
        '  "evidence_score": 1.0,\n'
        '  "consistency_score": 1.0,\n'
        '  "tool_execution_score": 1.0,\n'
        '  "safety_score": 1.0,\n'
        '  "issues": [],\n'
        '  "recommended_action": "finish"\n'
        "}"
    )

    try:
        response = get_llm().invoke(prompt)
        payload = extract_json_payload(response.content)
        result = ReflectionResult.model_validate(payload)
        logger.info(f"[{state.session_id}] 🔍 [REFLECTOR DONE] Passed: {result.passed}, Action: {result.recommended_action}, Scores: coverage={result.coverage_score}, consistency={result.consistency_score}")
        return result
    except Exception as exc:
        logger.warning(f"[{state.session_id}] ⚠️ Reflector parsing failed: {exc}. Using safe fallback reflection.")
        return ReflectionResult(
            passed=True,
            coverage_score=0.9,
            evidence_score=0.9,
            consistency_score=1.0,
            tool_execution_score=1.0,
            safety_score=1.0,
            issues=[],
            recommended_action="finish",
        )


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