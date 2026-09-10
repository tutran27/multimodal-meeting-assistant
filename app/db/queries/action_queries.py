"""Các hàm truy vấn SQL thuần cho bảng `action_items`."""
import json
from typing import Optional, List, Any, Union
from datetime import datetime
from app.db.pool import get_pool
from app.schemas.extraction import ActionItem


def _parse_datetime(val: Any) -> Optional[datetime]:
    if isinstance(val, str) and val.strip():
        try:
            return datetime.fromisoformat(val.strip())
        except Exception:
            return None
    return val if isinstance(val, datetime) else None


async def batch_insert_action_items(
    run_id: str,
    user_id: str,
    action_items: List[Union[ActionItem, dict[str, Any]]],
) -> List[dict]:
    """Lưu danh sách ActionItem bóc tách từ cuộc họp vào cơ sở dữ liệu."""
    if not action_items:
        return []

    inserted = []
    for item in action_items:
        d = item.model_dump() if isinstance(item, ActionItem) else item
        status_val = d.get("status", "unverified")
        verification_status = status_val.value if hasattr(status_val, "value") else str(status_val)
        evidence_json = json.dumps(d.get("evidence_ids", []), ensure_ascii=False)

        row = await get_pool().fetchrow(
            """
            INSERT INTO action_items (
                run_id, user_id, action_id, description, owner_name,
                deadline, priority, duration_minutes, verification_status, evidence_refs
            )
            VALUES (
                $1::uuid, $2::uuid, $3, $4, $5,
                $6, $7, $8, $9, $10::jsonb
            )
            RETURNING *
            """,
            run_id,
            user_id,
            d.get("action_id"),
            d.get("description", ""),
            d.get("owner"),
            _parse_datetime(d.get("deadline")),
            d.get("priority", "medium").lower(),
            d.get("duration_minutes"),
            verification_status.lower(),
            evidence_json,
        )
        if row:
            inserted.append(dict(row))
    return inserted


async def update_action_status(action_identifier: str, user_id: str, task_status: str) -> Optional[dict]:
    """Cập nhật tiến độ hoàn thành công việc (chấp nhận UUID hoặc action_id nghiệp vụ)."""
    row = await get_pool().fetchrow(
        """
        UPDATE action_items
        SET task_status = $1, updated_at = NOW()
        WHERE user_id = $3::uuid 
          AND (id::text = $2 OR action_id = $2)
        RETURNING *
        """,
        task_status.lower().strip(), action_identifier, user_id,
    )
    return dict(row) if row else None


async def list_action_items_by_user(
    user_id: str,
    run_id: Optional[str] = None,
    task_status: Optional[str] = None,
    verification_status: Optional[str] = None,
    priority: Optional[str] = None,
    deadline_before: Optional[datetime] = None,
) -> List[dict]:
    """Lấy danh sách công việc của người dùng theo bộ lọc."""
    conditions = ["user_id = $1::uuid"]
    params: list[Any] = [user_id]

    if run_id:
        params.append(run_id)
        conditions.append(f"run_id = ${len(params)}::uuid")
    if task_status:
        params.append(task_status.lower().strip())
        conditions.append(f"task_status = ${len(params)}")
    if verification_status:
        params.append(verification_status.lower().strip())
        conditions.append(f"verification_status = ${len(params)}")
    if priority:
        params.append(priority.lower().strip())
        conditions.append(f"priority = ${len(params)}")
    if deadline_before:
        params.append(deadline_before)
        conditions.append(f"deadline <= ${len(params)}")

    query = f"""
        SELECT * FROM action_items
        WHERE {" AND ".join(conditions)}
        ORDER BY 
            CASE priority 
                WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 
            END,
            deadline ASC NULLS LAST,
            created_at DESC
    """
    rows = await get_pool().fetch(query, *params)
    return [dict(row) for row in rows]


async def get_action_item_by_id(action_identifier: str, user_id: str) -> Optional[dict]:
    """Lấy chi tiết 1 nhiệm vụ công việc (chấp nhận UUID hoặc action_id nghiệp vụ)."""
    row = await get_pool().fetchrow(
        """
        SELECT * FROM action_items 
        WHERE user_id = $2::uuid 
          AND (id::text = $1 OR action_id = $1)
        """,
        action_identifier, user_id,
    )
    return dict(row) if row else None
