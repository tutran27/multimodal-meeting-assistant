from pathlib import Path

from app.schemas.extraction import MeetingExtraction
from app.schemas.state import RunState
from app.services.llm_service import get_llm


def _prompt_text() -> str:
    prompt_path = Path(__file__).parents[1] / "prompts" / "extraction.txt"
    return prompt_path.read_text(encoding="utf-8")


def extract_meeting_information(state: RunState) -> MeetingExtraction:
    evidence_text = "\n".join(
        f"[{item.evidence_id}] source={item.source_type.value}; speaker={item.speaker or 'unknown'}; text={item.content}"
        for item in state.all_evidence
    )

    prompt = (
        f"{_prompt_text()}\n\n"
        f"USER REQUEST:\n{state.user_request}\n\n"
        f"SCRIPT TYPE: {state.script_type.value}\n\n"
        f"EVIDENCE:\n{evidence_text}"
    )

    structured_llm = get_llm().with_structured_output(MeetingExtraction)
    result = structured_llm.invoke(prompt)

    for index, item in enumerate(result.action_items, start=1):
        if not item.action_id:
            item.action_id = f"ACTION_{index:03d}"

    return result


if __name__ == "__main__":

    from app.core.constants import ScriptType, SourceType
    from app.schemas.evidence import EvidenceRef

    demo = RunState(
        session_id="complex_demo_001",
        user_request="Trích xuất tóm tắt, người tham gia, các công ty liên quan, quyết định, việc cần làm và câu hỏi chưa giải quyết.",
        script_type=ScriptType.ACTUAL_TRANSCRIPT,
    )

    # 1. Bằng chứng từ file kịch bản (Script)
    demo.script_segments = [
        EvidenceRef(
            evidence_id="SCRIPT_001",
            source_type=SourceType.MEETING_SCRIPT,
            source_id="bien_ban_hop.docx",
            speaker="Nam (PM)",
            content="Cuộc họp bắt đầu lúc 9:00 với sự tham gia của Nam (PM), Minh (Sales), Lan (Tech Lead) đại diện công ty và anh Hoàng đại diện ABC Corporation.",
        ),
        EvidenceRef(
            evidence_id="SCRIPT_002",
            source_type=SourceType.MEETING_SCRIPT,
            source_id="bien_ban_hop.docx",
            speaker="Minh (Sales)",
            content="Minh sẽ chịu trách nhiệm hoàn thiện file báo giá chi tiết và gửi cho anh Hoàng trước 17:00 thứ Sáu tới (2026-08-15).",
        ),
    ]

    # 2. Bằng chứng từ file ghi âm cuộc họp (Audio STT)
    demo.transcript = [
        EvidenceRef(
            evidence_id="AUDIO_001",
            source_type=SourceType.AUDIO,
            source_id="cuoc_hop_p2.mp3",
            speaker="Lan (Tech Lead)",
            content="Phía kỹ thuật chốt dùng thư viện ReportLab để xuất file báo cáo PDF A4. Lan sẽ hoàn thành bản POC trước thứ Tư.",
            metadata={"start": 120.5, "end": 145.0},
        ),
        EvidenceRef(
            evidence_id="AUDIO_002",
            source_type=SourceType.AUDIO,
            source_id="cuoc_hop_p2.mp3",
            speaker="Hoàng (ABC)",
            content="Thắc mắc: Chiết khấu 5% cho hợp đồng năm có áp dụng đồng thời với ưu đãi hỗ trợ kỹ thuật không?",
            metadata={"start": 200.0, "end": 215.0},
        ),
    ]

    # 3. Bằng chứng từ hình ảnh bảng vẽ / slide họp (OCR)
    demo.ocr_blocks = [
        EvidenceRef(
            evidence_id="IMAGE_001",
            source_type=SourceType.IMAGE,
            source_id="slide_ket_luan.png",
            speaker="Slide",
            content="Quyết định: Hai bên thống nhất ký MOU hợp tác giai đoạn 1 trong tháng 8.",
        ),
    ]

    result = extract_meeting_information(demo)
    print(result.model_dump_json(indent=2))