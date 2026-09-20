"""
TRACE - Discrepancy & Evidence Pydantic Schemas
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class EvidenceResponse(BaseModel):
    id: str
    document_id: str
    document_name: str
    page_number: int
    field_name: str
    exact_value: str
    snippet: str
    relevance_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DiscrepancyResponse(BaseModel):
    id: str
    transaction_id: str
    rule_code: str
    discrepancy_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float  # 0.0 to 1.0
    title: str
    description: str
    difference_amount: float
    expected_value: Optional[str] = ""
    actual_value: Optional[str] = ""
    difference_value: Optional[str] = ""
    llm_explanation: str
    status: str
    created_at: datetime
    evidences: List[EvidenceResponse] = []

    model_config = ConfigDict(from_attributes=True)
