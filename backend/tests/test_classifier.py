"""
TRACE - Document Classifier & DocumentClassificationService Unit Tests
Validates real TF-IDF + Logistic Regression inference, probability calibration,
and explicit error raising on missing model weights.
"""

import pytest
from app.classification.classifier import (
    DocumentClassificationService,
    DocumentClassifierService,
    classifier_service
)

def test_document_classification_service_instance():
    svc = DocumentClassificationService.get_instance()
    assert svc is not None
    assert svc.is_model_loaded() is True
    info = svc.get_model_info()
    assert info["loaded"] is True
    assert "INVOICE" in info["classes"]
    assert "PURCHASE_ORDER" in info["classes"]

def test_classifier_po():
    text = "PURCHASE ORDER\nPO Number: PO-2024-9912\nVendor: Apex Tools\nLine Items:\n1. Bolt M10 Qty: 100 @ 500"
    doc_type, conf, dist = classifier_service.classify(text)
    assert doc_type == "PURCHASE_ORDER"
    assert 0.0 <= conf <= 1.0
    assert conf >= 0.50
    assert "PURCHASE_ORDER" in dist
    assert abs(sum(dist.values()) - 1.0) < 0.01  # True calibrated softmax probability distribution

def test_classifier_invoice():
    text = "TAX INVOICE\nInvoice No: INV-2425-8812\nGSTIN: 27AABCP1234F1Z1\nTotal Invoice Amount: INR 59000.00"
    doc_type, conf, dist = classifier_service.classify(text)
    assert doc_type == "INVOICE"
    assert 0.0 <= conf <= 1.0
    assert conf >= 0.50
    assert "INVOICE" in dist
    assert abs(sum(dist.values()) - 1.0) < 0.01

def test_classifier_delivery_note():
    text = "DELIVERY CHALLAN / NOTE\nDelivery Challan No: DC-9988\nVehicle No: MH-12-8821\nDispatched Qty: 90 PCS"
    doc_type, conf, dist = classifier_service.classify(text)
    assert doc_type == "DELIVERY_NOTE"
    assert 0.0 <= conf <= 1.0
    assert conf >= 0.50
    assert "DELIVERY_NOTE" in dist

def test_classifier_payment_receipt():
    text = "PAYMENT RECEIPT / VOUCHER\nReceipt No: PAY-7712\nBank Transaction Ref / UTR: UTR-HDFC-99182\nAmount Paid: INR 50000.00"
    doc_type, conf, dist = classifier_service.classify(text)
    assert doc_type == "PAYMENT_RECEIPT"
    assert 0.0 <= conf <= 1.0
    assert conf >= 0.50
    assert "PAYMENT_RECEIPT" in dist

def test_missing_model_raises_explicit_runtime_error():
    """
    Verifies that if the model artifact is missing, DocumentClassificationService
    raises an explicit RuntimeError instead of silently generating fake classifications.
    """
    # Instantiate service pointing to a non-existent file
    dummy_service = DocumentClassificationService(model_path="non_existent_model_weights.joblib")
    assert dummy_service.is_model_loaded() is False
    
    with pytest.raises(RuntimeError) as exc_info:
        dummy_service.classify("TAX INVOICE #123 Total INR 500")
    
    assert "missing" in str(exc_info.value).lower() or "not found" in str(exc_info.value).lower()
