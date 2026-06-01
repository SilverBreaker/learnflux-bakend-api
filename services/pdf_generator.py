from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def _build_pdf(path: str, elements: list):
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    doc.build(elements)

def create_summary_pdf(doc_id: str, title: str, summary: dict) -> str:
    path = f"outputs/summary_{doc_id}.pdf"
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("Title", parent=styles["Title"],
                                 fontSize=20, textColor=colors.HexColor("#9B6BFF"))
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"],
                                   fontSize=14, textColor=colors.HexColor("#333333"))
    body_style = ParagraphStyle("Body", parent=styles["Normal"],
                                fontSize=11, leading=16)

    elements = [
        Paragraph(f"Summary: {title}", title_style),
        Spacer(1, 0.5*cm),
        Paragraph("Overview", heading_style),
        Paragraph(summary.get("overview", ""), body_style),
        Spacer(1, 0.4*cm),
        Paragraph("Key Concepts", heading_style),
        Paragraph(summary.get("key_concepts", "").replace("\n", "<br/>"), body_style),
        Spacer(1, 0.4*cm),
        Paragraph("Important Definitions", heading_style),
        Paragraph(summary.get("definitions", "").replace("\n", "<br/>"), body_style),
        Spacer(1, 0.4*cm),
        Paragraph("Conclusion", heading_style),
        Paragraph(summary.get("conclusion", ""), body_style),
    ]
    _build_pdf(path, elements)
    return path

def create_questions_pdf(doc_id: str, title: str, questions: list) -> str:
    path = f"outputs/questions_{doc_id}.pdf"
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("Title", parent=styles["Title"],
                                 fontSize=20, textColor=colors.HexColor("#9B6BFF"))
    body_style = ParagraphStyle("Body", parent=styles["Normal"],
                                fontSize=11, leading=18)

    elements = [
        Paragraph(f"Important Questions: {title}", title_style),
        Spacer(1, 0.5*cm),
    ]
    for i, q in enumerate(questions, 1):
        elements.append(Paragraph(f"Q{i}. {q}", body_style))
        elements.append(Spacer(1, 0.3*cm))

    _build_pdf(path, elements)
    return path