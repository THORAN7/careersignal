"""Typed domain models for CareerSignal reports."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceFile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    size: int = Field(ge=0)
    uploaded_at: str


class StudentProfile(BaseModel):
    name: str = Field(default="", max_length=120)
    degree: str = Field(default="", max_length=160)
    year: str = Field(default="", max_length=80)
    school: str = Field(default="", max_length=180)
    skills: list[str] = Field(default_factory=list, max_length=30)
    interests: str = Field(default="", max_length=1200)
    goals: str = Field(default="", max_length=1200)
    experience: str = Field(default="", max_length=2400)
    target_role: str = Field(default="", max_length=120)
    uploads: list[EvidenceFile] = Field(default_factory=list)
    resume_analysis: dict[str, object] | None = None
    learning_completed: list[bool] = Field(default_factory=lambda: [False, False, False])


class ResumeAnalysis(BaseModel):
    status: str
    message: str = ""
    detected_skills: list[str] = Field(default_factory=list)
    sections: list[str] = Field(default_factory=list)
    contact: "ContactSignals" = Field(default_factory=lambda: ContactSignals())
    completeness_score: int = Field(ge=0, le=100)
    word_count: int = Field(ge=0)
    inferred_name: str = ""


class ContactSignals(BaseModel):
    email: str = ""
    phone: str = ""


class RequiredSkill(BaseModel):
    name: str
    weight: float = Field(gt=0, le=1)
    level: Literal["beginner", "intermediate", "advanced"]
    aliases: list[str] = Field(default_factory=list)
    project_ideas: list[str] = Field(default_factory=list)


class RoleBlueprint(BaseModel):
    name: str
    summary: str
    aliases: list[str] = Field(default_factory=list)
    required_skills: list[RequiredSkill]


class SkillGapItem(BaseModel):
    skill: str
    priority: Literal["HIGH", "MEDIUM", "LOW"]
    status: Literal["matched", "partial", "missing"]
    confidence: float = Field(ge=0, le=1)
    weight: float = Field(ge=0, le=1)
    level: str
    why: str
    action: str


class LearningStep(BaseModel):
    week: str
    title: str
    detail: str
    outcome: str
    gap_skill: str = ""
    estimated_hours: int = Field(default=4, ge=1, le=80)
    completed: bool = False


class InterviewPack(BaseModel):
    pitch: str
    questions: list[str] = Field(min_length=1)
    behavioral_questions: list[str] = Field(default_factory=list)
    project_questions: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)


class CareerReport(BaseModel):
    schema_version: str = "1.0"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    target_role: str
    score: int = Field(ge=0, le=100)
    headline: str
    professional_summary: str
    summary: str
    strengths: list[str]
    skill_gap_report: list[SkillGapItem]
    learning_recommendations: list[LearningStep]
    interview_preparation: InterviewPack
    evidence_files: list[EvidenceFile] = Field(default_factory=list)
    resume_analysis: ResumeAnalysis | dict[str, object] | None = None
    consistency_warnings: list[str] = Field(default_factory=list)
