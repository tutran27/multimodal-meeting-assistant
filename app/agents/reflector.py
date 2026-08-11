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