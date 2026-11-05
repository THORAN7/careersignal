"""Consistency checks for the canonical CareerReport."""

from .models import CareerReport


def check_report(report: CareerReport) -> list[str]:
    warnings: list[str] = []
    role = report.target_role.lower()
    if role not in report.headline.lower() or role not in report.professional_summary.lower():
        warnings.append("Target role is inconsistent across report sections.")
    high_gaps = {
        gap.skill
        for gap in report.skill_gap_report
        if gap.priority == "HIGH" and gap.status != "matched"
    }
    planned = {step.gap_skill for step in report.learning_recommendations}
    if missing := high_gaps - planned:
        warnings.append(f"High-priority gaps lack learning steps: {', '.join(sorted(missing))}.")
    return warnings
