"""
Module: plan_validator.py
Vai trò: Kiểm tra tính hợp lệ của Plan trước khi thực thi — giới hạn số bước,
         loại bỏ tool không được phép, phát hiện dependency thiếu và vòng lặp.
"""

from app.core.config import settings
from app.core.constants import ALLOWED_PLAN_TOOLS
from app.core.exceptions import PlanValidationError
from app.schemas.plan import PlanStep


def validate_plan(steps: list[PlanStep]) -> None:
    """Validate toàn bộ plan. Raise PlanValidationError nếu có vi phạm."""

    # 1. Kiểm tra số bước tối đa
    if len(steps) > settings.max_plan_steps:
        raise PlanValidationError(
            f"Plan has {len(steps)} steps; max is {settings.max_plan_steps}"
        )

    # 2. Kiểm tra step_id trùng lặp
    step_ids = [step.step_id for step in steps]
    if len(step_ids) != len(set(step_ids)):
        raise PlanValidationError("Duplicate step_id found")

    step_id_set = set(step_ids)

    # 3. Kiểm tra từng bước: tool hợp lệ + dependency tồn tại
    for step in steps:
        if step.tool_name not in ALLOWED_PLAN_TOOLS:
            raise PlanValidationError(f"Tool is not allowed: {step.tool_name}")

        missing = set(step.depends_on) - step_id_set
        if missing:
            raise PlanValidationError(
                f"Step {step.step_id} has missing dependencies: {sorted(missing)}"
            )

    # 4. Phát hiện vòng lặp trong dependency graph (DFS)
    graph = {step.step_id: step.depends_on for step in steps}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise PlanValidationError("Dependency cycle detected")
        if node in visited:
            return

        visiting.add(node)
        for dep in graph[node]:
            visit(dep)
        visiting.remove(node)
        visited.add(node)

    for step_id in graph:
        visit(step_id)


if __name__ == "__main__":
    validate_plan([
        PlanStep(
            step_id="step_1", 
            objective="Tìm thông tin đối tác", 
            tool_name="web_search",
        ),
        PlanStep(
            step_id="step_2", 
            objective="Kiểm tra lịch làm việc", 
            tool_name="calendar_freebusy",
            depends_on=["step_1"]
        ),
        PlanStep(
            step_id="step_3",
            objective="Gửi email nhắc nhở",
            tool_name="email_create_draft",
            depends_on=["step_2"],
        ),
    ])
    print("Plan is valid")