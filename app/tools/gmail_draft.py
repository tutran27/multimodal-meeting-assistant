"""
Module: gmail_draft.py
Vai trò: Công cụ tạo bản thảo email (Gmail Draft) tích hợp dịch vụ Google Workspace.
"""

import base64
import logging
from email.message import EmailMessage
from mimetypes import guess_type
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.exceptions import ConfigurationError, ToolExecutionError
from app.services.oauth_service import GoogleOAuthService

logger = logging.getLogger(__name__)


def _build_mime_message(recipient: str, subject: str, body: str, attachment_path: str | None = None) -> EmailMessage:
    """Tạo đối tượng EmailMessage chuẩn MIME kèm tệp đính kèm nếu có."""
    msg = EmailMessage()
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    if attachment_path:
        path = Path(attachment_path)
        if path.exists() and path.is_file():
            mime_type, _ = guess_type(path.name)
            maintype, subtype = (mime_type or "application/octet-stream").split("/", 1)
            msg.add_attachment(
                path.read_bytes(),
                maintype=maintype,
                subtype=subtype,
                filename=path.name,
            )
            logger.info(f"✉️ [GMAIL DRAFT] Attached file: {path.name} ({path.stat().st_size} bytes)")
        else:
            logger.warning(f"✉️ [GMAIL DRAFT] Attachment not found or invalid: {attachment_path}")

    return msg


def create_email_draft(
    recipient: str,
    subject: str,
    body: str,
    attachment_path: str | None = None,
) -> dict[str, Any]:
    """Tạo bản nháp email trên tài khoản Gmail của người dùng."""
    logger.info(f"✉️ [GMAIL DRAFT START] Creating draft to '{recipient}' with subject '{subject}'")

    if not recipient:
        raise ValueError("Email recipient is required")

    if not settings.google_enabled:
        logger.warning("✉️ [GMAIL DRAFT] GOOGLE_ENABLED is false in settings")
        raise ConfigurationError("GOOGLE_ENABLED=false: Google integration is disabled")

    # 1. Tạo và encode email sang Base64 URL-safe
    msg = _build_mime_message(recipient, subject, body, attachment_path)
    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    # 2. Gọi Gmail API
    try:
        service = GoogleOAuthService().build_gmail_service()
        draft = service.users().drafts().create(
            userId="me",
            body={"message": {"raw": raw_message}},
        ).execute()

        draft_id = draft.get("id")
        logger.info(f"✉️ [GMAIL DRAFT DONE] Created draft ID={draft_id} for recipient={recipient}")

        return {
            "draft_id": draft_id,
            "recipient": recipient,
            "subject": subject,
            "sent": False,
        }
    except Exception as exc:
        logger.error(f"✉️ [GMAIL DRAFT ERROR] Failed to create draft: {exc}")
        raise ToolExecutionError(f"Create Gmail draft failed: {exc}") from exc


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    try:
        result = create_email_draft(
            recipient=settings.default_boss_email or "boss@example.com",
            subject="Demo Meeting Report",
            body="Kính gửi sếp,\n\nĐây là email kiểm tra tạo bản thảo từ hệ thống trợ lý AI.",
        )
        print("Result:", result)
    except Exception as err:
        print(f"Error: {err}")