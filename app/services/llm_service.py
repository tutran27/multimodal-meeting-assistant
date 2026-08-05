"""
Module: llm_service.py
Vai trò: Service Layer chịu trách nhiệm khởi tạo và cung cấp đối tượng tương tác với Mô hình ngôn ngữ lớn (LLM).

Mô tả chi tiết:
- Cung cấp hàm `get_llm()` để khởi tạo và cấu hình instance của mô hình `ChatGroq` thông qua tích hợp LangChain.
- Tự động kiểm tra tính hợp lệ của khóa API (`groq_api_key`), ném ra lỗi cấu hình `ConfigurationError` nếu thiếu thông tin xác thực.
- Cấu hình các tham số quan trọng cho mô hình LLM bao gồm: nhiệt độ sáng tạo (temperature), thời gian chờ (timeout), số lần thử lại tối đa (max_retries), tên mô hình cụ thể.
- Cho phép chạy thử độc lập thông qua khối `__main__` để gửi câu hỏi kiểm tra tính kết nối của API sang máy chủ Groq.
"""

from app.core.config import settings
from app.core.exceptions import ConfigurationError

def get_llm():
    if not settings.groq_api_key:
        raise ConfigurationError("GROQ_API_KEY is required for LLM calls")
    from langchain_groq import ChatGroq
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_llm_model,
        temperature=settings.llm_temperature,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )

if __name__ == "__main__":
    if settings.mock_mode:
        print("MOCK_MODE=true: no LLM call")
    else:
        response = get_llm().invoke("Trả lời đúng một từ: OK")
        print(response.content)