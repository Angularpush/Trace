"""
TRACE - Document Segmentation and Boundary Detection
Detects document boundaries within physical files (PDFs, images, text) to satisfy:
FILE != DOCUMENT != TRANSACTION

Supports:
- Single-page single-document
- Multi-page single-document (e.g. 3-page invoice)
- Multi-document combined files (e.g. PO + Invoice + Delivery Note in one PDF)
- Multi-instance documents (e.g. 5 invoices in one PDF)
"""

import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from pypdf import PdfReader, PdfWriter
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

from app.extraction.pdf_extractor import DocumentExtractor
from app.classification.classifier import DocumentClassificationService

@dataclass
class DocumentSegment:
    page_start: int
    page_end: int
    document_type: str
    confidence: float
    classification_method: str
    raw_text: str
    lines: List[str] = field(default_factory=list)
    file_path: str = ""
    document_number_hint: Optional[str] = None
    supplier_hint: Optional[str] = None
    date_hint: Optional[str] = None

class DocumentSegmenter:
    """
    Analyzes physical files page-by-page to detect document boundaries.
    """

    # Strong header signatures indicating a new document boundary
    HEADER_SIGNATURES = {
        "PAYMENT_RECEIPT": [
            r"payment\s+receipt", r"money\s+receipt", r"receipt\s+voucher", r"payment\s+confirmation", r"remittance\s+advice", r"acknowledgement\s+receipt", r"\bpayment\s+receipt\s+no\b"
        ],
        "DELIVERY_NOTE": [
            r"delivery\s+note", r"delivery\s+challan", r"goods\s+received\s+note", r"\bgrn\b", r"packing\s+slip", r"dispatch\s+advice"
        ],
        "CREDIT_NOTE": [
            r"credit\s+note", r"credit\s+memo"
        ],
        "DEBIT_NOTE": [
            r"debit\s+note", r"debit\s+memo"
        ],
        "BANK_STATEMENT": [
            r"bank\s+statement", r"statement\s+of\s+account", r"account\s+statement"
        ],
        "PURCHASE_ORDER": [
            r"purchase\s+order", r"p\.o\.\s*(?:number|no\.?)", r"\bp\.o\.#", r"order\s+confirmation"
        ],
        "QUOTATION": [
            r"quotation", r"price\s+quote", r"proforma\s+invoice"
        ],
        "INVOICE": [
            r"tax\s+invoice", r"commercial\s+invoice", r"(?<!against\s)(?<!ref\s)(?<!for\s)\binvoice\s+no\.?", r"\binvoice\s+#", r"bill\s+to"
        ]
    }

    DOC_NUMBER_PATTERNS = [
        r"(?:Payment\s+Receipt|Receipt|REC|Voucher)(?:\s*(?:No\.?|Number|#))?[:\s\-]*([A-Z0-9\-\/]{3,20})",
        r"(?:Delivery\s+Challan|Delivery\s+Note|Challan|GRN|DN)(?:\s*(?:No\.?|Number|#))?[:\s\-]*([A-Z0-9\-\/]{3,20})",
        r"(?:Purchase\s+Order|PO|P\.O\.)(?:\s*(?:No\.?|Number|#))?[:\s\-]*([A-Z0-9\-\/]{3,20})",
        r"\b(?:Tax\s+Invoice|Commercial\s+Invoice|Invoice|Inv|Bill)(?:\s*(?:No\.?|Number|#))?[:\s\-]*([A-Z0-9\-\/]{3,20})",
        r"(?:Reference|Ref)(?:\s*(?:No\.?|Number|#))?[:\s\-]*([A-Z0-9\-\/]{3,20})",
    ]

    PAGE_X_OF_Y_PATTERN = re.compile(r"page\s+(\d+)\s+(?:of|\/)\s+(\d+)", re.IGNORECASE)

    @classmethod
    def extract_document_number(cls, text: str) -> Optional[str]:
        for pattern in cls.DOC_NUMBER_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                if len(val) >= 3 and not val.lower() in ["date", "number", "total", "amount"]:
                    return val
        return None

    @classmethod
    def detect_header_type(cls, text_top: str) -> Optional[str]:
        # Priority 1: Check top individual lines (titles like 'PAYMENT RECEIPT')
        top_lines = [l.strip() for l in text_top.split("\n")[:4] if l.strip()]
        for line in top_lines:
            for doc_type, regexes in cls.HEADER_SIGNATURES.items():
                for rgx in regexes:
                    if re.search(r"^" + rgx + r"$", line, re.IGNORECASE):
                        return doc_type
        # Priority 2: Check matching regex in full top snippet with priority order
        for doc_type, regexes in cls.HEADER_SIGNATURES.items():
            for rgx in regexes:
                if re.search(rgx, text_top, re.IGNORECASE):
                    return doc_type
        return None

    @classmethod
    def segment_file(cls, file_path: str, output_dir: Optional[str] = None) -> List[DocumentSegment]:
        """
        Segments a physical file into discrete business document units.
        Returns list of DocumentSegment instances.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        extracted = DocumentExtractor.extract(file_path)
        pages = extracted.get("pages", [])
        total_pages = len(pages)

        if total_pages <= 1:
            # Single page document
            text = pages[0]["text"] if pages else extracted.get("raw_text", "")
            lines = pages[0]["lines"] if pages else [l.strip() for l in text.split("\n") if l.strip()]
            
            # Classify
            classification_service = DocumentClassificationService.get_instance()
            header_type = cls.detect_header_type("\n".join(lines[:10]))
            try:
                ml_type, ml_conf, _ = classification_service.classify(text)
            except Exception:
                ml_type, ml_conf = "OTHER", 0.5
            
            final_type = header_type or ml_type
            method = "HEADER_HEURISTIC" if header_type else "ML_CLASSIFIER"
            doc_num = cls.extract_document_number(text)

            return [
                DocumentSegment(
                    page_start=1,
                    page_end=1,
                    document_type=final_type,
                    confidence=1.0 if header_type else ml_conf,
                    classification_method=method,
                    raw_text=text,
                    lines=lines,
                    file_path=file_path,
                    document_number_hint=doc_num
                )
            ]

        # Multi-page file: Perform boundary analysis
        # 1. Inspect each page individually
        page_analyses = []
        classification_service = DocumentClassificationService.get_instance()

        for idx, page in enumerate(pages):
            page_num = idx + 1
            p_text = page.get("text", "")
            p_lines = page.get("lines", [l.strip() for l in p_text.split("\n") if l.strip()])
            top_snippet = "\n".join(p_lines[:12]) if p_lines else ""

            header_type = cls.detect_header_type(top_snippet)
            try:
                ml_type, ml_conf, _ = classification_service.classify(p_text)
            except Exception:
                ml_type, ml_conf = "OTHER", 0.5

            doc_type = header_type or ml_type
            doc_num = cls.extract_document_number(p_text)

            # Check for Page X of Y
            page_x_of_y = None
            page_match = cls.PAGE_X_OF_Y_PATTERN.search(p_text)
            if page_match:
                curr_p = int(page_match.group(1))
                tot_p = int(page_match.group(2))
                page_x_of_y = (curr_p, tot_p)

            page_analyses.append({
                "page_num": page_num,
                "text": p_text,
                "lines": p_lines,
                "header_type": header_type,
                "ml_type": ml_type,
                "doc_type": doc_type,
                "confidence": 0.95 if header_type else ml_conf,
                "classification_method": "HEADER_HEURISTIC" if header_type else "ML_CLASSIFIER",
                "doc_num": doc_num,
                "page_x_of_y": page_x_of_y,
            })

        # 2. Group pages into document boundaries
        # A new document starts if:
        # - Header explicitly declares a different document type
        # - A new distinct document number appears (and doc_num != prev_doc_num)
        # - Explicit "Page 1 of Y" appears when prev page was at the end of a document
        # - Page type changed significantly and confidence is high
        segments: List[List[Dict[str, Any]]] = []
        curr_segment: List[Dict[str, Any]] = [page_analyses[0]]

        for i in range(1, len(page_analyses)):
            curr_page = page_analyses[i]
            prev_page = curr_segment[-1]
            first_page_of_segment = curr_segment[0]

            is_new_doc = False

            # Check 1: Explicit "Page 1 of Y" or "Page 1 / Y"
            if curr_page["page_x_of_y"] and curr_page["page_x_of_y"][0] == 1 and len(curr_segment) > 0:
                is_new_doc = True

            # Check 2: Header type differs from the segment's dominant type
            elif curr_page["header_type"] and curr_page["header_type"] != first_page_of_segment["doc_type"]:
                is_new_doc = True

            # Check 3: New Document number detected that differs from current segment
            elif curr_page["doc_num"] and first_page_of_segment["doc_num"] and curr_page["doc_num"] != first_page_of_segment["doc_num"]:
                is_new_doc = True

            # Check 4: ML Classifier has high confidence in a completely different type
            elif curr_page["ml_type"] != first_page_of_segment["doc_type"] and curr_page["confidence"] > 0.85:
                # Unless it's an continuation page like "Page 2 of 2"
                if not (curr_page["page_x_of_y"] and curr_page["page_x_of_y"][0] > 1):
                    is_new_doc = True

            if is_new_doc:
                segments.append(curr_segment)
                curr_segment = [curr_page]
            else:
                curr_segment.append(curr_page)

        if curr_segment:
            segments.append(curr_segment)

        # 3. Create DocumentSegment objects and extract sub-PDFs if needed
        out_dir = output_dir or os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        results: List[DocumentSegment] = []

        for seg_idx, seg_pages in enumerate(segments):
            p_start = seg_pages[0]["page_num"]
            p_end = seg_pages[-1]["page_num"]
            doc_type = seg_pages[0]["doc_type"]
            conf = seg_pages[0]["confidence"]
            method = seg_pages[0]["classification_method"]
            doc_num = seg_pages[0]["doc_num"]

            combined_text = "\n\n".join([p["text"] for p in seg_pages])
            all_lines = []
            for p in seg_pages:
                all_lines.extend(p["lines"])

            # Save sliced sub-PDF if file has multiple segments
            sub_pdf_path = file_path
            if len(segments) > 1 and file_path.lower().endswith(".pdf"):
                seg_pdf_name = f"{base_name}_seg_{seg_idx + 1}_{doc_type.lower()}_p{p_start}-p{p_end}.pdf"
                sub_pdf_path = os.path.join(out_dir, seg_pdf_name)
                
                try:
                    if PYMUPDF_AVAILABLE:
                        src_doc = fitz.open(file_path)
                        sub_doc = fitz.open()
                        sub_doc.insert_pdf(src_doc, from_page=p_start - 1, to_page=p_end - 1)
                        sub_doc.save(sub_pdf_path)
                        sub_doc.close()
                        src_doc.close()
                    elif PYPDF_AVAILABLE:
                        reader = PdfReader(file_path)
                        writer = PdfWriter()
                        for p in range(p_start - 1, p_end):
                            writer.add_page(reader.pages[p])
                        with open(sub_pdf_path, "wb") as f_out:
                            writer.write(f_out)
                except Exception as e:
                    print(f"[DocumentSegmenter] Error slicing sub-PDF: {e}")
                    sub_pdf_path = file_path

            results.append(DocumentSegment(
                page_start=p_start,
                page_end=p_end,
                document_type=doc_type,
                confidence=conf,
                classification_method=method,
                raw_text=combined_text,
                lines=all_lines,
                file_path=sub_pdf_path,
                document_number_hint=doc_num
            ))

        return results

document_segmenter = DocumentSegmenter()
