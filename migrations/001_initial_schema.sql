-- ==============================================================================
-- Migration: 001_initial_schema.sql
-- Mục đích: Khởi tạo cấu trúc 7 bảng nghiệp vụ cốt lõi (Production-Grade Multi-tenant)
-- Tuân thủ kiến trúc đã định nghĩa trong db_architecture_plan.md
-- ==============================================================================

-- Bật extension pgcrypto để hỗ trợ gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- 1. users: Quản lý thông tin người dùng (đồng bộ với auth.users của Supabase Auth)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 2. user_credentials: Quản lý OAuth Refresh Tokens (Google Workspace) mã hóa an toàn
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    account_email TEXT NOT NULL,
    encrypted_refresh_token TEXT NOT NULL,
    scopes JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    token_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_user_credentials_provider UNIQUE (user_id, provider, account_email)
);

-- ------------------------------------------------------------------------------
-- 3. contacts: Danh bạ liên hệ cá nhân hóa (thay thế contacts.json cũ)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT,
    company TEXT,
    phone TEXT,
    aliases JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- ------------------------------------------------------------------------------
-- 4. workflow_runs: Lịch sử cuộc họp & kết quả nghiệp vụ cuối cùng
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS workflow_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL UNIQUE,
    title TEXT,
    user_request TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created' CHECK (
        status IN ('created', 'extracting', 'planning', 'executing', 'validating', 'completed', 'failed')
    ),
    script_type TEXT CHECK (
        script_type IN ('actual_transcript', 'meeting_minutes', 'prepared_agenda', 'unknown')
    ),
    extraction_summary JSONB,
    report_path TEXT,
    email_draft_id TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER
);

-- ------------------------------------------------------------------------------
-- 5. input_files: Metadata tệp đa phương thức đính kèm trên Supabase Storage
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS input_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    run_id UUID NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('audio', 'image', 'script', 'document')),
    original_name TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    storage_url TEXT,
    sha256_hash TEXT,
    file_size_bytes BIGINT,
    mime_type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 6. action_items: Nhiệm vụ công việc trích xuất từ cuộc họp
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS action_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    run_id UUID NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    action_id TEXT NOT NULL,
    description TEXT NOT NULL,
    owner_name TEXT,
    owner_contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    deadline TIMESTAMPTZ,
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    duration_minutes INTEGER,
    verification_status TEXT DEFAULT 'unverified' CHECK (
        verification_status IN ('verified', 'partially_verified', 'unverified', 'conflicted')
    ),
    task_status TEXT DEFAULT 'pending' CHECK (
        task_status IN ('pending', 'in_progress', 'done', 'cancelled')
    ),
    evidence_refs JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 7. approval_requests: Hàng đợi phê duyệt Human-in-the-loop (EXTERNAL_WRITE)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    run_id UUID NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    arguments JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'expired')),
    decided_by TEXT,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    decided_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ
);
