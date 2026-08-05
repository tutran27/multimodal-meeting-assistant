"""
validation.py - Đánh giá chất lượng và an toàn
Schema: ValidationIssue (Lỗi phát hiện), FactValidationResult, ReflectionResult
Vai trò: Đánh giá xem kết quả trích xuất và kế hoạch thực thi có chính xác, an toàn và đầy đủ bằng chứng hay chưa.
Cách liên kết:
Phát hiện mâu thuẫn chéo (Ví dụ: OCR hóa đơn ghi giá 1.250.000 nhưng STT ghi âm người nói bảo giá 1.500.000 -> Tạo một ValidationIssue cảnh báo xung đột dữ liệu). Quyết định bước tiếp theo (recommended_action) như hỏi lại ý kiến người dùng (ask_user) hoặc chạy lại tool (rerun_tool).
"""
from typing import Any, Literal
from pydantic import BaseModel, Field

class ValidationIssue(BaseModel):
    issue_type: str
    message: str
    related_step: str | None = None
    repairable: bool = True

class FactValidationResult(BaseModel):
    normalized_entities: dict[str, Any] = Field(default_factory=dict)
    issues: list[ValidationIssue] = Field(default_factory=list)

class ReflectionResult(BaseModel):
    passed: bool
    coverage_score: float = 0.0
    evidence_score: float = 0.0
    consistency_score: float = 0.0
    tool_execution_score: float = 0.0
    safety_score: float = 0.0
    issues: list[ValidationIssue] = Field(default_factory=list)
    recommended_action: Literal["finish", "repair_output", "rerun_tool", "replan", "ask_user"] = "finish"

if __name__ == "__main__":
    result = ReflectionResult(passed=True, coverage_score=1.0)
    print(result.model_dump_json(indent=2))