"""Các hàm truy vấn SQL thuần cho bảng `approval_requests` (Hàng đợi phê duyệt Human-in-the-loop)."""
import json
from datetime import datetime, timedelta, timezone
from typing import Any
from app.db.pool import get_pool
from app.schemas.plan import PlanStep


# Truyền lẻ các tham số tool_name và arguments
async def create_approval_request(
    run_id: str,
    user_id: str,
    tool_name: str,
    arguments: dict[str, Any],
    step_id: str | None = None,
    expires_in_hours: int = 24,
) -> dict:
    """Tạo mới 1 yêu cầu phê duyệt cho 1 hành động/công cụ cụ thể (status = 'pending')."""
    payload = dict(arguments or {})
    if step_id:
        payload["step_id"] = step_id

    args_json = json.dumps(payload, ensure_ascii=False)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

    row = await get_pool().fetchrow(
        """
        INSERT INTO approval_requests (run_id, user_id, tool_name, arguments, status, expires_at)
        VALUES ($1::uuid, $2::uuid, $3, $4::jsonb, 'pending', $5)
        RETURNING *
        """,
        run_id, user_id, tool_name, args_json, expires_at
    )
    return dict(row) if row else {}

# Truyền object PlanStep
async def create_approval_for_step(
    run_id: str,
    user_id: str,
    step: PlanStep,
    expires_in_hours: int = 24,
) -> dict:
    """Tạo nhanh yêu cầu phê duyệt trực tiếp từ 1 đối tượng PlanStep."""
    return await create_approval_request(
        run_id=run_id,
        user_id=user_id,
        tool_name=step.tool_name,
        arguments=step.arguments,
        step_id=step.step_id,
        expires_in_hours=expires_in_hours,
    )


async def decide_approval(
    approval_id: str,
    user_id: str,
    status: str,
    decided_by: str = "user",
    reason: str | None = None,
) -> dict | None:
    """Cập nhật quyết định phê duyệt ('approved' hoặc 'rejected')."""
    valid_statuses = {"approved", "rejected", "expired"}
    normalized_status = status.lower().strip()
    
    if normalized_status not in valid_statuses:
        raise ValueError(f"Trạng thái không hợp lệ: '{status}'. Hợp lệ: {valid_statuses}")

    row = await get_pool().fetchrow(
        """
        UPDATE approval_requests
        SET status = $1, decided_by = $2, reason = $3, decided_at = NOW()
        WHERE id = $4::uuid AND user_id = $5::uuid AND status = 'pending'
        RETURNING *
        """,
        normalized_status, decided_by, reason, approval_id, user_id
    )
    return dict(row) if row else None


async def list_pending_approvals(user_id: str, run_id: str | None = None) -> list[dict]:
    """Lấy danh sách các yêu cầu phê duyệt đang chờ xử lý và chưa hết hạn."""
    if run_id:
        rows = await get_pool().fetch(
            """
            SELECT * FROM approval_requests
            WHERE user_id = $1::uuid AND status = 'pending'
              AND run_id = $2::uuid
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY created_at DESC
            """,
            user_id, run_id
        )
    else:
        rows = await get_pool().fetch(
            """
            SELECT * FROM approval_requests
            WHERE user_id = $1::uuid AND status = 'pending'
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY created_at DESC
            """,
            user_id
        )
    return [dict(row) for row in rows]


async def get_approval_by_id(approval_id: str, user_id: str) -> dict | None:
    """Lấy chi tiết một yêu cầu phê duyệt."""
    row = await get_pool().fetchrow(
        "SELECT * FROM approval_requests WHERE id = $1::uuid AND user_id = $2::uuid",
        approval_id, user_id
    )
    return dict(row) if row else None
