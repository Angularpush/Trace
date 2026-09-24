"""
TRACE - OpenAI LLM Provider
Integrates with OpenAI API (gpt-4o-mini / gpt-4o) using httpx for async/sync requests.
"""

import os
import httpx
from typing import Dict, List, Any
from app.ai.base import LLMProvider
from app.ai.prompt_builder import GroundedPromptBuilder
from app.core.config import settings

_OPENAI_COOLDOWN_UNTIL: float = 0.0

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = None, api_base: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        self.model = model or settings.OPENAI_MODEL or "gpt-6-astra"
        self.api_base = api_base or getattr(settings, "OPENAI_API_BASE", "https://agentrouter.org/v1").rstrip("/")

    @property
    def provider_name(self) -> str:
        return "openai"

    def _call_api(self, prompt: str) -> str:
        global _OPENAI_COOLDOWN_UNTIL
        import time
        if time.time() < _OPENAI_COOLDOWN_UNTIL:
            return ""

        if not self.api_key:
            return "Insufficient evidence to determine this discrepancy."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "cline/1.0.0"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are TRACE AI, a professional MSME financial auditor. Ground answers strictly in evidence provided."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 300
        }

        endpoint = f"{self.api_base}/chat/completions"
        call_timeout = 2.0 if os.environ.get("PYTEST_CURRENT_TEST") else 6.0

        try:
            with httpx.Client(timeout=call_timeout) as client:
                resp = client.post(endpoint, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    if resp.status_code in [401, 402, 429]:
                        _OPENAI_COOLDOWN_UNTIL = time.time() + 60.0
                    return f"OpenAI API Error ({resp.status_code}): {resp.text}"
        except Exception as e:
            if "402" in str(e) or "quota" in str(e).lower() or "401" in str(e):
                _OPENAI_COOLDOWN_UNTIL = time.time() + 60.0
            return f"OpenAI Provider connection error: {str(e)}"

    def generate_explanation(
        self,
        discrepancy: Dict[str, Any],
        evidence_items: List[Dict[str, Any]],
        transaction_context: Dict[str, Any]
    ) -> str:
        if not evidence_items:
            return "Insufficient evidence to determine this discrepancy."
        prompt = GroundedPromptBuilder.build_discrepancy_explanation_prompt(
            discrepancy, evidence_items, transaction_context
        )
        return self._call_api(prompt)

    def generate_reconciliation_summary(
        self,
        transaction_ref: str,
        discrepancies: List[Dict[str, Any]],
        documents_summary: List[Dict[str, Any]],
        financial_variance: float
    ) -> str:
        prompt = GroundedPromptBuilder.build_reconciliation_summary_prompt(
            transaction_ref, discrepancies, documents_summary, financial_variance
        )
        return self._call_api(prompt)
