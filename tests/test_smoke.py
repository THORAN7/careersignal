"""Phase 1 packaging smoke tests."""

from careercanvas.config import settings


def test_local_defaults_are_safe() -> None:
    assert settings.host == "127.0.0.1"
    assert settings.llm_provider == "rule_based"
    assert settings.allow_external_llm is False
