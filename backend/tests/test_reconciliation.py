"""
TRACE - Full Multi-Document Reconciliation Integration Tests
"""

from app.reconciliation.orchestrator import reconciliation_orchestrator

def test_full_reconciliation_cycle():
    documents = [
        {
            "id": "D1", "filename": "Purchase_Order.pdf", "doc_type": "PURCHASE_ORDER",
            "parsed_data": {
                "document_number": "PO-100",
                "supplier_name": "Apex Industrial Tools",
                "customer_name": "MSME Plant",
                "items": [{"description": "Stainless Steel Bolt M10", "quantity": "100", "unit": "PCS", "unit_price": "500.00", "total_amount": "50000.00"}],
                "grand_total": "50000.00"
            }
        },
        {
            "id": "D2", "filename": "Delivery_Challan.pdf", "doc_type": "DELIVERY_NOTE",
            "parsed_data": {
                "document_number": "DC-100", "po_reference": "PO-100",
                "items": [{"description": "SS Bolt 10mm", "quantity": "90", "unit": "PCS", "unit_price": "0.00", "total_amount": "0.00"}]
            }
        },
        {
            "id": "D3", "filename": "Tax_Invoice.pdf", "doc_type": "INVOICE",
            "parsed_data": {
                "document_number": "INV-100", "po_reference": "PO-100",
                "supplier_name": "Apex Industrial Tools",
                "customer_name": "MSME Plant",
                "items": [{"description": "SS Bolt 10mm", "quantity": "100", "unit": "PCS", "unit_price": "550.00", "total_amount": "55000.00"}],
                "subtotal": "55000.00", "grand_total": "55000.00"
            }
        },
        {
            "id": "D4", "filename": "Payment_Receipt.pdf", "doc_type": "PAYMENT_RECEIPT",
            "parsed_data": {
                "document_number": "PAY-100", "invoice_reference": "INV-100",
                "payment_amount": "45000.00", "grand_total": "45000.00"
            }
        }
    ]

    report = reconciliation_orchestrator.reconcile_transaction(
        transaction_ref="PO-100",
        documents=documents,
        mode="HYBRID",
        llm_provider_name="offline"
    )

    assert report["reconciliation_status"] == "DISCREPANCY_FOUND"
    assert report["total_discrepancies"] == 3
    
    rule_codes = [d["rule_code"] for d in report["discrepancies"]]
    assert "PRICE_MISMATCH" in rule_codes
    assert "QUANTITY_MISMATCH" in rule_codes
    assert "PAYMENT_MISMATCH" in rule_codes
    
    assert report["financial_variance_amount"] > 0
    assert len(report["ai_grounded_explanation"]) > 20
