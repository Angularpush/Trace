import os
import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.document import Document
from app.models.transaction import Transaction
from app.extraction.extractor_service import DocumentProcessingService
from app.reconciliation.linker import TransactionLinker
from app.reconciliation.orchestrator import reconciliation_orchestrator
from app.evaluation.benchmark import BenchmarkRunner


@pytest.fixture
def db_session(tmp_path):
    db_path = tmp_path / "test_e2e.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()


def test_e2e_full_pipeline(db_session, tmp_path):
    samples_dir = os.path.join(os.path.dirname(__file__), "..", "..", "sample_data", "raw_documents")
    assert os.path.exists(samples_dir), f"Sample directory not found at {samples_dir}"
    
    files = sorted([f for f in os.listdir(samples_dir) if f.endswith('.pdf')])
    assert len(files) == 8, f"Expected 8 sample PDFs, found {len(files)}"
    
    ingested_docs = []
    
    # 1. Ingest all 8 documents
    for filename in files:
        file_path = os.path.join(samples_dir, filename)
        processed = DocumentProcessingService.process_document(file_path)
        
        doc_record = Document(
            id=f"doc_{filename.replace('.', '_')}",
            filename=filename,
            file_path=file_path,
            file_type="pdf",
            doc_type=processed["doc_type"],
            classification_confidence=processed["classification_confidence"],
            page_count=processed["page_count"],
            raw_text=processed["raw_text"],
            parsed_data=processed["parsed_data"],
            status="processed"
        )
        db_session.add(doc_record)
        db_session.commit()
        db_session.refresh(doc_record)
        ingested_docs.append(doc_record)
        
    assert len(ingested_docs) == 8
    
    # Verify classifications
    for doc in ingested_docs:
        assert doc.doc_type in ["PURCHASE_ORDER", "INVOICE", "DELIVERY_NOTE", "PAYMENT_RECEIPT"]
        assert doc.classification_confidence > 0.50
        assert doc.parsed_data is not None
        
    # 2. Link transactions
    linked_txns = TransactionLinker.link_database_documents(db_session)
    assert len(linked_txns) == 2, f"Expected 2 linked transactions, got {len(linked_txns)}"
    
    # Identify TXN-001 and TXN-002
    txn_001 = next(t for t in linked_txns if "001" in t.transaction_ref)
    txn_002 = next(t for t in linked_txns if "002" in t.transaction_ref)
    
    assert len(txn_001.documents) == 4
    assert len(txn_002.documents) == 4
    
    # Format documents for orchestrator
    docs_001 = [
        {"id": d.id, "filename": d.filename, "doc_type": d.doc_type, "parsed_data": d.parsed_data or {}, "raw_text": d.raw_text, "page_count": d.page_count}
        for d in txn_001.documents
    ]
    docs_002 = [
        {"id": d.id, "filename": d.filename, "doc_type": d.doc_type, "parsed_data": d.parsed_data or {}, "raw_text": d.raw_text, "page_count": d.page_count}
        for d in txn_002.documents
    ]
    
    # 3. Reconcile Clean Transaction (TXN-001)
    rep_001 = reconciliation_orchestrator.reconcile_transaction(
        transaction_ref=txn_001.transaction_ref,
        documents=docs_001,
        mode="HYBRID",
        llm_provider_name="offline"
    )
    
    assert rep_001["reconciliation_status"] == "RECONCILED"
    assert rep_001["total_discrepancies"] == 0
    assert rep_001["financial_variance_amount"] == 0.0
    assert "reconciled" in rep_001["ai_grounded_explanation"].lower() or "clean" in rep_001["ai_grounded_explanation"].lower()
    
    # 4. Reconcile Discrepant Transaction (TXN-002)
    rep_002 = reconciliation_orchestrator.reconcile_transaction(
        transaction_ref=txn_002.transaction_ref,
        documents=docs_002,
        mode="HYBRID",
        llm_provider_name="offline"
    )
    
    assert rep_002["reconciliation_status"] in ["DISCREPANCY_FOUND", "MINOR_VARIANCE"]
    assert rep_002["total_discrepancies"] >= 2
    assert rep_002["financial_variance_amount"] > 0.0
    
    rule_codes = [d["rule_code"] for d in rep_002["discrepancies"]]
    # Expect quantity, price, and payment rules triggered
    assert "PRICE_MISMATCH" in rule_codes
    assert "QUANTITY_MISMATCH" in rule_codes
    assert "PAYMENT_MISMATCH" in rule_codes
    
    # Check evidence traceability
    for disc in rep_002["discrepancies"]:
        assert disc["confidence"] > 0.5
        assert len(disc["evidences"]) > 0
        for ev in disc["evidences"]:
            assert ev.get("document_name") is not None
            assert ev.get("snippet") != ""
            
    # 5. Run 3-Way Benchmark Suite
    benchmark_res = BenchmarkRunner.run_benchmark()
    
    assert benchmark_res["total_test_cases"] >= 4
    assert "RULE_BASED" in benchmark_res["modes"]
    assert "AI_ONLY" in benchmark_res["modes"]
    assert "HYBRID" in benchmark_res["modes"]
    
    # Verify benchmark accuracy metrics
    hybrid_perf = benchmark_res["modes"]["HYBRID"]
    assert hybrid_perf["precision"] >= 0.8
    assert hybrid_perf["recall"] >= 0.8
    assert hybrid_perf["f1_score"] >= 0.8
    assert hybrid_perf["reconciliation_accuracy"] >= 0.8
    assert hybrid_perf["avg_latency_ms"] >= 0
