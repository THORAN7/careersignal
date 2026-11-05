"""Role blueprint loading and role-aware skill-gap analysis."""

import json
import re
from pathlib import Path
from typing import Any, Literal, cast

from ..models import RequiredSkill, RoleBlueprint, SkillGapItem

ROLE_DIR = Path(__file__).resolve().parents[3] / "data" / "roles"


def load_roles() -> list[RoleBlueprint]:
    roles: list[RoleBlueprint] = []
    for path in sorted(ROLE_DIR.glob("*.json")):
        roles.append(RoleBlueprint.model_validate(json.loads(path.read_text(encoding="utf-8"))))
    return roles


def infer_role(target_role: str, interests: str, goals: str) -> RoleBlueprint:
    roles = load_roles()
    text = f"{target_role} {interests} {goals}".lower()
    if target_role.strip():
        explicit = target_role.lower()
        for role in roles:
            if explicit == role.name.lower() or any(alias in explicit for alias in role.aliases):
                return role
    return max(
        roles,
        key=lambda role: sum(
            1
            for term in [role.name.lower(), *role.aliases]
            if re.search(rf"\b{re.escape(term)}\b", text)
        ),
        default=roles[0],
    )


def _match(text: str, skill: RequiredSkill) -> float:
    haystack = text.lower()
    matches = [skill.name, *skill.aliases]
    if any(re.search(rf"(?<!\w){re.escape(term.lower())}(?!\w)", haystack) for term in matches):
        return 1.0
    if any(term.lower() in haystack for term in matches if len(term) > 4):
        return 0.55
    return 0.0


def analyze_gaps(profile: dict[str, Any], role: RoleBlueprint) -> tuple[list[SkillGapItem], int]:
    analysis = profile.get("resume_analysis") or {}
    text = " ".join(
        [
            str(profile.get("skills", "")),
            str(profile.get("interests", "")),
            str(profile.get("goals", "")),
            str(profile.get("experience", "")),
            str(analysis.get("text_preview", "")),
            str(analysis.get("detected_skills", "")),
        ]
    )
    gaps: list[SkillGapItem] = []
    weighted_coverage = 0.0
    total_weight = sum(skill.weight for skill in role.required_skills)
    for skill in role.required_skills:
        confidence = _match(text, skill)
        status = "matched" if confidence >= 0.9 else "partial" if confidence else "missing"
        weighted_coverage += skill.weight * confidence
        priority = (
            "HIGH"
            if skill.weight * (1 - confidence) >= 0.22
            else "MEDIUM"
            if skill.weight * (1 - confidence) >= 0.10
            else "LOW"
        )
        gaps.append(
            SkillGapItem(
                skill=skill.name,
                priority=cast(Literal["HIGH", "MEDIUM", "LOW"], priority),
                status=cast(Literal["matched", "partial", "missing"], status),
                confidence=round(confidence, 2),
                weight=skill.weight,
                level=skill.level,
                why=f"{skill.name} is a {skill.level}-level capability expected for {role.name}.",
                action=skill.project_ideas[0]
                if skill.project_ideas
                else f"Build a practical {skill.name} project.",
            )
        )
    coverage = round((weighted_coverage / total_weight) * 100) if total_weight else 0
    evidence_quality = min(
        100,
        25
        + len(str(profile.get("experience", ""))) // 30
        + int((analysis.get("completeness_score") or 0) * 0.5),
    )
    return gaps, round(coverage * 0.7 + evidence_quality * 0.3)
