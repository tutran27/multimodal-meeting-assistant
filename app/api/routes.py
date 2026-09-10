from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.api.dependencies import get_storage_service, get_workflow
from app.orchestration.workflow import Workflow
from app.services.storage_service import StorageService
from app.db.queries import (
    list_runs_by_user,
    get_run_by_session_id,
    list_files_by_run,
    list_action_items_by_user,
    update_action_status,
    list_pending_approvals,
    decide_approval,
    list_contacts,
    find_contact,
    create_contact,
)

router = APIRouter()
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class UpdateActionStatusRequest(BaseModel):
    task_status: str = Field(..., description="Trạng thái: pending, in_progress, done, cancelled")


class DecideApprovalRequest(BaseModel):
    status: str = Field(..., description="Quyết định: approved hoặc rejected")
    reason: str | None = Field(default=None, description="Lý do duyệt hoặc từ chối")
    decided_by: str = Field(default="user", description="Người ra quyết định")


class CreateContactRequest(BaseModel):
    name: str = Field(..., description="Họ và tên")
    email: str = Field(..., description="Địa chỉ email")
    role: str | None = Field(default=None, description="Chức danh")
    company: str | None = Field(default=None, description="Công ty")
    phone: str | None = Field(default=None, description="Số điện thoại")
    aliases: list[str] | None = Field(default=None, description="Biệt danh / tên gọi khác")


# ---------------------------------------------------------------------------
# 1. Workflows
# ---------------------------------------------------------------------------

@router.post("/workflows/run", tags=["Workflows"])
async def run_workflow(
    instruction: str = Form(..., description="Yêu cầu của người dùng về cuộc họp"),
    script_text: str | None = Form(default=None, description="Văn bản cuộc họp dạng text thuần"),
    audio_file: UploadFile = File(default=None, description="File ghi âm cuộc họp (.mp3, .wav, .m4a)"),
    image_file: UploadFile = File(default=None, description="Ảnh tài liệu, slide, hóa đơn (.jpg, .png)"),
    script_file: UploadFile = File(default=None, description="File kịch bản, biên bản (.txt, .md, .docx, .pdf)"),
    user_id: str | None = Form(default=None, description="UUID của người dùng (mặc định demo user)"),
    workflow: Workflow = Depends(get_workflow),
    storage: StorageService = Depends(get_storage_service),
) -> dict:
    """Chạy quy trình phân tích cuộc họp đa phương thức (Audio, Image, Script)."""
    saved = {
        kind: storage.save_upload(f, kind)
        for kind, f in [("audio", audio_file), ("image", image_file), ("script", script_file)]
        if f and f.filename and f.filename.strip()
    }
    clean_text = script_text.strip() if script_text and script_text.strip() != "string" else None

    state = await workflow.run(
        user_request=instruction,
        audio_path=str(saved["audio"]) if "audio" in saved else None,
        image_path=str(saved["image"]) if "image" in saved else None,
        script_path=str(saved["script"]) if "script" in saved else None,
        script_text=clean_text,
        user_id=user_id,
    )
    return state.model_dump(mode="json")


@router.get("/workflows/history", tags=["Workflows"])
async def get_workflow_history(
    user_id: str = Query(default=DEFAULT_USER_ID, description="UUID người dùng"),
    limit: int = Query(default=20, ge=1, le=100, description="Số bản ghi tối đa"),
    offset: int = Query(default=0, ge=0, description="Vị trí bắt đầu (phân trang)"),
) -> list[dict]:
    """Lấy danh sách lịch sử các phiên phân tích gần nhất."""
    return await list_runs_by_user(user_id=user_id, limit=limit, offset=offset)


@router.get("/workflows/{session_id}", tags=["Workflows"])
async def get_workflow_detail(
    session_id: str,
    user_id: str = Query(default=DEFAULT_USER_ID, description="UUID người dùng"),
) -> dict:
    """Chi tiết phiên họp: thông tin phiên, tệp đính kèm và action items."""
    run = await get_run_by_session_id(user_id=user_id, session_id=session_id)
    if not run:
        raise HTTPException(status_code=404, detail="Session not found")

    run_id = str(run["id"])
    return {
        "run": run,
        "input_files": await list_files_by_run(run_id=run_id, user_id=user_id),
        "action_items": await list_action_items_by_user(user_id=user_id, run_id=run_id),
    }


@router.get("/workflows/health", tags=["Workflows"])
async def workflow_health() -> dict:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# 2. Action Items
# ---------------------------------------------------------------------------

@router.get("/actions", tags=["Action Items"])
async def get_action_items(
    user_id: str = Query(default=DEFAULT_USER_ID, description="UUID người dùng"),
    run_id: str | None = Query(default=None, description="Lọc theo ID cuộc họp cụ thể"),
    task_status: str | None = Query(default=None, description="Lọc: pending, in_progress, done, cancelled"),
    priority: str | None = Query(default=None, description="Lọc: low, medium, high, urgent"),
) -> list[dict]:
    """Lấy danh sách nhiệm vụ bóc tách từ các cuộc họp."""
    return await list_action_items_by_user(
        user_id=user_id, run_id=run_id, task_status=task_status, priority=priority
    )


@router.patch("/actions/{action_id}", tags=["Action Items"])
async def update_action_item_status(
    action_id: str,
    body: UpdateActionStatusRequest,
    user_id: str = Query(default=DEFAULT_USER_ID, description="UUID người dùng"),
) -> dict:
    """Cập nhật trạng thái nhiệm vụ (pending, in_progress, done, cancelled)."""
    updated = await update_action_status(
        action_identifier=action_id, user_id=user_id, task_status=body.task_status
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Action item not found")
    return updated


# ---------------------------------------------------------------------------
# 3. Approvals (Human-in-the-loop)
# ---------------------------------------------------------------------------

@router.get("/approvals", tags=["Approvals"])
async def get_pending_approvals(
    user_id: str = Query(default=DEFAULT_USER_ID, description="UUID người dùng"),
    run_id: str | None = Query(default=None, description="Lọc theo ID phiên họp cụ thể"),
) -> list[dict]:
    """Danh sách tác vụ nhạy cảm đang chờ người dùng phê duyệt."""
    return await list_pending_approvals(user_id=user_id, run_id=run_id)


@router.post("/approvals/{approval_id}/decide", tags=["Approvals"])
async def decide_approval_request(
    approval_id: str,
    body: DecideApprovalRequest,
    user_id: str = Query(default=DEFAULT_USER_ID, description="UUID người dùng"),
) -> dict:
    """Phê duyệt ('approved') hoặc từ chối ('rejected') tác vụ."""
    try:
        updated = await decide_approval(
            approval_id=approval_id,
            user_id=user_id,
            status=body.status,
            decided_by=body.decided_by,
            reason=body.reason,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

    if not updated:
        raise HTTPException(status_code=404, detail="Approval not found or already processed")
    return updated


# ---------------------------------------------------------------------------
# 4. Contacts
# ---------------------------------------------------------------------------

@router.get("/contacts", tags=["Contacts"])
async def get_contacts(
    query: str | None = Query(default=None, description="Tìm kiếm thông minh (khớp mờ tên, email, chức danh)"),
    user_id: str = Query(default=DEFAULT_USER_ID, description="UUID người dùng"),
) -> list[dict]:
    """Lấy danh bạ hoặc tìm kiếm liên hệ thông minh."""
    if query and query.strip():
        contact = await find_contact(user_id=user_id, query=query.strip())
        return [contact] if contact else []
    return await list_contacts(user_id=user_id)


@router.post("/contacts", tags=["Contacts"])
async def add_contact(
    body: CreateContactRequest,
    user_id: str = Query(default=DEFAULT_USER_ID, description="UUID người dùng"),
) -> dict:
    """Thêm mới một liên hệ vào danh bạ."""
    return await create_contact(
        user_id=user_id,
        name=body.name,
        email=body.email,
        role=body.role,
        company=body.company,
        phone=body.phone,
        aliases=body.aliases,
    )