"""
plan.py - Kế hoạch chạy tool tự động
Schema: PlanStep (Bước chạy), ExecutionPlan (Toàn bộ kế hoạch)
Vai trò: Định nghĩa chuỗi hành động mà Agent lập ra để giải quyết các ActionItem đã trích xuất từ cuộc họp.
Cách liên kết:
Liên kết trực tiếp với các Tools tự động hóa trong hệ thống: tool_name sẽ nhận các giá trị như web_search (tìm thông tin), calendar_create_event (đặt lịch làm việc dựa trên deadline), email_create_draft (tạo email báo cáo), pdf_generator (xuất file báo cáo).
"""
from typing import Any
from pydantic import BaseModel, Field
from app.core.constants import RiskLevel, StepStatus

class PlanStep(BaseModel):
    step_id: str
    objective: str
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.READ
    approval_required: bool = False
    expected_output: str = ""
    success_criteria: list[str] = Field(default_factory=list)
    status: StepStatus = StepStatus.PENDING

class ExecutionPlan(BaseModel):
    steps: list[PlanStep] = Field(default_factory=list)

if __name__ == "__main__":
    plan = ExecutionPlan(
        steps=[
            PlanStep(
                step_id="step_1",
                objective="Tìm thông tin đối tác",
                tool_name="web_search",
            )
        ]
    )
    print(plan.model_dump_json(indent=2))