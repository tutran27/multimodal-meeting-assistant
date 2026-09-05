"""Các hàm truy vấn SQL thuần cho `approval_requests` (Hàng đợi phê duyệt Human-in-the-loop).

Danh sách hàm dự kiến triển khai:
1. `create_approval_request(conn, run_id, user_id, step_id, tool_name, arguments, expires_in_hours=24)`:
   - Được PolicyGate kích hoạt khi gặp tool có mức độ rủi ro `EXTERNAL_WRITE` (ví dụ: gửi email thật, sửa lịch).
   - INSERT vào `approval_requests` với status = 'pending'.

2. `decide_approval(conn, approval_id, user_id, status, decided_by, reason=None)`:
   - Xử lý quyết định của người dùng (`approved` hoặc `rejected`).
   - Cập nhật `decided_at = NOW()`.
   - Khi được approve, hệ thống sẽ tiếp tục unpause luồng Workflow để Executor Agent chạy tool.

3. `list_pending_approvals(conn, user_id)`:
   - SELECT tất cả các yêu cầu phê duyệt đang chờ xử lý của người dùng để hiển thị thông báo trên giao diện frontend.
"""
