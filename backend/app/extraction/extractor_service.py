"""
TRACE - Document Processing and Extraction Service
Coordinates file segmentation (FILE != DOCUMENT), classification, and structured extraction.
"""

import os
from typing import Dict, Any, List, Optional
from app.extraction.pdf_extractor import DocumentExtractor
from app.extraction.segmenter import DocumentSegmenter, DocumentSegment
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
    def parse_segment_data(doc_type: str, raw_text: str, lines: List[str]) -> Dict[str, Any]:
        """
        Invokes domain parser based on document type and returns structured data.
        """
        extracted_payload = {
            "raw_text": raw_text,
            "page_count": 1,
            "pages": [{
                "page_number": 1,
                "text": raw_text,
                "lines": lines
            }]
        }

        try:
            if doc_type == "PURCHASE_ORDER":
                parsed = PurchaseOrderParser.parse(extracted_payload)
            elif doc_type == "INVOICE":
                parsed = InvoiceParser.parse(extracted_payload)
            elif doc_type == "DELIVERY_NOTE":
                parsed = DeliveryNoteParser.parse(extracted_payload)
            elif doc_type in ["PAYMENT_RECEIPT", "PAYMENT"]:
                parsed = PaymentReceiptParser.parse(extracted_payload)
            elif doc_type == "QUOTATION":
                parsed = NoteParser.parse_quotation(extracted_payload)
            elif doc_type == "CREDIT_NOTE":
                parsed = NoteParser.parse_credit_note(extracted_payload)
            elif doc_type == "DEBIT_NOTE":
                parsed = NoteParser.parse_debit_note(extracted_payload)
            else:
                parsed = {
                    "document_number": None,
                    "document_date": None,
                    "supplier_name": None,
                    "customer_name": None,
                    "items": [],
                    "grand_total": "0.00",
                    "extra_metadata": {}
                }
        except Exception as e:
            parsed = {
                "document_number": None,
                "document_date": None,
                "supplier_name": None,
                "customer_name": None,
                "items": [],
                "grand_total": "0.00",
                "extra_metadata": {"parse_error": str(e)}
            }
        return parsed

    @staticmethod
    def process_file_segments(file_path: str, user_doc_type: Optional[str] = None, output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Pipeline: File -> Boundary Segmentation -> Document Classification -> Information Extraction.
        Returns list of segmented documents with structured data.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Step 1: Detect Document Boundaries
        segments = DocumentSegmenter.segment_file(file_path, output_dir=output_dir)

        results = []
        for idx, seg in enumerate(segments):
            doc_type = user_doc_type.upper() if user_doc_type and user_doc_type.upper() != "AUTO" else seg.document_type
            
            # Step 2: Information Extraction
            parsed_data = DocumentProcessingService.parse_segment_data(doc_type, seg.raw_text, seg.lines)
            
            # If segment had hint for doc number, ensure it's populated
            if seg.document_number_hint and not parsed_data.get("document_number"):
                parsed_data["document_number"] = seg.document_number_hint

            doc_record = {
                "page_start": seg.page_start,
                "page_end": seg.page_end,
                "document_type": doc_type,
                "doc_type": doc_type,  # backward compatibility
                "confidence": seg.confidence,
                "classification_confidence": seg.confidence,  # backward compatibility
                "classification_method": seg.classification_method,
                "document_number": parsed_data.get("document_number"),
                "file_path": seg.file_path,
                "raw_text": seg.raw_text,
                "lines": seg.lines,
                "parsed_data": parsed_data,
                "page_number": seg.page_start,
                "page_count": seg.page_end - seg.page_start + 1
            }
            results.append(doc_record)

        return results

    @staticmethod
    def process_single_page(page_dict: Dict[str, Any], user_doc_type: str = None) -> Dict[str, Any]:
        """
        Backwards-compatible single page processor.
        """
        raw_text = page_dict.get("raw_text", "")
        page_num = page_dict.get("page_number", 1)
        lines = page_dict.get("lines", [])

        if user_doc_type and user_doc_type.upper() != "AUTO":
            doc_type = user_doc_type.upper()
            confidence = 1.0
            method = "USER_SPECIFIED"
        else:
            classification_service = DocumentClassificationService.get_instance()
            doc_type, confidence, _ = classification_service.classify(raw_text)
            method = "ML_CLASSIFIER"

        parsed_data = DocumentProcessingService.parse_segment_data(doc_type, raw_text, lines)

        return {
            "page_number": page_num,
            "page_start": page_num,
            "page_end": page_num,
            "file_path": page_dict.get("file_path", ""),
            "doc_type": doc_type,
            "document_type": doc_type,
            "classification_confidence": confidence,
            "confidence": confidence,
            "classification_method": method,
            "page_count": 1,
            "raw_text": raw_text,
            "parsed_data": parsed_data
        }

    @staticmethod
    def process_multi_page_document(file_path: str, user_doc_type: str = None, output_dir: str = None) -> List[Dict[str, Any]]:
        """
        Uses segmentation pipeline to process multi-page or multi-document files.
        """
        return DocumentProcessingService.process_file_segments(file_path, user_doc_type=user_doc_type, output_dir=output_dir)

    @staticmethod
    def process_document(file_path: str, user_doc_type: str = None) -> Dict[str, Any]:
        """
        Backward compatible single document processor.
        """
        results = DocumentProcessingService.process_file_segments(file_path, user_doc_type=user_doc_type)
        if len(results) == 1:
            return results[0]
        primary = results[0]
        all_text = "\n\n".join([r["raw_text"] for r in results])
        return {
            "doc_type": primary["doc_type"],
            "document_type": primary["document_type"],
            "classification_confidence": primary["classification_confidence"],
            "confidence": primary["confidence"],
            "page_count": len(results),
            "raw_text": all_text,
            "parsed_data": primary["parsed_data"],
            "all_pages": results
        }
