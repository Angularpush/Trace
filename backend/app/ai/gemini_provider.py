"""
TRACE - Google Gemini AI Explanation Provider
Generates grounded, evidence-based audit explanations using the official google-genai SDK.
"""

import os
from typing import Dict, List, Any
from app.ai.base import LLMProvider
from app.ai.prompt_builder import GroundedPromptBuilder
from app.ai.offline_provider import OfflineProvider

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.model = model
        self.offline_fallback = OfflineProvider()
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[TRACE GeminiProvider Warning] Failed to initialize google-genai client: {e}")

    @property
    def provider_name(self) -> str:
        return "gemini"

    def generate_explanation(
        self,
        discrepancy: Dict[str, Any],
        evidence_items: List[Dict[str, Any]],
        transaction_context: Dict[str, Any]
    ) -> str:
        if not self.client:
            return self.offline_fallback.generate_explanation(discrepancy, evidence_items, transaction_context)

        prompt = GroundedPromptBuilder.build_discrepancy_explanation_prompt(
            discrepancy=discrepancy,
            evidence_items=evidence_items,
            transaction_context=transaction_context
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text.strip() if response.text else self.offline_fallback.generate_explanation(discrepancy, evidence_items, transaction_context)
        except Exception as e:
            print(f"[TRACE GeminiProvider Error] API call failed: {e}. Falling back to offline provider.")
            return self.offline_fallback.generate_explanation(discrepancy, evidence_items, transaction_context)

    def generate_reconciliation_summary(
        self,
        transaction_ref: str,
        discrepancies: List[Dict[str, Any]],
        documents_summary: List[Dict[str, Any]],
        financial_variance: float
    ) -> str:
        if not self.client:
            return self.offline_fallback.generate_reconciliation_summary(
                transaction_ref, discrepancies, documents_summary, financial_variance
            )

        prompt = GroundedPromptBuilder.build_reconciliation_summary_prompt(
            transaction_ref=transaction_ref,
            discrepancies=discrepancies,
            documents_summary=documents_summary,
            financial_variance=financial_variance
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text.strip() if response.text else self.offline_fallback.generate_reconciliation_summary(
                transaction_ref, discrepancies, documents_summary, financial_variance
            )
        except Exception as e:
            print(f"[TRACE GeminiProvider Error] Summary generation failed: {e}. Using offline fallback.")
            return self.offline_fallback.generate_reconciliation_summary(
                transaction_ref, discrepancies, documents_summary, financial_variance
            )

