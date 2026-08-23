"""
Module: script_parser.py
Vai trò: Công cụ đọc, phân loại và phân tích kịch bản / tài liệu cuộc họp (Meeting Script Parser).

Mô tả chi tiết:
- Sử dụng `DocumentReader` để đọc nội dung từ nhiều định dạng file khác nhau (DOCX, PDF, TXT, MD,...).
- Tự động phân loại tài liệu (`classify_script`) thành: Kịch bản chuẩn bị trước (Agenda), Biên bản cuộc họp (Meeting Minutes), hoặc Lời thoại ghi lại (Actual Transcript).
- Chia nhỏ văn bản thành các đoạn hợp lý (`split_text`) bằng `RecursiveCharacterTextSplitter`.
- Nhận diện người phát biểu (speaker) theo cú pháp hội thoại và đóng gói thành danh sách `EvidenceRef` với loại nguồn `SourceType.MEETING_SCRIPT`.
"""

import logging
import re
from pathlib import Path

from app.core.constants import ScriptType, SourceType
from app.schemas.evidence import EvidenceRef
from app.services.document_reader import DocumentReader

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

def split_text(raw_text: str) -> list[str]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=400,
        separators=["\n\n", "\n", ". ", " "]
    )
    return text_splitter.split_text(raw_text)

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


def parse_script(file_path: str | Path | None = None,
                 raw_text: str | None = None) -> tuple[ScriptType, list[EvidenceRef]]:
    source_name = Path(file_path).name if file_path else "pasted_script"
    logger.info(f"📄 [SCRIPT PARSER START] Parsing script from source: {source_name}")

    if raw_text is None:
        if not file_path:
            logger.info("📄 [SCRIPT PARSER] No script file or text provided.")
            return ScriptType.UNKNOWN, []
        raw_text = DocumentReader().read(file_path)

    script_type = classify_script(raw_text)
    blocks = split_text(raw_text)
    logger.info(f"📄 [SCRIPT PARSER] Classified as '{script_type.value}', length={len(raw_text)} chars, split into {len(blocks)} chunks")

    evidence = []
    for idx, block in enumerate(blocks, start=1):
        speaker = None
        content = block
        
        match = re.match(r"^([^:]{1,40}):\s*(.+)$", block)
        if match:
            speaker = match.group(1).strip()
            content = match.group(2).strip()

        evidence.append(
            EvidenceRef(
                evidence_id=f"SCRIPT_{idx:03d}",
                source_type=SourceType.MEETING_SCRIPT,
                source_id=source_name,
                content=content,
                speaker=speaker,
                confidence=1.0,
                metadata={"script_type": script_type.value},
            )
        )

    logger.info(f"📄 [SCRIPT PARSER DONE] Created {len(evidence)} evidence segments")
    return script_type, evidence


if __name__ == "__main__":
    import json

    file_path = r"C:\Users\Admin\Downloads\project.docx"
    kind, items = parse_script(file_path=file_path)
    
    with open("./outputs/step/script_parsed.json", "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in items], f, ensure_ascii=False, indent=2)
        
    print(f"Đã lưu {len(items)} items vào script_parsed.json")