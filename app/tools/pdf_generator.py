from pathlib import Path
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import settings
from app.schemas.state import RunState
from app.services.storage_service import StorageService


def _find_font() -> Path | None:
    candidates = [
        settings.report_font_path,
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Users/Admin/Downloads/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    return None


def _register_font() -> str:
    if font_path := _find_font():
        pdfmetrics.registerFont(TTFont("ReportFont", str(font_path)))
        return "ReportFont"
    return "Helvetica"


def _get_custom_styles(font_name: str) -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "CustomTitle",
            parent=styles["Title"],
            fontName=font_name,
            alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "heading": ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontName=font_name,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "CustomBody",
            parent=styles["BodyText"],
            fontName=font_name,
            leading=16,
        ),
    }


def _build_decisions_section(state: RunState, styles: dict) -> list:
    story = [Paragraph("Key Decisions", styles["heading"])]
    decisions = state.extraction.decisions or ["Chưa ghi nhận quyết định."]
    for decision in decisions:
        story.append(Paragraph(f"• {decision}", styles["body"]))
    return story


def _build_action_items_section(state: RunState, font_name: str, styles: dict) -> list:
    story = [
        Spacer(1, 8),
        Paragraph("Action Items", styles["heading"]),
    ]

    rows = [["Task", "Owner", "Deadline", "Evidence"]]
    for item in state.extraction.action_items:
        rows.append([
            item.description,
            item.owner or "Chưa rõ",
            item.deadline or "Chưa rõ",
            ", ".join(item.evidence_ids) or "Không có",
        ])

    if len(rows) == 1:
        rows.append(["Chưa có action item", "", "", ""])

    table = Table(rows, colWidths=[7.2 * cm, 3 * cm, 3 * cm, 4 * cm])
    table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("GRID", (0, 0), (-1, -1), 0.5, "#999999"),
            ("BACKGROUND", (0, 0), (-1, 0), "#EEEEEE"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    story.append(table)
    return story


def _build_calendar_section(state: RunState, styles: dict) -> list:
    story = []
    calendar_result = next(
        (v for v in state.tool_results.values() if v.get("_tool_name") == "calendar_freebusy"),
        None,
    )
    if calendar_result:
        story.append(Paragraph("Calendar Suggestions", styles["heading"]))
        for slot in calendar_result.get("candidate_slots", []):
            story.append(Paragraph(f"• {slot['start']} → {slot['end']}", styles["body"]))
    return story


def _build_web_section(state: RunState, styles: dict) -> list:
    story = []
    web_result = next(
        (v for v in state.tool_results.values() if v.get("_tool_name") == "web_search"),
        None,
    )
    if web_result:
        story.append(Paragraph("Partner Background", styles["heading"]))
        for result in web_result.get("results", []):
            story.append(
                Paragraph(
                    f"• {result.get('title', '')}: {result.get('snippet', '')} ({result.get('url', '')})",
                    styles["body"],
                )
            )
    return story

def _build_evidence_section(state: RunState, styles: dict) -> list:
    story = [Paragraph("Evidence Appendix", styles["heading"])]
    for evidence in state.all_evidence:
        story.append(Paragraph(f"[{evidence.evidence_id}] {evidence.content}", styles["body"]))
    return story


def generate_pdf(state: RunState) -> dict:
    output_dir = settings.output_dir / state.session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "meeting_report.pdf"

    font_name = _register_font()
    styles = _get_custom_styles(font_name)

    story = [
        Paragraph(settings.pdf_default_title, styles["title"]),
        Paragraph("Executive Summary", styles["heading"]),
        Paragraph(state.extraction.summary or "Chưa có tóm tắt.", styles["body"]),
    ]

    story.extend(_build_decisions_section(state, styles))
    story.extend(_build_action_items_section(state, font_name, styles))
    story.extend(_build_calendar_section(state, styles))
    story.extend(_build_web_section(state, styles))
    story.extend(_build_evidence_section(state, styles))

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    document.build(story)

    return {
        "file_path": str(output_path),
        "sha256": StorageService.sha256(output_path),
        "file_size": output_path.stat().st_size,
    }


if __name__ == "__main__":
    from app.schemas.extraction import ActionItem, MeetingExtraction

    demo = RunState(
        session_id="pdf_demo",
        user_request="Create report",
        extraction=MeetingExtraction(
            summary="Cuộc họp thống nhất gửi báo giá.",
            action_items=[
                ActionItem(
                    action_id="ACTION_001",
                    description="Gửi báo giá",
                    owner="Minh",
                    evidence_ids=["SCRIPT_001"],
                )
            ],
        ),
    )

    print(generate_pdf(demo))