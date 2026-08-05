"""
Module: contact_repository.py
Vai trò: Repository Layer chịu trách nhiệm quản lý và truy xuất danh sách danh bạ (contacts).

Mô tả chi tiết:
- Đọc dữ liệu danh bạ từ tệp tin định dạng JSON cấu hình bởi `settings.contacts_file`.
- Cung cấp các phương thức để hiển thị danh sách danh bạ (`list_contacts`) và tìm kiếm thông tin liên lạc (`find`).
- Hỗ trợ tìm kiếm không phân biệt chữ hoa/chữ thường dựa trên các trường thông tin: name, email, role, và company.
- Tích hợp hàm `__main__` giúp kiểm tra nhanh việc tải danh sách danh bạ từ môi trường chạy cục bộ.
"""

import json
from pathlib import Path
from app.core.config import settings

class ContactRepository:
    def __init__(self, file_path: str | Path | None = None):
        self.file_path = Path(file_path or settings.contacts_file)

    def list_contacts(self) -> list[dict]:
        if not self.file_path.exists(): return []
        data = json.loads(self.file_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []

    def find(self, query: str) -> dict | None:
        query_lower = query.strip().lower()
        for contact in self.list_contacts():
            values = [
                str(contact.get("name", "")),
                str(contact.get("email", "")),
                str(contact.get("role", "")),
                str(contact.get("company", ""))
            ]
            if any(query_lower in value.lower() for value in values):
                return contact
        return None

if __name__ == "__main__":
    repository = ContactRepository()
    print(repository.list_contacts())