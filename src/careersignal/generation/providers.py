"""Provider interface with deterministic and optional hosted implementations."""

import json
import urllib.request
from abc import ABC, abstractmethod

from ..models import CareerReport


class LLMProvider(ABC):
    """Generate only grounded prose for an existing report."""

    @abstractmethod
    def rewrite_summary(self, report: CareerReport) -> str:
        raise NotImplementedError


class RuleBasedProvider(LLMProvider):
    def rewrite_summary(self, report: CareerReport) -> str:
        return report.professional_summary


class OpenAICompatibleProvider(LLMProvider):
    """Small standard-library client for OpenAI-compatible JSON endpoints."""

    def __init__(self, endpoint: str, api_key: str, model: str) -> None:
        self.endpoint, self.api_key, self.model = endpoint, api_key, model

    def rewrite_summary(self, report: CareerReport) -> str:
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Rewrite only the summary. Use no facts outside this grounded report. "
                            f"Report JSON: {report.model_dump_json()}"
                        ),
                    }
                ],
                "response_format": {"type": "json_object"},
            }
        ).encode()
        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read())
        content = data["choices"][0]["message"]["content"]
        return str(json.loads(content)["summary"])
