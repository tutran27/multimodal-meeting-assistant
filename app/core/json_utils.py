"""
Module: json_utils.py
Vai trò: Tiện ích bóc tách và tự động sửa lỗi JSON an toàn (Robust JSON extraction & repair)
cho các LLM Agents (Planner, Extractor, Reflector).
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def _sanitize_json_string(text: str) -> str:
    """Loại bỏ markdown fences, thinking tags và trích xuất chuỗi JSON từ văn bản LLM."""
    text = text.strip()

    # Bỏ thẻ suy nghĩ <think>...</think> nếu có từ các mô hình reasoning
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # 1. Ưu tiên lấy nội dung bên trong markdown block ```json ... ``` hoặc ``` ... ```
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()

    # 2. Tìm cặp ngoặc nhọn { ... } ngoài cùng
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return text[start_idx : end_idx + 1].strip()

    return text


def _repair_common_syntax_issues(s: str) -> str:
    """Sửa các lỗi cú pháp JSON thường gặp từ LLM (trailing commas, control chars)."""
    # Xóa trailing commas trước dấu đóng '}' hoặc ']'
    repaired = re.sub(r",\s*(\}|\])", r"\1", s)
    # Chuẩn hóa tab thành khoảng trắng
    repaired = repaired.replace("\t", "  ")
    return repaired


def extract_json_payload(text: str) -> dict[str, Any]:
    """
    Bóc tách và parse JSON object từ output của LLM.
    Tự động xử lý markdown fences, trailing commas và ký tự điều khiển.
    """
    cleaned = _sanitize_json_string(text)
    if not cleaned.startswith("{") or not cleaned.endswith("}"):
        raise ValueError(f"LLM không trả về JSON object hợp lệ: {text[:200]}...")

    # 1. Thử parse trực tiếp (chuẩn)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 2. Thử parse ở chế độ strict=False (bỏ qua ký tự điều khiển trong chuỗi)
    try:
        return json.loads(cleaned, strict=False)
    except json.JSONDecodeError:
        pass

    # 3. Sửa lỗi cú pháp phổ biến (trailing commas, tabs) và parse lại
    repaired = _repair_common_syntax_issues(cleaned)
    try:
        return json.loads(repaired, strict=False)
    except json.JSONDecodeError:
        pass

    # 4. Sửa lỗi unescaped newlines trong các chuỗi văn bản dài
    try:
        fixed_newlines = re.sub(r"(?<!\\)\n", r"\\n", cleaned)
        fixed_newlines = re.sub(r"\\n\s*([\{\}\[\]:,])", r"\n\1", fixed_newlines)
        fixed_newlines = re.sub(r"([\{\}\[\]:,])\s*\\n", r"\1\n", fixed_newlines)
        return json.loads(fixed_newlines, strict=False)
    except Exception as exc:
        logger.error(f"❌ Không thể parse JSON từ LLM: {exc}")
        raise ValueError(f"LLM không trả về JSON object hợp lệ ({exc}): {cleaned[:250]}...") from exc


if __name__ == "__main__":
    # Test cases demo
    sample_markdown = '```json\n{"status": "ok", "items": [1, 2, ],}\n```'
    print("Test 1 (Markdown & trailing comma):", extract_json_payload(sample_markdown))

    sample_control_chars = '{\n  "name": "Test",\n  "desc": "Dòng 1\nDòng 2"\n}'
    print("Test 2 (Unescaped newline):", extract_json_payload(sample_control_chars))
