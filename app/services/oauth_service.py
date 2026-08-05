"""
Module: oauth_service.py
Vai trò: Service Layer chịu trách nhiệm xử lý xác thực OAuth 2.0 và khởi tạo dịch vụ Google API (Calendar và Gmail).

Mô tả chi tiết:
- Cấu hình phạm vi truy cập (OAuth Scopes) cần thiết cho việc thao tác với Google Calendar và soạn thư Gmail.
- Quản lý vòng đời của token: Tải thông tin đăng nhập từ tệp cấu hình token (`settings.google_token_file`), tự động làm mới (refresh token) nếu hết hạn, hoặc tiến hành chạy local server để thực hiện đăng nhập và cấp quyền mới từ trình duyệt.
- Kiểm tra tính đầy đủ của thông tin xác thực từ phía Client (`settings.google_client_secret_file`), ném ra lỗi `ConfigurationError` nếu không tìm thấy tệp bí mật.
- Cung cấp các hàm xây dựng dịch vụ nhanh chóng (`build_calendar_service`, `build_gmail_service`) thông qua thư viện `google-api-python-client`.
- Hỗ trợ khối lệnh thực thi trực tiếp `__main__` giúp kiểm tra nhanh xem OAuth đã được cấp quyền thành công chưa.
"""

from pathlib import Path
from app.core.config import settings
from app.core.exceptions import ConfigurationError

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.compose"
]

class GoogleOAuthService:
    def get_credentials(self):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        token_file = Path(settings.google_token_file)
        client_secret_file = Path(settings.google_client_secret_file)
        credentials = None

        if token_file.exists():
            credentials = Credentials.from_authorized_user_file(token_file, GOOGLE_SCOPES)

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        if not credentials or not credentials.valid:
            if not client_secret_file.exists():
                raise ConfigurationError(f"Missing Google client secret: {client_secret_file}")
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, GOOGLE_SCOPES)
            credentials = flow.run_local_server(port=0)
            token_file.parent.mkdir(parents=True, exist_ok=True)
            token_file.write_text(credentials.to_json(), encoding="utf-8")

        return credentials

    def build_calendar_service(self):
        from googleapiclient.discovery import build
        return build("calendar", "v3", credentials=self.get_credentials())

    def build_gmail_service(self):
        from googleapiclient.discovery import build
        return build("gmail", "v1", credentials=self.get_credentials())

if __name__ == "__main__":
    if not settings.google_enabled:
        print("GOOGLE_ENABLED=false. Enable it in .env before OAuth testing.")
    else:
        service = GoogleOAuthService()
        print(service.get_credentials().valid)