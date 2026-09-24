"""
TRACE - Ground Truth Benchmark Dataset Generator
Generates 39 realistic annotated MSME transactions across 15 discrepancy categories
to evaluate and compare Rule-Based, AI/LLM, and Hybrid reconciliation approaches.
"""

import json
import os

def create_benchmark():
    dataset = []

    # Category 1: CLEAN_RECONCILED (Transactions 1 to 5)
    for i in range(1, 6):
        txn_ref = f"TXN-CLEAN-{i:03d}"
        po_no = f"PO-2024-C{i:03d}"
        inv_no = f"INV-2024-C{i:03d}"
        dn_no = f"DN-2024-C{i:03d}"
        rec_no = f"REC-2024-C{i:03d}"
        supp = f"Bharat Engineering Pvt Ltd"
        cust = f"Apex Industrial Solutions"
        qty = 100 * i
        unit_p = 250.00
        subtotal = qty * unit_p
        tax = subtotal * 0.18
        grand_total = subtotal + tax

        docs = [
            {
                "id": f"doc_{txn_ref}_PO",
                "doc_type": "PURCHASE_ORDER",
                "document_type": "PURCHASE_ORDER",
                "filename": f"{txn_ref}_Purchase_Order.pdf",
                "page_start": 1,
                "page_end": 1,
                "parsed_data": {
                    "document_number": po_no,
                    "document_date": f"2024-0{min(9, i)}-01",
                    "supplier_name": supp,
                    "customer_name": cust,
                    "items": [{"description": "M12 High Tensile Hex Bolts", "quantity": qty, "unit": "PCS", "unit_price": unit_p, "tax_rate": 18.0, "total_amount": subtotal}],
                    "subtotal": str(subtotal),
                    "tax_total": str(tax),
                    "grand_total": str(grand_total)
                }
            },
            {
                "id": f"doc_{txn_ref}_DN",
                "doc_type": "DELIVERY_NOTE",
                "document_type": "DELIVERY_NOTE",
                "filename": f"{txn_ref}_Delivery_Challan.pdf",
                "page_start": 1,
                "page_end": 1,
                "parsed_data": {
                    "document_number": dn_no,
                    "po_reference": po_no,
                    "document_date": f"2024-0{min(9, i)}-03",
                    "supplier_name": supp,
                    "customer_name": cust,
                    "items": [{"description": "M12 High Tensile Hex Bolts", "quantity": qty, "unit": "PCS"}]
                }
            },
            {
                "id": f"doc_{txn_ref}_INV",
                "doc_type": "INVOICE",
                "document_type": "INVOICE",
                "filename": f"{txn_ref}_Tax_Invoice.pdf",
                "page_start": 1,
                "page_end": 1,
                "parsed_data": {
                    "document_number": inv_no,
                    "po_reference": po_no,
                    "document_date": f"2024-0{min(9, i)}-05",
                    "supplier_name": supp,
                    "customer_name": cust,
                    "items": [{"description": "M12 High Tensile Hex Bolts", "quantity": qty, "unit": "PCS", "unit_price": unit_p, "tax_rate": 18.0, "total_amount": subtotal}],
                    "subtotal": str(subtotal),
                    "tax_total": str(tax),
                    "grand_total": str(grand_total)
                }
            },
            {
                "id": f"doc_{txn_ref}_REC",
                "doc_type": "PAYMENT_RECEIPT",
                "document_type": "PAYMENT_RECEIPT",
                "filename": f"{txn_ref}_Payment_Receipt.pdf",
                "page_start": 1,
                "page_end": 1,
                "parsed_data": {
                    "document_number": rec_no,
                    "invoice_reference": inv_no,
                    "document_date": f"2024-0{min(9, i)}-10",
                    "supplier_name": supp,
                    "customer_name": cust,
                    "payment_amount": str(grand_total),
                    "grand_total": str(grand_total),
                    "transaction_reference": f"NEFT-UTR-{txn_ref}-01"
                }
            }
        ]

        dataset.append({
            "transaction_id": f"txn_{txn_ref.lower()}",
            "transaction_reference": txn_ref,
            "category": "CLEAN_RECONCILED",
            "supplier": supp,
            "customer": cust,
            "documents": docs,
            "ground_truth_discrepancies": []  # Clean! 0 discrepancies
        })

    # Category 2: QUANTITY_MISMATCH (4 transactions)
    for i in range(1, 5):
        txn_ref = f"TXN-QTY-{i:03d}"
        po_no = f"PO-2024-Q{i:03d}"
        inv_no = f"INV-2024-Q{i:03d}"
        dn_no = f"DN-2024-Q{i:03d}"
        supp = "Precision Fasteners Ltd"
        cust = "Apex Industrial Solutions"
        ordered_qty = 500
        delivered_qty = 400  # 100 units short
        billed_qty = 500     # billed for 500 (overbilling of 100 units)
        unit_p = 150.0

        docs = [
            {
                "id": f"doc_{txn_ref}_PO",
                "doc_type": "PURCHASE_ORDER",
                "document_type": "PURCHASE_ORDER",
                "filename": f"{txn_ref}_PO.pdf",
                "parsed_data": {
                    "document_number": po_no,
                    "document_date": "2024-02-01",
                    "supplier_name": supp,
                    "customer_name": cust,
                    "items": [{"description": "Stainless Steel Flange 2 Inch", "quantity": ordered_qty, "unit_price": unit_p, "total_amount": ordered_qty * unit_p}],
                    "grand_total": str(ordered_qty * unit_p * 1.18)
                }
            },
            {
                "id": f"doc_{txn_ref}_DN",
                "doc_type": "DELIVERY_NOTE",
                "document_type": "DELIVERY_NOTE",
                "filename": f"{txn_ref}_DN.pdf",
                "parsed_data": {
                    "document_number": dn_no,
                    "po_reference": po_no,
                    "document_date": "2024-02-04",
                    "supplier_name": supp,
                    "customer_name": cust,
                    "items": [{"description": "Stainless Steel Flange 2 Inch", "quantity": delivered_qty}]
                }
            },
            {
                "id": f"doc_{txn_ref}_INV",
                "doc_type": "INVOICE",
                "document_type": "INVOICE",
                "filename": f"{txn_ref}_INV.pdf",
                "parsed_data": {
                    "document_number": inv_no,
                    "po_reference": po_no,
                    "document_date": "2024-02-05",
                    "supplier_name": supp,
                    "customer_name": cust,
                    "items": [{"description": "Stainless Steel Flange 2 Inch", "quantity": billed_qty, "unit_price": unit_p, "total_amount": billed_qty * unit_p}],
                    "grand_total": str(billed_qty * unit_p * 1.18)
                }
            }
        ]

        dataset.append({
            "transaction_id": f"txn_{txn_ref.lower()}",
            "transaction_reference": txn_ref,
            "category": "QUANTITY_MISMATCH",
            "supplier": supp,
            "customer": cust,
            "documents": docs,
            "ground_truth_discrepancies": [
                {
                    "discrepancy_type": "QUANTITY_MISMATCH",
                    "severity": "CRITICAL",
                    "expected_value": "400.00 PCS",
                    "actual_value": "500.00 PCS"
                }
            ]
        })

    # Category 3: PRICE_MISMATCH (4 transactions)
    for i in range(1, 5):
        txn_ref = f"TXN-PRICE-{i:03d}"
        po_no = f"PO-2024-P{i:03d}"
        inv_no = f"INV-2024-P{i:03d}"
        supp = "Dynamic Valve Systems"
        cust = "Apex Industrial Solutions"
        po_price = 1200.00
        inv_price = 1450.00  # Unauthorized price increase
        qty = 20

        docs = [
            {
                "id": f"doc_{txn_ref}_PO",
                "doc_type": "PURCHASE_ORDER",
                "document_type": "PURCHASE_ORDER",
                "filename": f"{txn_ref}_PO.pdf",
                "parsed_data": {
                    "document_number": po_no,
                    "document_date": "2024-03-01",
                    "supplier_name": supp,
                    "customer_name": cust,
                    "items": [{"description": "Industrial Ball Valve 50mm", "quantity": qty, "unit_price": po_price, "total_amount": qty * po_price}],
                    "grand_total": str(qty * po_price * 1.18)
                }
            },
            {
                "id": f"doc_{txn_ref}_INV",
                "doc_type": "INVOICE",
                "document_type": "INVOICE",
                "filename": f"{txn_ref}_INV.pdf",
                "parsed_data": {
                    "document_number": inv_no,
                    "po_reference": po_no,
                    "document_date": "2024-03-05",
                    "supplier_name": supp,
                    "customer_name": cust,
                    "items": [{"description": "Industrial Ball Valve 50mm", "quantity": qty, "unit_price": inv_price, "total_amount": qty * inv_price}],
                    "grand_total": str(qty * inv_price * 1.18)
                }
            }
        ]

        dataset.append({
            "transaction_id": f"txn_{txn_ref.lower()}",
            "transaction_reference": txn_ref,
            "category": "PRICE_MISMATCH",
            "supplier": supp,
            "customer": cust,
            "documents": docs,
            "ground_truth_discrepancies": [
                {
                    "discrepancy_type": "PRICE_MISMATCH",
                    "severity": "HIGH",
                    "expected_value": f"₹{po_price:.2f}",
                    "actual_value": f"₹{inv_price:.2f}"
                }
            ]
        })

    # Category 4: TAX_MISMATCH (3 transactions)
    for i in range(1, 4):
        txn_ref = f"TXN-TAX-{i:03d}"
        inv_no = f"INV-2024-T{i:03d}"
        supp = "Standard Chemicals Ltd"
        cust = "Apex Industrial Solutions"
        subtotal = 50000.00
        # Tax should be 18% (9000), but invoice billed 28% (14000) or miscalculated
        err_tax = 14000.00

        docs = [
            {
                "id": f"doc_{txn_ref}_INV",
                "doc_type": "INVOICE",
                "document_type": "INVOICE",
                "filename": f"{txn_ref}_INV.pdf",
                "parsed_data": {
                    "document_number": inv_no,
                    "document_date": "2024-04-01",
                    "supplier_name": supp,
                    "customer_name": cust,
                    "items": [{"description": "Solvent Chemical Grade A", "quantity": 10, "unit_price": 5000.00, "tax_rate": 18.0, "tax_amount": 9000.00, "total_amount": 50000.00}],
                    "subtotal": str(subtotal),
                    "tax_total": str(err_tax),
                    "grand_total": str(subtotal + err_tax)
                }
            }
        ]

        dataset.append({
            "transaction_id": f"txn_{txn_ref.lower()}",
            "transaction_reference": txn_ref,
            "category": "TAX_MISMATCH",
            "supplier": supp,
            "customer": cust,
            "documents": docs,
            "ground_truth_discrepancies": [
                {
                    "discrepancy_type": "TAX_MISMATCH",
                    "severity": "MEDIUM",
                    "expected_value": "₹9000.00",
                    "actual_value": f"₹{err_tax:.2f}"
                }
            ]
        })

    # Category 5: TOTAL_MISMATCH (3 transactions)
    for i in range(1, 4):
        txn_ref = f"TXN-TOTAL-{i:03d}"
        inv_no = f"INV-2024-TOT{i:03d}"
        supp = "Universal Components"
        cust = "Apex Industrial Solutions"
        item_tot = 30000.00
        err_grand = 35000.00  # doesn't match sum of items

        docs = [
            {
                "id": f"doc_{txn_ref}_INV",
                "doc_type": "INVOICE",
                "document_type": "INVOICE",
                "filename": f"{txn_ref}_INV.pdf",
                "parsed_data": {
                    "document_number": inv_no,
                    "document_date": "2024-04-10",
                    "supplier_name": supp,
                    "customer_name": cust,
                    "items": [{"description": "Roller Bearing 6204", "quantity": 50, "unit_price": 600.00, "total_amount": 30000.00}],
                    "subtotal": "30000.00",
                    "tax_total": "0.00",
                    "grand_total": str(err_grand)
                }
            }
        ]

        dataset.append({
            "transaction_id": f"txn_{txn_ref.lower()}",
            "transaction_reference": txn_ref,
            "category": "TOTAL_MISMATCH",
            "supplier": supp,
            "customer": cust,
            "documents": docs,
            "ground_truth_discrepancies": [
                {
                    "discrepancy_type": "TOTAL_MISMATCH",
                    "severity": "MEDIUM",
                    "expected_value": f"₹{item_tot:.2f}",
                    "actual_value": f"₹{err_grand:.2f}"
                }
            ]
        })

    # Category 6: PAYMENT_MISMATCH (4 transactions)
    for i in range(1, 5):
        txn_ref = f"TXN-PAY-{i:03d}"
        inv_no = f"INV-2024-PAY{i:03d}"
        rec_no = f"REC-2024-PAY{i:03d}"
        supp = "Metro Electricals Ltd"
        cust = "Apex Industrial Solutions"
        inv_total = 75000.00
        paid_amt = 60000.00  # 15,000 shortage

        docs = [
            {
                "id": f"doc_{txn_ref}_INV",
                "doc_type": "INVOICE",
                "document_type": "INVOICE",
                "filename": f"{txn_ref}_INV.pdf",
                "parsed_data": {
                    "document_number": inv_no,
                    "document_date": "2024-05-01",
                    "supplier_name": supp,
                    "customer_name": cust,
                    "grand_total": str(inv_total),
                    "items": [{"description": "Copper Cable 4 sqmm", "quantity": 100, "unit_price": 750.00, "total_amount": 75000.00}]
                }
            },
            {
                "id": f"doc_{txn_ref}_REC",
                "doc_type": "PAYMENT_RECEIPT",
                "document_type": "PAYMENT_RECEIPT",
                "filename": f"{txn_ref}_REC.pdf",
                "parsed_data": {
                    "document_number": rec_no,
                    "invoice_reference": inv_no,
                    "document_date": "2024-05-10",
                    "supplier_name": supp,
                    "customer_name": cust,
                    "payment_amount": str(paid_amt),
                    "grand_total": str(paid_amt)
                }
            }
        ]

        dataset.append({
            "transaction_id": f"txn_{txn_ref.lower()}",
            "transaction_reference": txn_ref,
            "category": "PAYMENT_MISMATCH",
            "supplier": supp,
            "customer": cust,
            "documents": docs,
            "ground_truth_discrepancies": [
                {
                    "discrepancy_type": "PAYMENT_MISMATCH",
                    "severity": "HIGH",
                    "expected_value": f"₹{inv_total:.2f}",
                    "actual_value": f"₹{paid_amt:.2f}"
                }
            ]
        })

    # Category 7: DATE_MISMATCH (3 transactions)
    for i in range(1, 4):
        txn_ref = f"TXN-DATE-{i:03d}"
        po_no = f"PO-2024-D{i:03d}"
        inv_no = f"INV-2024-D{i:03d}"
        supp = "Pioneer Hydraulics"
        cust = "Apex Industrial Solutions"

        docs = [
            {
                "id": f"doc_{txn_ref}_PO",
                "doc_type": "PURCHASE_ORDER",
                "document_type": "PURCHASE_ORDER",
                "filename": f"{txn_ref}_PO.pdf",
                "parsed_data": {
                    "document_number": po_no,
                    "document_date": "2024-06-15",  # PO issued on 15th
                    "supplier_name": supp,
                    "customer_name": cust,
                    "items": [{"description": "Hydraulic Pump 10HP", "quantity": 2, "unit_price": 45000.00, "total_amount": 90000.00}],
                    "grand_total": "90000.00"
                }
            },
            {
                "id": f"doc_{txn_ref}_INV",
                "doc_type": "INVOICE",
                "document_type": "INVOICE",
                "filename": f"{txn_ref}_INV.pdf",
                "parsed_data": {
                    "document_number": inv_no,
                    "po_reference": po_no,
                    "document_date": "2024-06-05",  # Invoice dated 5th (BEFORE PO!)
                    "supplier_name": supp,
                    "customer_name": cust,
                    "items": [{"description": "Hydraulic Pump 10HP", "quantity": 2, "unit_price": 45000.00, "total_amount": 90000.00}],
                    "grand_total": "90000.00"
                }
            }
        ]

        dataset.append({
            "transaction_id": f"txn_{txn_ref.lower()}",
            "transaction_reference": txn_ref,
            "category": "DATE_MISMATCH",
            "supplier": supp,
            "customer": cust,
            "documents": docs,
            "ground_truth_discrepancies": [
                {
                    "discrepancy_type": "DATE_MISMATCH",
                    "severity": "MEDIUM",
                    "expected_value": "Invoice Date >= PO Date",
                    "actual_value": "2024-06-05 < 2024-06-15"
                }
            ]
        })

    # Category 8: SUPPLIER_MISMATCH (3 transactions)
    for i in range(1, 4):
        txn_ref = f"TXN-SUPP-{i:03d}"
        po_no = f"PO-2024-S{i:03d}"
        inv_no = f"INV-2024-S{i:03d}"
        supp_po = "Apex Heavy Industries Pvt Ltd"
        supp_inv = "Completely Different Vendor Enterprises"

        docs = [
            {
                "id": f"doc_{txn_ref}_PO",
                "doc_type": "PURCHASE_ORDER",
                "document_type": "PURCHASE_ORDER",
                "filename": f"{txn_ref}_PO.pdf",
                "parsed_data": {
                    "document_number": po_no,
                    "document_date": "2024-07-01",
                    "supplier_name": supp_po,
                    "customer_name": "Apex Industrial Solutions",
                    "items": [{"description": "Steel Girders 6M", "quantity": 10, "unit_price": 12000.00, "total_amount": 120000.00}],
                    "grand_total": "120000.00"
                }
            },
            {
                "id": f"doc_{txn_ref}_INV",
                "doc_type": "INVOICE",
                "document_type": "INVOICE",
                "filename": f"{txn_ref}_INV.pdf",
                "parsed_data": {
                    "document_number": inv_no,
                    "po_reference": po_no,
                    "document_date": "2024-07-05",
                    "supplier_name": supp_inv,
                    "customer_name": "Apex Industrial Solutions",
                    "items": [{"description": "Steel Girders 6M", "quantity": 10, "unit_price": 12000.00, "total_amount": 120000.00}],
                    "grand_total": "120000.00"
                }
            }
        ]

        dataset.append({
            "transaction_id": f"txn_{txn_ref.lower()}",
            "transaction_reference": txn_ref,
            "category": "SUPPLIER_MISMATCH",
            "supplier": supp_po,
            "customer": "Apex Industrial Solutions",
            "documents": docs,
            "ground_truth_discrepancies": [
                {
                    "discrepancy_type": "SUPPLIER_MISMATCH",
                    "severity": "HIGH",
                    "expected_value": supp_po,
                    "actual_value": supp_inv
                }
            ]
        })

    # Category 9: ITEM_MISMATCH (3 transactions)
    for i in range(1, 4):
        txn_ref = f"TXN-ITEM-{i:03d}"
        po_no = f"PO-2024-IT{i:03d}"
        inv_no = f"INV-2024-IT{i:03d}"
        supp = "Global Tooling Corporation"

        docs = [
            {
                "id": f"doc_{txn_ref}_PO",
                "doc_type": "PURCHASE_ORDER",
                "document_type": "PURCHASE_ORDER",
                "filename": f"{txn_ref}_PO.pdf",
                "parsed_data": {
                    "document_number": po_no,
                    "document_date": "2024-08-01",
                    "supplier_name": supp,
                    "customer_name": "Apex Industrial Solutions",
                    "items": [{"description": "Carbide End Mill Cutter 12mm 4-Flute", "quantity": 5, "unit_price": 3200.00, "total_amount": 16000.00}],
                    "grand_total": "16000.00"
                }
            },
            {
                "id": f"doc_{txn_ref}_INV",
                "doc_type": "INVOICE",
                "document_type": "INVOICE",
                "filename": f"{txn_ref}_INV.pdf",
                "parsed_data": {
                    "document_number": inv_no,
                    "po_reference": po_no,
                    "document_date": "2024-08-05",
                    "supplier_name": supp,
                    "customer_name": "Apex Industrial Solutions",
                    "items": [{"description": "Standard HSS Twist Drill Bit Set", "quantity": 5, "unit_price": 3200.00, "total_amount": 16000.00}],
                    "grand_total": "16000.00"
                }
            }
        ]

        dataset.append({
            "transaction_id": f"txn_{txn_ref.lower()}",
            "transaction_reference": txn_ref,
            "category": "ITEM_MISMATCH",
            "supplier": supp,
            "customer": "Apex Industrial Solutions",
            "documents": docs,
            "ground_truth_discrepancies": [
                {
                    "discrepancy_type": "ITEM_MISMATCH",
                    "severity": "MEDIUM",
                    "expected_value": "Carbide End Mill Cutter 12mm 4-Flute",
                    "actual_value": "Standard HSS Twist Drill Bit Set"
                }
            ]
        })

    # Category 10: MISSING_DOCUMENT (3 transactions)
    for i in range(1, 4):
        txn_ref = f"TXN-MISS-{i:03d}"
        inv_no = f"INV-2024-M{i:03d}"
        supp = "Eastern Steel Tubes"

        # Only Invoice exists, Delivery Note and PO missing
        docs = [
            {
                "id": f"doc_{txn_ref}_INV",
                "doc_type": "INVOICE",
                "document_type": "INVOICE",
                "filename": f"{txn_ref}_INV.pdf",
                "parsed_data": {
                    "document_number": inv_no,
                    "document_date": "2024-08-20",
                    "supplier_name": supp,
                    "customer_name": "Apex Industrial Solutions",
                    "items": [{"description": "Seamless Steel Pipe 3 Inch", "quantity": 30, "unit_price": 2800.00, "total_amount": 84000.00}],
                    "grand_total": "84000.00"
                }
            }
        ]

        dataset.append({
            "transaction_id": f"txn_{txn_ref.lower()}",
            "transaction_reference": txn_ref,
            "category": "MISSING_DOCUMENT",
            "supplier": supp,
            "customer": "Apex Industrial Solutions",
            "documents": docs,
            "ground_truth_discrepancies": [
                {
                    "discrepancy_type": "MISSING_DOCUMENT",
                    "severity": "HIGH",
                    "expected_value": "PURCHASE_ORDER, DELIVERY_NOTE present",
                    "actual_value": "Missing"
                }
            ]
        })

    # Category 11: DUPLICATE_DOCUMENT (2 transactions)
    for i in range(1, 3):
        txn_ref = f"TXN-DUP-{i:03d}"
        dup_inv_no = f"INV-2024-DUP-{i:03d}"
        supp = "Omega Logistics Pvt Ltd"

        docs = [
            {
                "id": f"doc_{txn_ref}_INV1",
                "doc_type": "INVOICE",
                "document_type": "INVOICE",
                "filename": f"{txn_ref}_Invoice_Copy1.pdf",
                "parsed_data": {
                    "document_number": dup_inv_no,
                    "document_date": "2024-09-01",
                    "supplier_name": supp,
                    "customer_name": "Apex Industrial Solutions",
                    "items": [{"description": "Freight Transportation Service", "quantity": 1, "unit_price": 42000.00, "total_amount": 42000.00}],
                    "grand_total": "42000.00"
                }
            },
            {
                "id": f"doc_{txn_ref}_INV2",
                "doc_type": "INVOICE",
                "document_type": "INVOICE",
                "filename": f"{txn_ref}_Invoice_Copy2.pdf",
                "parsed_data": {
                    "document_number": dup_inv_no,  # Same invoice number!
                    "document_date": "2024-09-01",
                    "supplier_name": supp,
                    "customer_name": "Apex Industrial Solutions",
                    "items": [{"description": "Freight Transportation Service", "quantity": 1, "unit_price": 42000.00, "total_amount": 42000.00}],
                    "grand_total": "42000.00"
                }
            }
        ]

        dataset.append({
            "transaction_id": f"txn_{txn_ref.lower()}",
            "transaction_reference": txn_ref,
            "category": "DUPLICATE_DOCUMENT",
            "supplier": supp,
            "customer": "Apex Industrial Solutions",
            "documents": docs,
            "ground_truth_discrepancies": [
                {
                    "discrepancy_type": "DUPLICATE_DOCUMENT",
                    "severity": "CRITICAL",
                    "expected_value": "Unique document numbers",
                    "actual_value": f"Duplicate document: {dup_inv_no}"
                }
            ]
        })

    # Category 12: MULTI_DOC_COMBINED_PDF (3 transactions)
    for i in range(1, 4):
        txn_ref = f"TXN-COMBINED-{i:03d}"
        po_no = f"PO-2024-COMB{i:03d}"
        inv_no = f"INV-2024-COMB{i:03d}"
        dn_no = f"DN-2024-COMB{i:03d}"
        supp = "Zenith Automation Systems"

        # 3 documents extracted from 1 physical multi-doc scan
        docs = [
            {
                "id": f"doc_{txn_ref}_P1_PO",
                "file_id": f"file_{txn_ref}_combined.pdf",
                "doc_type": "PURCHASE_ORDER",
                "document_type": "PURCHASE_ORDER",
                "filename": f"{txn_ref}_Scan_Page1.pdf",
                "page_start": 1,
                "page_end": 1,
                "parsed_data": {
                    "document_number": po_no,
                    "document_date": "2024-09-10",
                    "supplier_name": supp,
                    "customer_name": "Apex Industrial Solutions",
                    "items": [{"description": "PLC Controller Module", "quantity": 4, "unit_price": 28000.00, "total_amount": 112000.00}],
                    "grand_total": "112000.00"
                }
            },
            {
                "id": f"doc_{txn_ref}_P2_DN",
                "file_id": f"file_{txn_ref}_combined.pdf",
                "doc_type": "DELIVERY_NOTE",
                "document_type": "DELIVERY_NOTE",
                "filename": f"{txn_ref}_Scan_Page2.pdf",
                "page_start": 2,
                "page_end": 2,
                "parsed_data": {
                    "document_number": dn_no,
                    "po_reference": po_no,
                    "document_date": "2024-09-12",
                    "supplier_name": supp,
                    "customer_name": "Apex Industrial Solutions",
                    "items": [{"description": "PLC Controller Module", "quantity": 4}]
                }
            },
            {
                "id": f"doc_{txn_ref}_P3_INV",
                "file_id": f"file_{txn_ref}_combined.pdf",
                "doc_type": "INVOICE",
                "document_type": "INVOICE",
                "filename": f"{txn_ref}_Scan_Page3.pdf",
                "page_start": 3,
                "page_end": 3,
                "parsed_data": {
                    "document_number": inv_no,
                    "po_reference": po_no,
                    "document_date": "2024-09-13",
                    "supplier_name": supp,
                    "customer_name": "Apex Industrial Solutions",
                    "items": [{"description": "PLC Controller Module", "quantity": 4, "unit_price": 28000.00, "total_amount": 112000.00}],
                    "grand_total": "112000.00"
                }
            }
        ]

        dataset.append({
            "transaction_id": f"txn_{txn_ref.lower()}",
            "transaction_reference": txn_ref,
            "category": "MULTI_DOC_COMBINED_PDF",
            "supplier": supp,
            "customer": "Apex Industrial Solutions",
            "documents": docs,
            "ground_truth_discrepancies": []  # Clean match across combined scan
        })

    return dataset

if __name__ == "__main__":
    data = create_benchmark()
    out_path = os.path.join(os.path.dirname(__file__), "benchmark_dataset.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Generated {len(data)} annotated benchmark transactions in {out_path}")

