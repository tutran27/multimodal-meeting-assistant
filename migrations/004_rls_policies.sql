-- ==============================================================================
-- Migration: 004_rls_policies.sql
-- Mục đích: Kích hoạt bảo mật phân quyền đa người dùng (Row Level Security - RLS)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- BƯỚC 1: Kích hoạt RLS trên tất cả 7 bảng cốt lõi
-- ------------------------------------------------------------------------------
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE input_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE action_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_requests ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------------------------------------
-- BƯỚC 2: Thiết lập Policies (Người dùng chỉ xem & thao tác trên dữ liệu của chính mình)
-- ------------------------------------------------------------------------------

-- 1. Bảng users: Người dùng quản lý thông tin tài khoản của chính mình (id = auth.uid())
DROP POLICY IF EXISTS "Users can view and edit own profile" ON users;
CREATE POLICY "Users can view and edit own profile"
ON users
FOR ALL
TO authenticated
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

-- 2. Bảng user_credentials: Chỉ chủ tài khoản mới được truy cập OAuth tokens
DROP POLICY IF EXISTS "Users own credentials" ON user_credentials;
CREATE POLICY "Users own credentials"
ON user_credentials
FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- 3. Bảng contacts: Chỉ xem và quản lý danh bạ của bản thân
DROP POLICY IF EXISTS "Users own contacts" ON contacts;
CREATE POLICY "Users own contacts"
ON contacts
FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- 4. Bảng workflow_runs: Lịch sử cuộc họp và tiến trình cá nhân
DROP POLICY IF EXISTS "Users own workflow runs" ON workflow_runs;
CREATE POLICY "Users own workflow runs"
ON workflow_runs
FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- 5. Bảng input_files: Tệp đính kèm cá nhân
DROP POLICY IF EXISTS "Users own input files" ON input_files;
CREATE POLICY "Users own input files"
ON input_files
FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- 6. Bảng action_items: Danh sách việc cần làm của người dùng
DROP POLICY IF EXISTS "Users own action items" ON action_items;
CREATE POLICY "Users own action items"
ON action_items
FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- 7. Bảng approval_requests: Yêu cầu phê duyệt công việc cá nhân
DROP POLICY IF EXISTS "Users own approval requests" ON approval_requests;
CREATE POLICY "Users own approval requests"
ON approval_requests
FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);