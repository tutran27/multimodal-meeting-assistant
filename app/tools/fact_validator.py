"""
Module: fact_validator.py
Vai trò: Công cụ kiểm tra và đối soát tính xác thực (Fact Validation) cho dữ liệu trích xuất từ cuộc họp.

Mô tả chi tiết:
- Kiểm tra các đầu việc (`ActionItem`) có đính kèm bằng chứng (`evidence_ids`) hợp lệ hay không, tự động cập nhật trạng thái kiểm chứng (`VerificationStatus`).
- Xác thực tính hợp lệ của hạn chót (`deadline`) và cảnh báo nếu deadline nằm trong quá khứ hoặc sai định dạng ngày tháng.
- Chuẩn hóa thông tin người phụ trách (`owner`) với danh bạ người dùng từ database và kiểm tra định dạng email người nhận.
- Trả về kết quả đối soát (`FactValidationResult`) gồm thực thể đã chuẩn hóa và danh sách cảnh báo/vấn đề phát hiện (`ValidationIssue`).
"""

import logging
import re
from datetime import date

from app.core.constants import VerificationStatus
from app.schemas.extraction import MeetingExtraction
from app.schemas.validation import FactValidationResult, ValidationIssue

logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_extraction(
    extraction: MeetingExtraction,
    contacts: list[dict] | None = None,
) -> FactValidationResult:
    logger.info(f"🔍 [FACT VALIDATOR START] Validating {len(extraction.action_items)} action items against contacts & facts...")
    issues: list[ValidationIssue] = []
    contact_list = contacts or []
    normalized_entities: dict = {"contacts": {}}

    for item in extraction.action_items:
        if not item.evidence_ids:
            item.status = VerificationStatus.UNVERIFIED
            issues.append(
                ValidationIssue(
                    issue_type="missing_evidence",
                    message=f"Action item {item.action_id} has no evidence.",
                )
            )
        elif item.status == VerificationStatus.UNVERIFIED:
            item.status = VerificationStatus.PARTIALLY_VERIFIED

        if item.deadline:
            try:
                deadline = date.fromisoformat(item.deadline)
                if deadline < date.today():
                    issues.append(
                        ValidationIssue(
                            issue_type="past_deadline",
                            message=f"Deadline is in the past: {item.deadline}",
                        )
                    )
            except ValueError:
                issues.append(
                    ValidationIssue(
                        issue_type="invalid_date",
                        message=f"Invalid deadline: {item.deadline}",
                    )
                )

        if item.owner and contact_list:
            owner_lower = item.owner.strip().lower()
            matched = next(
                (c for c in contact_list if any(owner_lower in str(c.get(k, "")).lower() for k in ("name", "email", "role"))),
                None
            )
            if matched:
                normalized_entities["contacts"][item.owner] = matched
                logger.info(f"🔍 [FACT VALIDATOR] Matched owner '{item.owner}' to contact: {matched.get('email')}")

    for name, contact in normalized_entities["contacts"].items():
        email = contact.get("email")
        if email and not EMAIL_PATTERN.match(email):
            issues.append(
                ValidationIssue(
                    issue_type="invalid_email",
                    message=f"Invalid email for {name}: {email}",
                )
            )

    logger.info(f"🔍 [FACT VALIDATOR DONE] Found {len(issues)} issues, matched {len(normalized_entities['contacts'])} contacts")
    return FactValidationResult(normalized_entities=normalized_entities, issues=issues)

if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    from app.schemas.extraction import ActionItem

    demo = MeetingExtraction(
        summary=(
            "Cuộc họp diễn ra lúc 9:00 với Nam (PM), Minh (Sales), Lan (Tech Lead) và Hoàng (ABC Corporation). "
            "Các bên thống nhất ký MOU giai đoạn 1 trong tháng 8. Lan sẽ hoàn thành bản POC trước thứ Tư, "
            "Minh sẽ gửi báo giá chi tiết cho Hoàng trước 17:00 thứ Sáu (2026-08-15). "
            "Hoàng đặt câu hỏi về việc áp dụng chiết khấu 5% cùng ưu đãi hỗ trợ kỹ thuật."
        ),
        participants=["Nam", "Minh", "Lan", "Hoàng"],
        organizations=["ABC Corporation"],
        decisions=["Hai bên thống nhất ký MOU hợp tác giai đoạn 1 trong tháng 8."],
        action_items=[
            ActionItem(
                action_id="ACTION_001",
                description="Hoàn thành bản POC trước thứ Tư",
                owner="Lan",
                deadline=None,
                priority="medium",
                duration_minutes=None,
                evidence_ids=["AUDIO_001"],
                status=VerificationStatus.UNVERIFIED,
            ),
            ActionItem(
                action_id="ACTION_002",
                description="Gửi báo giá chi tiết cho Hoàng trước 17:00 thứ Sáu (2026-08-15)",
                owner="Minh",
                deadline="2026-08-15",
                priority="medium",
                duration_minutes=None,
                evidence_ids=["SCRIPT_002"],
                status=VerificationStatus.UNVERIFIED,
            ),
            ActionItem(
                action_id="ACTION_003",
                description="Công việc demo với deadline trong quá khứ",
                owner="Hoàng",
                deadline="2026-08-01",
                priority="low",
                duration_minutes=None,
                evidence_ids=["AUDIO_001"],
                status=VerificationStatus.UNVERIFIED,
            ),
        ],
        unresolved_questions=[
            "Chiết khấu 5% cho hợp đồng năm có áp dụng đồng thời với ưu đãi hỗ trợ kỹ thuật không?"
        ],
    )
    result = validate_extraction(demo)
    print(result.model_dump_json(indent=2))