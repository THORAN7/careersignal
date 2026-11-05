"""Build the canonical report used by every presentation format."""

from typing import Any

from ..models import CareerReport, EvidenceFile, InterviewPack, LearningStep, StudentProfile
from .roles import analyze_gaps, infer_role


def build_report(raw_profile: dict[str, Any]) -> CareerReport:
    profile = StudentProfile.model_validate(raw_profile)
    role = infer_role(profile.target_role, profile.interests, profile.goals)
    gaps, score = analyze_gaps(raw_profile, role)
    skills = profile.skills[:3] or ["Curiosity", "Structured thinking", "Collaboration"]
    name = profile.name or "Your profile"
    has_inputs = bool(profile.name or profile.skills or profile.resume_analysis)
    summary = (
        f"{name} is an aspiring {role.name.lower()} who combines {', '.join(skills)} with practical project experience. "
        "Their strongest next step is to turn that evidence into outcomes a hiring team can understand."
        if has_inputs
        else "Start by entering your details or uploading a resume/project file. CareerSignal will build your personalized profile from your own evidence."
    )
    learning = [
        LearningStep(
            week=f"{index + 1:02d}",
            title=f"Build evidence for {gap.skill}",
            detail=gap.action,
            outcome=f"A portfolio proof point for {gap.skill}",
            gap_skill=gap.skill,
            estimated_hours=8 if gap.priority == "HIGH" else 5,
        )
        for index, gap in enumerate([g for g in gaps if g.status != "matched"][:4])
    ]
    if not learning:
        learning = [
            LearningStep(
                week="01",
                title="Strengthen your strongest signal",
                detail="Document one measurable project outcome.",
                outcome="A concise case study",
                gap_skill="evidence",
            )
        ]
    questions = [
        f"How have you used {skills[0]} in a project?",
        f"How would you demonstrate {role.name} impact in your next project?",
        "What feedback changed one of your decisions?",
    ]
    report = CareerReport(
        target_role=role.name,
        score=score if has_inputs else 0,
        headline=f"{role.name} with a systems mindset.",
        professional_summary=summary,
        summary=summary,
        strengths=skills,
        skill_gap_report=gaps,
        learning_recommendations=learning,
        interview_preparation=InterviewPack(
            pitch=f"I bring {', '.join(skills[:2])} to {role.name.lower()} problems, supported by {profile.experience or 'my project work'}.",
            questions=questions,
            behavioral_questions=["Tell me about a time you received difficult feedback."],
            project_questions=["What would you improve if you had another week?"],
            checklist=[
                "Review the role requirements",
                "Prepare two evidence stories",
                "Practice your 30-second pitch",
            ],
        ),
        evidence_files=[EvidenceFile.model_validate(file) for file in profile.uploads],
        resume_analysis=profile.resume_analysis,
    )
    for index, step in enumerate(report.learning_recommendations):
        if index < len(profile.learning_completed):
            step.completed = profile.learning_completed[index]
    return report
