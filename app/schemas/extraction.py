"""
extraction.py - Dữ liệu trích xuất cuộc họp
Schema: ActionItem (Công việc), MeetingExtraction (Nội dung tổng hợp cuộc họp)
Vai trò: Là cấu trúc dữ liệu đại diện cho kết quả phân tích cuộc họp (đã hợp nhất dữ liệu từ STT, OCR và file văn bản).
Cách liên kết:
Mỗi ActionItem (nhiệm vụ như "gửi báo giá trước thứ Sáu") sẽ có danh sách evidence_ids. Các ID này liên kết trực tiếp ngược lại với EvidenceRef trong evidence.py để chứng minh nhiệm vụ này được nói bởi ai trong file ghi âm (STT) hoặc ghi ở trang nào trong tài liệu (OCR/Văn bản).
"""
from pydantic import BaseModel, Field
from app.core.constants import VerificationStatus

class ActionItem(BaseModel):
    action_id: str
    description: str
    owner: str | None = None
    deadline: str | None = None
    priority: str = "medium"
    duration_minutes: int | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    status: VerificationStatus = VerificationStatus.UNVERIFIED

class MeetingExtraction(BaseModel):
    summary: str = ""
    participants: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)

if __name__ == "__main__":
    data = MeetingExtraction(
        summary="Demo meeting",
        action_items=[
            ActionItem(
                action_id="ACTION_001",
                description="Gửi báo giá",
                evidence_ids=["SCRIPT_001"],
            )
        ],
    )
    print(data.model_dump_json(indent=2))