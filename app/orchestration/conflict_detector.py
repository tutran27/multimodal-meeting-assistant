"""
Module: conflict_detector.py
Vai trò: Cross-source Conflict Detector (Bộ phát hiện mâu thuẫn chéo) trong tầng Điều phối (Orchestration).

Mô tả chi tiết:
- Tiếp nhận danh sách các mẩu bằng chứng (`EvidenceRef`) từ nhiều nguồn dữ liệu đa phương thức khác nhau (Audio STT, Ảnh OCR, Tài liệu/Kịch bản cuộc họp).
- Sử dụng biểu thức chính quy (Regex) để trích xuất các thực thể nhạy cảm như ngày tháng (`DATE_PATTERN`) và số tiền / ngân sách (`MONEY_PATTERN`).
- Gom nhóm và theo dõi các nguồn (`source_type`) đã cung cấp từng giá trị thực thể nhằm kiểm tra tính nhất quán (cross-verification).
- Tự động sinh ra các cảnh báo `ValidationIssue` (như `possible_date_conflict`, `possible_amount_conflict`) nếu phát hiện có sự mâu thuẫn về số liệu giữa các nguồn, giúp hệ thống gắn cờ để người dùng hoặc Reflection Agent xử lý.
"""

import re
from app.schemas.evidence import EvidenceRef
from app.schemas.validation import ValidationIssue


DATE_PATTERN = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\b")
MONEY_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:triệu|tỷ|million|billion|m|bn)\b", re.IGNORECASE)


def detect_conflicts(evidence: list[EvidenceRef]) -> list[ValidationIssue]:
    """Quét và phát hiện các xung đột về ngày tháng hoặc số tiền giữa các nguồn dữ liệu đa phương thức.

    Args:
        evidence: Danh sách các mẩu bằng chứng (EvidenceRef) đã được tiền xử lý từ Audio, OCR, Text.

    Returns:
        Danh sách các đối tượng ValidationIssue mô tả chi tiết các điểm mâu thuẫn phát hiện được.
    """
    dates: dict[str, set[str]] = {}
    amounts: dict[str, set[str]] = {}

    for item in evidence:
        source = item.source_type.value

        for value in DATE_PATTERN.findall(item.content):
            if value not in dates:
                dates[value] = set()
            dates[value].add(source)

        for value in MONEY_PATTERN.findall(item.content):
            key = value.lower()
            if key not in amounts:
                amounts[key] = set()
            amounts[key].add(source)

    issues: list[ValidationIssue] = []

    if len(dates) > 1:
        issues.append(
            ValidationIssue(
                issue_type="possible_date_conflict",
                message=f"Phát hiện nhiều giá trị ngày tháng khác nhau giữa các nguồn: {sorted(dates)}",
            )
        )

    if len(amounts) > 1:
        issues.append(
            ValidationIssue(
                issue_type="possible_amount_conflict",
                message=f"Phát hiện nhiều giá trị số tiền/ngân sách khác nhau giữa các nguồn: {sorted(amounts)}",
            )
        )

    return issues


if __name__ == "__main__":
    from app.core.constants import SourceType

    sample_evidence = [
        EvidenceRef(
            evidence_id="AUDIO_001",
            source_type=SourceType.AUDIO,
            source_id="recording.mp3",
            content="Báo giá dự án là 50 triệu và chốt trước ngày 15/09/2026.",
        ),
        EvidenceRef(
            evidence_id="OCR_001",
            source_type=SourceType.IMAGE,
            source_id="quote.png",
            content="Tổng chi phí: 70 triệu, hạn hoàn thành: 20/09/2026.",
        ),
    ]

    conflicts = detect_conflicts(sample_evidence)
    for issue in conflicts:
        print(f"[{issue.issue_type}] {issue.message}")