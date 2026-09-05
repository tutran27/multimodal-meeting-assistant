"""Các hàm truy vấn SQL thuần cho `contacts` (thay thế hoàn toàn `contacts.json`).

Danh sách hàm dự kiến triển khai:
1. `find_contact(conn, user_id, query)`:
   - SELECT tìm kiếm danh bạ thông minh theo thứ tự ưu tiên:
     a) Tìm kiếm khớp mờ (Fuzzy match) qua extension `pg_trgm` trên cột `name`.
     b) Tìm kiếm ILIKE trên `company`, `role` hoặc mảng `aliases` (JSONB).
   - Trả về contact record chứa email, chức danh để Planner và Google Calendar sử dụng.

2. `list_contacts(conn, user_id)`:
   - Lấy toàn bộ danh bạ thuộc quyền sở hữu của `user_id` mà chưa bị xóa (`deleted_at IS NULL`).

3. `create_contact(conn, user_id, name, email, role=None, company=None, phone=None, aliases=None)`:
   - Thêm liên hệ mới vào CSDL, kiểm tra ràng buộc duy nhất (UNIQUE) trên cặp (`user_id`, `email`).

4. `soft_delete_contact(conn, user_id, contact_id)`:
   - UPDATE `deleted_at = NOW()` để ẩn liên hệ mà không làm mất dữ liệu lịch sử liên kết với các action items cũ.
"""
