"""
TRACE - Multi-Page Document Processing & Reconciliation Pipeline Test
Tests 4-page PDF splitting, independent page classification, structured field extraction,
quantity discrepancy detection against PO, and payment matching verification.
"""

import os
import pytest
from decimal import Decimal
from app.extraction.pdf_extractor import DocumentExtractor
from app.extraction.extractor_service import DocumentProcessingService
from app.extraction.normalizer import normalize_decimal, normalize_date
from app.reconciliation.orchestrator import reconciliation_orchestrator
from app.reconciliation.linker import TransactionLinker
from app.core.database import SessionLocal, init_db
from app.models.document import Document
from app.models.transaction import Transaction

SAMPLE_4PAGE_PDF = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../storage/doc_cdb819b150_sample_invoice_document_set.pdf")
)

def test_currency_and_ocr_glyph_normalization():
    """Requirement 13 & 14: Strip black squares (■), OCR artifacts (I, ?), and currencies."""
    assert normalize_decimal("■3,30,990") == Decimal("330990.00")
    assert normalize_decimal("I52,000") == Decimal("52000.00")
    assert normalize_decimal("I3,30,990") == Decimal("330990.00")
    assert normalize_decimal("?330990") == Decimal("330990.00")
    assert normalize_decimal("₹ 1,500.00") == Decimal("1500.00")
    assert normalize_decimal("Rs. 65,000") == Decimal("65000.00")
    assert normalize_decimal("INR 14,02,500") == Decimal("1402500.00")

def test_date_normalization_alphanumeric():
    """Requirement 8: Normalize alphanumeric dates like 19-Sep-2026."""
    assert normalize_date("19-Sep-2026") == "2026-09-19"
    assert normalize_date("19 Sep 2026") == "2026-09-19"
    assert normalize_date("19/Sep/2026") == "2026-09-19"

def test_multipage_pdf_splitting_and_page_classification():
    """
    Requirements 1, 2, 3, 4, 5, 7:
    - Split multi-page PDF into 4 individual pages.
    - Extract text independently.
    - Page 1 -> purchase_order
    - Page 2 -> invoice
    - Page 3 -> delivery_note
    - Page 4 -> payment_receipt (payment)
    """
    assert os.path.exists(SAMPLE_4PAGE_PDF), f"Test PDF not found at {SAMPLE_4PAGE_PDF}"
    
    pages = DocumentProcessingService.process_multi_page_document(SAMPLE_4PAGE_PDF)
    assert len(pages) == 4, f"Expected 4 split pages, got {len(pages)}"

    # Page 1 = Purchase Order
    p1 = pages[0]
    assert p1["page_number"] == 1
    assert p1["doc_type"] == "PURCHASE_ORDER"
    assert p1["classification_confidence"] > 0.4
    assert len(p1["raw_text"]) > 100

    # Page 2 = Invoice
    p2 = pages[1]
    assert p2["page_number"] == 2
    assert p2["doc_type"] == "INVOICE"
    assert p2["classification_confidence"] > 0.4

    # Page 3 = Delivery Note / Challan
    p3 = pages[2]
    assert p3["page_number"] == 3
    assert p3["doc_type"] == "DELIVERY_NOTE"

    # Page 4 = Payment Receipt
    p4 = pages[3]
    assert p4["page_number"] == 4
    assert p4["doc_type"] == "PAYMENT_RECEIPT"

def test_invoice_field_and_item_extraction():
    """
    Requirements 8 & 9:
    Extract exact invoice fields from page 2:
    - invoice_number = INV-2026-2231
    - invoice_date = 19-Sep-2026 (normalized to 2026-09-19)
    - supplier = ACME OFFICE SOLUTIONS PVT. LTD.
    - buyer = ABC TECHNOLOGIES INDIA PVT. LTD.
    - GSTIN = 09ABCDE1234F1Z5
    - total = 330990
    - line items correctly extracted
    """
    pages = DocumentProcessingService.process_multi_page_document(SAMPLE_4PAGE_PDF)
    inv = pages[1]["parsed_data"]

    assert inv["document_number"] == "INV-2026-2231"
    assert inv["document_date"] == "2026-09-19"
    assert inv["supplier_name"] == "ACME OFFICE SOLUTIONS PVT. LTD."
    assert inv["customer_name"] == "ABC TECHNOLOGIES INDIA PVT. LTD."
    assert inv["supplier_gstin"] == "09ABCDE1234F1Z5"
    assert Decimal(inv["grand_total"]) == Decimal("330990.00")

    # Check 3 line items
    items = inv["items"]
    assert len(items) == 3

    # Item 1: Laptop
    assert "laptop" in items[0]["description"].lower()
    assert Decimal(items[0]["quantity"]) == Decimal("5.00")
    assert Decimal(items[0]["unit_price"]) == Decimal("52000.00")

    # Item 2: Keyboard & Mouse
    assert "keyboard" in items[1]["description"].lower()
    assert Decimal(items[1]["quantity"]) == Decimal("5.00")
    assert Decimal(items[1]["unit_price"]) == Decimal("1500.00")

    # Item 3: Docking Station
    assert "docking" in items[2]["description"].lower()
    assert Decimal(items[2]["quantity"]) == Decimal("2.00")
    assert Decimal(items[2]["unit_price"]) == Decimal("6500.00")

def test_reconciliation_quantity_discrepancies_and_payment_match():
    """
    Requirements 10, 11, 12:
    - Compare invoice against PO.
    - Detect quantity discrepancies:
      * Laptop: PO = 25, Invoice = 5
      * Wireless Keyboard & Mouse: PO = 25, Invoice = 5
      * USB-C Docking Station: PO = 10, Invoice = 2
    - Verify payment matching:
      * Invoice total = 330990, Payment received = 330990 -> Matched (no payment shortfall).
    """
    pages = DocumentProcessingService.process_multi_page_document(SAMPLE_4PAGE_PDF)

    doc_dicts = [
        {
            "id": f"doc_page_{p['page_number']}",
            "filename": f"Sample_Page_{p['page_number']}.pdf",
            "doc_type": p["doc_type"],
            "parsed_data": p["parsed_data"],
            "raw_text": p["raw_text"],
            "page_count": 1,
            "page_number": p["page_number"]
        }
        for p in pages
    ]

    result = reconciliation_orchestrator.reconcile_transaction(
        transaction_ref="PO-2026-1048",
        documents=doc_dicts,
        mode="HYBRID"
    )

    discrepancies = result.get("discrepancies", [])
    
    # 1. Quantity discrepancies against PO
    qty_discs = [d for d in discrepancies if d.get("rule_code") == "QUANTITY_MISMATCH"]
    assert len(qty_discs) >= 3, f"Expected 3 quantity discrepancies, got {len(qty_discs)}"

    laptop_disc = next((d for d in qty_discs if "laptop" in d.get("title", "").lower()), None)
    assert laptop_disc is not None
    assert "25" in str(laptop_disc.get("expected_value", ""))
    assert "5" in str(laptop_disc.get("actual_value", ""))

    kb_disc = next((d for d in qty_discs if "keyboard" in d.get("title", "").lower()), None)
    assert kb_disc is not None
    assert "25" in str(kb_disc.get("expected_value", ""))
    assert "5" in str(kb_disc.get("actual_value", ""))

    dock_disc = next((d for d in qty_discs if "docking" in d.get("title", "").lower()), None)
    assert dock_disc is not None
    assert "10" in str(dock_disc.get("expected_value", ""))
    assert "2" in str(dock_disc.get("actual_value", ""))

    # 2. Payment verification: Matched (no payment shortfall discrepancy)
    pay_discs = [d for d in discrepancies if d.get("rule_code") == "PAYMENT_MISMATCH"]
    assert len(pay_discs) == 0, f"Expected 0 payment shortfall discrepancies (payment matched), found: {pay_discs}"

