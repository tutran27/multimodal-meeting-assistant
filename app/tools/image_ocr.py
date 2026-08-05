from __future__ import annotations

import html
import os
import requests
from pathlib import Path
from app.core.config import settings


os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("FLAGS_enable_pir_api", "0")

IMAGE_PATH = Path(r"C:\Users\Admin\Downloads\ocr_demo.png")
OUTPUT_PATH = Path("outputs") / "ocr_text.txt"
OUTPUT_HTML_PATH = Path("outputs") / "ocr_text.html"


def get_device() -> str:
    import paddle

    return "gpu:0" if paddle.device.is_compiled_with_cuda() else "cpu"


def extract_text(image_path: Path) -> list[str]:
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(
        lang="vi",
        device=get_device(),
        det_limit_side_len=1600,
        det_db_box_thresh=0.5,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=True,
    )

    texts: list[str] = []
    for result in ocr.predict(str(image_path)):
        data = result.json if hasattr(result, "json") else result
        texts.extend(data.get("res", {}).get("rec_texts", []))

    return texts


def correct_text_with_llm(texts: list[str]) -> list[str]:
    """Sử dụng LLM qua Groq API để sửa lỗi chính tả và khôi phục dấu tiếng Việt"""
    if not settings.GROQ_API_KEY:
        print("[WARN] Chưa cấu hình GROQ_API_KEY trong file .env. Bỏ qua bước sửa lỗi chính tả bằng LLM.")
        return texts

    print("Đang gửi văn bản OCR qua LLM để sửa lỗi chính tả tiếng Việt...")
    raw_text = "\n".join(texts)
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    model = settings.MODEL_NAME or "llama-3.1-8b-instant"
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Bạn là một trợ lý AI chuyên sửa lỗi chính tả và lỗi nhận diện OCR cho tiếng Việt. "
                    "Hãy sửa các lỗi chính tả, khôi phục dấu tiếng Việt bị thiếu/sai cho đoạn văn bản OCR sau. "
                    "YÊU CẦU:\n"
                    "1. Giữ nguyên cấu trúc các dòng, khoảng cách và các số liệu số lượng/đơn giá.\n"
                    "2. Không giải thích, không dịch sang tiếng Anh, chỉ trả về duy nhất văn bản tiếng Việt đã sửa lỗi."
                )
            },
            {
                "role": "user",
                "content": raw_text
            }
        ],
        "temperature": 0.0
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        corrected_content = response.json()["choices"][0]["message"]["content"]
        return [line.strip() for line in corrected_content.strip().split("\n") if line.strip()]
    except Exception as e:
        print(f"[ERROR] Không thể sửa lỗi bằng LLM: {e}")
        return texts


def save_html(texts: list[str]) -> None:
    body = "<br>\n".join(html.escape(text) for text in texts)
    content = f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <title>OCR Text</title>
  <style>
    body {{
      font-family: Arial, Tahoma, sans-serif;
      font-size: 16px;
      line-height: 1.6;
      white-space: normal;
    }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
    OUTPUT_HTML_PATH.write_text(content, encoding="utf-8")


def main() -> None:
    if not IMAGE_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy ảnh: {IMAGE_PATH}")

    raw_texts = extract_text(IMAGE_PATH)
    texts = correct_text_with_llm(raw_texts)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(texts), encoding="utf-8")
    save_html(texts)

    print(f"OCR completed: {len(texts)} text lines")
    print(f"Saved text to: {OUTPUT_PATH}")
    print(f"Saved HTML to: {OUTPUT_HTML_PATH}")


if __name__ == "__main__":
    main()
