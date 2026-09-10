"""Các hàm truy vấn SQL thuần cho bảng `input_files`."""
from typing import Optional, List, Union
from app.db.pool import get_pool
from app.schemas.state import InputFile


async def create_input_file(
    run_id: str,
    user_id: str,
    kind: Optional[str] = None,
    original_name: Optional[str] = None,
    storage_path: Optional[str] = None,
    file: Optional[InputFile] = None,
    storage_url: Optional[str] = None,
    sha256_hash: Optional[str] = None,
    file_size_bytes: Optional[int] = None,
    mime_type: Optional[str] = None,
) -> dict:
    """Lưu metadata của tệp đa phương thức đính kèm vào phiên họp.
    Hỗ trợ truyền trực tiếp đối tượng `InputFile` hoặc các trường lẻ.
    """
    if file:
        kind = kind or file.kind
        original_name = original_name or file.original_name
        storage_path = storage_path or file.path

    row = await get_pool().fetchrow(
        """
        INSERT INTO input_files (
            run_id, user_id, kind, original_name, storage_path,
            storage_url, sha256_hash, file_size_bytes, mime_type
        )
        VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *
        """,
        run_id, user_id, (kind or "").lower(), original_name or "", storage_path or "",
        storage_url, sha256_hash, file_size_bytes, mime_type
    )
    return dict(row) if row else {}


async def batch_create_input_files(
    run_id: str,
    user_id: str,
    files: List[Union[InputFile, dict]],
) -> List[dict]:
    """Lưu hàng loạt tệp đa phương thức từ danh sách InputFile trong RunState."""
    if not files:
        return []

    inserted = []
    for f in files:
        if isinstance(f, InputFile):
            row = await create_input_file(
                run_id=run_id,
                user_id=user_id,
                file=f,
            )
        else:
            row = await create_input_file(
                run_id=run_id,
                user_id=user_id,
                kind=f.get("kind"),
                original_name=f.get("original_name"),
                storage_path=f.get("storage_path") or f.get("path"),
                storage_url=f.get("storage_url"),
                sha256_hash=f.get("sha256_hash"),
                file_size_bytes=f.get("file_size_bytes"),
                mime_type=f.get("mime_type"),
            )
        if row:
            inserted.append(row)
    return inserted


async def list_files_by_run(run_id: str, user_id: str) -> List[dict]:
    """Lấy danh sách tệp đính kèm của một phiên họp cụ thể."""
    rows = await get_pool().fetch(
        """
        SELECT * FROM input_files
        WHERE run_id = $1::uuid AND user_id = $2::uuid
        ORDER BY created_at ASC
        """,
        run_id, user_id
    )
    return [dict(row) for row in rows]


async def get_file_by_id(file_id: str, user_id: str) -> Optional[dict]:
    """Lấy chi tiết metadata một tệp theo file_id và user_id."""
    row = await get_pool().fetchrow(
        "SELECT * FROM input_files WHERE id = $1::uuid AND user_id = $2::uuid",
        file_id, user_id
    )
    return dict(row) if row else None
