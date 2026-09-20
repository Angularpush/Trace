"""
TRACE - LLM Provider Abstract Interface
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any

class LLMProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def generate_explanation(
        self,
        discrepancy: Dict[str, Any],
        evidence_items: List[Dict[str, Any]],
        transaction_context: Dict[str, Any]
    ) -> str:
        """
        Generates a natural-language evidence-grounded explanation.
        If evidence is insufficient, returns "Insufficient evidence to determine this discrepancy."
        """
        pass

    @abstractmethod
    def generate_reconciliation_summary(
        self,
        transaction_ref: str,
        discrepancies: List[Dict[str, Any]],
        documents_summary: List[Dict[str, Any]],
        financial_variance: float
    ) -> str:
        """
        Generates an overall executive reconciliation summary for the transaction report.
        """
        pass
