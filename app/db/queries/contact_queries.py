"""Các hàm truy vấn SQL thuần cho bảng `contacts`."""
import asyncio
import json
from typing import Optional, List
from app.db.pool import get_pool, close_db, init_db


async def find_contact(user_id: str, query: str) -> Optional[dict]:
    """Tìm kiếm danh bạ thông minh theo tên (khớp mờ pg_trgm), email, chức danh hoặc biệt danh."""
    search_term = query.strip()
    search_pattern = f"%{search_term}%"
    result = await get_pool().fetchrow(
        """
        SELECT * FROM contacts
        WHERE user_id = $1::uuid AND deleted_at IS NULL
          AND (
              similarity(name, $2) > 0.2
              OR name ILIKE $3
              OR email ILIKE $3
              OR role ILIKE $3
              OR company ILIKE $3
              OR aliases::text ILIKE $3
          )
        ORDER BY 
          CASE WHEN lower(name) = lower($2) THEN 1.0 ELSE 0.0 END DESC,
          similarity(name, $2) DESC,
          created_at DESC
        LIMIT 1
        """,
        user_id, search_term, search_pattern
    )
    return dict(result) if result else None


async def list_contacts(user_id: str) -> List[dict]:
    """Lấy toàn bộ danh bạ còn hoạt động của user."""
    rows = await get_pool().fetch(
        """
        SELECT * FROM contacts
        WHERE user_id = $1::uuid AND deleted_at IS NULL
        ORDER BY name ASC
        """,
        user_id
    )
    return [dict(row) for row in rows]


async def get_contact_by_id(contact_id: str, user_id: str) -> Optional[dict]:
    """Lấy thông tin chi tiết một liên hệ theo id."""
    row = await get_pool().fetchrow(
        """
        SELECT * FROM contacts
        WHERE id = $1::uuid AND user_id = $2::uuid AND deleted_at IS NULL
        """,
        contact_id, user_id
    )
    return dict(row) if row else None


async def create_contact(
    user_id: str,
    name: str,
    email: str,
    role: Optional[str] = None,
    company: Optional[str] = None,
    phone: Optional[str] = None,
    aliases: Optional[list] = None,
) -> dict:
    """Thêm mới một liên hệ vào danh bạ (ngăn chặn trùng lặp email theo từng user)."""
    aliases_json = json.dumps(aliases or [], ensure_ascii=False)
    result = await get_pool().fetchrow(
        """
        INSERT INTO contacts (user_id, name, email, role, company, phone, aliases)
        VALUES ($1::uuid, $2, $3, $4, $5, $6, $7::jsonb)
        RETURNING *
        """,
        user_id, name.strip(), email.strip().lower(), role, company, phone, aliases_json
    )
    return dict(result) if result else {}


async def soft_delete_contact(user_id: str, contact_id: str) -> bool:
    """Xóa mềm liên hệ (đánh dấu deleted_at = NOW())."""
    status = await get_pool().execute(
        """
        UPDATE contacts
        SET deleted_at = NOW(), updated_at = NOW()
        WHERE id = $1::uuid AND user_id = $2::uuid AND deleted_at IS NULL
        """,
        contact_id, user_id
    )
    return status.endswith("1")


async def main():
    try:
        await init_db()
        demo_user_id = "00000000-0000-0000-0000-000000000001"
        print("--- Test find_contact ('Hoàng') ---")
        contact = await find_contact(demo_user_id, "Hoàng")
        print(contact)

        print("\n--- Test list_contacts ---")
        all_contacts = await list_contacts(demo_user_id)
        print(f"Tổng số liên hệ: {len(all_contacts)}")
        for c in all_contacts:
            print(f"- {c['name']} ({c['email']}) - {c.get('role')}")
    except Exception as e:
        print("Lỗi:", e)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())