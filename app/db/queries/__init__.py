"""Package chứa các module truy vấn SQL thuần (Raw SQL) sử dụng asyncpg.

Phục vụ 7 bảng nghiệp vụ cốt lõi:
- workflow_queries: Bảng workflow_runs (Tạo phiên, cập nhật trạng thái, lưu tóm tắt cuộc họp).
- action_queries: Bảng action_items (CRUD nhiệm vụ bóc tách từ cuộc họp, cập nhật tiến độ).
- contact_queries: Bảng contacts (Tra cứu danh bạ qua pg_trgm fuzzy matching).
- evidence_queries: Bảng input_files (Quản lý metadata file upload trên Supabase Storage).
- approval_queries: Bảng approval_requests (Hàng đợi phê duyệt tác vụ nhạy cảm).
"""
