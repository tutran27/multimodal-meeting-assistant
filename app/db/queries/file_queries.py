"""Các hàm truy vấn SQL thuần cho bảng `input_files`.

Danh sách hàm dự kiến triển khai:
1. `create_input_file(conn, run_id, user_id, kind, original_name, storage_path, storage_url, sha256_hash, file_size_bytes, mime_type)`:
   - INSERT thông tin tệp đầu vào sau khi đã upload thành công lên Supabase Storage bucket `meeting-inputs`.

2. `list_files_by_run(conn, run_id, user_id)`:
   - SELECT danh sách các tệp đính kèm thuộc một phiên họp cụ thể để trả về cho giao diện người dùng.

3. `get_file_by_id(conn, file_id, user_id)`:
   - Lấy chi tiết storage_path của một tệp để sinh Signed URL tải về.
"""
