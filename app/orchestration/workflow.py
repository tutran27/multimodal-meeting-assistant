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
            logger.info(f"[{state.session_id}] 🎙️ Queueing Audio STT: {audio_path}")
            tasks.append(asyncio.to_thread(transcribe_audio, audio_path))
            labels.append("audio")

        if image_path:
            logger.info(f"[{state.session_id}] 🖼️ Queueing Image OCR: {image_path}")
            tasks.append(asyncio.to_thread(extract_image_text, image_path))
            labels.append("image")

        if script_path or script_text:
            logger.info(f"[{state.session_id}] 📄 Queueing Script Parser (file={script_path}, text_len={len(script_text) if script_text else 0})")
            tasks.append(asyncio.to_thread(parse_script, script_path, script_text))
            labels.append("script")

        if not tasks:
            logger.info(f"[{state.session_id}] ℹ️ No multi-modal inputs provided.")
            return

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for label, result in zip(labels, results):
            if isinstance(result, Exception):
                logger.error(f"[{state.session_id}] ❌ Input processing error in {label}: {result}")
                raise result

            if label == "audio":
                state.transcript = result
                logger.info(f"[{state.session_id}] ✅ Audio transcribed ({len(result.segments) if result else 0} segments)")
            elif label == "image":
                state.ocr_blocks = result
                logger.info(f"[{state.session_id}] ✅ OCR completed ({len(result)} text blocks)")
            elif label == "script":
                state.script_type, state.script_segments = result
                logger.info(f"[{state.session_id}] ✅ Script parsed ({len(state.script_segments)} segments, type={state.script_type.value})")

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

        logger.info(f"============================================================")
        logger.info(f"🚀 [START WORKFLOW] Session: {state.session_id}")
        logger.info(f"📝 User Request: {user_request}")
        logger.info(f"============================================================")

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
            logger.info(f"[{state.session_id}] 🔹 [STAGE 1/6] Multi-modal Input Processing...")
            state.status = WorkflowStatus.EXTRACTING
            await self._process_inputs(
                state=state,
                audio_path=audio_path,
                image_path=image_path,
                script_path=script_path,
                script_text=script_text,
            )
            logger.info(f"[{state.session_id}] 📦 Total evidence items collected: {len(state.all_evidence)}")

            # Bước 2: Align & detect conflict giữa các nguồn
            logger.info(f"[{state.session_id}] 🔹 [STAGE 2/6] Aligning Sources & Detecting Conflicts...")
            align_sources(state.all_evidence)
            conflicts = detect_conflicts(state.all_evidence)
            if conflicts:
                logger.warning(f"[{state.session_id}] ⚠️ Detected {len(conflicts)} cross-source conflicts")
                state.validation_issues.extend(conflicts)
            else:
                logger.info(f"[{state.session_id}] ✅ No cross-source conflicts found.")

            # Bước 3: Trích xuất thông tin cuộc họp
            logger.info(f"[{state.session_id}] 🔹 [STAGE 3/6] Running Information Extractor Agent...")
            state.extraction = await asyncio.to_thread(extract_meeting_information, state)
            logger.info(f"[{state.session_id}] ✅ Extractor returned: {len(state.extraction.action_items)} action items, {len(state.extraction.decisions)} decisions")
            
            fact_result = validate_extraction(state.extraction)
            if fact_result.issues:
                logger.warning(f"[{state.session_id}] ⚠️ Fact Validator reported {len(fact_result.issues)} issues")
                state.validation_issues.extend(fact_result.issues)
            else:
                logger.info(f"[{state.session_id}] ✅ Fact Validation passed cleanly.")

            # Bước 4: Lập kế hoạch
            logger.info(f"[{state.session_id}] 🔹 [STAGE 4/6] Running Planner Agent...")
            state.status = WorkflowStatus.PLANNING
            execution_plan = await asyncio.to_thread(create_plan, state)
            state.plan = execution_plan.steps
            logger.info(f"[{state.session_id}] ✅ Planner generated {len(state.plan)} steps: {[s.step_id + ':' + s.tool_name for s in state.plan]}")

            # Bước 5: Thực thi plan
            logger.info(f"[{state.session_id}] 🔹 [STAGE 5/6] Executing Plan with Orchestration Executor...")
            state.status = WorkflowStatus.EXECUTING
            state = await execute_plan(state, approved_steps)
            logger.info(f"[{state.session_id}] ✅ Plan execution completed. Results keys: {list(state.tool_results.keys())}")

            # Bước 6: Reflection & đánh giá kết quả
            logger.info(f"[{state.session_id}] 🔹 [STAGE 6/6] Running Reflector Agent...")
            state.status = WorkflowStatus.VALIDATING
            state.reflection = await asyncio.to_thread(reflect, state)
            state.status = WorkflowStatus.COMPLETED if state.reflection.passed else WorkflowStatus.FAILED
            
            verdict = "PASSED" if state.reflection.passed else "FAILED"
            logger.info(f"[{state.session_id}] 🏁 Reflection Verdict: {verdict} (Action: {state.reflection.recommended_action}, Scores: coverage={state.reflection.coverage_score}, consistency={state.reflection.consistency_score}, safety={state.reflection.safety_score})")

        except Exception as exc:
            logger.exception(f"[{state.session_id}] ❌ Workflow failed with exception: {exc}")
            state.status = WorkflowStatus.FAILED
            state.validation_issues.append(ValidationIssue(
                issue_type="workflow_error",
                message=str(exc),
                repairable=False,
            ))

        logger.info(f"============================================================")
        logger.info(f"🎉 [END WORKFLOW] Session: {state.session_id} - Final Status: {state.status.value}")
        logger.info(f"============================================================")
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