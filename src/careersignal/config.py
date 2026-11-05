"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings with safe local-first defaults."""

    host: str = os.getenv("CAREERSIGNAL_HOST", "127.0.0.1")
    port: int = int(os.getenv("CAREERSIGNAL_PORT", "8000"))
    llm_provider: str = os.getenv("CAREERSIGNAL_LLM_PROVIDER", "rule_based")
    allow_external_llm: bool = (
        os.getenv("CAREERSIGNAL_ALLOW_EXTERNAL_LLM", "false").lower() == "true"
    )


settings = Settings()
