"""
Module: workflow.py
Vai trò: Điều phối toàn bộ pipeline — từ xử lý input đa phương thức,
         trích xuất thông tin, lập kế hoạch, thực thi, đến reflection.
"""

import asyncio
import logging
from pathlib import Path
from uuid import uuid4

from app.agents.extractor import extract_meeting_information
from app.agents.planner import create_plan
from app.agents.reflector import reflect
from app.core.constants import WorkflowStatus
from app.orchestration.conflict_detector import detect_conflicts
from app.orchestration.executor import execute_plan
from app.orchestration.source_aligner import align_sources
from app.schemas.state import InputFile, RunState
from app.schemas.validation import ValidationIssue
from app.tools.audio_stt import transcribe_audio
from app.tools.fact_validator import validate_extraction
from app.tools.image_ocr import extract_image_text
from app.tools.script_parser import parse_script


logger = logging.getLogger(__name__)


class Workflow:
    async def _process_inputs(
        self,
        state: RunState,
        audio_path: str | None,
        image_path: str | None,
        script_path: str | None,
        script_text: str | None,
    ) -> None:
        """Chạy song song các bước xử lý input (audio, image, script)."""
        tasks = []
        labels = []

        if audio_path:
            tasks.append(asyncio.to_thread(transcribe_audio, audio_path))
            labels.append("audio")

        if image_path:
            tasks.append(asyncio.to_thread(extract_image_text, image_path))
            labels.append("image")

        if script_path or script_text:
            tasks.append(asyncio.to_thread(parse_script, script_path, script_text))
            labels.append("script")

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for label, result in zip(labels, results):
            if isinstance(result, Exception):
                raise result

            if label == "audio":
                state.transcript = result
            elif label == "image":
                state.ocr_blocks = result
            elif label == "script":
                state.script_type, state.script_segments = result

    async def run(
        self,
        user_request: str,
        audio_path: str | None = None,
        image_path: str | None = None,
        script_path: str | None = None,
        script_text: str | None = None,
        approved_steps: set[str] | None = None,
    ) -> RunState:
        """Entry point chính — chạy toàn bộ pipeline và trả về RunState cuối cùng."""
        state = RunState(
            session_id=f"run_{uuid4().hex[:12]}",
            user_request=user_request,
        )

        # Ghi nhận các file input vào state
        for kind, path in [("audio", audio_path), ("image", image_path), ("script", script_path)]:
            if path:
                state.input_files.append(InputFile(
                    kind=kind,
                    path=str(path),
                    original_name=Path(path).name,
                ))

        try:
            # Bước 1: Xử lý input đa phương thức
            state.status = WorkflowStatus.EXTRACTING
            await self._process_inputs(
                state=state,
                audio_path=audio_path,
                image_path=image_path,
                script_path=script_path,
                script_text=script_text,
            )

            # Bước 2: Align & detect conflict giữa các nguồn
            align_sources(state.all_evidence)  # kết quả có thể lưu vào state ở phiên bản sau
            state.validation_issues.extend(detect_conflicts(state.all_evidence))

            # Bước 3: Trích xuất thông tin cuộc họp
            state.extraction = await asyncio.to_thread(extract_meeting_information, state)
            fact_result = validate_extraction(state.extraction)
            state.validation_issues.extend(fact_result.issues)

            # Bước 4: Lập kế hoạch
            state.status = WorkflowStatus.PLANNING
            execution_plan = await asyncio.to_thread(create_plan, state)
            state.plan = execution_plan.steps

            # Bước 5: Thực thi plan
            state.status = WorkflowStatus.EXECUTING
            state = await execute_plan(state, approved_steps)

            # Bước 6: Reflection & đánh giá kết quả
            state.status = WorkflowStatus.VALIDATING
            state.reflection = await asyncio.to_thread(reflect, state)
            state.status = WorkflowStatus.COMPLETED if state.reflection.passed else WorkflowStatus.FAILED

        except Exception as exc:
            logger.exception("Workflow failed")
            state.status = WorkflowStatus.FAILED
            state.validation_issues.append(ValidationIssue(
                issue_type="workflow_error",
                message=str(exc),
                repairable=False,
            ))

        return state


if __name__ == "__main__":
    async def demo() -> None:
        workflow = Workflow()
        state = await workflow.run(
            user_request="Trích xuất việc cần làm, kiểm tra lịch, tìm thông tin đối tác, tạo PDF và email draft",
            script_text="Nam: Minh sẽ gửi báo giá cho ABC Corporation trước thứ Sáu.",
        )
        print(state.model_dump_json(indent=2))

    asyncio.run(demo())