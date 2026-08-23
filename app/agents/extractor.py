"""
Module: extractor.py
Vai trò: Extraction Agent chịu trách nhiệm trích xuất thông tin có cấu trúc từ dữ liệu đa phương thức (Audio, OCR, Meeting Script).

Mô tả chi tiết:
- Sử dụng mô hình LLM để phân tích và trích xuất các thông tin cốt lõi từ bằng chứng (evidence): tóm tắt nội dung (summary), người tham gia (participants), tổ chức liên quan (organizations), quyết định đưa ra (decisions), các đầu việc cần làm (action items kèm người phụ trách, hạn chót, mức độ ưu tiên), và câu hỏi chưa giải quyết (unresolved questions).
- Hỗ trợ cơ chế Map-Reduce khi khối lượng bằng chứng lớn: chia nhỏ evidence thành các batch nhỏ hơn, trích xuất song song qua `asyncio.gather`, sau đó tổng hợp thành một bản trích xuất thống nhất.
- Chuẩn hóa và làm sạch dữ liệu đầu ra từ LLM (đồng bộ `owner`/`assigned_to`, gán trạng thái kiểm chứng mặc định).
"""

import asyncio
import json
import logging
import re
from typing import Any
from typing import List

from app.core.json_utils import extract_json_payload
from app.core.prompts import EXTRACTION_PROMPT
from app.schemas.evidence import EvidenceRef
from app.schemas.extraction import ActionItem, MeetingExtraction
from app.schemas.state import RunState
from app.services.llm_service import get_llm

logger = logging.getLogger(__name__)


async def _extract_batch(batch: List[EvidenceRef], user_request: str, script_type: str, batch_idx: int = 1) -> MeetingExtraction:
    """Map step: Trích xuất thông tin cho 1 batch evidence nhỏ."""
    logger.info(f"🧠 [EXTRACTOR] Processing batch #{batch_idx} ({len(batch)} evidence items)...")
    evidence_text = "\n".join(
        f"[{item.evidence_id}] source={item.source_type.value}; speaker={item.speaker or 'unknown'}; text={item.content}"
        for item in batch
    )
    prompt = (
        f"{EXTRACTION_PROMPT}\n\n"
        f"USER REQUEST:\n{user_request}\n\n"
        f"SCRIPT TYPE:\n{script_type}\n\n"
        f"EVIDENCE:\n{evidence_text}\n\n"
        "Chỉ trả về một JSON object, không markdown, không giải thích.\n"
        "JSON bắt buộc có các key: summary, participants, organizations, decisions, action_items, unresolved_questions.\n"
        "Mỗi action item có các key: action_id, description, owner, deadline, priority, duration_minutes, evidence_ids, status.\n"
        "Giữ output ngắn gọn và chuẩn xác: summary tối đa 3-4 câu; decisions tối đa 3-4 mục cốt lõi (gộp các ý kỹ thuật liên quan, TUYỆT ĐỐI không đưa task cá nhân/deadline hay nhận định tình trạng vào); action_items tối đa 5-7 mục; unresolved_questions tối đa 3 mục."
    )
    response = await get_llm().ainvoke(prompt)
    payload = extract_json_payload(response.content)
    result = MeetingExtraction.model_validate(payload)
    logger.info(f"🧠 [EXTRACTOR] Batch #{batch_idx} done: found {len(result.action_items)} actions, {len(result.decisions)} decisions")
    return result


def _merge_results(results: List[MeetingExtraction]) -> MeetingExtraction:
    """Reduce step: Hợp nhất kết quả từ các batches."""
    summaries = [r.summary for r in results if r.summary]
    participants = list(dict.fromkeys(p for r in results for p in r.participants if p))
    organizations = list(dict.fromkeys(o for r in results for o in r.organizations if o))
    decisions = list(dict.fromkeys(d for r in results for d in r.decisions if d))
    unresolved = list(dict.fromkeys(u for r in results for u in r.unresolved_questions if u))

    action_items: list[ActionItem] = []
    for r in results:
        for item in r.action_items:
            item.action_id = f"ACTION_{len(action_items) + 1:03d}"
            action_items.append(item)

    merged = MeetingExtraction(
        summary="\n\n".join(summaries),
        participants=participants,
        organizations=organizations,
        decisions=decisions,
        action_items=action_items,
        unresolved_questions=unresolved,
    )
    logger.info(f"🧠 [EXTRACTOR MERGED] Final Summary: {len(merged.summary)} chars | Participants: {merged.participants} | Actions: {len(merged.action_items)} | Decisions: {len(merged.decisions)}")
    return merged

async def extract_meeting_information_async(state: RunState, batch_size: int = 2) -> MeetingExtraction:
    """Hàm chính: Thực thi Map-Reduce bất đồng bộ song song."""
    all_evidence = state.all_evidence
    if not all_evidence:
        logger.info("🧠 [EXTRACTOR] No evidence found to extract.")
        return MeetingExtraction()

    batches = [all_evidence[i : i + batch_size] for i in range(0, len(all_evidence), batch_size)]
    logger.info(f"🧠 [EXTRACTOR START] Extracting from {len(all_evidence)} total evidences across {len(batches)} batches (batch_size={batch_size})")
    results = []
    for idx, batch in enumerate(batches, start=1):
        result = await _extract_batch(batch, state.user_request, state.script_type.value, batch_idx=idx)
        results.append(result)
    return _merge_results(results)


def extract_meeting_information(state: RunState, batch_size: int = 2) -> MeetingExtraction:
    """Wrapper đồng bộ cho extract_meeting_information_async."""
    return asyncio.run(extract_meeting_information_async(state, batch_size=batch_size))


if __name__ == "__main__":
    import json
    from app.core.constants import ScriptType

    with open(r"outputs\step\script_parsed.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    demo_state = RunState(
        session_id="demo_001",
        user_request="Trích xuất tóm tắt và công việc từ văn bản.",
        script_type=ScriptType.ACTUAL_TRANSCRIPT,
        script_segments=[EvidenceRef(**item) for item in raw_data],
    )

    result = extract_meeting_information(demo_state)
    print(result.model_dump_json(indent=2))

    with open("./outputs/step/extractor.json", "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
        
    print(f"Đã lưu {len(result.action_items)} action items vào extractor.json")
