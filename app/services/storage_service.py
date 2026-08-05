"""
Module: storage_service.py
Vai trò: Service Layer quản lý việc lưu trữ tệp tin và tính toán giá trị băm (checksum) của tệp tin.

Mô tả chi tiết:
- Cung cấp phương thức `save_upload` để lưu trữ tệp tin tải lên từ FastAPI (`UploadFile`) vào thư mục tải lên cục bộ, sử dụng UUID để sinh tên tệp tin duy nhất nhằm tránh xung đột tên.
- Cung cấp phương thức `save_bytes` để ghi dữ liệu nhị phân (bytes) trực tiếp thành tệp tin cục bộ với hậu tố và tiền tố chỉ định.
- Cung cấp hàm tiện ích tĩnh `sha256` hỗ trợ tính toán mã băm SHA256 của tệp tin, giúp kiểm tra tính toàn vẹn và xác định tệp trùng lặp.
- Tích hợp hàm chạy thử nghiệm độc lập `__main__` để tạo tệp tin mẫu và in ra mã băm tương ứng.
"""

import hashlib
import shutil
from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile
from app.core.config import settings

class StorageService:
    def save_upload(self, upload: UploadFile, kind: str) -> Path:
        suffix = Path(upload.filename or "file").suffix.lower()
        destination = settings.upload_dir / f"{kind}_{uuid4().hex}{suffix}"
        with destination.open("wb") as output:
            shutil.copyfileobj(upload.file, output)
        return destination

    def save_bytes(self, data: bytes, suffix: str, prefix: str = "file") -> Path:
        destination = settings.upload_dir / f"{prefix}_{uuid4().hex}{suffix}"
        destination.write_bytes(data)
        return destination

    @staticmethod
    def sha256(path: str | Path) -> str:
        digest = hashlib.sha256()
        with Path(path).open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

if __name__ == "__main__":
    service = StorageService()
    demo = service.save_bytes(b"hello", ".txt", "demo")
    print(demo)
    print(service.sha256(demo))