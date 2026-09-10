"""Các hàm truy vấn SQL thuần cho bảng `workflow_runs`."""
import json
from typing import Optional, List, Union
from pydantic import BaseModel
from app.db.pool import get_pool
from app.core.constants import ScriptType, WorkflowStatus
from app.schemas.state import RunState


async def create_run(
    user_id: str,
    session_id: str,
    user_request: str,
    title: Optional[str] = None,
    script_type: Optional[Union[str, ScriptType]] = None,
) -> dict:
    """Tạo mới một phiên xử lý cuộc họp (status = 'created')."""
    type_val = script_type.value if hasattr(script_type, "value") else script_type
    row = await get_pool().fetchrow(
        """
        INSERT INTO workflow_runs (user_id, session_id, user_request, title, script_type, status)
        VALUES ($1::uuid, $2, $3, $4, $5, 'created')
        RETURNING *
        """,
        user_id, session_id, user_request, title, type_val
    )
    return dict(row) if row else {}


async def update_run_status(
    session_id: str,
    user_id: str,
    status: Union[str, WorkflowStatus],
    title: Optional[str] = None,
    extraction_summary: Optional[Union[dict, BaseModel]] = None,
    report_path: Optional[str] = None,
    email_draft_id: Optional[str] = None,
    error_message: Optional[str] = None,
    duration_ms: Optional[int] = None,
) -> Optional[dict]:
    """Cập nhật trạng thái và kết quả đầu ra của phiên xử lý cuộc họp."""
    status_str = status.value if hasattr(status, "value") else str(status)
    is_completed = status_str in ("completed", "failed")

    summary_data = None
    if extraction_summary is not None:
        summary_data = (
            extraction_summary.model_dump() if isinstance(extraction_summary, BaseModel)
            else extraction_summary
        )
    summary_json = json.dumps(summary_data, ensure_ascii=False) if summary_data is not None else None

    row = await get_pool().fetchrow(
        """
        UPDATE workflow_runs
        SET status = $1,
            title = COALESCE($2, title),
            extraction_summary = COALESCE($3::jsonb, extraction_summary),
            report_path = COALESCE($4, report_path),
            email_draft_id = COALESCE($5, email_draft_id),
            error_message = COALESCE($6, error_message),
            duration_ms = COALESCE($7, duration_ms),
            completed_at = CASE WHEN $8::boolean THEN NOW() ELSE completed_at END
        WHERE session_id = $9 AND user_id = $10::uuid
        RETURNING *
        """,
        status_str, title, summary_json, report_path, email_draft_id,
        error_message, duration_ms, is_completed, session_id, user_id
    )
    return dict(row) if row else None


async def sync_run_state(
    user_id: str,
    state: RunState,
    duration_ms: Optional[int] = None,
    error_message: Optional[str] = None,
) -> Optional[dict]:
    """Đồng bộ nhanh toàn bộ RunState hiện tại vào database."""
    title = state.extraction.summary[:120] if (state.extraction and state.extraction.summary) else None
    if not error_message and state.reflection and not state.reflection.passed:
        error_message = state.reflection.reasoning

    return await update_run_status(
        session_id=state.session_id,
        user_id=user_id,
        status=state.status,
        title=title,
        extraction_summary=state.extraction,
        report_path=state.report_path,
        email_draft_id=state.email_draft_id,
        error_message=error_message,
        duration_ms=duration_ms,
    )


async def get_run_by_session_id(user_id: str, session_id: str) -> Optional[dict]:
    """Lấy chi tiết một phiên chạy theo session_id và user_id."""
    row = await get_pool().fetchrow(
        "SELECT * FROM workflow_runs WHERE session_id = $1 AND user_id = $2::uuid",
        session_id, user_id
    )
    return dict(row) if row else None


async def list_runs_by_user(user_id: str, limit: int = 20, offset: int = 0) -> List[dict]:
    """Lấy danh sách lịch sử các phiên họp của user theo thứ tự mới nhất."""
    rows = await get_pool().fetch(
        """
        SELECT * FROM workflow_runs
        WHERE user_id = $1::uuid
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
        """,
        user_id, limit, offset
    )
    return [dict(row) for row in rows]
