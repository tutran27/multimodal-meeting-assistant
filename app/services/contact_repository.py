"""
Module: contact_repository.py
Vai trò: Quản lý và truy xuất danh bạ liên hệ trực tiếp từ Database (PostgreSQL).
"""
from app.db.queries import find_contact, list_contacts

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"


class ContactRepository:
    def __init__(self, user_id: str = DEFAULT_USER_ID):
        self.user_id = user_id

    async def list_contacts(self) -> list[dict]:
        """Lấy toàn bộ danh bạ từ database."""
        return await list_contacts(self.user_id)

    async def find(self, query: str) -> dict | None:
        """Tìm kiếm liên hệ thông minh bằng khớp mờ pg_trgm từ database."""
        return await find_contact(self.user_id, query)