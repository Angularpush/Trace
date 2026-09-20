"""
TRACE - Document Processing and Extraction Service
Coordinates multi-format PDF/Image text extraction, ML classification inference, and structured entity normalization.
"""

from typing import Dict, Any
from app.extraction.pdf_extractor import DocumentExtractor
from app.classification.classifier import DocumentClassificationService
from app.extraction.parsers import (
    PurchaseOrderParser,
    InvoiceParser,
    DeliveryNoteParser,
    PaymentReceiptParser,
    NoteParser
)

class DocumentProcessingService:
    @staticmethod
    def process_document(file_path: str, user_doc_type: str = None) -> Dict[str, Any]:
        """
        Processes document end-to-end:
        1. Extract text and page layout via PyMuPDF / OCR
        2. Classify document type via DocumentClassificationService (TF-IDF + Logistic Regression)
        3. Parse domain-specific structured fields with fallback handlers
        """
        # Step 1: Text extraction
        extracted = DocumentExtractor.extract(file_path)
        raw_text = extracted.get("raw_text", "")

        # Step 2: Classification inference via DocumentClassificationService
        if user_doc_type and user_doc_type.upper() != "AUTO":
            doc_type = user_doc_type.upper()
            confidence = 1.0
            prob_dist = {doc_type: 1.0}
        else:
            classification_service = DocumentClassificationService.get_instance()
            doc_type, confidence, prob_dist = classification_service.classify(raw_text)

        # Step 3: Domain-specific parsing
        parsed_data = {}
        if doc_type == "PURCHASE_ORDER":
            parsed_data = PurchaseOrderParser.parse(extracted)
        elif doc_type == "INVOICE":
            parsed_data = InvoiceParser.parse(extracted)
        elif doc_type == "DELIVERY_NOTE":
            parsed_data = DeliveryNoteParser.parse(extracted)
        elif doc_type == "PAYMENT_RECEIPT":
            parsed_data = PaymentReceiptParser.parse(extracted)
        elif doc_type == "QUOTATION":
            parsed_data = NoteParser.parse_quotation(extracted)
        elif doc_type == "CREDIT_NOTE":
            parsed_data = NoteParser.parse_credit_note(extracted)
        elif doc_type == "DEBIT_NOTE":
            parsed_data = NoteParser.parse_debit_note(extracted)
        else:
            parsed_data = {
                "document_number": None,
                "document_date": None,
                "supplier_name": None,
                "customer_name": None,
                "items": [],
                "grand_total": "0.00",
                "extra_metadata": {}
            }

        parsed_data["prob_dist"] = prob_dist

        return {
            "doc_type": doc_type,
            "classification_confidence": confidence,
            "page_count": extracted.get("page_count", 1),
            "raw_text": raw_text,
            "parsed_data": parsed_data
        }
