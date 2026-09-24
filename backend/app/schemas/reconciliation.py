"""
TRACE - Reconciliation & Evaluation Pydantic Schemas
Defines structured schemas for runs, findings, 3-way comparator, and evaluation benchmark results.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class EvidenceItemSchema(BaseModel):
    document_id: Optional[str] = None
    document_name: Optional[str] = None
    page_number: int = 1
    field_name: Optional[str] = None
    exact_value: Optional[str] = ""
    snippet: str = ""
    relevance_score: float = 1.0

class ReconciliationFindingResponse(BaseModel):
    id: Optional[str] = None
    reconciliation_run_id: Optional[str] = None
    discrepancy_type: str
    severity: str = "MEDIUM"
    expected_value: str = ""
    actual_value: str = ""
    difference_value: str = ""
    explanation: str = ""
    confidence: float = 1.0
    evidence: List[Dict[str, Any]] = []
    source_documents: List[str] = []
    provenance: str = "rule"  # rule, semantic, llm
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ReconciliationRunRequest(BaseModel):
    transaction_id: str
    approach: str = "RULE_BASED"  # RULE_BASED, AI_LLM, HYBRID
    configuration: Dict[str, Any] = {}

class ReconciliationRunResponse(BaseModel):
    id: Optional[str] = None
    transaction_id: Optional[str] = None
    approach: str  # RULE_BASED, AI_LLM, HYBRID
    run_time: Optional[datetime] = None
    model_version: str = "1.0.0"
    configuration: Dict[str, Any] = {}
    overall_result: str = "RECONCILED"  # RECONCILED, DISCREPANCIES_FOUND, ERROR
    execution_time_ms: float = 0.0
    cost_usd: float = 0.0
    findings_count: int = 0
    findings: List[ReconciliationFindingResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ComparisonResultResponse(BaseModel):
    transaction_id: str
    transaction_reference: str
    rule_based_run: Optional[ReconciliationRunResponse] = None
    ai_llm_run: Optional[ReconciliationRunResponse] = None
    hybrid_run: Optional[ReconciliationRunResponse] = None
    agreement_score: float = 1.0  # 0.0 to 1.0 Jaccard or consensus overlap
    consensus_discrepancies: List[str] = []
    conflicting_discrepancies: List[str] = []
    latency_comparison: Dict[str, float] = {}  # {RULE_BASED: ms, AI_LLM: ms, HYBRID: ms}
    cost_comparison: Dict[str, float] = {}  # {RULE_BASED: $, AI_LLM: $, HYBRID: $}
    explanation_summary: str = ""

class DiscrepancyMetricDetail(BaseModel):
    discrepancy_type: str
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0

class ApproachEvaluationSummary(BaseModel):
    approach: str  # RULE_BASED, AI_LLM, HYBRID
    total_evaluated_transactions: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    linking_accuracy: float = 0.0
    evidence_accuracy: float = 0.0
    reconciliation_accuracy: float = 0.0
    avg_execution_time_ms: float = 0.0
    total_cost_usd: float = 0.0
    cost_per_transaction_usd: float = 0.0
    category_breakdown: List[DiscrepancyMetricDetail] = []

class BenchmarkEvaluationReport(BaseModel):
    benchmark_id: str
    run_timestamp: datetime
    dataset_size: int
    categories_tested: int
    rule_based_metrics: ApproachEvaluationSummary
    ai_llm_metrics: ApproachEvaluationSummary
    hybrid_metrics: ApproachEvaluationSummary
    key_findings: List[str] = []
    modes: Dict[str, Any] = {}
