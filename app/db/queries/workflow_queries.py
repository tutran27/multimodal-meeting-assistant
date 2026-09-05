"""Các hàm truy vấn SQL thuần cho bảng `workflow_runs`.

Danh sách hàm dự kiến triển khai:
1. `create_run(conn, user_id, session_id, user_request, title=None)`:
   - INSERT bản ghi mới vào `workflow_runs` với status = 'created'.
   - Trả về thông tin phiên họp vừa tạo.

2. `update_run_status(conn, session_id, status, title=None, extraction_summary=None, report_path=None, email_draft_id=None, error_message=None)`:
   - UPDATE trạng thái của phiên họp (`extracting`, `planning`, `executing`, `completed`, `failed`).
   - Cập nhật `completed_at = NOW()` và `duration_ms` nếu phiên kết thúc.
   - Lưu snapshot kết quả trích xuất vào cột `extraction_summary` (JSONB) và đường dẫn file PDF vào `report_path`.

3. `get_run_by_session_id(conn, user_id, session_id)`:
   - SELECT thông tin chi tiết một phiên chạy theo `session_id` và `user_id` (đảm bảo multi-tenant).

4. `list_runs_by_user(conn, user_id, limit=20, offset=0)`:
   - Lấy danh sách lịch sử các phiên họp của user (tiêu đề, thời gian, trạng thái, link PDF), sắp xếp theo `created_at DESC`.
"""
