"""
Module: audio_stt.py
Vai trò: Công cụ Speech-to-Text (STT) - Chuyển đổi file âm thanh cuộc họp thành văn bản.

Mô tả chi tiết:
- Sử dụng Groq Audio API (Whisper model) để nhận diện giọng nói với độ chính xác cao và tốc độ xử lý nhanh.
- Phân tích chi tiết theo từng phân đoạn (segments) kèm mốc thời gian (timestamp start/end) và thông tin người nói (nếu có).
- Đóng gói dữ liệu đầu ra thành danh sách các mẩu bằng chứng (EvidenceRef) chuẩn hóa mang loại nguồn `SourceType.AUDIO`.
"""

from pathlib import Path
from groq import Groq

from app.core.config import settings
from app.core.constants import SourceType
from app.core.exceptions import ConfigurationError, ToolExecutionError
from app.schemas.evidence import EvidenceRef


def transcribe_audio(file_path: str | Path) -> list[EvidenceRef]:
    path = Path(file_path)

    if not settings.groq_api_key:
        raise ConfigurationError("GROQ_API_KEY is required for STT")

    if not path.exists():
        raise FileNotFoundError(path)

    try:
        client = Groq(api_key=settings.groq_api_key)
        with path.open("rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(path.name, audio_file.read()),
                model=settings.groq_stt_model,
                language=settings.stt_language,
                response_format="verbose_json",
                temperature=0.0,
                timestamp_granularities=["segment"],
            )
        trans_dict = transcription.model_dump() if hasattr(transcription, 'model_dump') else (transcription.dict() if hasattr(transcription, 'dict') else vars(transcription))
    except Exception as exc:
        raise ToolExecutionError(f"Groq STT failed: {exc}") from exc

    raw_segments = trans_dict.get("segments", []) 
    evidence: list[EvidenceRef] = []

    if raw_segments:
        for index, segment in enumerate(raw_segments, start=1):
            data = segment if isinstance(segment, dict) else (segment.model_dump() if hasattr(segment, "model_dump") else vars(segment))
            text= str(data.get("text", "")).strip()
            if text:
                evidence.append(
                    EvidenceRef(
                        evidence_id=f"AUDIO_{index:03d}",
                        source_type=SourceType.AUDIO,
                        source_id=path.name,
                        content=text,
                        speaker=data.get("speaker", "Unknown"),
                        metadata={"start": data.get("start"), "end": data.get("end")},
                    )
                )
    elif text := str(getattr(transcription, "text", "")).strip():
        evidence.append(
            EvidenceRef(
                evidence_id="AUDIO_001",
                source_type=SourceType.AUDIO,
                source_id=path.name,
                content=text,
            )
        )

    return evidence


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m app.tools.audio_stt <audio_file>")
    else:
        for item in transcribe_audio(sys.argv[1]):
            print(item.model_dump())