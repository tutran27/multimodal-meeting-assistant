-- ==============================================================================
-- Migration: 003_create_indexes.sql
-- Mục đích: Thiết lập các chỉ mục (Indexes) tối ưu hóa truy vấn cho 7 bảng cốt lõi
-- ==============================================================================
-- Danh sách các index sẽ được tạo:
-- 1. B-Tree Indexes cho khóa ngoại và phân vùng Tenant:
--    - idx_workflow_runs_user_id ON workflow_runs(user_id)
--    - idx_input_files_user_id ON input_files(user_id)
--    - idx_input_files_run_id ON input_files(run_id)
--    - idx_contacts_user_id ON contacts(user_id)
--    - idx_action_items_user_id ON action_items(user_id)
--    - idx_action_items_run_id ON action_items(run_id)
--    - idx_action_items_owner_contact ON action_items(owner_contact_id)
--    - idx_approval_user_status ON approval_requests(user_id, status)
--    - idx_approval_run_id ON approval_requests(run_id)
--
-- 2. Indexes cho thứ tự thời gian & lọc trạng thái:
--    - idx_workflow_runs_created_at ON workflow_runs(created_at DESC)
--    - idx_workflow_runs_session_id ON workflow_runs(session_id)
--    - idx_action_items_deadline ON action_items(deadline) WHERE deadline IS NOT NULL
--    - idx_action_items_task_status ON action_items(task_status)
--
-- 3. GIN Trigram Indexes cho tìm kiếm mờ (Fuzzy matching) danh bạ:
--    - idx_contacts_name_trgm ON contacts USING gin (name gin_trgm_ops)
--    - idx_contacts_aliases ON contacts USING gin (aliases)
--
-- Ghi chú: File này hiện chỉ là khung mô tả.


CREATE INDEX IF NOT EXISTS idx_workflow_runs_user_id ON workflow_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_created_at ON workflow_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_session_id ON workflow_runs(session_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_status ON workflow_runs(status);

CREATE INDEX IF NOT EXISTS idx_action_items_user_id ON action_items(user_id);
CREATE INDEX IF NOT EXISTS idx_action_items_run_id ON action_items(run_id);
CREATE INDEX IF NOT EXISTS idx_action_items_owner_contact_id ON action_items(owner_contact_id);
CREATE INDEX IF NOT EXISTS idx_action_items_deadline ON action_items(deadline);
CREATE INDEX IF NOT EXISTS idx_action_items_priority ON action_items(priority);
CREATE INDEX IF NOT EXISTS idx_action_items_task_status ON action_items(task_status);
CREATE INDEX IF NOT EXISTS idx_action_items_verification_status ON action_items(verification_status);
