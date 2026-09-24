"""
TRACE - Research Objective Unit Test Suite
Validates:
1. Document Segmentation: Detects boundaries and document units inside files
2. Multi-Signal Graph Linker: Evaluates exact, metadata, semantic, and hybrid links
3. Three Isolated Reconciliation Engines: RULE_BASED, AI_LLM, HYBRID on same transaction
4. Benchmark Evaluator: Computes Precision, Recall, F1, Latency, and Cost tracking
"""

import pytest
from decimal import Decimal

from app.extraction.segmenter import DocumentSegmenter
from app.reconciliation.linker import TransactionLinker
from app.reconciliation.engines.rule_based import rule_based_engine
from app.reconciliation.engines.ai_llm import ai_llm_engine
from app.reconciliation.engines.hybrid import hybrid_engine
from app.reconciliation.engines.comparator import reconciliation_comparator
from app.evaluation.evaluator import evaluator


def test_segmenter_header_signatures():
    po_text = "PURCHASE ORDER\nPO Number: PO-2024-999\nVendor: Industrial Ltd"
    inv_text = "TAX INVOICE\nInvoice No: INV-2024-999\nDate: 2024-03-01"
    dn_text = "DELIVERY CHALLAN\nChallan No: DC-999\nItems: 50 Bolts"
    pay_text = "PAYMENT RECEIPT\nPayment Receipt No: PAY-999\nAgainst Invoice No: INV-2024-999"

    assert DocumentSegmenter.detect_header_type(po_text) == "PURCHASE_ORDER"
    assert DocumentSegmenter.detect_header_type(inv_text) == "INVOICE"
    assert DocumentSegmenter.detect_header_type(dn_text) == "DELIVERY_NOTE"
    assert DocumentSegmenter.detect_header_type(pay_text) == "PAYMENT_RECEIPT"


def test_segmenter_extract_document_number():
    assert DocumentSegmenter.extract_document_number("Invoice No: INV-2024-999") == "INV-2024-999"
    assert DocumentSegmenter.extract_document_number("PO Number: PO-2024-888") == "PO-2024-888"
    assert DocumentSegmenter.extract_document_number("Payment Receipt No: PAY-777") == "PAY-777"
    assert DocumentSegmenter.extract_document_number("Delivery Challan No: DC-666") == "DC-666"


def test_multi_signal_graph_linker_pair_evaluation():
    doc_po = {
        "id": "doc_po",
        "doc_type": "PURCHASE_ORDER",
        "filename": "PO-1001.pdf",
        "parsed_data": {
            "document_number": "PO-1001",
            "supplier_name": "Kirloskar Supplies Ltd",
            "grand_total": 50000.0
        }
    }
    doc_inv = {
        "id": "doc_inv",
        "doc_type": "INVOICE",
        "filename": "INV-5001.pdf",
        "parsed_data": {
            "document_number": "INV-5001",
            "po_reference": "PO-1001",
            "supplier_name": "Kirloskar Supplies",
            "grand_total": 50000.0
        }
    }

    meta_a = TransactionLinker.extract_document_identifiers(doc_po)
    meta_b = TransactionLinker.extract_document_identifiers(doc_inv)

    is_linked, method, conf, details = TransactionLinker.evaluate_pair_link(meta_a, meta_b)
    assert is_linked is True
    assert method == "exact_identifier"
    assert conf >= 0.98
    assert details["matched_key"] == "PO_NUMBER"


def test_three_reconciliation_engines_on_clean_transaction():
    clean_transaction = {
        "id": "txn_clean_test",
        "transaction_reference": "TXN-TEST-001",
        "supplier": "Acme Tools Ltd",
        "customer": "Bharat Motors",
        "total_amount": 10000.0,
        "documents": [
            {
                "id": "d1",
                "document_type": "PURCHASE_ORDER",
                "filename": "PO.pdf",
                "parsed_data": {
                    "document_number": "PO-1",
                    "items": [{"description": "Nut M8", "quantity": 100, "unit_price": 100.0, "total": 10000.0}]
                }
            },
            {
                "id": "d2",
                "document_type": "INVOICE",
                "filename": "INV.pdf",
                "parsed_data": {
                    "document_number": "INV-1",
                    "po_reference": "PO-1",
                    "items": [{"description": "Nut M8", "quantity": 100, "unit_price": 100.0, "total": 10000.0}],
                    "grand_total": "10000.00"
                }
            },
            {
                "id": "d3",
                "document_type": "DELIVERY_NOTE",
                "filename": "DN.pdf",
                "parsed_data": {
                    "document_number": "DN-1",
                    "items": [{"description": "Nut M8", "quantity": 100}]
                }
            },
            {
                "id": "d4",
                "document_type": "PAYMENT_RECEIPT",
                "filename": "PAY.pdf",
                "parsed_data": {
                    "document_number": "PAY-1",
                    "invoice_reference": "INV-1",
                    "payment_amount": "10000.00"
                }
            }
        ]
    }

    # 1. Rule-Based Engine
    rule_res = rule_based_engine.reconcile(clean_transaction)
    assert rule_res.approach == "RULE_BASED"
    assert rule_res.cost_usd == 0.00
    assert rule_res.execution_time_ms < 100.0  # sub-100ms
    assert len(rule_res.findings) == 0
    assert rule_res.overall_result == "RECONCILED"

    # 2. AI/LLM Engine
    ai_res = ai_llm_engine.reconcile(clean_transaction)
    assert ai_res.approach == "AI_LLM"
    assert ai_res.overall_result == "RECONCILED"

    # 3. Hybrid Engine
    hyb_res = hybrid_engine.reconcile(clean_transaction)
    assert hyb_res.approach == "HYBRID"
    assert hyb_res.overall_result == "RECONCILED"


def test_three_reconciliation_engines_on_discrepancy_transaction():
    discrepant_transaction = {
        "id": "txn_disc_test",
        "transaction_reference": "TXN-TEST-002",
        "supplier": "Acme Tools Ltd",
        "customer": "Bharat Motors",
        "total_amount": 10000.0,
        "documents": [
            {
                "id": "d1",
                "document_type": "PURCHASE_ORDER",
                "filename": "PO.pdf",
                "parsed_data": {
                    "document_number": "PO-2",
                    "items": [{"description": "Nut M8", "quantity": 100, "unit_price": 100.0, "total": 10000.0}]
                }
            },
            {
                "id": "d2",
                "document_type": "INVOICE",
                "filename": "INV.pdf",
                "parsed_data": {
                    "document_number": "INV-2",
                    "po_reference": "PO-2",
                    # Price Mismatch: 120.0 instead of 100.0
                    "items": [{"description": "Nut M8", "quantity": 100, "unit_price": 120.0, "total": 12000.0}],
                    "grand_total": "12000.00"
                }
            },
            {
                "id": "d3",
                "document_type": "DELIVERY_NOTE",
                "filename": "DN.pdf",
                "parsed_data": {
                    "document_number": "DN-2",
                    # Quantity Shortfall: 90 delivered instead of 100 billed
                    "items": [{"description": "Nut M8", "quantity": 90}]
                }
            },
            {
                "id": "d4",
                "document_type": "PAYMENT_RECEIPT",
                "filename": "PAY.pdf",
                "parsed_data": {
                    "document_number": "PAY-2",
                    "invoice_reference": "INV-2",
                    # Payment Shortfall: 8000 paid instead of 12000 billed
                    "payment_amount": "8000.00"
                }
            }
        ]
    }

    # 1. Rule-Based Engine
    rule_res = rule_based_engine.reconcile(discrepant_transaction)
    types_found = {f.discrepancy_type for f in rule_res.findings}
    assert "PRICE_MISMATCH" in types_found
    assert "QUANTITY_MISMATCH" in types_found
    assert "PAYMENT_MISMATCH" in types_found
    assert rule_res.cost_usd == 0.00

    # 2. Comparator
    comp = reconciliation_comparator.compare_transaction(discrepant_transaction)
    assert comp["agreement_score"] > 0.0
    assert "consensus_discrepancies" in comp
    assert "latency_comparison" in comp
    assert "cost_comparison" in comp


def test_benchmark_evaluator_metrics():
    dataset = evaluator.load_benchmark_dataset()
    assert len(dataset) == 40
    report = evaluator.run_full_benchmark()

    assert report.dataset_size == 40
    assert report.categories_tested == 12
    assert report.rule_based_metrics.f1_score > 0.5
    assert report.rule_based_metrics.recall >= 0.9
    assert report.rule_based_metrics.total_cost_usd == 0.00
    assert report.hybrid_metrics.f1_score > 0.5
    assert len(report.key_findings) >= 3
