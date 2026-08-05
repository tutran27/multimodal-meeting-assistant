"""
state.py - Trạng thái phiên làm việc (Session Memory)
Schema: InputFile, RunState
Vai trò: Quản lý vòng đời chạy của ứng dụng, lưu trữ toàn bộ dữ liệu từ các schema trên vào một đối tượng duy nhất (RunState) để chuyển giao xuyên suốt qua các Agent và Service.
Cách liên kết:
Lưu danh sách file đầu vào (input_files), danh sách bằng chứng (transcript, ocr_blocks, script_segments), kế hoạch thực thi (plan), kết quả của các công cụ sau khi chạy (tool_results), kết quả đánh giá (reflection) và trạng thái hiện tại (status như Đang trích xuất, Đang lập kế hoạch, Thành công, Lỗi).
"""
from typing import Any
from pydantic import BaseModel, Field
from app.core.constants import ScriptType, WorkflowStatus
from app.schemas.evidence import EvidenceRef
from app.schemas.extraction import MeetingExtraction
from app.schemas.plan import PlanStep
from app.schemas.validation import ReflectionResult, ValidationIssue

class InputFile(BaseModel):
    kind: str
    path: str
    original_name: str

class RunState(BaseModel):
    session_id: str
    user_request: str
    input_files: list[InputFile] = Field(default_factory=list)
    transcript: list[EvidenceRef] = Field(default_factory=list)
    ocr_blocks: list[EvidenceRef] = Field(default_factory=list)
    script_segments: list[EvidenceRef] = Field(default_factory=list)
    script_type: ScriptType = ScriptType.UNKNOWN
    extraction: MeetingExtraction = Field(default_factory=MeetingExtraction)
    plan: list[PlanStep] = Field(default_factory=list)
    tool_results: dict[str, Any] = Field(default_factory=dict)
    validation_issues: list[ValidationIssue] = Field(default_factory=list)
    reflection: ReflectionResult | None = None
    report_path: str | None = None
    email_draft_id: str | None = None
    status: WorkflowStatus = WorkflowStatus.CREATED

    @property
    def all_evidence(self) -> list[EvidenceRef]:
        return self.transcript + self.ocr_blocks + self.script_segments

if __name__ == "__main__":
    state = RunState(
        session_id="demo",
        user_request="Tạo báo cáo",
    )
    print(state.model_dump_json(indent=2))