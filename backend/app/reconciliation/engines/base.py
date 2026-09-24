"""
TRACE - Base Reconciliation Engine
Defines the standard abstract contract, data structures, and instrumentation
for all three reconciliation approaches: RULE_BASED, AI_LLM, and HYBRID.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class EngineEvidence:
    document_id: Optional[str] = None
    document_name: Optional[str] = None
    page_number: int = 1
    field_name: Optional[str] = None
    exact_value: Optional[str] = ""
    snippet: str = ""
    relevance_score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_name": self.document_name,
            "page_number": self.page_number,
            "field_name": self.field_name,
            "exact_value": self.exact_value,
            "snippet": self.snippet,
            "relevance_score": self.relevance_score
        }

@dataclass
class EngineFinding:
    discrepancy_type: str  # QUANTITY_MISMATCH, PRICE_MISMATCH, etc.
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    expected_value: str = ""
    actual_value: str = ""
    difference_value: str = ""
    difference_amount: float = 0.0
    explanation: str = ""
    confidence: float = 1.0
    evidence: List[EngineEvidence] = field(default_factory=list)
    source_documents: List[str] = field(default_factory=list)
    provenance: str = "rule"  # rule, semantic, llm
    rule_code: Optional[str] = None
    title: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "discrepancy_type": self.discrepancy_type,
            "severity": self.severity,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "difference_value": self.difference_value,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "evidence": [e.to_dict() for e in self.evidence],
            "source_documents": self.source_documents,
            "provenance": self.provenance,
            "rule_code": self.rule_code,
            "title": self.title
        }

@dataclass
class EngineResult:
    approach: str  # RULE_BASED, AI_LLM, HYBRID
    overall_result: str  # RECONCILED, DISCREPANCIES_FOUND, ERROR
    execution_time_ms: float
    cost_usd: float
    findings: List[EngineFinding] = field(default_factory=list)
    model_version: str = "1.0.0"
    configuration: Dict[str, Any] = field(default_factory=dict)
    summary_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approach": self.approach,
            "overall_result": self.overall_result,
            "execution_time_ms": self.execution_time_ms,
            "cost_usd": self.cost_usd,
            "findings_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
            "model_version": self.model_version,
            "configuration": self.configuration,
            "summary_text": self.summary_text
        }

class BaseReconciliationEngine(ABC):
    """
    Abstract interface for all reconciliation engines.
    """
    @property
    @abstractmethod
    def approach_name(self) -> str:
        """Returns RULE_BASED, AI_LLM, or HYBRID."""
        pass

    @abstractmethod
    def reconcile(self, transaction_data: Dict[str, Any]) -> EngineResult:
        """
        Executes reconciliation on a transaction and its associated documents.
        """
        pass
