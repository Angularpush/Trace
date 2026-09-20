"""
TRACE - Document Pydantic Schemas
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

class LineItemSchema(BaseModel):
    item_id: Optional[str] = None
    description: str
    normalized_description: Optional[str] = None
    quantity: Decimal
    unit: str = "PCS"
    unit_price: Decimal
    discount: Decimal = Decimal("0.00")
    tax_rate: Decimal = Decimal("0.00")  # e.g., 18.00%
    tax_amount: Decimal = Decimal("0.00")
    total_amount: Decimal
    evidence_snippet: Optional[str] = None
    page_number: int = 1

class ParsedDocumentData(BaseModel):
    document_number: Optional[str] = None
    po_reference: Optional[str] = None
    invoice_reference: Optional[str] = None
    document_date: Optional[str] = None
    due_date: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_gstin: Optional[str] = None
    customer_name: Optional[str] = None
    customer_gstin: Optional[str] = None
    delivery_address: Optional[str] = None
    items: List[LineItemSchema] = []
    subtotal: Decimal = Decimal("0.00")
    tax_total: Decimal = Decimal("0.00")
    grand_total: Decimal = Decimal("0.00")
    payment_amount: Optional[Decimal] = None
    payment_method: Optional[str] = None
    transaction_reference: Optional[str] = None
    adjustment_amount: Optional[Decimal] = None
    reason_for_adjustment: Optional[str] = None
    extra_metadata: Dict[str, Any] = {}

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    doc_type: str
    classification_confidence: float
    page_count: int
    raw_text: str
    parsed_data: Dict[str, Any]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
