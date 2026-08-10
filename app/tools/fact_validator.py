import re
from datetime import date

from app.core.constants import VerificationStatus
from app.schemas.extraction import MeetingExtraction
from app.schemas.validation import FactValidationResult, ValidationIssue
from app.services.contact_repository import ContactRepository

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_extraction(extraction: MeetingExtraction) -> FactValidationResult:
    issues: list[ValidationIssue] = []
    contacts = ContactRepository()
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

        if item.owner:
            contact = contacts.find(item.owner)
            if contact:
                normalized_entities["contacts"][item.owner] = contact

    for name, contact in normalized_entities["contacts"].items():
        email = contact.get("email")
        if email and not EMAIL_PATTERN.match(email):
            issues.append(
                ValidationIssue(
                    issue_type="invalid_email",
                    message=f"Invalid email for {name}: {email}",
                )
            )

    return FactValidationResult(normalized_entities=normalized_entities, issues=issues)

if __name__ == "__main__":
    from app.schemas.extraction import ActionItem

    demo = MeetingExtraction(
        action_items=[
            ActionItem(
                action_id="ACTION_001",
                description="Gửi báo giá",
                owner="Minh",
                evidence_ids=["SCRIPT_001"],
            )
        ]
    )
    result = validate_extraction(demo)
    print(result.model_dump_json(indent=2))