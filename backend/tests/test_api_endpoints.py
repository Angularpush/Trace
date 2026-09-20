"""
TRACE - Comprehensive End-to-End API Integration Tests
Validates all 13 specified endpoints with real request/response lifecycles.
"""

import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_api_endpoint_suite():
    # 1. Seed demo documents or upload test document
    seed_res = client.post("/api/documents/seed-demo")
    assert seed_res.status_code in [200, 201]
    docs = seed_res.json()
    assert len(docs) > 0
    sample_doc_id = docs[0]["id"]

    # 2. GET /api/documents
    get_docs_res = client.get("/api/documents")
    assert get_docs_res.status_code == 200
    assert isinstance(get_docs_res.json(), list)

    # 3. GET /api/documents/{id}
    get_single_doc_res = client.get(f"/api/documents/{sample_doc_id}")
    assert get_single_doc_res.status_code == 200
    assert get_single_doc_res.json()["id"] == sample_doc_id

    # 4. POST /api/transactions/match
    match_res = client.post("/api/transactions/match")
    assert match_res.status_code == 200
    txns = match_res.json()
    assert len(txns) > 0
    sample_txn_id = txns[0]["id"]

    # 5. GET /api/transactions
    list_txns_res = client.get("/api/transactions")
    assert list_txns_res.status_code == 200
    assert len(list_txns_res.json()) > 0

    # 6. GET /api/transactions/{id}
    get_single_txn_res = client.get(f"/api/transactions/{sample_txn_id}")
    assert get_single_txn_res.status_code == 200
    assert get_single_txn_res.json()["id"] == sample_txn_id

    # 7. POST /api/transactions/{id}/reconcile
    reconcile_res = client.post(f"/api/transactions/{sample_txn_id}/reconcile?mode=HYBRID")
    assert reconcile_res.status_code == 200
    report = reconcile_res.json()
    assert report["transaction_id"] == sample_txn_id
    assert "reconciliation_status" in report

    # 8. GET /api/transactions/{id}/report
    report_res = client.get(f"/api/transactions/{sample_txn_id}/report")
    assert report_res.status_code == 200
    assert report_res.json()["transaction_id"] == sample_txn_id

    # 9. GET /api/transactions/{id}/discrepancies
    discrepancies_res = client.get(f"/api/transactions/{sample_txn_id}/discrepancies")
    assert discrepancies_res.status_code == 200
    discrepancies = discrepancies_res.json()
    assert isinstance(discrepancies, list)

    # 10. GET /api/evidence/{id} (if discrepancies have evidence)
    if discrepancies and discrepancies[0].get("evidences"):
        sample_ev_id = discrepancies[0]["evidences"][0]["id"]
        ev_res = client.get(f"/api/evidence/{sample_ev_id}")
        assert ev_res.status_code == 200
        assert ev_res.json()["id"] == sample_ev_id

    # 11. POST /api/evaluation/run
    eval_run_res = client.post("/api/evaluation/run")
    assert eval_run_res.status_code == 200
    eval_data = eval_run_res.json()
    assert "modes" in eval_data
    assert "RULE_BASED" in eval_data["modes"]
    assert "AI_ONLY" in eval_data["modes"]
    assert "HYBRID" in eval_data["modes"]

    # 12. GET /api/evaluation/results
    eval_results_res = client.get("/api/evaluation/results")
    assert eval_results_res.status_code == 200
    assert eval_results_res.json() is not None

    # 13. GET /api/dashboard/stats
    stats_res = client.get("/api/dashboard/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "total_transactions" in stats
    assert "reconciled_transactions" in stats
    assert "discrepancy_transactions" in stats
    assert "total_outstanding_amount" in stats
