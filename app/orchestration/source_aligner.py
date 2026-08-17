"""
Module: source_aligner.py
Vai trò: Evidence Source Aligner (Gom cụm và căn chỉnh bằng chứng đa phương thức) trong tầng Điều phối.

Mô tả chi tiết:
- Sử dụng mô hình Cross-Encoder (`BAAI/bge-reranker-v2-m3`) để đo độ tương đồng ngữ nghĩa giữa các mẩu bằng chứng (EvidenceRef) từ Audio, OCR và Meeting Script.
- Gom các bằng chứng độc lập cùng nói về một nội dung/công việc vào chung một nhóm (`group_id`).
- Tạo cơ sở để liên kết `evidence_ids` vào `ActionItem`, giúp truy vết nguồn gốc và chống bịa đặt (hallucination).
"""

from sentence_transformers import CrossEncoder
from app.core.config import settings
from app.schemas.evidence import EvidenceRef
from app.core.constants import SourceType

model = CrossEncoder(
    "BAAI/bge-reranker-v2-m3",
    automodel_args={"token": settings.hf_token} if settings.hf_token else None,
)
  
def align_sources_cross_encoder(
    evidence: list[EvidenceRef],
    threshold: float = 0.7,
) -> list[dict]:
    """Gom nhóm các mẩu bằng chứng có ngữ nghĩa tương đồng bằng mô hình Cross-Encoder."""
    groups: list[dict] = []

    for item in evidence:
        best_group = None
        best_score = -1.0

        if groups:
            pairs = [(item.content, g["representative_text"]) for g in groups]
            scores = model.predict(pairs) 

            for group, score in zip(groups, scores):
                if score > best_score:
                    best_score = float(score)
                    best_group = group

        if best_group and best_score >= threshold:
            best_group["evidence_ids"].append(item.evidence_id)
        else:
            groups.append({
                "group_id": f"GROUP_{len(groups) + 1:03d}",
                "representative_text": item.content,
                "evidence_ids": [item.evidence_id],
            })

    return groups

if __name__ == "__main__":
    sample_evidence = [
        EvidenceRef(
            evidence_id="AUDIO_01",
            source_type=SourceType.AUDIO,
            source_id="meeting.mp3",
            content="Minh bảo chốt gửi báo giá trước thứ 6 tuần này nha.",
        ),
        EvidenceRef(
            evidence_id="OCR_01",
            source_type=SourceType.IMAGE,
            source_id="invoice.jpg",
            content="Hạn chót bản chào giá: Thứ Sáu - Anh Minh phụ trách",
        ),
        EvidenceRef(
            evidence_id="TEXT_01",
            source_type=SourceType.MEETING_SCRIPT,
            source_id="notes.txt",  
            content="Đặt lịch họp phòng 302 vào lúc 9h sáng thứ Hai.",
        ),
        EvidenceRef(
            evidence_id="AUDIO_02",
            source_type=SourceType.AUDIO,
            source_id="call.mp3",
            content="Sáng T2 tuần sau 9 giờ họp ở phòng ba trăm lẻ hai.",
        ),
    ]

    res=align_sources_cross_encoder(sample_evidence)
    for g in res:
        print(g)