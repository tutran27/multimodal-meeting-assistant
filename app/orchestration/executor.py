"""
Module: executor.py
Vai trò: Thực thi Plan từng bước — hỗ trợ chạy song song, retry, policy gate,
         và cập nhật kết quả vào RunState.
"""

import asyncio
import json
import logging
from typing import Any

from app.core.config import settings
from app.core.constants import StepStatus
from app.core.exceptions import ApprovalRequiredError
from app.orchestration.plan_validator import validate_plan
from app.orchestration.policy_gate import check_policy
from app.orchestration.reference_resolver import resolve_arguments
from app.schemas.plan import PlanStep
from app.schemas.state import RunState
from app.schemas.validation import ValidationIssue
from app.tools.gmail_draft import create_email_draft
from app.tools.google_calendar import calendar_create_event, calendar_freebusy
from app.tools.pdf_generator import generate_pdf
from app.tools.web_search import web_search

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers & Tool Execution
# ---------------------------------------------------------------------------

def _handle_email_draft(arguments: dict[str, Any], state: RunState) -> dict:
    """Xử lý tạo email nháp từ arguments hoặc state."""
    recipient = arguments.get("recipient") or settings.default_boss_email
    if not recipient:
        raise ValueError("Missing email recipient. Set DEFAULT_BOSS_EMAIL in .env or plan.")

    body = arguments.get("body") or state.extraction.summary or "Tóm tắt cuộc họp"
    return create_email_draft(
        recipient=recipient,
        subject=arguments.get("subject", "Meeting summary and follow-up actions"),
        body=body,
        attachment_path=arguments.get("attachment_path") or state.report_path,
    )


def _execute_tool(step: PlanStep, state: RunState) -> dict:
    """Gọi tool phù hợp dựa trên step.tool_name."""
    arguments = resolve_arguments(step.arguments, state)
    tool_name = step.tool_name

    if tool_name == "calendar_freebusy":
        result = calendar_freebusy(**arguments)
    elif tool_name == "calendar_create_event":
        result = calendar_create_event(**arguments)
    elif tool_name == "web_search":
        result = web_search(**arguments)
    elif tool_name == "pdf_generator":
        result = generate_pdf(state)
    elif tool_name == "email_create_draft":
        result = _handle_email_draft(arguments, state)
    else:
        raise ValueError(f"Unsupported tool: {tool_name}")

    result["_tool_name"] = tool_name
    return result


async def _run_step_with_retry(step: PlanStep, state: RunState) -> dict:
    """Chạy tool với cơ chế retry nếu xảy ra lỗi."""
    last_error: Exception | None = None

    for attempt in range(settings.max_tool_retries + 1):
        try:
            return await asyncio.to_thread(_execute_tool, step, state)
        except Exception as exc:
            last_error = exc
            logger.warning("Step %s failed (attempt %d): %s", step.step_id, attempt + 1, exc)

    raise last_error  # type: ignore[misc]


def _apply_result(step: PlanStep, result: dict, state: RunState) -> None:
    """Cập nhật kết quả vào state."""
    state.tool_results[step.step_id] = result

    if step.tool_name == "pdf_generator":
        state.report_path = result.get("file_path")
    elif step.tool_name == "email_create_draft":
        state.email_draft_id = result.get("draft_id")


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

async def execute_plan(state: RunState, approved_steps: set[str] | None = None) -> RunState:
    """Thực thi toàn bộ plan theo thứ tự phụ thuộc (dependency graph)."""
    validate_plan(state.plan)

    completed: set[str] = set()
    failed: set[str] = set()

    while len(completed) + len(failed) < len(state.plan):
        # 1. Tìm các bước có thể chạy ngay (dependencies đã completed)
        runnable = [
            s for s in state.plan
            if s.step_id not in completed and s.step_id not in failed
            and all(dep in completed for dep in s.depends_on)
        ]

        if not runnable:
            state.validation_issues.append(ValidationIssue(
                issue_type="deadlock",
                message="No runnable step remains. The plan is blocked.",
                repairable=False,
            ))
            break

        # 2. Kiểm tra Policy Gate (phê duyệt an toàn)
        allowed_steps: list[PlanStep] = []
        for step in runnable:
            try:
                check_policy(step, approved_steps)
                step.status = StepStatus.RUNNING
                allowed_steps.append(step)
            except ApprovalRequiredError as exc:
                step.status = StepStatus.SKIPPED
                failed.add(step.step_id)
                state.validation_issues.append(ValidationIssue(
                    issue_type="approval_required",
                    message=str(exc),
                    related_step=step.step_id,
                ))

        if not allowed_steps:
            continue

        # 3. Thực thi (dùng asyncio.gather gom lỗi tự động)
        results = await asyncio.gather(
            *[_run_step_with_retry(step, state) for step in allowed_steps],
            return_exceptions=True,
        )

        # 4. Ghi nhận kết quả
        for step, result in zip(allowed_steps, results):
            if isinstance(result, Exception):
                step.status = StepStatus.FAILED
                failed.add(step.step_id)
                state.validation_issues.append(ValidationIssue(
                    issue_type="tool_error",
                    message=str(result),
                    related_step=step.step_id,
                ))
            else:
                step.status = StepStatus.COMPLETED
                completed.add(step.step_id)
                _apply_result(step, result, state)

    return state


if __name__ == "__main__":
    from app.schemas.extraction import MeetingExtraction, ActionItem

    async def demo() -> None:
        state = RunState(
            session_id="executor_demo",
            user_request="Tạo báo cáo PDF",
            extraction=MeetingExtraction(
                summary="Cuộc họp thống nhất gửi báo giá cho đối tác.",
                action_items=[
                    ActionItem(
                        action_id="ACTION_001",
                        description="Gửi bản báo giá chính thức",
                        owner="Nam",
                        deadline="2025-01-05",
                    )
                ],
            ),
        )
        
        state.plan = [
            PlanStep(
                step_id="pdf_1",
                objective="Create PDF",
                tool_name="pdf_generator",
            )
        ]
        
        result = await execute_plan(state)
        print(json.dumps(result.tool_results, ensure_ascii=False, indent=2))

    asyncio.run(demo())
