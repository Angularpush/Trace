"""
TRACE - 50 Document Test Pack Evaluation Runner
Evaluates TRACE against the 50 synthetic documents in TRACE_50_Document_Test_Pack.
"""

import os
import sys
import json
import time
from collections import defaultdict
from typing import Dict, List, Any

backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.extraction.extractor_service import DocumentProcessingService
from app.reconciliation.orchestrator import reconciliation_orchestrator
from app.extraction.normalizer import normalize_decimal

TEST_PACK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_pack_50", "TRACE_50_Document_Test_Pack")
DOCUMENTS_DIR = os.path.join(TEST_PACK_DIR, "documents")
GROUND_TRUTH_PATH = os.path.join(TEST_PACK_DIR, "ground_truth", "ground_truth.json")

def main():
    if not os.path.exists(GROUND_TRUTH_PATH):
        print(f"Ground truth not found at {GROUND_TRUTH_PATH}")
        return

    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    print(f"Loaded {len(ground_truth)} transactions from Ground Truth.")
    
    total_docs = 0
    correct_classifications = 0
    
    # Track document type mappings
    # PO -> PURCHASE_ORDER, INV -> INVOICE, DN -> DELIVERY_NOTE, PAY -> PAYMENT_RECEIPT
    type_map = {
        "PO": "PURCHASE_ORDER",
        "INV": "INVOICE",
        "DN": "DELIVERY_NOTE",
        "PAY": "PAYMENT_RECEIPT"
    }

    results = []

    for txn in ground_truth:
        txn_id = txn["transaction_id"]
        doc_files = txn["documents"]
        exp_types = txn.get("expected_document_types", [])
        
        extracted_docs = []
        for idx, fn in enumerate(doc_files):
            total_docs += 1
            path = os.path.join(DOCUMENTS_DIR, fn)
            if not os.path.exists(path):
                print(f"Warning: file {path} does not exist!")
                continue

            doc_res = DocumentProcessingService.process_document(path)
            pred_type = doc_res["doc_type"]
            exp_t = type_map.get(exp_types[idx]) if idx < len(exp_types) else None
            
            is_correct = (pred_type == exp_t)
            if is_correct:
                correct_classifications += 1
            else:
                print(f"Classification Mismatch in {fn}: expected {exp_t}, got {pred_type}")

            extracted_docs.append({
                "id": f"{txn_id}_{fn}",
                "filename": fn,
                "doc_type": pred_type,
                "classification_confidence": doc_res["classification_confidence"],
                "parsed_data": doc_res["parsed_data"],
                "raw_text": doc_res["raw_text"],
                "page_number": 1
            })

        # Run reconciliation
        rec_out = reconciliation_orchestrator.reconcile_transaction(
            transaction_ref=txn_id,
            documents=extracted_docs,
            mode="HYBRID"
        )

        results.append({
            "transaction_id": txn_id,
            "anomaly_expected": txn.get("anomaly"),
            "expected_discrepancies": txn.get("expected_discrepancies", []),
            "predicted_discrepancies": rec_out.get("discrepancies", []),
            "reconciliation_status": rec_out.get("reconciliation_status")
        })

    print("\n" + "=" * 60)
    print("50-DOCUMENT TEST PACK EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total Transactions : {len(ground_truth)}")
    print(f"Total Documents    : {total_docs}")
    print(f"Classification Acc : {correct_classifications}/{total_docs} ({correct_classifications/total_docs*100:.2f}%)")
    print("\nTransaction-by-Transaction Discrepancy Detections:")
    for r in results:
        print(f"[{r['transaction_id']}] Expected: {r['anomaly_expected']} | Status: {r['reconciliation_status']} | Discrepancies detected: {len(r['predicted_discrepancies'])}")
        for d in r['predicted_discrepancies']:
            print(f"   -> {d.get('rule_code')}: {d.get('title')}")

if __name__ == "__main__":
    main()

