"""
Module: gmail_draft.py
Vai trò: Công cụ tạo bản thảo email (Gmail Draft) tích hợp dịch vụ Google Workspace.

Mô tả chi tiết:
- Kết nối tới Google Gmail API thông qua dịch vụ xác thực OAuth2 (`GoogleOAuthService`).
- Hỗ trợ tạo email với tiêu đề, nội dung và tự động đính kèm tệp tin (ví dụ: báo cáo PDF cuộc họp) theo chuẩn MIME.
- Tạo bản thảo an toàn ở trạng thái chưa gửi (`sent: False`), cho phép người dùng kiểm tra trước khi quyết định gửi đi.
"""

import base64
from email.message import EmailMessage
from mimetypes import guess_type
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import ConfigurationError, ToolExecutionError
from app.services.oauth_service import GoogleOAuthService


def create_email_draft(recipient: str, subject: str, body: str, attachment_path: str | None = None) -> dict:
    if not recipient:
        raise ValueError("Recipient is required")
    if not settings.google_enabled:
        raise ConfigurationError("GOOGLE_ENABLED=false")

    msg = EmailMessage()
    msg["To"], msg["Subject"] = recipient, subject
    msg.set_content(body)

    if attachment_path:
        path = Path(attachment_path)
        maintype, subtype = (guess_type(path.name)[0] or "application/octet-stream").split("/", 1)
        msg.add_attachment(path.read_bytes(), maintype=maintype, subtype=subtype, filename=path.name)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    try:
        service = GoogleOAuthService().build_gmail_service()
        draft = service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
        return {"draft_id": draft.get("id"), "recipient": recipient, "subject": subject, "sent": False}
    except Exception as exc:
        raise ToolExecutionError(f"Create Gmail draft failed: {exc}") from exc


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        print(create_email_draft(settings.default_boss_email or "boss@example.com", "Demo", "Body demo"))
    except Exception as err:
        print(f"Result: {err}")