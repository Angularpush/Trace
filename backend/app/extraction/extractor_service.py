"""
TRACE - Document Processing and Extraction Service
Coordinates multi-format PDF/Image text extraction, ML classification inference, and structured entity normalization.
"""

import os
from typing import Dict, Any, List
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
    def process_single_page(page_dict: Dict[str, Any], user_doc_type: str = None) -> Dict[str, Any]:
        """
        Processes a single page extraction dict:
        1. Classify document type via DocumentClassificationService (TF-IDF + Logistic Regression)
        2. Parse domain-specific structured fields with fallback handlers
        """
        # Step 1: Text extraction
        raw_text = page_dict.get("raw_text", "")
        page_num = page_dict.get("page_number", 1)

        # Step 2: Classification inference
        if user_doc_type and user_doc_type.upper() != "AUTO":
            doc_type = user_doc_type.upper()
            confidence = 1.0
            prob_dist = {doc_type: 1.0}
        else:
            classification_service = DocumentClassificationService.get_instance()
            try:
                doc_type, confidence, prob_dist = classification_service.classify(raw_text)
            except Exception as e:
                raise RuntimeError(f"Classification failed on page {page_num}: {str(e)}")

        extracted_payload = {
            "raw_text": raw_text,
            "page_count": 1,
            "pages": [{
                "page_number": page_num,
                "text": raw_text,
                "lines": page_dict.get("lines", [])
            }]
        }

        # Step 3: Domain-specific parsing
        try:
            if doc_type == "PURCHASE_ORDER":
                parsed_data = PurchaseOrderParser.parse(extracted_payload)
            elif doc_type == "INVOICE":
                parsed_data = InvoiceParser.parse(extracted_payload)
            elif doc_type == "DELIVERY_NOTE":
                parsed_data = DeliveryNoteParser.parse(extracted_payload)
            elif doc_type in ["PAYMENT_RECEIPT", "PAYMENT"]:
                doc_type = "PAYMENT_RECEIPT"
                parsed_data = PaymentReceiptParser.parse(extracted_payload)
            elif doc_type == "QUOTATION":
                parsed_data = NoteParser.parse_quotation(extracted_payload)
            elif doc_type == "CREDIT_NOTE":
                parsed_data = NoteParser.parse_credit_note(extracted_payload)
            elif doc_type == "DEBIT_NOTE":
                parsed_data = NoteParser.parse_debit_note(extracted_payload)
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
        except Exception as e:
            raise RuntimeError(f"Structured field extraction failed on page {page_num} ({doc_type}): {str(e)}")

        parsed_data["prob_dist"] = prob_dist

        return {
            "page_number": page_num,
            "file_path": page_dict.get("file_path", ""),
            "doc_type": doc_type,
            "classification_confidence": confidence,
            "page_count": 1,
            "raw_text": raw_text,
            "parsed_data": parsed_data
        }

    @staticmethod
    def process_multi_page_document(file_path: str, user_doc_type: str = None, output_dir: str = None) -> List[Dict[str, Any]]:
        """
        Processes document end-to-end with detailed stage logging:
        PDF received -> Page count -> Text extraction -> Page classification -> Structured extraction
        """
        # Stage 1: PDF received
        fname = os.path.basename(file_path)
        print(f"\n[TRACE Pipeline] 1. PDF received: {fname} (Path: {file_path})")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input document not found at: {file_path}")

        # Stage 2: Page count & Splitting
        try:
            pages = DocumentExtractor.split_pdf_pages(file_path, output_dir=output_dir)
            total_pages = len(pages)
            print(f"[TRACE Pipeline] 2. Page count: {total_pages} page(s) detected and split")
        except Exception as e:
            raise RuntimeError(f"Failed during page splitting and inspection: {str(e)}")

        # Stage 3: Text extraction & Stage 4/5: Classification and Structured extraction per page
        processed_pages = []
        for p in pages:
            p_num = p["page_number"]
            p_txt = p.get("raw_text", "")
            print(f"[TRACE Pipeline] 3. Text extraction: Page {p_num} extracted {len(p_txt)} characters ({len(p.get('lines', []))} lines)")
            
            # Stage 4: Page classification & Stage 5: Structured extraction
            res = DocumentProcessingService.process_single_page(p, user_doc_type=user_doc_type)
            print(f"[TRACE Pipeline] 4. Page classification: Page {p_num} -> {res['doc_type']} (Confidence: {res['classification_confidence']:.2%})")
            items_count = len(res.get("parsed_data", {}).get("items", []))
            doc_num = res.get("parsed_data", {}).get("document_number", "N/A")
            print(f"[TRACE Pipeline] 5. Structured extraction: Page {p_num} Doc No: {doc_num}, Items: {items_count}, Total: ₹{res.get('parsed_data', {}).get('grand_total', '0.00')}")
            processed_pages.append(res)

        return processed_pages

    @staticmethod
    def process_document(file_path: str, user_doc_type: str = None) -> Dict[str, Any]:
        """
        Backward compatible single document processor.
        """
        results = DocumentProcessingService.process_multi_page_document(file_path, user_doc_type=user_doc_type)
        if len(results) == 1:
            return results[0]
        # Return merged view for single-dict callers
        primary = results[0]
        all_text = "\n\n".join([r["raw_text"] for r in results])
        return {
            "doc_type": primary["doc_type"],
            "classification_confidence": primary["classification_confidence"],
            "page_count": len(results),
            "raw_text": all_text,
            "parsed_data": primary["parsed_data"],
            "all_pages": results
        }

