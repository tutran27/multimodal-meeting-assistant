import re
import sys
from pathlib import Path

from app.core.constants import ScriptType, SourceType
from app.schemas.evidence import EvidenceRef
from app.services.document_reader import DocumentReader


def classify_script(text: str) -> ScriptType:
    lower = text.lower()
    agenda_words = ["agenda", "chương trình họp", "nội dung dự kiến", "mục tiêu cuộc họp"]
    minutes_words = ["meeting minutes", "biên bản họp", "kết luận cuộc họp", "quyết định"]

    if any(word in lower for word in agenda_words):
        return ScriptType.PREPARED_AGENDA

    if any(word in lower for word in minutes_words):
        return ScriptType.MEETING_MINUTES
    if re.search(r"^[^:\n]{1,40}:\s+.+", text, flags=re.MULTILINE):
        return ScriptType.ACTUAL_TRANSCRIPT
    return ScriptType.UNKNOWN


def parse_script(file_path: str | Path | None = None, raw_text: str | None = None) -> tuple[ScriptType, list[EvidenceRef]]:
    if raw_text is None:
        if not file_path:
            return ScriptType.UNKNOWN, []
        raw_text = DocumentReader().read(file_path)

    source_name = Path(file_path).name if file_path else "pasted_script"
    script_type = classify_script(raw_text)
    blocks = [b.strip() for b in raw_text.splitlines() if b.strip()]

    evidence = []
    for idx, block in enumerate(blocks, start=1):
        match = re.match(r"^([^:]{1,40}):\s*(.+)$", block)
        if match:
            speaker = match.group(1).strip()
            content = match.group(2).strip()

        evidence.append(
            EvidenceRef(
                evidence_id=f"SCRIPT_{index:03d}",
                source_type=SourceType.MEETING_SCRIPT,
                source_id=source_name,
                content=content,
                speaker=speaker,
                confidence=1.0,
                metadata={"script_type": script_type.value},
            )
        )

    return script_type, evidence


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    demo = "Nam: Minh sẽ gửi báo giá trước thứ Sáu.\nLan: Hẹn lịch follow-up."
    kind, items = parse_script(raw_text=demo)
    print(kind)
    for item in items:
        print(item.model_dump())