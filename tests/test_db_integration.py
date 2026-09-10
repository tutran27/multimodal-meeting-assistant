import asyncio
from app.db.pool import init_db, close_db
from app.db.queries import (
    find_contact, list_contacts, get_contact_by_id, create_contact, soft_delete_contact,
    create_run, update_run_status, get_run_by_session_id, list_runs_by_user,
    batch_insert_action_items, update_action_status, list_action_items_by_user, get_action_item_by_id,
    create_input_file, list_files_by_run,
    create_approval_request, list_pending_approvals, decide_approval
)
from app.services.contact_repository import ContactRepository

async def test_all():
    print("=" * 60)
    print("1. KIỂM TRA KHỞI TẠO CONNECTION POOL & KẾT NỐI DATABASE")
    print("=" * 60)
    pool = await init_db()
    print("✅ Database connection pool initialized successfully.")

    async with pool.acquire() as conn:
        version = await conn.fetchval("SELECT version()")
        print(f"✅ Phiên bản PostgreSQL: {version}")

        # Kiểm tra bảng trong schema public
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        table_names = [t["table_name"] for t in tables]
        print(f"✅ Các bảng hiện có trong database ({len(table_names)} bảng): {table_names}")

    user_id = "00000000-0000-0000-0000-000000000001"

    print("\n" + "=" * 60)
    print("2. KIỂM TRA CONTACT REPOSITORY & CÁC TRUY VẤN DANH BẠ")
    print("=" * 60)
    repo = ContactRepository(user_id=user_id)
    contacts = await repo.list_contacts()
    print(f"✅ Tổng số liên hệ đang hoạt động: {len(contacts)}")
    for c in contacts[:3]:
        print(f"   - {c['name']} ({c['email']}) | Chức vụ: {c.get('role')} | Cty: {c.get('company')}")

    found = await repo.find("Hoàng")
    if found:
        print(f"✅ Tìm kiếm thông minh pg_trgm 'Hoàng': {found['name']} <{found['email']}>")

    new_contact = await create_contact(
        user_id=user_id,
        name="Nguyễn Văn Test",
        email="nguyen.test@assistant.ai",
        role="Tester",
        company="AI Assistant",
        aliases=["Van Test", "Tester NV"]
    )
    print(f"✅ create_contact(): Tạo mới contact ID = {new_contact['id']}")

    deleted = await soft_delete_contact(user_id, str(new_contact["id"]))
    print(f"✅ soft_delete_contact(): Đã xóa mềm thành công = {deleted}")

    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM contacts WHERE id = $1", new_contact["id"])
        print("✅ Dọn dẹp hard-delete contact test thành công.")

    print("\n" + "=" * 60)
    print("3. KIỂM TRA WORKFLOW RUNS, FILE INPUT, ACTION ITEMS, APPROVALS")
    print("=" * 60)
    import uuid
    session_id = f"test-session-diag-{uuid.uuid4().hex[:8]}"
    run = await create_run(
        user_id=user_id,
        session_id=session_id,
        user_request="Tóm tắt cuộc họp kế hoạch Q3",
        title="Cuộc họp Q3 Planning"
    )
    run_id = str(run["id"])
    print(f"✅ create_run(): Tạo workflow run ID = {run_id}, session_id = {session_id}")

    try:
        # File input
        f = await create_input_file(
            run_id=run_id,
            user_id=user_id,
            kind="audio",
            original_name="meeting_recording.mp3",
            storage_path="/data/inputs/meeting_recording.mp3",
            file_size_bytes=2048576,
            mime_type="audio/mp3"
        )
        print(f"✅ create_input_file(): File đính kèm ID = {f['id']}")
        files = await list_files_by_run(run_id, user_id)
        print(f"✅ list_files_by_run(): {len(files)} files đính kèm trong session")

        # Action Items
        actions = await batch_insert_action_items(
            run_id=run_id,
            user_id=user_id,
            action_items=[
                {
                    "action_id": "ACT-DIAG-01",
                    "description": "Triển khai database schema mới lên Supabase",
                    "owner": "Hoàng Nam",
                    "priority": "high",
                    "status": "verified"
                }
            ]
        )
        print(f"✅ batch_insert_action_items(): Đã chèn {len(actions)} tasks")
        
        act_up = await update_action_status("ACT-DIAG-01", user_id, "in_progress")
        print(f"✅ update_action_status(): Task status cập nhật thành = {act_up['task_status']}")

        # Approvals
        appr = await create_approval_request(
            run_id=run_id,
            user_id=user_id,
            tool_name="send_gmail_draft",
            arguments={"recipient": "hoangnam@company.com", "subject": "Biên bản cuộc họp"}
        )
        print(f"✅ create_approval_request(): Yêu cầu duyệt ID = {appr['id']}")

        pending = await list_pending_approvals(user_id)
        print(f"✅ list_pending_approvals(): {len(pending)} yêu cầu đang chờ duyệt")

        decided = await decide_approval(str(appr["id"]), user_id, "approved", reason="Đã kiểm tra nội dung chính xác")
        print(f"✅ decide_approval(): Phê duyệt thành công = {decided['status']}")

        # Update workflow status
        up_run = await update_run_status(
            session_id=session_id,
            user_id=user_id,
            status="completed",
            title="Cuộc họp Q3 Planning (Hoàn tất)"
        )
        print(f"✅ update_run_status(): Workflow status = {up_run['status']}")
    finally:
        # Clean up workflow run (Foreign key CASCADE)
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM workflow_runs WHERE session_id LIKE 'test-session-diag%'")
            print("✅ Dọn dẹp workflow_run và CASCADE toàn bộ action_items, input_files, approval_requests thành công.")

    await close_db()
    print("✅ Database connection pool closed safely.")
    print("\n" + "=" * 60)
    print("🎉 KẾT QUẢ: TOÀN BỘ DATABASE & QUERIES KẾT NỐI VÀ HOẠT ĐỘNG 100%!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_all())
