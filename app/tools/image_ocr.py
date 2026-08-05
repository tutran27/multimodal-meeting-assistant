from pathlib import Path
from typing import Any
from paddleocr import PaddleOCR

from app.core.config import settings
from app.core.constants import SourceType
from app.core.exceptions import ToolExecutionError
from app.schemas.evidence import EvidenceRef


def _to_python(value: Any) -> Any:
    return value.tolist() if hasattr(value, "tolist") else value


def _result_payload(result: Any) -> dict:
    if isinstance(result, dict):
        return result
    val = getattr(result, "json", None)
    if callable(val):
        val = val()
    if isinstance(val, dict):
        return val
    res = getattr(result, "res", None)
    return {"res": res} if isinstance(res, dict) else {}


def extract_image_text(file_path: str | Path) -> list[EvidenceRef]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(path)

    try:
        pipeline = PaddleOCR(
            lang=settings.ocr_language,
            device=settings.ocr_device,
            use_doc_orientation_classify=settings.ocr_use_doc_orientation_classify,
            use_doc_unwarping=settings.ocr_use_doc_unwarping,
            use_textline_orientation=settings.ocr_use_textline_orientation,
        )
        results = pipeline.predict(str(path))
    except Exception as exc:
        raise ToolExecutionError(f"PaddleOCR failed: {exc}") from exc

    output: list[EvidenceRef] = []
    counter = 1

    for page_index, result in enumerate(results):
        payload = _result_payload(result)
        data = payload.get("res", payload)

        texts = data.get("rec_texts", []) or []
        scores = _to_python(data.get("rec_scores", []) or [])
        boxes = _to_python(data.get("rec_boxes", []) or data.get("rec_polys", []) or [])

        for index, text in enumerate(texts):
            if clean_text := str(text).strip():
                confidence = float(scores[index]) if index < len(scores) else None
                box = boxes[index] if index < len(boxes) else None

                output.append(
                    EvidenceRef(
                        evidence_id=f"IMAGE_{counter:03d}",
                        source_type=SourceType.IMAGE,
                        source_id=path.name,
                        content=clean_text,
                        confidence=confidence,
                        page_number=page_index + 1,
                        metadata={"bbox": box},
                    )
                )
                counter += 1

    return output


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m app.tools.image_ocr <image_file>")
    else:
        for item in extract_image_text(sys.argv[1]):
            print(item.model_dump())