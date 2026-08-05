"""
evidence.py - Truy vết bằng chứng nguồn
Schema: EvidenceRef
Vai trò: Lưu trữ nguồn gốc và vị trí của bất kỳ thông tin nào được trích xuất để làm cơ sở chứng minh (giúp Agent tự đối chiếu thông tin tránh ảo giác).
Cách ứng với các luồng dữ liệu:
- STT (Audio): Lưu dòng hội thoại trích xuất từ audio, ghi rõ người nói (speaker), file gốc (source_id), và độ tin cậy nhận diện âm thanh (confidence).
- OCR (Ảnh): Lưu đoạn text đọc được từ hóa đơn, ảnh chụp, kèm số trang (page_number).
- Script Parser (Văn bản): Lưu các dòng trích từ file kế hoạch .txt, .pdf kèm vị trí chương mục (section).
"""
from typing import Any
from pydantic import BaseModel, Field
from app.core.constants import SourceType

class EvidenceRef(BaseModel):
    evidence_id: str
    source_type: SourceType
    source_id: str
    content: str
    confidence: float | None = None
    speaker: str | None = None
    section: str | None = None
    page_number: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

if __name__ == "__main__":
    item = EvidenceRef(
        evidence_id="AUDIO_001",
        source_type=SourceType.AUDIO,
        source_id="meeting.mp3",
        content="Minh gửi báo giá trước thứ Sáu.",
    )
    print(item.model_dump_json(indent=2))