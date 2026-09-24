"""
TRACE - Document & File Pydantic Schemas
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

class UploadBatchResponse(BaseModel):
    id: str
    uploaded_by: str = "system"
    upload_time: datetime
    original_filename: Optional[str] = None
    number_of_files: int = 1
    processing_status: str = "COMPLETED"

    model_config = ConfigDict(from_attributes=True)

class FileResponse(BaseModel):
    id: str
    upload_batch_id: Optional[str] = None
    filename: str
    file_type: str = "pdf"
    file_size: int = 0
    storage_path: str
    checksum: Optional[str] = None
    upload_time: datetime
    processing_status: str = "PROCESSED"
    document_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class DocumentResponse(BaseModel):
    id: str
    file_id: Optional[str] = None
    document_type: str = "OTHER"
    page_start: int = 1
    page_end: int = 1
    document_number: Optional[str] = None
    confidence: float = 1.0
    extracted_text: str = ""
    structured_data: Dict[str, Any] = {}
    classification_method: str = "ML_CLASSIFIER"

    # Backwards-compatible fields
    filename: Optional[str] = ""
    file_path: Optional[str] = ""
    file_type: Optional[str] = "pdf"
    doc_type: Optional[str] = "UNKNOWN"
    classification_confidence: Optional[float] = 0.0
    original_pdf_id: Optional[str] = None
    page_number: Optional[int] = 1
    page_count: Optional[int] = 1
    raw_text: Optional[str] = ""
    parsed_data: Optional[Dict[str, Any]] = {}
    status: Optional[str] = "processed"
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TransactionDocumentLinkResponse(BaseModel):
    id: Optional[str] = None
    transaction_id: str
    document_id: str
    link_method: str = "exact_identifier"
    link_confidence: float = 1.0
    confirmed: bool = False
    link_details: Dict[str, Any] = {}
    created_at: Optional[datetime] = None
    document: Optional[DocumentResponse] = None

    model_config = ConfigDict(from_attributes=True)
