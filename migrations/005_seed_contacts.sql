-- ==============================================================================
-- Migration: 005_seed_contacts.sql
-- Mục đích: Chuyển giao dữ liệu mẫu ban đầu từ contacts.json vào bảng contacts
-- ==============================================================================
-- Nội dung chuyển đổi dự kiến:
-- 1. Trích xuất danh sách liên hệ mẫu từ file data/contacts.json hiện tại:
--    - Nguyễn Văn A (nva@company.com, Product Manager)
--    - Trần Thị B (ttb@company.com, Tech Lead)
--    - Lê Văn C (lvc@partner.com, External Partner)
--    - Phạm Thị D (ptd@company.com, QA Lead)
--    - Hoàng Văn E (hve@company.com, Designer)
--
-- 2. Chuyển thành các câu lệnh SQL:
--    INSERT INTO contacts (user_id, name, email, role, company, aliases)
--    VALUES (...);
--
-- Ghi chú: File này hiện chỉ là khung mô tả.

-- 1. Tạo người dùng mẫu (Default Demo User) nếu chưa tồn tại
-- (Bắt buộc để thỏa mãn ràng buộc khóa ngoại REFERENCES users(id))
INSERT INTO users (id, email, full_name)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'demo@smartassistant.ai',
    'Demo User'
)
ON CONFLICT (email) DO NOTHING;

-- 2. Đổ toàn bộ 9 liên hệ từ data/contacts.json vào bảng contacts
INSERT INTO contacts (user_id, name, email, role, company, phone, aliases)
VALUES 
    (
        '00000000-0000-0000-0000-000000000001',
        'Minh Hoàng',
        'minhhoang@company.com',
        'Product Manager',
        'Smart Assistant AI',
        '0312345678',
        '["Minh Hoang", "Hoàng", "Hoang", "PM Hoàng"]'::jsonb
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        'Thanh Tú',
        'thanhtu@company.com',
        'Lead Backend Engineer',
        'Smart Assistant AI',
        '0312345679',
        '["Thanh Tu", "Tú", "Tu", "Tu Tran", "Tech Lead"]'::jsonb
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        'Lan Anh',
        'lananh@company.com',
        'UI/UX Designer',
        'Smart Assistant AI',
        '0312345680',
        '["Lan Anh", "Lan", "Designer"]'::jsonb
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        'Hoàng Nam',
        'hoangnam@company.com',
        'Marketing Director',
        'Smart Assistant AI',
        '0312345681',
        '["Hoang Nam", "Nam", "Marketing"]'::jsonb
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        'Mai Phương',
        'maiphuong@company.com',
        'Head of Sales',
        'Smart Assistant AI',
        '0312345682',
        '["Mai Phuong", "Phương", "Phuong", "Sales Lead"]'::jsonb
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        'Quốc Bảo',
        'quocbao@company.com',
        'Tech Support Lead',
        'Smart Assistant AI',
        '0312345683',
        '["Quoc Bao", "Bảo", "Bao", "Support Lead"]'::jsonb
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        'Hương Giang',
        'huonggiang@company.com',
        'Project Manager',
        'Smart Assistant AI',
        '0312345684',
        '["Huong Giang", "Giang", "PM Giang"]'::jsonb
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        'Anh Đức',
        'duc.nguyen@fpt.com',
        'Solution Architect',
        'FPT Software',
        '0312345685',
        '["Anh Duc", "Duc", "Duc Nguyen", "Architect"]'::jsonb
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        'Tuấn Kiệt',
        'tuankiet@company.com',
        'AI Engineer',
        'Smart Assistant AI',
        '0312345686',
        '["Tuan Kiet", "Kiệt", "Kiet", "AI Dev"]'::jsonb
    );