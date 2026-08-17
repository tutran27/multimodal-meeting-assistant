"""
Module: policy_gate.py
Vai trò: Kiểm tra chính sách trước khi thực thi một step —
         các hành động nhạy cảm (ghi calendar, gửi email) phải được phê duyệt.
"""

from app.core.config import settings
from app.core.exceptions import ApprovalRequiredError
from app.schemas.plan import PlanStep


def check_policy(
    step: PlanStep, 
    approved_steps: set[str] | None = None
) -> None:
    
    """Raise ApprovalRequiredError nếu step vi phạm chính sách."""
    approved_steps = approved_steps or set()

    # Ghi calendar: yêu cầu phê duyệt nếu setting bật
    if step.tool_name == "calendar_create_event":
        if settings.require_approval_for_calendar_write and step.step_id not in approved_steps:
            raise ApprovalRequiredError(f"Calendar write requires approval: {step.step_id}")

    # Gửi email: luôn bị chặn trong project này
    if step.tool_name == "email_send":
        raise ApprovalRequiredError("Email sending is disabled in this project")


if __name__ == "__main__":
    from app.core.constants import RiskLevel

    demo = PlanStep(
        step_id="calendar_write",
        objective="Create event",
        tool_name="calendar_create_event",
        risk_level=RiskLevel.EXTERNAL_WRITE,
    )

    try:
        check_policy(demo)
    except ApprovalRequiredError as exc:
        print(exc)