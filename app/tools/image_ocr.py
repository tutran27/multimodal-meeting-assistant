from pathlib import Path
from huggingface_hub import snapshot_download
from paddleocr import PaddleOCR

from app.core.config import settings
from app.core.constants import SourceType
from app.core.exceptions import ToolExecutionError
from app.schemas.evidence import EvidenceRef


def extract_image_text(file_path: str | Path) -> list[EvidenceRef]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(path)

    try:
        rec_model_dir = snapshot_download(repo_id=settings.ocr_rec_model_repo)
        pipeline = PaddleOCR(
            text_recognition_model_dir=rec_model_dir,
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
        data = result if isinstance(result, dict) else getattr(result, "res", {}) or {}

        texts = data.get("rec_texts", []) or []
        scores = data.get("rec_scores", []) or []
        raw_boxes = data.get("rec_boxes") or data.get("rec_polys") or []

        scores_list = scores.tolist() if hasattr(scores, "tolist") else list(scores)
        boxes_list = raw_boxes.tolist() if hasattr(raw_boxes, "tolist") else list(raw_boxes)

        for index, text in enumerate(texts):
            clean_text = str(text).strip()
            if clean_text:
                confidence = float(scores_list[index]) if index < len(scores_list) else None
                box = boxes_list[index] if index < len(boxes_list) else None

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

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if len(sys.argv) < 2:
        print("Usage: python -m app.tools.image_ocr <image_file>")
    else:
        for item in extract_image_text(sys.argv[1]):
            print(item.model_dump())
