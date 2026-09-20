"""
TRACE - Financial Rule Engine Base Classes
Enforces Decimal precision and standardized discrepancy payload structure.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class RuleEvidenceItem(BaseModel):
    document_id: str
    document_name: str
    page_number: int = 1
    field_name: str
    exact_value: str
    snippet: str
    relevance_score: float = 1.0

class DiscrepancyResult(BaseModel):
    rule_code: str
    discrepancy_type: str
    title: str
    description: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float  # 0.0 to 1.0
    difference_amount: Decimal = Decimal("0.00")
    expected_value: str = ""
    actual_value: str = ""
    difference_value: str = ""
    evidences: List[RuleEvidenceItem] = []
    metadata: Dict[str, Any] = {}

class BaseReconciliationRule(ABC):
    @property
    @abstractmethod
    def rule_code(self) -> str:
        """Unique identifier code for the rule (e.g. PRICE_MISMATCH)."""
        pass

    @abstractmethod
    def evaluate(self, transaction_data: Dict[str, Any]) -> List[DiscrepancyResult]:
        """
        Evaluates the transaction data and returns a list of detected discrepancies.
        """
        pass
