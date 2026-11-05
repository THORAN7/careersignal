"""Render every export format from one CareerReport instance."""

import io

from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas

from ..models import CareerReport


def to_json(report: CareerReport) -> str:
    return report.model_dump_json(indent=2)


def to_markdown(report: CareerReport) -> str:
    gaps = "\n".join(
        f"- **{gap.priority}** {gap.skill} ({gap.status})" for gap in report.skill_gap_report
    )
    learning = "\n".join(
        f"- {step.week}: **{step.title}** — {step.outcome}"
        for step in report.learning_recommendations
    )
    questions = "\n".join(f"- {question}" for question in report.interview_preparation.questions)
    return f"# {report.target_role}\n\n**Career signal score:** {report.score}/100\n\n## Summary\n{report.professional_summary}\n\n## Skill gaps\n{gaps}\n\n## Learning plan\n{learning}\n\n## Interview preparation\n{report.interview_preparation.pitch}\n\n{questions}\n"


def to_docx(report: CareerReport) -> bytes:
    document = Document()
    document.add_heading(report.target_role, 0)
    document.add_paragraph(f"Career signal score: {report.score}/100")
    document.add_heading("Professional summary", level=1)
    document.add_paragraph(report.professional_summary)
    document.add_heading("Skill gaps", level=1)
    for gap in report.skill_gap_report:
        document.add_paragraph(f"{gap.priority}: {gap.skill} ({gap.status})", style="List Bullet")
    document.add_heading("Learning plan", level=1)
    for step in report.learning_recommendations:
        document.add_paragraph(f"{step.week}: {step.title} — {step.outcome}", style="List Bullet")
    document.add_heading("Interview preparation", level=1)
    document.add_paragraph(report.interview_preparation.pitch)
    for question in report.interview_preparation.questions:
        document.add_paragraph(question, style="List Bullet")
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def to_pdf(report: CareerReport) -> bytes:
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=letter)
    text = canvas.beginText(50, 750)
    text.setFont("Helvetica-Bold", 18)
    text.textLine(report.target_role)
    text.setFont("Helvetica", 11)
    for line in to_markdown(report).replace("#", "").splitlines():
        text.textLine(line[:110])
        if text.getY() < 50:
            canvas.drawText(text)
            canvas.showPage()
            text = canvas.beginText(50, 750)
    canvas.drawText(text)
    canvas.save()
    return output.getvalue()
