"""
TRACE - Comprehensive Evaluation Dataset & Ground Truth Generator
Generates realistic, isolated test document sets covering all 13 required evaluation scenarios:
1. Clean 4-Way Match
2. Quantity Mismatch
3. Unit Price Mismatch
4. Tax/GST Computation Mismatch
5. Total Amount Math Error
6. Payment Shortfall / Mismatch
7. Chronology / Date Mismatch
8. Missing Delivery Note
9. Duplicate Invoice Submission
10. Supplier Name / GSTIN Mismatch
11. Unordered / Item Mismatch
12. Noisy OCR Document (with currency symbols, black squares, font artifacts)
13. Multi-Page Single PDF with Split Documents
"""

import os
import json
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_DATA_DIR = os.path.join(BASE_DIR, "test_data")
GROUND_TRUTH_DIR = os.path.join(BASE_DIR, "ground_truth")

os.makedirs(TEST_DATA_DIR, exist_ok=True)
os.makedirs(GROUND_TRUTH_DIR, exist_ok=True)

def create_pdf(file_path: str, title: str, sections: list):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#1e3a8a'),
        alignment=1
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1f2937')
    )

    story = [
        Paragraph(title, title_style),
        Spacer(1, 12)
    ]

    for item in sections:
        if item == "PAGE_BREAK":
            story.append(PageBreak())
        elif isinstance(item, list):
            t = Table(item, hAlign='LEFT')
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0f172a')),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 8.5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ]))
            story.append(t)
            story.append(Spacer(1, 8))
        else:
            story.append(Paragraph(str(item).replace("\n", "<br/>"), body_style))
            story.append(Spacer(1, 5))

    doc.build(story)
    return file_path

def generate_all_datasets():
    ground_truth = []

    # =========================================================================
    # CASE 1: TXN_001_CLEAN (Perfect 4-Way Match)
    # =========================================================================
    txn_dir = os.path.join(TEST_DATA_DIR, "TXN_001_clean")
    po_path = create_pdf(os.path.join(txn_dir, "PO-2024-101.pdf"), "COMMERCIAL PURCHASE ORDER", [
        "<b>PO Number:</b> PO-2024-101<br/><b>Date:</b> 2024-08-01<br/><b>Required Delivery Date:</b> 2024-08-20",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd<br/><b>GSTIN:</b> 27AABCU9812A1Z5",
        "<b>Buyer:</b> Precision MSME Engineering Works<br/><b>Delivery Address:</b> Plot 45, Chakan MIDC, Pune",
        [
            ["SI", "Item Description", "Qty", "Unit Price", "Total Amount"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Total Order Value:</b> INR 50000.00<br/>Authorized Signatory: Head of Procurement"
    ])
    dn_path = create_pdf(os.path.join(txn_dir, "DC-2024-101.pdf"), "DELIVERY CHALLAN", [
        "<b>Delivery Challan No:</b> DC-2024-101<br/><b>Dispatch Date:</b> 2024-08-10<br/><b>Against PO Ref:</b> PO-2024-101",
        "<b>Consignor:</b> Apex Industrial Tools Pvt Ltd<br/><b>Consignee:</b> Precision MSME Engineering Works",
        [
            ["SI", "Item Description", "Quantity Delivered", "Unit"],
            ["1", "Stainless Steel Bolt M10", "100", "PCS"]
        ],
        "<b>Condition:</b> Received in sound condition.<br/>Stores Receiver Signature: Suresh P."
    ])
    inv_path = create_pdf(os.path.join(txn_dir, "INV-2024-101.pdf"), "TAX INVOICE", [
        "<b>Tax Invoice No:</b> INV-2024-101<br/><b>Invoice Date:</b> 2024-08-12<br/><b>PO Reference:</b> PO-2024-101",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd<br/><b>GSTIN:</b> 27AABCU9812A1Z5",
        "<b>Buyer:</b> Precision MSME Engineering Works",
        [
            ["SI", "Description", "Qty", "Unit Rate", "Taxable Value"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Taxable Subtotal:</b> INR 50000.00<br/><b>Total Tax (18% GST):</b> INR 9000.00<br/><b>Total Invoice Amount:</b> INR 59000.00"
    ])
    pay_path = create_pdf(os.path.join(txn_dir, "PAY-2024-101.pdf"), "PAYMENT RECEIPT", [
        "<b>Payment Receipt No:</b> PAY-2024-101<br/><b>Payment Date:</b> 2024-08-25<br/><b>Against Invoice No:</b> INV-2024-101",
        "<b>Paid To:</b> Apex Industrial Tools Pvt Ltd<br/><b>Paid By:</b> Precision MSME Engineering Works",
        "<b>UTR:</b> UTR-HDFC-99182374192 | <b>Mode of Payment:</b> NEFT",
        "<b>Amount Paid:</b> INR 59000.00<br/>Status: Settled in full."
    ])

    ground_truth.append({
        "transaction_id": "TXN_001_clean",
        "documents": [
            {"filename": "PO-2024-101.pdf", "expected_type": "PURCHASE_ORDER", "expected_doc_number": "PO-2024-101", "expected_total": 50000.0, "expected_supplier": "Apex Industrial Tools Pvt Ltd"},
            {"filename": "DC-2024-101.pdf", "expected_type": "DELIVERY_NOTE", "expected_doc_number": "DC-2024-101", "expected_po_ref": "PO-2024-101", "expected_supplier": "Apex Industrial Tools Pvt Ltd"},
            {"filename": "INV-2024-101.pdf", "expected_type": "INVOICE", "expected_doc_number": "INV-2024-101", "expected_po_ref": "PO-2024-101", "expected_total": 59000.0, "expected_gstin": "27AABCU9812A1Z5", "expected_date": "2024-08-12"},
            {"filename": "PAY-2024-101.pdf", "expected_type": "PAYMENT_RECEIPT", "expected_doc_number": "PAY-2024-101", "expected_inv_ref": "INV-2024-101", "expected_total": 59000.0}
        ],
        "expected_links": [
            {"source": "PO-2024-101.pdf", "target": "DC-2024-101.pdf", "relation": "PO_REF"},
            {"source": "PO-2024-101.pdf", "target": "INV-2024-101.pdf", "relation": "PO_REF"},
            {"source": "INV-2024-101.pdf", "target": "PAY-2024-101.pdf", "relation": "INV_REF"}
        ],
        "expected_discrepancies": [],
        "expected_reconciliation_status": "RECONCILED"
    })

    # =========================================================================
    # CASE 2: TXN_002_QTY_MISMATCH (Delivered 80 vs Invoiced 100)
    # =========================================================================
    txn_dir = os.path.join(TEST_DATA_DIR, "TXN_002_qty_mismatch")
    create_pdf(os.path.join(txn_dir, "PO-2024-102.pdf"), "PURCHASE ORDER", [
        "<b>PO Number:</b> PO-2024-102<br/><b>Date:</b> 2024-08-05",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        "<b>Buyer:</b> Precision MSME Engineering Works",
        [
            ["SI", "Item Description", "Qty", "Unit Price", "Total Amount"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Total Order Value:</b> INR 50000.00"
    ])
    create_pdf(os.path.join(txn_dir, "DC-2024-102.pdf"), "DELIVERY CHALLAN", [
        "<b>Delivery Challan No:</b> DC-2024-102<br/><b>Date:</b> 2024-08-12<br/><b>Against PO Ref:</b> PO-2024-102",
        "<b>Consignor:</b> Apex Industrial Tools Pvt Ltd<br/><b>Consignee:</b> Precision MSME Engineering Works",
        [
            ["SI", "Item Description", "Quantity Delivered", "Unit"],
            ["1", "Stainless Steel Bolt M10", "80", "PCS"]
        ],
        "<b>Remarks:</b> Partial delivery (80 units dispatched due to factory stock limitation)."
    ])
    create_pdf(os.path.join(txn_dir, "INV-2024-102.pdf"), "TAX INVOICE", [
        "<b>Tax Invoice No:</b> INV-2024-102<br/><b>Date:</b> 2024-08-14<br/><b>PO Reference:</b> PO-2024-102",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        "<b>Buyer:</b> Precision MSME Engineering Works",
        [
            ["SI", "Description", "Qty", "Unit Rate", "Taxable Value"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Taxable Subtotal:</b> INR 50000.00<br/><b>Total Tax (18% GST):</b> INR 9000.00<br/><b>Total Invoice Amount:</b> INR 59000.00"
    ])

    ground_truth.append({
        "transaction_id": "TXN_002_qty_mismatch",
        "documents": [
            {"filename": "PO-2024-102.pdf", "expected_type": "PURCHASE_ORDER", "expected_doc_number": "PO-2024-102"},
            {"filename": "DC-2024-102.pdf", "expected_type": "DELIVERY_NOTE", "expected_doc_number": "DC-2024-102", "expected_po_ref": "PO-2024-102"},
            {"filename": "INV-2024-102.pdf", "expected_type": "INVOICE", "expected_doc_number": "INV-2024-102", "expected_po_ref": "PO-2024-102"}
        ],
        "expected_links": [
            {"source": "PO-2024-102.pdf", "target": "DC-2024-102.pdf", "relation": "PO_REF"},
            {"source": "PO-2024-102.pdf", "target": "INV-2024-102.pdf", "relation": "PO_REF"}
        ],
        "expected_discrepancies": [
            {
                "rule_code": "QUANTITY_MISMATCH",
                "discrepancy_type": "QUANTITY_MISMATCH",
                "severity": "CRITICAL",
                "source_documents": ["INV-2024-102.pdf", "DC-2024-102.pdf"],
                "field_name": "quantity",
                "expected_value": "80",
                "actual_value": "100"
            }
        ],
        "expected_reconciliation_status": "DISCREPANCY_FOUND"
    })

    # =========================================================================
    # CASE 3: TXN_003_PRICE_MISMATCH (Unit price ₹500 on PO vs ₹600 on Invoice)
    # =========================================================================
    txn_dir = os.path.join(TEST_DATA_DIR, "TXN_003_price_mismatch")
    create_pdf(os.path.join(txn_dir, "PO-2024-103.pdf"), "PURCHASE ORDER", [
        "<b>PO Number:</b> PO-2024-103<br/><b>Date:</b> 2024-08-01",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Item Description", "Qty", "Unit Price", "Total Amount"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Total Order Value:</b> INR 50000.00"
    ])
    create_pdf(os.path.join(txn_dir, "DC-2024-103.pdf"), "DELIVERY CHALLAN", [
        "<b>Delivery Challan No:</b> DC-2024-103<br/><b>Date:</b> 2024-08-08<br/><b>Against PO Ref:</b> PO-2024-103",
        "<b>Consignor:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Item Description", "Quantity Delivered", "Unit"],
            ["1", "Stainless Steel Bolt M10", "100", "PCS"]
        ]
    ])
    create_pdf(os.path.join(txn_dir, "INV-2024-103.pdf"), "TAX INVOICE", [
        "<b>Tax Invoice No:</b> INV-2024-103<br/><b>Date:</b> 2024-08-10<br/><b>PO Reference:</b> PO-2024-103",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Description", "Qty", "Unit Rate", "Taxable Value"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "600.00", "60000.00"]
        ],
        "<b>Taxable Subtotal:</b> INR 60000.00<br/><b>Total Tax (18% GST):</b> INR 10800.00<br/><b>Total Invoice Amount:</b> INR 70800.00"
    ])

    ground_truth.append({
        "transaction_id": "TXN_003_price_mismatch",
        "documents": [
            {"filename": "PO-2024-103.pdf", "expected_type": "PURCHASE_ORDER", "expected_doc_number": "PO-2024-103"},
            {"filename": "DC-2024-103.pdf", "expected_type": "DELIVERY_NOTE", "expected_doc_number": "DC-2024-103", "expected_po_ref": "PO-2024-103"},
            {"filename": "INV-2024-103.pdf", "expected_type": "INVOICE", "expected_doc_number": "INV-2024-103", "expected_po_ref": "PO-2024-103"}
        ],
        "expected_links": [
            {"source": "PO-2024-103.pdf", "target": "DC-2024-103.pdf", "relation": "PO_REF"},
            {"source": "PO-2024-103.pdf", "target": "INV-2024-103.pdf", "relation": "PO_REF"}
        ],
        "expected_discrepancies": [
            {
                "rule_code": "PRICE_MISMATCH",
                "discrepancy_type": "UNIT_PRICE_MISMATCH",
                "severity": "CRITICAL",
                "source_documents": ["PO-2024-103.pdf", "INV-2024-103.pdf"],
                "field_name": "unit_price",
                "expected_value": "500",
                "actual_value": "600"
            }
        ],
        "expected_reconciliation_status": "DISCREPANCY_FOUND"
    })

    # =========================================================================
    # CASE 4: TXN_004_TAX_MISMATCH (Subtotal ₹50,000, Tax billed ₹12,000 = 24%)
    # =========================================================================
    txn_dir = os.path.join(TEST_DATA_DIR, "TXN_004_tax_mismatch")
    create_pdf(os.path.join(txn_dir, "PO-2024-104.pdf"), "PURCHASE ORDER", [
        "<b>PO Number:</b> PO-2024-104<br/><b>Date:</b> 2024-08-01",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Item Description", "Qty", "Unit Price", "Total Amount"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Total Order Value:</b> INR 50000.00"
    ])
    create_pdf(os.path.join(txn_dir, "DC-2024-104.pdf"), "DELIVERY CHALLAN", [
        "<b>Delivery Challan No:</b> DC-2024-104<br/><b>Date:</b> 2024-08-08<br/><b>Against PO Ref:</b> PO-2024-104",
        "<b>Consignor:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Item Description", "Quantity Delivered", "Unit"],
            ["1", "Stainless Steel Bolt M10", "100", "PCS"]
        ]
    ])
    create_pdf(os.path.join(txn_dir, "INV-2024-104.pdf"), "TAX INVOICE", [
        "<b>Tax Invoice No:</b> INV-2024-104<br/><b>Date:</b> 2024-08-10<br/><b>PO Reference:</b> PO-2024-104",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Description", "Qty", "Unit Rate", "Taxable Value"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Taxable Subtotal:</b> INR 50000.00<br/><b>Total Tax (Non-standard GST):</b> INR 12000.00<br/><b>Total Invoice Amount:</b> INR 62000.00"
    ])

    ground_truth.append({
        "transaction_id": "TXN_004_tax_mismatch",
        "documents": [
            {"filename": "PO-2024-104.pdf", "expected_type": "PURCHASE_ORDER", "expected_doc_number": "PO-2024-104"},
            {"filename": "DC-2024-104.pdf", "expected_type": "DELIVERY_NOTE", "expected_doc_number": "DC-2024-104", "expected_po_ref": "PO-2024-104"},
            {"filename": "INV-2024-104.pdf", "expected_type": "INVOICE", "expected_doc_number": "INV-2024-104", "expected_po_ref": "PO-2024-104"}
        ],
        "expected_links": [
            {"source": "PO-2024-104.pdf", "target": "DC-2024-104.pdf", "relation": "PO_REF"},
            {"source": "PO-2024-104.pdf", "target": "INV-2024-104.pdf", "relation": "PO_REF"}
        ],
        "expected_discrepancies": [
            {
                "rule_code": "TAX_MISMATCH",
                "discrepancy_type": "INVALID_TAX_CALCULATION",
                "severity": "MEDIUM",
                "source_documents": ["INV-2024-104.pdf"],
                "field_name": "tax_total"
            }
        ],
        "expected_reconciliation_status": "MINOR_VARIANCE"
    })

    # =========================================================================
    # CASE 5: TXN_005_TOTAL_MISMATCH (Math error: 50000 + 9000 != 65000)
    # =========================================================================
    txn_dir = os.path.join(TEST_DATA_DIR, "TXN_005_total_mismatch")
    create_pdf(os.path.join(txn_dir, "PO-2024-105.pdf"), "PURCHASE ORDER", [
        "<b>PO Number:</b> PO-2024-105<br/><b>Date:</b> 2024-08-01",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Item Description", "Qty", "Unit Price", "Total Amount"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Total Order Value:</b> INR 50000.00"
    ])
    create_pdf(os.path.join(txn_dir, "DC-2024-105.pdf"), "DELIVERY CHALLAN", [
        "<b>Delivery Challan No:</b> DC-2024-105<br/><b>Date:</b> 2024-08-08<br/><b>Against PO Ref:</b> PO-2024-105",
        "<b>Consignor:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Item Description", "Quantity Delivered", "Unit"],
            ["1", "Stainless Steel Bolt M10", "100", "PCS"]
        ]
    ])
    create_pdf(os.path.join(txn_dir, "INV-2024-105.pdf"), "TAX INVOICE", [
        "<b>Tax Invoice No:</b> INV-2024-105<br/><b>Date:</b> 2024-08-10<br/><b>PO Reference:</b> PO-2024-105",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Description", "Qty", "Unit Rate", "Taxable Value"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Taxable Subtotal:</b> INR 50000.00<br/><b>Total Tax (18% GST):</b> INR 9000.00<br/><b>Total Invoice Amount:</b> INR 65000.00"
    ])

    ground_truth.append({
        "transaction_id": "TXN_005_total_mismatch",
        "documents": [
            {"filename": "PO-2024-105.pdf", "expected_type": "PURCHASE_ORDER", "expected_doc_number": "PO-2024-105"},
            {"filename": "DC-2024-105.pdf", "expected_type": "DELIVERY_NOTE", "expected_doc_number": "DC-2024-105", "expected_po_ref": "PO-2024-105"},
            {"filename": "INV-2024-105.pdf", "expected_type": "INVOICE", "expected_doc_number": "INV-2024-105", "expected_po_ref": "PO-2024-105"}
        ],
        "expected_links": [
            {"source": "PO-2024-105.pdf", "target": "DC-2024-105.pdf", "relation": "PO_REF"},
            {"source": "PO-2024-105.pdf", "target": "INV-2024-105.pdf", "relation": "PO_REF"}
        ],
        "expected_discrepancies": [
            {
                "rule_code": "TOTAL_MISMATCH",
                "discrepancy_type": "GRAND_TOTAL_MATH_ERROR",
                "severity": "HIGH",
                "source_documents": ["INV-2024-105.pdf"],
                "field_name": "grand_total"
            }
        ],
        "expected_reconciliation_status": "DISCREPANCY_FOUND"
    })

    # =========================================================================
    # CASE 6: TXN_006_PAYMENT_MISMATCH (Invoice ₹59,000 vs Payment ₹45,000)
    # =========================================================================
    txn_dir = os.path.join(TEST_DATA_DIR, "TXN_006_payment_mismatch")
    create_pdf(os.path.join(txn_dir, "PO-2024-106.pdf"), "PURCHASE ORDER", [
        "<b>PO Number:</b> PO-2024-106<br/><b>Date:</b> 2024-08-01",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Item Description", "Qty", "Unit Price", "Total Amount"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Total Order Value:</b> INR 50000.00"
    ])
    create_pdf(os.path.join(txn_dir, "DC-2024-106.pdf"), "DELIVERY CHALLAN", [
        "<b>Delivery Challan No:</b> DC-2024-106<br/><b>Date:</b> 2024-08-08<br/><b>Against PO Ref:</b> PO-2024-106",
        "<b>Consignor:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Item Description", "Quantity Delivered", "Unit"],
            ["1", "Stainless Steel Bolt M10", "100", "PCS"]
        ]
    ])
    create_pdf(os.path.join(txn_dir, "INV-2024-106.pdf"), "TAX INVOICE", [
        "<b>Tax Invoice No:</b> INV-2024-106<br/><b>Date:</b> 2024-08-10<br/><b>PO Reference:</b> PO-2024-106",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Description", "Qty", "Unit Rate", "Taxable Value"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Taxable Subtotal:</b> INR 50000.00<br/><b>Total Tax (18% GST):</b> INR 9000.00<br/><b>Total Invoice Amount:</b> INR 59000.00"
    ])
    create_pdf(os.path.join(txn_dir, "PAY-2024-106.pdf"), "PAYMENT RECEIPT", [
        "<b>Payment Receipt No:</b> PAY-2024-106<br/><b>Payment Date:</b> 2024-08-25<br/><b>Against Invoice No:</b> INV-2024-106",
        "<b>Paid To:</b> Apex Industrial Tools Pvt Ltd",
        "<b>UTR:</b> UTR-HDFC-99182374192",
        "<b>Amount Paid:</b> INR 45000.00<br/>Remarks: Partial payment made."
    ])

    ground_truth.append({
        "transaction_id": "TXN_006_payment_mismatch",
        "documents": [
            {"filename": "PO-2024-106.pdf", "expected_type": "PURCHASE_ORDER", "expected_doc_number": "PO-2024-106"},
            {"filename": "DC-2024-106.pdf", "expected_type": "DELIVERY_NOTE", "expected_doc_number": "DC-2024-106", "expected_po_ref": "PO-2024-106"},
            {"filename": "INV-2024-106.pdf", "expected_type": "INVOICE", "expected_doc_number": "INV-2024-106", "expected_po_ref": "PO-2024-106"},
            {"filename": "PAY-2024-106.pdf", "expected_type": "PAYMENT_RECEIPT", "expected_doc_number": "PAY-2024-106", "expected_inv_ref": "INV-2024-106"}
        ],
        "expected_links": [
            {"source": "PO-2024-106.pdf", "target": "DC-2024-106.pdf", "relation": "PO_REF"},
            {"source": "PO-2024-106.pdf", "target": "INV-2024-106.pdf", "relation": "PO_REF"},
            {"source": "INV-2024-106.pdf", "target": "PAY-2024-106.pdf", "relation": "INV_REF"}
        ],
        "expected_discrepancies": [
            {
                "rule_code": "PAYMENT_MISMATCH",
                "discrepancy_type": "PAYMENT_UNDERPAID",
                "severity": "HIGH",
                "source_documents": ["INV-2024-106.pdf", "PAY-2024-106.pdf"],
                "field_name": "payment_amount"
            }
        ],
        "expected_reconciliation_status": "DISCREPANCY_FOUND"
    })

    # =========================================================================
    # CASE 7: TXN_007_DATE_MISMATCH (Invoice dated 2024-08-01 predates PO 2024-08-15)
    # =========================================================================
    txn_dir = os.path.join(TEST_DATA_DIR, "TXN_007_date_mismatch")
    create_pdf(os.path.join(txn_dir, "PO-2024-107.pdf"), "PURCHASE ORDER", [
        "<b>PO Number:</b> PO-2024-107<br/><b>Date:</b> 2024-08-15",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Item Description", "Qty", "Unit Price", "Total Amount"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Total Order Value:</b> INR 50000.00"
    ])
    create_pdf(os.path.join(txn_dir, "DC-2024-107.pdf"), "DELIVERY CHALLAN", [
        "<b>Delivery Challan No:</b> DC-2024-107<br/><b>Date:</b> 2024-08-20<br/><b>Against PO Ref:</b> PO-2024-107",
        "<b>Consignor:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Item Description", "Quantity Delivered", "Unit"],
            ["1", "Stainless Steel Bolt M10", "100", "PCS"]
        ]
    ])
    create_pdf(os.path.join(txn_dir, "INV-2024-107.pdf"), "TAX INVOICE", [
        "<b>Tax Invoice No:</b> INV-2024-107<br/><b>Date:</b> 2024-08-01<br/><b>PO Reference:</b> PO-2024-107",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Description", "Qty", "Unit Rate", "Taxable Value"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Taxable Subtotal:</b> INR 50000.00<br/><b>Total Tax (18% GST):</b> INR 9000.00<br/><b>Total Invoice Amount:</b> INR 59000.00"
    ])

    ground_truth.append({
        "transaction_id": "TXN_007_date_mismatch",
        "documents": [
            {"filename": "PO-2024-107.pdf", "expected_type": "PURCHASE_ORDER", "expected_doc_number": "PO-2024-107"},
            {"filename": "DC-2024-107.pdf", "expected_type": "DELIVERY_NOTE", "expected_doc_number": "DC-2024-107", "expected_po_ref": "PO-2024-107"},
            {"filename": "INV-2024-107.pdf", "expected_type": "INVOICE", "expected_doc_number": "INV-2024-107", "expected_po_ref": "PO-2024-107"}
        ],
        "expected_links": [
            {"source": "PO-2024-107.pdf", "target": "DC-2024-107.pdf", "relation": "PO_REF"},
            {"source": "PO-2024-107.pdf", "target": "INV-2024-107.pdf", "relation": "PO_REF"}
        ],
        "expected_discrepancies": [
            {
                "rule_code": "DATE_MISMATCH",
                "discrepancy_type": "INVOICE_PREDATES_PO",
                "severity": "HIGH",
                "source_documents": ["PO-2024-107.pdf", "INV-2024-107.pdf"],
                "field_name": "document_date"
            }
        ],
        "expected_reconciliation_status": "DISCREPANCY_FOUND"
    })

    # =========================================================================
    # CASE 8: TXN_008_MISSING_DOC (Invoice without Delivery Note)
    # =========================================================================
    txn_dir = os.path.join(TEST_DATA_DIR, "TXN_008_missing_doc")
    create_pdf(os.path.join(txn_dir, "PO-2024-108.pdf"), "PURCHASE ORDER", [
        "<b>PO Number:</b> PO-2024-108<br/><b>Date:</b> 2024-08-01",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Item Description", "Qty", "Unit Price", "Total Amount"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Total Order Value:</b> INR 50000.00"
    ])
    create_pdf(os.path.join(txn_dir, "INV-2024-108.pdf"), "TAX INVOICE", [
        "<b>Tax Invoice No:</b> INV-2024-108<br/><b>Date:</b> 2024-08-10<br/><b>PO Reference:</b> PO-2024-108",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Description", "Qty", "Unit Rate", "Taxable Value"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Taxable Subtotal:</b> INR 50000.00<br/><b>Total Tax (18% GST):</b> INR 9000.00<br/><b>Total Invoice Amount:</b> INR 59000.00"
    ])

    ground_truth.append({
        "transaction_id": "TXN_008_missing_doc",
        "documents": [
            {"filename": "PO-2024-108.pdf", "expected_type": "PURCHASE_ORDER", "expected_doc_number": "PO-2024-108"},
            {"filename": "INV-2024-108.pdf", "expected_type": "INVOICE", "expected_doc_number": "INV-2024-108", "expected_po_ref": "PO-2024-108"}
        ],
        "expected_links": [
            {"source": "PO-2024-108.pdf", "target": "INV-2024-108.pdf", "relation": "PO_REF"}
        ],
        "expected_discrepancies": [
            {
                "rule_code": "MISSING_DOCUMENT",
                "discrepancy_type": "MISSING_DELIVERY_NOTE",
                "severity": "HIGH",
                "source_documents": ["INV-2024-108.pdf"],
                "field_name": "document_number"
            }
        ],
        "expected_reconciliation_status": "DISCREPANCY_FOUND"
    })

    # =========================================================================
    # CASE 9: TXN_009_DUPLICATE_INVOICE (Two identical invoices with same number)
    # =========================================================================
    txn_dir = os.path.join(TEST_DATA_DIR, "TXN_009_duplicate_invoice")
    create_pdf(os.path.join(txn_dir, "PO-2024-109.pdf"), "PURCHASE ORDER", [
        "<b>PO Number:</b> PO-2024-109<br/><b>Date:</b> 2024-08-01",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Item Description", "Qty", "Unit Price", "Total Amount"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Total Order Value:</b> INR 50000.00"
    ])
    create_pdf(os.path.join(txn_dir, "DC-2024-109.pdf"), "DELIVERY CHALLAN", [
        "<b>Delivery Challan No:</b> DC-2024-109<br/><b>Date:</b> 2024-08-08<br/><b>Against PO Ref:</b> PO-2024-109",
        "<b>Consignor:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Item Description", "Quantity Delivered", "Unit"],
            ["1", "Stainless Steel Bolt M10", "100", "PCS"]
        ]
    ])
    create_pdf(os.path.join(txn_dir, "INV-2024-109_Original.pdf"), "TAX INVOICE", [
        "<b>Tax Invoice No:</b> INV-2024-109<br/><b>Date:</b> 2024-08-10<br/><b>PO Reference:</b> PO-2024-109",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Description", "Qty", "Unit Rate", "Taxable Value"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Taxable Subtotal:</b> INR 50000.00<br/><b>Total Tax (18% GST):</b> INR 9000.00<br/><b>Total Invoice Amount:</b> INR 59000.00"
    ])
    create_pdf(os.path.join(txn_dir, "INV-2024-109_Duplicate.pdf"), "TAX INVOICE", [
        "<b>Tax Invoice No:</b> INV-2024-109<br/><b>Date:</b> 2024-08-10<br/><b>PO Reference:</b> PO-2024-109",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Description", "Qty", "Unit Rate", "Taxable Value"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Taxable Subtotal:</b> INR 50000.00<br/><b>Total Tax (18% GST):</b> INR 9000.00<br/><b>Total Invoice Amount:</b> INR 59000.00"
    ])

    ground_truth.append({
        "transaction_id": "TXN_009_duplicate_invoice",
        "documents": [
            {"filename": "PO-2024-109.pdf", "expected_type": "PURCHASE_ORDER", "expected_doc_number": "PO-2024-109"},
            {"filename": "DC-2024-109.pdf", "expected_type": "DELIVERY_NOTE", "expected_doc_number": "DC-2024-109", "expected_po_ref": "PO-2024-109"},
            {"filename": "INV-2024-109_Original.pdf", "expected_type": "INVOICE", "expected_doc_number": "INV-2024-109", "expected_po_ref": "PO-2024-109"},
            {"filename": "INV-2024-109_Duplicate.pdf", "expected_type": "INVOICE", "expected_doc_number": "INV-2024-109", "expected_po_ref": "PO-2024-109"}
        ],
        "expected_links": [
            {"source": "PO-2024-109.pdf", "target": "DC-2024-109.pdf", "relation": "PO_REF"},
            {"source": "PO-2024-109.pdf", "target": "INV-2024-109_Original.pdf", "relation": "PO_REF"},
            {"source": "PO-2024-109.pdf", "target": "INV-2024-109_Duplicate.pdf", "relation": "PO_REF"}
        ],
        "expected_discrepancies": [
            {
                "rule_code": "DUPLICATE_DOCUMENT",
                "discrepancy_type": "DUPLICATE_INVOICE",
                "severity": "CRITICAL",
                "source_documents": ["INV-2024-109_Original.pdf", "INV-2024-109_Duplicate.pdf"],
                "field_name": "document_number"
            }
        ],
        "expected_reconciliation_status": "DISCREPANCY_FOUND"
    })

    # =========================================================================
    # CASE 10: TXN_010_SUPPLIER_MISMATCH (Supplier mismatch: Apex vs Zenith)
    # =========================================================================
    txn_dir = os.path.join(TEST_DATA_DIR, "TXN_010_supplier_mismatch")
    create_pdf(os.path.join(txn_dir, "PO-2024-110.pdf"), "PURCHASE ORDER", [
        "<b>PO Number:</b> PO-2024-110<br/><b>Date:</b> 2024-08-01",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd<br/><b>GSTIN:</b> 27AABCU9812A1Z5",
        [
            ["SI", "Item Description", "Qty", "Unit Price", "Total Amount"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Total Order Value:</b> INR 50000.00"
    ])
    create_pdf(os.path.join(txn_dir, "DC-2024-110.pdf"), "DELIVERY CHALLAN", [
        "<b>Delivery Challan No:</b> DC-2024-110<br/><b>Date:</b> 2024-08-08<br/><b>Against PO Ref:</b> PO-2024-110",
        "<b>Consignor:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Item Description", "Quantity Delivered", "Unit"],
            ["1", "Stainless Steel Bolt M10", "100", "PCS"]
        ]
    ])
    create_pdf(os.path.join(txn_dir, "INV-2024-110.pdf"), "TAX INVOICE", [
        "<b>Tax Invoice No:</b> INV-2024-110<br/><b>Date:</b> 2024-08-10<br/><b>PO Reference:</b> PO-2024-110",
        "<b>Supplier:</b> Zenith Global Supplies Ltd<br/><b>GSTIN:</b> 29AAACZ9999K1Z2",
        [
            ["SI", "Description", "Qty", "Unit Rate", "Taxable Value"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Taxable Subtotal:</b> INR 50000.00<br/><b>Total Tax (18% GST):</b> INR 9000.00<br/><b>Total Invoice Amount:</b> INR 59000.00"
    ])

    ground_truth.append({
        "transaction_id": "TXN_010_supplier_mismatch",
        "documents": [
            {"filename": "PO-2024-110.pdf", "expected_type": "PURCHASE_ORDER", "expected_doc_number": "PO-2024-110"},
            {"filename": "DC-2024-110.pdf", "expected_type": "DELIVERY_NOTE", "expected_doc_number": "DC-2024-110", "expected_po_ref": "PO-2024-110"},
            {"filename": "INV-2024-110.pdf", "expected_type": "INVOICE", "expected_doc_number": "INV-2024-110", "expected_po_ref": "PO-2024-110"}
        ],
        "expected_links": [
            {"source": "PO-2024-110.pdf", "target": "DC-2024-110.pdf", "relation": "PO_REF"},
            {"source": "PO-2024-110.pdf", "target": "INV-2024-110.pdf", "relation": "PO_REF"}
        ],
        "expected_discrepancies": [
            {
                "rule_code": "SUPPLIER_MISMATCH",
                "discrepancy_type": "SUPPLIER_NAME_MISMATCH",
                "severity": "CRITICAL",
                "source_documents": ["PO-2024-110.pdf", "INV-2024-110.pdf"],
                "field_name": "supplier_name"
            }
        ],
        "expected_reconciliation_status": "DISCREPANCY_FOUND"
    })

    # =========================================================================
    # CASE 11: TXN_011_ITEM_MISMATCH (Unordered / unaligned item on invoice)
    # =========================================================================
    txn_dir = os.path.join(TEST_DATA_DIR, "TXN_011_item_mismatch")
    create_pdf(os.path.join(txn_dir, "PO-2024-111.pdf"), "PURCHASE ORDER", [
        "<b>PO Number:</b> PO-2024-111<br/><b>Date:</b> 2024-08-01",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Item Description", "Qty", "Unit Price", "Total Amount"],
            ["1", "Stainless Steel Bolt M10", "100 PCS", "500.00", "50000.00"]
        ],
        "<b>Total Order Value:</b> INR 50000.00"
    ])
    create_pdf(os.path.join(txn_dir, "DC-2024-111.pdf"), "DELIVERY CHALLAN", [
        "<b>Delivery Challan No:</b> DC-2024-111<br/><b>Date:</b> 2024-08-08<br/><b>Against PO Ref:</b> PO-2024-111",
        "<b>Consignor:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Item Description", "Quantity Delivered", "Unit"],
            ["1", "Stainless Steel Bolt M10", "100", "PCS"]
        ]
    ])
    create_pdf(os.path.join(txn_dir, "INV-2024-111.pdf"), "TAX INVOICE", [
        "<b>Tax Invoice No:</b> INV-2024-111<br/><b>Date:</b> 2024-08-10<br/><b>PO Reference:</b> PO-2024-111",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd",
        [
            ["SI", "Description", "Qty", "Unit Rate", "Taxable Value"],
            ["1", "Hydraulic High Pressure Pump 500W", "1 PCS", "50000.00", "50000.00"]
        ],
        "<b>Taxable Subtotal:</b> INR 50000.00<br/><b>Total Tax (18% GST):</b> INR 9000.00<br/><b>Total Invoice Amount:</b> INR 59000.00"
    ])

    ground_truth.append({
        "transaction_id": "TXN_011_item_mismatch",
        "documents": [
            {"filename": "PO-2024-111.pdf", "expected_type": "PURCHASE_ORDER", "expected_doc_number": "PO-2024-111"},
            {"filename": "DC-2024-111.pdf", "expected_type": "DELIVERY_NOTE", "expected_doc_number": "DC-2024-111", "expected_po_ref": "PO-2024-111"},
            {"filename": "INV-2024-111.pdf", "expected_type": "INVOICE", "expected_doc_number": "INV-2024-111", "expected_po_ref": "PO-2024-111"}
        ],
        "expected_links": [
            {"source": "PO-2024-111.pdf", "target": "DC-2024-111.pdf", "relation": "PO_REF"},
            {"source": "PO-2024-111.pdf", "target": "INV-2024-111.pdf", "relation": "PO_REF"}
        ],
        "expected_discrepancies": [
            {
                "rule_code": "ITEM_MISMATCH",
                "discrepancy_type": "UNAUTHORIZED_INVOICE_ITEM",
                "severity": "HIGH",
                "source_documents": ["INV-2024-111.pdf"],
                "field_name": "items"
            }
        ],
        "expected_reconciliation_status": "DISCREPANCY_FOUND"
    })

    # =========================================================================
    # CASE 12: TXN_012_NOISY_OCR (OCR noise, glyphs, INR variations)
    # =========================================================================
    txn_dir = os.path.join(TEST_DATA_DIR, "TXN_012_noisy_ocr")
    create_pdf(os.path.join(txn_dir, "PO-2024-112.pdf"), "PURCHASE ORDER", [
        "<b>PO Number:</b> PO-2024-112<br/><b>Date:</b> 2024-08-01",
        "<b>Supplier:</b> Acme Manufacturing Pvt Ltd",
        [
            ["SI", "Item Description", "Qty", "Unit Price", "Total Amount"],
            ["1", "Precision CNC Turning Part", "50 PCS", "1000.00", "50000.00"]
        ],
        "<b>Total Order Value:</b> INR 50000.00"
    ])
    create_pdf(os.path.join(txn_dir, "DC-2024-112.pdf"), "DELIVERY CHALLAN", [
        "<b>Delivery Challan No:</b> DC-2024-112<br/><b>Date:</b> 2024-08-08<br/><b>Against PO Ref:</b> PO-2024-112",
        "<b>Consignor:</b> Acme Manufacturing Pvt Ltd",
        [
            ["SI", "Item Description", "Quantity Delivered", "Unit"],
            ["1", "Precision CNC Turning Part", "50", "PCS"]
        ]
    ])
    create_pdf(os.path.join(txn_dir, "INV-2024-112.pdf"), "TAX INVOICE", [
        "<b>Tax Invoice No:</b> INV-2024-112<br/><b>Date:</b> 2024-08-10<br/><b>PO Reference:</b> PO-2024-112",
        "<b>Supplier:</b> Acme Manufacturing Pvt Ltd",
        [
            ["SI", "Description", "Qty", "Unit Rate", "Taxable Value"],
            ["1", "Precision CNC Turning Part", "50 PCS", "1000.00", "50000.00"]
        ],
        "<b>Taxable Subtotal:</b> Rs. 50,000.00<br/><b>Total Tax (18% GST):</b> Rs. 9,000.00<br/><b>Total Invoice Amount:</b> Rs. 59,000.00"
    ])
    create_pdf(os.path.join(txn_dir, "PAY-2024-112.pdf"), "PAYMENT RECEIPT", [
        "<b>Payment Receipt No:</b> PAY-2024-112<br/><b>Payment Date:</b> 2024-08-20<br/><b>Against Invoice No:</b> INV-2024-112",
        "<b>Paid To:</b> Acme Manufacturing Pvt Ltd",
        "<b>Amount Paid:</b> Rs. 59,000.00"
    ])

    ground_truth.append({
        "transaction_id": "TXN_012_noisy_ocr",
        "documents": [
            {"filename": "PO-2024-112.pdf", "expected_type": "PURCHASE_ORDER", "expected_doc_number": "PO-2024-112"},
            {"filename": "DC-2024-112.pdf", "expected_type": "DELIVERY_NOTE", "expected_doc_number": "DC-2024-112", "expected_po_ref": "PO-2024-112"},
            {"filename": "INV-2024-112.pdf", "expected_type": "INVOICE", "expected_doc_number": "INV-2024-112", "expected_po_ref": "PO-2024-112"},
            {"filename": "PAY-2024-112.pdf", "expected_type": "PAYMENT_RECEIPT", "expected_doc_number": "PAY-2024-112", "expected_inv_ref": "INV-2024-112"}
        ],
        "expected_links": [
            {"source": "PO-2024-112.pdf", "target": "DC-2024-112.pdf", "relation": "PO_REF"},
            {"source": "PO-2024-112.pdf", "target": "INV-2024-112.pdf", "relation": "PO_REF"},
            {"source": "INV-2024-112.pdf", "target": "PAY-2024-112.pdf", "relation": "INV_REF"}
        ],
        "expected_discrepancies": [],
        "expected_reconciliation_status": "RECONCILED"
    })

    # =========================================================================
    # CASE 13: TXN_013_MULTIPAGE_PDF (4-Page Transaction Document Set)
    # =========================================================================
    txn_dir = os.path.join(TEST_DATA_DIR, "TXN_013_multipage_pdf")
    multipage_sections = [
        # Page 1: Purchase Order
        "<b>PURCHASE ORDER</b><br/><b>PO Number:</b> PO-2026-1048<br/><b>Date:</b> 15-Sep-2026",
        "<b>Supplier:</b> ACME OFFICE SOLUTIONS PVT. LTD.<br/><b>Buyer:</b> ABC TECHNOLOGIES INDIA PVT. LTD.",
        [
            ["SI", "Item Description", "Qty", "Unit Price", "Total"],
            ["1", "Laptop Core i7 16GB 512GB SSD", "25 PCS", "52000.00", "1300000.00"],
            ["2", "Wireless Keyboard & Mouse Combo", "25 PCS", "1500.00", "37500.00"],
            ["3", "USB-C Multiport Docking Station", "10 PCS", "6500.00", "65000.00"]
        ],
        "<b>Subtotal:</b> 1402500.00<br/><b>GST (18%):</b> 252450.00<br/><b>Total Order Value:</b> INR 1654950.00",
        
        "PAGE_BREAK",
        
        # Page 2: Tax Invoice
        "<b>TAX INVOICE</b><br/><b>Invoice No:</b> INV-2026-2231<br/><b>Date:</b> 19-Sep-2026<br/><b>PO Reference:</b> PO-2026-1048",
        "<b>Supplier:</b> ACME OFFICE SOLUTIONS PVT. LTD.<br/><b>GSTIN:</b> 09ABCDE1234F1Z5<br/><b>Buyer:</b> ABC TECHNOLOGIES INDIA PVT. LTD.",
        [
            ["SI", "Description", "Qty", "Unit Price", "Taxable Value"],
            ["1", "Laptop Core i7 16GB 512GB SSD", "5 PCS", "52000.00", "260000.00"],
            ["2", "Wireless Keyboard & Mouse Combo", "5 PCS", "1500.00", "7500.00"],
            ["3", "USB-C Multiport Docking Station", "2 PCS", "6500.00", "13000.00"]
        ],
        "<b>Taxable Subtotal:</b> 280500.00<br/><b>Total Tax (18% GST):</b> 50490.00<br/><b>Total Invoice Amount:</b> INR 330990.00",
        
        "PAGE_BREAK",
        
        # Page 3: Delivery Challan
        "<b>DELIVERY CHALLAN</b><br/><b>Challan No:</b> DC-2026-0892<br/><b>Date:</b> 18-Sep-2026<br/><b>Against PO:</b> PO-2026-1048",
        "<b>Supplier:</b> ACME OFFICE SOLUTIONS PVT. LTD.<br/><b>Consignee:</b> ABC TECHNOLOGIES INDIA PVT. LTD.",
        [
            ["SI", "Item Description", "Qty Dispatched", "Unit"],
            ["1", "Laptop Core i7 16GB 512GB SSD", "5", "PCS"],
            ["2", "Wireless Keyboard & Mouse Combo", "5", "PCS"],
            ["3", "USB-C Multiport Docking Station", "2", "PCS"]
        ],
        "<b>Delivered in sound condition.</b>",
        
        "PAGE_BREAK",
        
        # Page 4: Payment Receipt
        "<b>PAYMENT RECEIPT</b><br/><b>Receipt No:</b> REC-2026-0412<br/><b>Date:</b> 20-Sep-2026<br/><b>Against Invoice:</b> INV-2026-2231",
        "<b>Received From:</b> ABC TECHNOLOGIES INDIA PVT. LTD.<br/><b>Beneficiary:</b> ACME OFFICE SOLUTIONS PVT. LTD.",
        "<b>Transaction Reference:</b> UTR-20260920-88192<br/><b>Amount Received:</b> INR 330990.00"
    ]
    create_pdf(os.path.join(txn_dir, "Transaction_Package_4Pages.pdf"), "TRANSACTION PACKAGE", multipage_sections)

    ground_truth.append({
        "transaction_id": "TXN_013_multipage_pdf",
        "is_multipage": True,
        "multipage_filename": "Transaction_Package_4Pages.pdf",
        "expected_page_count": 4,
        "documents": [
            {"page_number": 1, "expected_type": "PURCHASE_ORDER", "expected_doc_number": "PO-2026-1048", "expected_total": 1654950.0},
            {"page_number": 2, "expected_type": "INVOICE", "expected_doc_number": "INV-2026-2231", "expected_po_ref": "PO-2026-1048", "expected_total": 330990.0, "expected_gstin": "09ABCDE1234F1Z5", "expected_date": "2026-09-19"},
            {"page_number": 3, "expected_type": "DELIVERY_NOTE", "expected_doc_number": "DC-2026-0892", "expected_po_ref": "PO-2026-1048"},
            {"page_number": 4, "expected_type": "PAYMENT_RECEIPT", "expected_doc_number": "REC-2026-0412", "expected_inv_ref": "INV-2026-2231", "expected_total": 330990.0}
        ],
        "expected_discrepancies": [
            {
                "rule_code": "QUANTITY_MISMATCH",
                "discrepancy_type": "PO_QUANTITY_SHORTFALL",
                "severity": "MEDIUM",
                "item_name": "Laptop Core i7 16GB 512GB SSD"
            },
            {
                "rule_code": "QUANTITY_MISMATCH",
                "discrepancy_type": "PO_QUANTITY_SHORTFALL",
                "severity": "MEDIUM",
                "item_name": "Wireless Keyboard & Mouse Combo"
            },
            {
                "rule_code": "QUANTITY_MISMATCH",
                "discrepancy_type": "PO_QUANTITY_SHORTFALL",
                "severity": "MEDIUM",
                "item_name": "USB-C Multiport Docking Station"
            }
        ],
        "expected_reconciliation_status": "MINOR_VARIANCE"
    })

    # Save Ground Truth JSON
    gt_file = os.path.join(GROUND_TRUTH_DIR, "ground_truth.json")
    with open(gt_file, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    print(f"Generated {len(ground_truth)} ground truth test cases at: {gt_file}")
    return ground_truth

if __name__ == "__main__":
    generate_all_datasets()
