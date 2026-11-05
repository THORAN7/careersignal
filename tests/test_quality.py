"""Canonical report, export, and accessibility contract tests."""

from careersignal.analysis.report import build_report
from careersignal.consistency import check_report
from careersignal.exporters.render import to_docx, to_json, to_markdown, to_pdf
from careersignal.models import ResumeAnalysis


def sample_profile() -> dict[str, object]:
    return {
        "name": "Jordan Lee",
        "skills": ["Python", "SQL"],
        "interests": "analytics and dashboards",
        "goals": "Become a data analyst",
        "experience": "Built a dashboard for a student club.",
        "target_role": "Data Analyst",
        "uploads": [],
    }


def test_report_is_typed_and_consistent() -> None:
    report = build_report(sample_profile())
    assert report.target_role == "Data Analyst"
    assert not check_report(report)
    assert report.score >= 0


def test_all_exports_share_canonical_facts() -> None:
    report = build_report(sample_profile())
    for output in (to_json(report), to_markdown(report), to_docx(report), to_pdf(report)):
        assert output
    assert report.target_role in to_json(report)
    assert report.target_role in to_markdown(report)


def test_frontend_has_accessible_form_labels() -> None:
    with open("static/index.html", encoding="utf-8") as file:
        html = file.read()
    assert "aria-live" in html or "<label" in html
    assert 'id="profileForm"' in html


def test_resume_analysis_preserves_contact_signals() -> None:
    analysis = ResumeAnalysis.model_validate(
        {
            "status": "extracted",
            "message": "Extracted resume text.",
            "detected_skills": ["Python"],
            "sections": ["skills"],
            "contact": {"email": "student@example.com", "phone": "+1 555 0100"},
            "completeness_score": 80,
            "word_count": 120,
            "inferred_name": "Student Example",
        }
    )
    assert analysis.contact.email == "student@example.com"
    assert analysis.contact.phone == "+1 555 0100"
