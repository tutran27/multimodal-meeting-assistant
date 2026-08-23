"""
Module: executor.py
Vai trò: Thực thi Plan từng bước — hỗ trợ chạy song song, retry, policy gate,
         và cập nhật kết quả vào RunState.
"""

import asyncio
import json
import logging
import re
from typing import Any

from app.core.config import settings
from app.core.constants import StepStatus
from app.core.exceptions import ApprovalRequiredError
from app.core.prompts import EMAIL_DRAFT_PROMPT
from app.orchestration.plan_validator import validate_plan
from app.orchestration.policy_gate import check_policy
from app.orchestration.reference_resolver import resolve_arguments
from app.schemas.plan import PlanStep
from app.schemas.state import RunState
from app.schemas.validation import ValidationIssue
from app.services.llm_service import get_llm
from app.tools.gmail_draft import create_email_draft
from app.tools.google_calendar import calendar_create_event, calendar_freebusy
from app.tools.pdf_generator import generate_pdf
from app.tools.web_search import web_search

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers & Tool Execution
# ---------------------------------------------------------------------------

def _compose_email_body(state: RunState, recipient: str, subject: str) -> str:
    """Sử dụng LLM để tự động soạn nội dung email trang trọng và hoàn chỉnh từ state."""
    logger.info(f"[{state.session_id}] ✍️ [EMAIL DRAFTER] Composing professional email body for {recipient}...")
    
    actions_desc = "\n".join(
        f"- {item.description}" + (f" (Phụ trách: {item.owner})" if item.owner else "") + (f" [Deadline: {item.deadline}]" if item.deadline else "")
        for item in state.extraction.action_items
    ) or "Không có đầu việc phát sinh."

    decisions_desc = "\n".join(f"- {d}" for d in state.extraction.decisions) or "Không có quyết định đặc biệt."

    prompt = (
        f"{EMAIL_DRAFT_PROMPT}\n\n"
        f"NGỮ CẢNH CUỘC HỌP & HỆ THỐNG:\n"
        f"- Người nhận: {recipient}\n"
        f"- Tiêu đề email: {subject}\n"
        f"- Yêu cầu của người dùng: {state.user_request}\n"
        f"- Tóm tắt cuộc họp: {state.extraction.summary}\n"
        f"- Các quyết định chính:\n{decisions_desc}\n"
        f"- Danh sách công việc cần làm (Action Items):\n{actions_desc}\n"
        f"- File báo cáo PDF đính kèm: {'Có đính kèm file báo cáo chi tiết' if state.report_path else 'Không có'}\n\n"
        f"Hãy soạn thảo nội dung email hoàn chỉnh:"
    )

    try:
        response = get_llm().invoke(prompt)
        content = response.content.strip()
        content = re.sub(r"^```(?:markdown|text|email)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        logger.info(f"[{state.session_id}] ✍️ [EMAIL DRAFTER DONE] Composed email body ({len(content)} chars)")
        return content
    except Exception as exc:
        logger.warning(f"[{state.session_id}] ⚠️ Failed to compose email with LLM: {exc}. Falling back to summary.")
        return state.extraction.summary or "Tóm tắt cuộc họp"


def _handle_email_draft(arguments: dict[str, Any], state: RunState) -> dict:
    """Xử lý tạo email nháp từ arguments hoặc sinh tự động bằng LLM."""
    recipient = arguments.get("recipient") or settings.default_boss_email
    if not recipient:
        raise ValueError("Missing email recipient. Set DEFAULT_BOSS_EMAIL in .env or plan.")

    subject = arguments.get("subject", "Meeting summary and follow-up actions")
    raw_body = arguments.get("body")

    # Nếu body chưa có hoặc chỉ là summary thô / placeholder, dùng LLM để tự soạn email chuẩn
    if not raw_body or raw_body.strip() == "" or (state.extraction.summary and raw_body.strip() == state.extraction.summary.strip()):
        body = _compose_email_body(state, recipient, subject)
    else:
        body = raw_body

    return create_email_draft(
        recipient=recipient,
        subject=subject,
        body=body,
        attachment_path=arguments.get("attachment_path") or state.report_path,
    )


def _handle_calendar_create_event(arguments: dict[str, Any], state: RunState) -> dict:
    """Tạo sự kiện lịch: nếu chưa có start/end, tự động lấy slot rảnh đầu tiên từ freebusy."""
    if not arguments.get("start") or str(arguments.get("start")).startswith("{{"):
        for res in state.tool_results.values():
            slots = res.get("candidate_slots", []) if isinstance(res, dict) else []
            if slots:
                arguments["start"] = slots[0]["start"]
                arguments["end"] = slots[0]["end"]
                break

    return calendar_create_event(**arguments)


def _execute_tool(step: PlanStep, state: RunState) -> dict:
    """Gọi tool phù hợp dựa trên step.tool_name."""
    arguments = resolve_arguments(step.arguments, state)
    tool_name = step.tool_name
    logger.info(f"[{state.session_id}] 🔧 [TOOL START] {step.step_id} -> {tool_name} with arguments: {arguments}")

    if tool_name == "calendar_freebusy":
        result = calendar_freebusy(**arguments)
    elif tool_name == "calendar_create_event":
        result = _handle_calendar_create_event(arguments, state)
    elif tool_name == "web_search":
        result = web_search(**arguments)
    elif tool_name == "pdf_generator":
        result = generate_pdf(state)
    elif tool_name == "email_create_draft":
        result = _handle_email_draft(arguments, state)
    else:
        raise ValueError(f"Unsupported tool: {tool_name}")

    result["_tool_name"] = tool_name
    logger.info(f"[{state.session_id}] 🎯 [TOOL SUCCESS] {step.step_id} -> {tool_name} returned: {result}")
    return result


async def _run_step_with_retry(step: PlanStep, state: RunState) -> dict:
    """Chạy tool với cơ chế retry nếu xảy ra lỗi."""
    last_error: Exception | None = None

    for attempt in range(settings.max_tool_retries + 1):
        try:
            return await asyncio.to_thread(_execute_tool, step, state)
        except Exception as exc:
            last_error = exc
            logger.warning(f"[{state.session_id}] ⚠️ Step {step.step_id} ({step.tool_name}) failed attempt {attempt + 1}/{settings.max_tool_retries + 1}: {exc}")

    raise last_error  # type: ignore[misc]


def _apply_result(step: PlanStep, result: dict, state: RunState) -> None:
    """Cập nhật kết quả vào state."""
    state.tool_results[step.step_id] = result

    if step.tool_name == "pdf_generator":
        state.report_path = result.get("file_path")
        logger.info(f"[{state.session_id}] 📄 Set state.report_path = {state.report_path}")
    elif step.tool_name == "email_create_draft":
        state.email_draft_id = result.get("draft_id")
        logger.info(f"[{state.session_id}] ✉️ Set state.email_draft_id = {state.email_draft_id}")


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

async def execute_plan(state: RunState, approved_steps: set[str] | None = None) -> RunState:
    """Thực thi toàn bộ plan theo thứ tự phụ thuộc (dependency graph)."""
    validate_plan(state.plan)

    completed: set[str] = set()
    failed: set[str] = set()

    logger.info(f"[{state.session_id}] 🚀 Starting DAG Execution for {len(state.plan)} steps...")

    while len(completed) + len(failed) < len(state.plan):
        # 1. Tìm các bước có thể chạy ngay (dependencies đã completed)
        runnable = [
            s for s in state.plan
            if s.step_id not in completed and s.step_id not in failed
            and all(dep in completed for dep in s.depends_on)
        ]

        if not runnable:
            logger.error(f"[{state.session_id}] ❌ Deadlock detected! Completed: {completed}, Failed: {failed}")
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
                logger.warning(f"[{state.session_id}] ⛔ Policy Gate BLOCKED step {step.step_id} ({step.tool_name}): Approval required")
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
        logger.info(f"[{state.session_id}] ⚡ Executing batch of {len(allowed_steps)} steps in parallel: {[s.step_id for s in allowed_steps]}")
        results = await asyncio.gather(
            *[_run_step_with_retry(step, state) for step in allowed_steps],
            return_exceptions=True,
        )

        # 4. Ghi nhận kết quả
        for step, result in zip(allowed_steps, results):
            if isinstance(result, Exception):
                logger.error(f"[{state.session_id}] ❌ Step {step.step_id} ({step.tool_name}) FAILED: {result}")
                step.status = StepStatus.FAILED
                failed.add(step.step_id)
                state.validation_issues.append(ValidationIssue(
                    issue_type="tool_error",
                    message=str(result),
                    related_step=step.step_id,
                ))
            else:
                logger.info(f"[{state.session_id}] ✅ Step {step.step_id} ({step.tool_name}) COMPLETED successfully")
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
