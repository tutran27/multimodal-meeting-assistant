"""Các hàm truy vấn SQL thuần cho `action_items` và bảng nối `action_item_evidence`.

Danh sách hàm dự kiến triển khai:
1. `batch_insert_action_items(conn, run_id, user_id, action_items_list)`:
   - INSERT các task cần làm được bóc tách từ cuộc họp vào bảng `action_items`.
   - Lưu trữ song song mảng `evidence_ids` (JSONB) để hiển thị nhanh trên UI.

2. `link_action_evidence(conn, action_item_id, evidence_item_id)`:
   - INSERT cặp quan hệ vào bảng nối `action_item_evidence` nhằm đảm bảo tính toàn vẹn khóa ngoại (relational grounding).

3. `update_action_status(conn, action_id, user_id, task_status)`:
   - UPDATE trạng thái công việc của người dùng (`pending` -> `in_progress` -> `done` -> `cancelled`).
   - Khác biệt hoàn toàn với `verification_status` (vốn thể hiện chất lượng bằng chứng do AI thẩm định).

4. `list_action_items_by_user(conn, user_id, status=None, deadline_before=None)`:
   - Lọc danh sách công việc cần làm của người dùng theo hạn chót (deadline) và trạng thái.
"""
