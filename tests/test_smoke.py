"""Phase 1 packaging smoke tests."""

from careercanvas.api import EMPTY_PROFILE, demo_state, report_for
from careercanvas.config import settings


def test_local_defaults_are_safe() -> None:
    assert settings.host == "127.0.0.1"
    assert settings.llm_provider == "rule_based"
    assert settings.allow_external_llm is False


def test_frontend_profile_contract_is_available() -> None:
    state = demo_state(EMPTY_PROFILE.copy())
    assert state["profile"]["name"] == ""
    assert state["report"]["headline"]
    assert len(state["report"]["interview_preparation"]["questions"]) == 3


def test_empty_profile_has_onboarding_summary() -> None:
    report = report_for({"name": "", "skills": [], "learning_completed": [False, False, False]})
    assert "entering your details" in report["professional_summary"]
