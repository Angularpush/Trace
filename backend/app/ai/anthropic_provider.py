"""
TRACE - Anthropic Claude LLM Provider
Integrates with Anthropic Claude API (claude-3-5-sonnet) using httpx.
"""

import os
import httpx
from typing import Dict, List, Any
from app.ai.base import LLMProvider
from app.ai.prompt_builder import GroundedPromptBuilder
from app.core.config import settings

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = None, api_base: str = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = model or settings.ANTHROPIC_MODEL or "claude-opus-5"
        self.api_base = api_base or getattr(settings, "ANTHROPIC_API_BASE", "https://agentrouter.org/v1").rstrip("/")

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def _call_api(self, prompt: str) -> str:
        if not self.api_key:
            return "Insufficient evidence to determine this discrepancy."

        # If pointing to an OpenAI-compatible proxy like agentrouter
        if "agentrouter" in self.api_base or "/v1" in self.api_base:
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
                "max_tokens": 350,
                "temperature": 0.1
            }
            endpoint = f"{self.api_base}/chat/completions"
        else:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
                "User-Agent": "cline/1.0.0"
            }
            payload = {
                "model": self.model,
                "system": "You are TRACE AI, a professional MSME financial auditor. Ground answers strictly in evidence provided.",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 350,
                "temperature": 0.1
            }
            endpoint = f"{self.api_base}/messages" if not self.api_base.endswith("/v1") else f"{self.api_base}/messages"

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(endpoint, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    if "choices" in data:
                        return data["choices"][0]["message"]["content"].strip()
                    elif "content" in data:
                        return data["content"][0]["text"].strip()
                    return str(data)
                else:
                    return f"Anthropic API Error ({resp.status_code}): {resp.text}"
        except Exception as e:
            return f"Anthropic Provider connection error: {str(e)}"

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
