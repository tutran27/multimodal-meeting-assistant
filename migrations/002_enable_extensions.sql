-- ==============================================================================
-- Migration: 002_enable_extensions.sql
-- Mục đích: Kích hoạt các extension cần thiết trên PostgreSQL / Supabase
-- ==============================================================================
-- Các extension sẽ được kích hoạt:
-- 1. pg_trgm (PostgreSQL Trigram):
--    - Phục vụ tìm kiếm mờ (Fuzzy matching) danh bạ người liên hệ trong bảng contacts.
--    - Tối ưu hóa các truy vấn `ILIKE` và tìm kiếm tên không dấu / gõ nhầm chữ.
--
-- 2. pgcrypto:
--    - Cung cấp các hàm tạo UUID (`gen_random_uuid()`) và mã hóa/giải mã khóa token bí mật.
--
-- Ghi chú: File này hiện chỉ là khung mô tả.

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;  