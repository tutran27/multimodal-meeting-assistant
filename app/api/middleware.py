"""FastAPI Middleware: Xác thực Supabase Auth JWT và Phân quyền Multi-tenant.

Nhiệm vụ & Chức năng dự kiến:
1. `AuthMiddleware`:
   - Lắng nghe các HTTP request gửi tới API (`/api/v1/*`, `/workflows/*`).
   - Trích xuất token từ Header: `Authorization: Bearer <jwt_access_token>`.
   - Xác thực tính hợp lệ của JWT thông qua public key của Supabase Auth (hoặc gọi `supabase.auth.get_user(jwt)`).
   - Nếu hợp lệ:
     + Lấy `user_id = token["sub"]`.
     + Gắn vào request context: `request.state.user_id = user_id`.
   - Nếu không có token hoặc token hết hạn:
     + Trả về lỗi `401 Unauthorized`.
     + Cho phép bypass đối với các public endpoints (Healthcheck, Docs).

2. Cảnh báo bảo mật:
   - Middleware chỉ verify token người dùng, tuyệt đối không dùng `SUPABASE_SERVICE_ROLE_KEY` ở tầng này.
"""
