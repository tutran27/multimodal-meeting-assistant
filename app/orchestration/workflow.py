"""
Module: workflow.py
Vai trò: Điều phối toàn bộ pipeline — từ xử lý input đa phương thức,
         trích xuất thông tin, lập kế hoạch, thực thi, reflection,
         và đồng bộ kết quả vào Database.
"""
import asyncio
import logging
import time
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
from app.services.contact_repository import ContactRepository
from app.db.queries import (
    create_run,
    sync_run_state,
    batch_create_input_files,
    batch_insert_action_items,
    create_approval_for_step,
)

logger = logging.getLogger(__name__)

DEFAULT_DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"


class Workflow:
    # ---------------------------------------------------------------------------
    # Database Helper Methods (Tách gọn để không làm rối luồng chính)
    # ---------------------------------------------------------------------------

    def _record_input_files(self, state: RunState, audio_path: str | None, image_path: str | None, script_path: str | None) -> None:
        for kind, path in [("audio", audio_path), ("image", image_path), ("script", script_path)]:
            if path:
                state.input_files.append(InputFile(kind=kind, path=str(path), original_name=Path(path).name))

    async def _init_db_run(self, state: RunState, user_id: str, user_request: str) -> str | None:
        try:
            db_run = await create_run(user_id=user_id, session_id=state.session_id, user_request=user_request)
            db_run_id = str(db_run["id"]) if db_run and "id" in db_run else None
            if db_run_id and state.input_files:
                await batch_create_input_files(run_id=db_run_id, user_id=user_id, files=state.input_files)
            return db_run_id
        except Exception as err:
            logger.warning(f"[{state.session_id}] ⚠️ DB init skipped: {err}")
            return None

    async def _save_actions(self, state: RunState, db_run_id: str | None, user_id: str) -> None:
        if not db_run_id or not state.extraction.action_items:
            return
        try:
            await batch_insert_action_items(run_id=db_run_id, user_id=user_id, action_items=state.extraction.action_items)
            logger.info(f"[{state.session_id}] 💾 Saved {len(state.extraction.action_items)} action items to DB")
        except Exception as err:
            logger.warning(f"[{state.session_id}] ⚠️ DB save actions failed: {err}")

    async def _save_approvals(self, state: RunState, db_run_id: str | None, user_id: str) -> None:
        if not db_run_id:
            return
        blocked_step_ids = {
            issue.related_step
            for issue in state.validation_issues
            if issue.issue_type == "approval_required" and issue.related_step
        }
        for step in state.plan:
            if step.step_id in blocked_step_ids:
                try:
                    await create_approval_for_step(run_id=db_run_id, user_id=user_id, step=step)
                    logger.info(f"[{state.session_id}] 🛡️ Created approval request for step: {step.step_id}")
                except Exception as err:
                    logger.warning(f"[{state.session_id}] ⚠️ DB save approval failed: {err}")

    async def _finalize_db_run(self, state: RunState, db_run_id: str | None, user_id: str, start_time: float) -> None:
        if not db_run_id:
            return
        duration_ms = int((time.time() - start_time) * 1000)
        try:
            await sync_run_state(user_id=user_id, state=state, duration_ms=duration_ms)
            logger.info(f"[{state.session_id}] 💾 Synced final RunState to DB ({duration_ms}ms)")
        except Exception as err:
            logger.warning(f"[{state.session_id}] ⚠️ DB sync final state failed: {err}")

    # ---------------------------------------------------------------------------
    # Multi-modal Input Processing
    # ---------------------------------------------------------------------------

    async def _process_inputs(
        self,
        state: RunState,
        audio_path: str | None,
        image_path: str | None,
        script_path: str | None,
        script_text: str | None,
    ) -> None:
        tasks, labels = [], []

        if audio_path:
            logger.info(f"[{state.session_id}] 🎙️ Queueing Audio STT: {audio_path}")
            tasks.append(asyncio.to_thread(transcribe_audio, audio_path))
            labels.append("audio")

        if image_path:
            logger.info(f"[{state.session_id}] 🖼️ Queueing Image OCR: {image_path}")
            tasks.append(asyncio.to_thread(extract_image_text, image_path))
            labels.append("image")

        if script_path or script_text:
            logger.info(f"[{state.session_id}] 📄 Queueing Script Parser")
            tasks.append(asyncio.to_thread(parse_script, script_path, script_text))
            labels.append("script")

        if not tasks:
            return

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

    # ---------------------------------------------------------------------------
    # Main Workflow Pipeline
    # ---------------------------------------------------------------------------

    async def run(
        self,
        user_request: str,
        audio_path: str | None = None,
        image_path: str | None = None,
        script_path: str | None = None,
        script_text: str | None = None,
        approved_steps: set[str] | None = None,
        user_id: str | None = None,
    ) -> RunState:
        """Entry point — điều phối 6 giai đoạn và tự động đồng bộ vào Database."""
        start_time = time.time()
        effective_user_id = user_id or DEFAULT_DEMO_USER_ID

        state = RunState(session_id=f"run_{uuid4().hex[:12]}", user_request=user_request)
        self._record_input_files(state, audio_path, image_path, script_path)

        logger.info(f"🚀 [START WORKFLOW] Session: {state.session_id} (User: {effective_user_id})")
        db_run_id = await self._init_db_run(state, effective_user_id, user_request)

        try:
            # 1. Multi-modal Input
            state.status = WorkflowStatus.EXTRACTING
            await self._process_inputs(state, audio_path, image_path, script_path, script_text)

            # 2. Align & Conflict Detection
            align_sources(state.all_evidence)
            conflicts = detect_conflicts(state.all_evidence)
            if conflicts:
                state.validation_issues.extend(conflicts)

            # 3. Extraction & Save Action Items
            state.extraction = await asyncio.to_thread(extract_meeting_information, state)

            # Lấy danh bạ người dùng trực tiếp từ Database
            contacts: list[dict] = []
            try:
                contacts = await ContactRepository(effective_user_id).list_contacts()
            except Exception as err:
                logger.warning(f"[{state.session_id}] ⚠️ DB contacts lookup skipped: {err}")

            fact_res = validate_extraction(state.extraction, contacts)
            if fact_res.issues:
                state.validation_issues.extend(fact_res.issues)
            await self._save_actions(state, db_run_id, effective_user_id)

            # 4. Planning
            state.status = WorkflowStatus.PLANNING
            plan = await asyncio.to_thread(create_plan, state, contacts)
            state.plan = plan.steps

            # 5. Execution & Save Approvals
            state.status = WorkflowStatus.EXECUTING
            state = await execute_plan(state, approved_steps)
            await self._save_approvals(state, db_run_id, effective_user_id)

            # 6. Reflection
            state.status = WorkflowStatus.VALIDATING
            state.reflection = await asyncio.to_thread(reflect, state)
            state.status = WorkflowStatus.COMPLETED if state.reflection.passed else WorkflowStatus.FAILED

        except Exception as exc:
            logger.exception(f"[{state.session_id}] ❌ Workflow failed: {exc}")
            state.status = WorkflowStatus.FAILED
            state.validation_issues.append(ValidationIssue(issue_type="workflow_error", message=str(exc), repairable=False))

        finally:
            # Luôn luôn đồng bộ trạng thái cuối cùng vào Database (bất kể thành công hay có lỗi)
            await self._finalize_db_run(state, db_run_id, effective_user_id, start_time)

        logger.info(f"🎉 [END WORKFLOW] Session: {state.session_id} - Final: {state.status.value}")
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