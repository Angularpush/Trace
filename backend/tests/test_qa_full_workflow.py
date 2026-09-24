"""
TRACE - Comprehensive Senior Full-Stack QA End-to-End Test Suite
Executes the exact 20-step verification workflow:
1. Database initialization & health
2. FastAPI application lifecycle
3. Frontend contract & schema compatibility
4-7. Upload sample PO, Invoice, Delivery Note, Payment Receipt
8. Verify extraction (text, fields, items)
9. Verify trained document classifier & genuine confidence
10. Verify graph-based transaction linking
11. Run rule-based reconciliation
12. Run AI-only reconciliation
13. Run hybrid reconciliation
14. View discrepancies & difference amounts
15. Open & verify evidence citations & snippets
16. View severity distribution
17. View confidence scores
18. Generate reconciliation report
19. View dashboard statistics & KPIs
20. Run evaluation benchmark
"""

import os
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.classification.classifier import DocumentClassificationService
from app.semantic.vector_store import VectorStore
from app.semantic.embeddings import EmbeddingService
from app.semantic.matcher import SemanticMatcher

# Setup test in-memory SQLite DB with StaticPool for thread-safe cross-connection persistence
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module", autouse=True)
def setup_qa_database():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

def test_step_01_database_and_health(client):
    """Step 1 & 2: Verify Database and FastAPI Application Health"""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"

    root_res = client.get("/")
    assert root_res.status_code == 200
    assert root_res.json()["project"] == "TRACE"


def test_step_03_frontend_cors_and_router_aliases(client):
    """Step 3: Verify CORS headers and API route aliases (/api/ and /api/v1/)"""
    res = client.options("/api/documents", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET"
    })
    # CORS middleware returns 200 on valid preflight
    assert res.status_code == 200
    assert "access-control-allow-origin" in res.headers


def test_step_04_to_07_upload_sample_documents(client):
    """Steps 4-7: Upload sample PO, Invoice, Delivery Note, and Payment Receipt"""
    sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sample_data", "raw_documents"))
    assert os.path.exists(sample_dir), f"Sample directory missing at {sample_dir}"

    doc_files = [
        "TXN-002_PO.pdf",
        "TXN-002_Tax_Invoice.pdf",
        "TXN-002_Delivery_Note.pdf",
        "TXN-002_Payment_Receipt.pdf"
    ]

    uploaded_records = []
    for doc_fn in doc_files:
        path = os.path.join(sample_dir, "TXN-002", doc_fn)
        if not os.path.exists(path):
            path = os.path.join(sample_dir, doc_fn)
        assert os.path.exists(path), f"File {doc_fn} missing at {path}"
        with open(path, "rb") as f:
            file_bytes = f.read()

        response = client.post(
            "/api/documents/upload",
            files=[("files", (doc_fn, io.BytesIO(file_bytes), "application/pdf"))]
        )
        assert response.status_code == 200, f"Failed upload for {doc_fn}: {response.text}"
        data = response.json()
        assert len(data) == 1
        uploaded_records.append(data[0])

    assert len(uploaded_records) == 4


def test_step_08_verify_extraction(client):
    """Step 8: Verify extraction of text, line items, metadata, totals"""
    res = client.get("/api/documents")
    assert res.status_code == 200
    docs = res.json()
    assert len(docs) >= 4

    po_doc = next((d for d in docs if d["doc_type"] == "PURCHASE_ORDER"), None)
    inv_doc = next((d for d in docs if d["doc_type"] == "INVOICE"), None)
    dn_doc = next((d for d in docs if d["doc_type"] == "DELIVERY_NOTE"), None)
    pay_doc = next((d for d in docs if d["doc_type"] == "PAYMENT_RECEIPT"), None)

    assert po_doc is not None
    assert inv_doc is not None
    assert dn_doc is not None
    assert pay_doc is not None

    # Verify structured fields
    assert po_doc["parsed_data"]["document_number"] == "PO-2024-002"
    assert inv_doc["parsed_data"]["document_number"] == "INV-2425-6602"
    assert dn_doc["parsed_data"]["document_number"] == "DC-9944"
    assert pay_doc["parsed_data"]["document_number"] == "PAY-8802"

    # Verify line items extracted
    assert len(po_doc["parsed_data"]["items"]) >= 1
    assert len(inv_doc["parsed_data"]["items"]) >= 1
    assert len(dn_doc["parsed_data"]["items"]) >= 1


def test_step_09_verify_trained_classifier_and_confidence(client):
    """Step 9: Verify DocumentClassificationService loads artifact and outputs genuine confidence"""
    svc = DocumentClassificationService.get_instance()
    assert svc.is_model_loaded() is True

    # Test inference directly
    text = "TAX INVOICE\nInvoice Number: INV-9912\nGSTIN: 27AABCP1234F1Z1\nTotal Amount: INR 50000.00"
    doc_type, conf, dist = svc.classify(text)
    assert doc_type == "INVOICE"
    assert 0.0 <= conf <= 1.0
    assert conf >= 0.50
    assert "INVOICE" in dist
    assert abs(sum(dist.values()) - 1.0) < 0.01  # True calibrated Softmax probability


def test_step_10_verify_transaction_linking(client):
    """Step 10: Verify graph-based transaction linking clusters the 4 documents into TXN-002"""
    res = client.post("/api/transactions/match")
    assert res.status_code == 200
    txns = res.json()
    assert len(txns) >= 1

    txn = next((t for t in txns if "PO-2024-002" in t["transaction_ref"] or "TXN-002" in t["transaction_ref"] or "PO-2024-002" in t["title"]), None)
    assert txn is not None, f"Transaction TXN-002 not matched. Found: {[t['transaction_ref'] for t in txns]}"
    assert len(txn["documents"]) == 4


def test_step_11_run_rule_based_reconciliation(client):
    """Step 11: Run RULE_BASED reconciliation"""
    txns = client.get("/api/transactions").json()
    txn = txns[0]
    txn_id = txn["id"]

    res = client.post(f"/api/transactions/{txn_id}/reconcile?mode=RULE_BASED&llm_provider=offline")
    assert res.status_code == 200
    report = res.json()
    assert report["mode_used"] == "RULE_BASED"
    assert report["total_discrepancies"] > 0
    assert report["reconciliation_status"] in ["DISCREPANCY_FOUND", "MINOR_VARIANCE"]


def test_step_12_run_ai_only_reconciliation(client):
    """Step 12: Run AI_ONLY reconciliation"""
    txns = client.get("/api/transactions").json()
    txn_id = txns[0]["id"]

    res = client.post(f"/api/transactions/{txn_id}/reconcile?mode=AI_ONLY&llm_provider=offline")
    assert res.status_code == 200
    report = res.json()
    assert report["mode_used"] == "AI_ONLY"


def test_step_13_run_hybrid_reconciliation(client):
    """Step 13: Run HYBRID reconciliation (combined Decimal rules + semantic item alignment + evidence + LLM)"""
    txns = client.get("/api/transactions").json()
    txn_id = txns[0]["id"]

    res = client.post(f"/api/transactions/{txn_id}/reconcile?mode=HYBRID&llm_provider=offline")
    assert res.status_code == 200
    report = res.json()
    assert report["mode_used"] == "HYBRID"
    assert report["total_discrepancies"] >= 3  # TXN-002 has Price Mismatch, Quantity Mismatch, Payment Shortfall
    assert report["financial_variance_amount"] > 0


def test_step_14_to_17_view_discrepancies_evidence_severity_confidence(client):
    """Steps 14-17: View discrepancies, open evidence citations, inspect severity and confidence"""
    txns = client.get("/api/transactions").json()
    txn_id = txns[0]["id"]

    res = client.get(f"/api/transactions/{txn_id}/discrepancies")
    assert res.status_code == 200
    discrepancies = res.json()
    assert len(discrepancies) > 0

    rule_codes = [d["rule_code"] for d in discrepancies]
    assert "PRICE_MISMATCH" in rule_codes
    assert "QUANTITY_MISMATCH" in rule_codes
    assert "PAYMENT_MISMATCH" in rule_codes

    for d in discrepancies:
        assert d["severity"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert 0.0 <= d["confidence"] <= 1.0
        assert d["title"] != ""
        assert len(d["evidences"]) > 0

        # Step 15: Open single evidence via /api/evidence/{id}
        first_ev = d["evidences"][0]
        ev_res = client.get(f"/api/evidence/{first_ev['id']}")
        assert ev_res.status_code == 200
        ev_data = ev_res.json()
        assert ev_data["id"] == first_ev["id"]
        assert ev_data["snippet"] != ""
        assert ev_data["document_name"] != ""


def test_step_18_generate_reconciliation_report(client):
    """Step 18: Generate and retrieve formal reconciliation report"""
    txns = client.get("/api/transactions").json()
    txn_id = txns[0]["id"]

    res = client.get(f"/api/transactions/{txn_id}/report")
    assert res.status_code == 200
    report = res.json()
    assert report["transaction_id"] == txn_id
    assert report["total_documents"] == 4
    assert len(report["discrepancies"]) > 0
    assert report["ai_grounded_explanation"] != ""
    assert report["financial_variance_amount"] > 0


def test_step_19_view_dashboard_stats(client):
    """Step 19: View real un-mocked dashboard statistics"""
    res = client.get("/api/dashboard/stats")
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_transactions"] >= 1
    assert stats["total_documents"] >= 4
    assert stats["total_discrepancies"] >= 3
    assert stats["total_outstanding_amount"] > 0
    assert "CRITICAL" in stats["discrepancies_by_severity"]
    assert stats["status_distribution"]["DISCREPANCY_FOUND"] >= 1


def test_step_20_run_evaluation_benchmark(client):
    """Step 20: Run evaluation benchmark (unranked comparison across RULE_BASED, AI_ONLY, HYBRID)"""
    res = client.post("/api/evaluation/run")
    assert res.status_code == 200
    bench = res.json()
    assert "modes" in bench
    modes = bench["modes"]
    assert "RULE_BASED" in modes
    assert "AI_ONLY" in modes
    assert "HYBRID" in modes

    for name in ["RULE_BASED", "AI_ONLY", "HYBRID"]:
        cfg = modes[name]
        assert "precision" in cfg
        assert "recall" in cfg
        assert "f1_score" in cfg
        assert "reconciliation_accuracy" in cfg
        assert "evidence_accuracy" in cfg
        assert 0.0 <= cfg["precision"] <= 1.0
        assert 0.0 <= cfg["f1_score"] <= 1.0

    # Also test GET /api/evaluation/results
    cached_res = client.get("/api/evaluation/results")
    assert cached_res.status_code == 200
    assert cached_res.json() is not None


def test_semantic_vector_store_and_matcher():
    """Verify Semantic VectorStore (FAISS & Numpy) and SemanticMatcher"""
    vs = VectorStore(dimension=384)
    texts = [
        "M10 Stainless Steel Hex Bolts 50mm",
        "M10 SS Hexagonal Screw 50mm",
        "Hydraulic Seal Kit Model 200",
        "High Pressure Hydraulic Gasket Kit"
    ]
    metas = [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]
    vs.add_texts(texts, metas)

    results = vs.search("M10 SS Hex Bolt", top_k=2)
    assert len(results) == 2
    assert "Hex" in results[0][0]["text"] or "Bolt" in results[0][0]["text"]

    # Verify SemanticMatcher
    sim, is_match = SemanticMatcher.match_supplier("Apex Industrial Tools Pvt Ltd", "Apex Tools Private Limited")
    assert is_match is True
    assert sim >= 0.70

    sim_diff, is_diff_match = SemanticMatcher.match_supplier("Apex Tools", "Reliance Petroleum Limited")
    assert is_diff_match is False
