"""
TRACE - Financial Rule Engine Unit Tests
"""

from decimal import Decimal
from app.rules.price_rules import PriceMismatchRule
from app.rules.quantity_rules import QuantityMismatchRule
from app.rules.payment_rules import PaymentMismatchRule
from app.rules.missing_doc_rules import MissingDocumentRule

def test_price_mismatch_detection():
    rule = PriceMismatchRule()
    context = {
        "documents_by_type": {
            "PURCHASE_ORDER": {"id": "PO1", "filename": "PO.pdf"},
            "INVOICE": {"id": "INV1", "filename": "Invoice.pdf"}
        },
        "aligned_items": [
            {
                "item_key": "Stainless Steel Bolt M10",
                "po_item": {"description": "Stainless Steel Bolt M10", "unit_price": "500.00", "quantity": "100"},
                "invoice_item": {"description": "SS Bolt 10mm", "unit_price": "550.00", "quantity": "100"}
            }
        ]
    }
    discrepancies = rule.evaluate(context)
    assert len(discrepancies) == 1
    assert discrepancies[0].rule_code == "PRICE_MISMATCH"
    assert discrepancies[0].difference_amount == Decimal("5000.00")
    assert discrepancies[0].expected_value == "₹500.00"
    assert discrepancies[0].actual_value == "₹550.00"
    assert len(discrepancies[0].evidences) == 2
    assert discrepancies[0].evidences[0].document_name == "PO.pdf"
    assert discrepancies[0].evidences[1].document_name == "Invoice.pdf"
    assert discrepancies[0].severity in ["HIGH", "CRITICAL"]

def test_quantity_overbilling_detection():
    rule = QuantityMismatchRule()
    context = {
        "documents_by_type": {
            "PURCHASE_ORDER": {"id": "PO1", "filename": "PO.pdf"},
            "INVOICE": {"id": "INV1", "filename": "Invoice.pdf"},
            "DELIVERY_NOTE": {"id": "DN1", "filename": "Delivery.pdf"}
        },
        "aligned_items": [
            {
                "item_key": "Industrial Nut M10",
                "po_item": {"description": "Industrial Nut M10", "quantity": "100", "unit_price": "500.00"},
                "invoice_item": {"description": "Industrial Nut M10", "quantity": "100", "unit_price": "500.00"},
                "delivery_item": {"description": "Industrial Nut M10", "quantity": "90", "unit_price": "0.00"}
            }
        ]
    }
    discrepancies = rule.evaluate(context)
    assert len(discrepancies) == 1
    assert discrepancies[0].rule_code == "QUANTITY_MISMATCH"
    assert discrepancies[0].discrepancy_type == "INVOICE_EXCEEDS_DELIVERY"
    assert discrepancies[0].difference_amount == Decimal("5000.00")  # 10 units * 500
    assert "90" in discrepancies[0].expected_value
    assert "100" in discrepancies[0].actual_value
    assert len(discrepancies[0].evidences) == 2

def test_payment_shortfall_detection():
    rule = PaymentMismatchRule()
    context = {
        "documents_by_type": {
            "INVOICE": {"id": "INV1", "filename": "Invoice.pdf", "parsed_data": {"grand_total": "55000.00"}},
            "PAYMENT_RECEIPT": {"id": "PAY1", "filename": "Payment.pdf", "parsed_data": {"payment_amount": "45000.00"}}
        }
    }
    discrepancies = rule.evaluate(context)
    assert len(discrepancies) == 1
    assert discrepancies[0].rule_code == "PAYMENT_MISMATCH"
    assert discrepancies[0].difference_amount == Decimal("10000.00")
    assert discrepancies[0].expected_value == "₹55000.00"
    assert discrepancies[0].actual_value == "₹45000.00"
    assert len(discrepancies[0].evidences) == 2

def test_missing_delivery_note_detection():
    rule = MissingDocumentRule()
    context = {
        "documents_by_type": {
            "PURCHASE_ORDER": {"id": "PO1", "filename": "PO.pdf"},
            "INVOICE": {"id": "INV1", "filename": "Invoice.pdf", "parsed_data": {"document_number": "INV-100"}}
        }
    }
    discrepancies = rule.evaluate(context)
    assert any(d.discrepancy_type == "MISSING_DELIVERY_NOTE" for d in discrepancies)
    missing_dn = next(d for d in discrepancies if d.discrepancy_type == "MISSING_DELIVERY_NOTE")
    assert "Delivery Note" in missing_dn.expected_value
    assert "Missing" in missing_dn.actual_value
