"""Phase 1 packaging smoke tests."""

from careercanvas.api import demo_state
from careercanvas.config import settings


def test_local_defaults_are_safe() -> None:
    assert settings.host == "127.0.0.1"
    assert settings.llm_provider == "rule_based"
    assert settings.allow_external_llm is False


def test_frontend_profile_contract_is_available() -> None:
    state = demo_state()
    assert state["profile"]["name"] == "Maya Chen"
    assert state["report"]["headline"]
    assert len(state["report"]["interview_preparation"]["questions"]) == 3
