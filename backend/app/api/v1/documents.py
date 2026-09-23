"""
TRACE - Documents API Endpoints
Handles document uploads, multi-format extraction, classification, and metadata retrieval.
"""

import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.document import Document
from app.schemas.document import DocumentResponse
from app.extraction.extractor_service import DocumentProcessingService

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".json"}

@router.post("/upload", response_model=List[DocumentResponse])
async def upload_documents(
    files: List[UploadFile] = File(...),
    doc_type: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload one or more business documents (PDF, PNG, JPG, JPEG, TXT, JSON).
    Extracts text, classifies document type via trained model, and normalizes fields.
    Splits multi-page PDFs page-by-page, classifies each page independently via trained model,
    normalizes structured fields, groups into transactions, and runs automated reconciliation.
    """
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    saved_docs = []
    
    for upload in files:
        doc_id = f"doc_{uuid.uuid4().hex[:10]}"
        orig_pdf_id = f"pdf_{uuid.uuid4().hex[:10]}"
        ext = os.path.splitext(upload.filename)[1].lower()
        if not ext or ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format '{ext or 'unknown'}' for file '{upload.filename}'. Allowed formats: PDF, PNG, JPG, JPEG, TXT, JSON."
            )

        file_name = f"{doc_id}_{upload.filename}"
        file_name = f"{orig_pdf_id}_{upload.filename}"
        target_path = os.path.join(settings.STORAGE_DIR, file_name)

        # Save uploaded file to storage
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)

        try:
            # Multi-page extraction and classification pipeline
            processed_pages = DocumentProcessingService.process_multi_page_document(
                target_path,
                user_doc_type=doc_type,
                output_dir=settings.STORAGE_DIR
            )

            for p_info in processed_pages:
                p_num = p_info["page_number"]
                total_p = len(processed_pages)
                page_fn = upload.filename if total_p == 1 else f"{os.path.splitext(upload.filename)[0]} (Page {p_num}){ext}"

                # Check if document already exists to prevent duplicate insertion
                existing_doc = db.query(Document).filter(
                    Document.filename == page_fn,
                    Document.page_number == p_num
                ).first()

                if existing_doc:
                    existing_doc.file_path = p_info.get("file_path") or target_path
                    existing_doc.file_type = ext.replace(".", "")
                    existing_doc.doc_type = p_info["doc_type"]
                    existing_doc.classification_confidence = p_info["classification_confidence"]
                    existing_doc.raw_text = p_info["raw_text"]
                    existing_doc.parsed_data = p_info["parsed_data"]
                    existing_doc.status = "processed"
                    db.commit()
                    db.refresh(existing_doc)
                    saved_docs.append(existing_doc)
                else:
                    page_doc_id = f"doc_{uuid.uuid4().hex[:10]}"
                    doc_record = Document(
                        id=page_doc_id,
                        original_pdf_id=orig_pdf_id,
                        page_number=p_num,
                        filename=page_fn,
                        file_path=p_info.get("file_path") or target_path,
                        file_type=ext.replace(".", ""),
                        doc_type=p_info["doc_type"],
                        classification_confidence=p_info["classification_confidence"],
                        page_count=1,
                        raw_text=p_info["raw_text"],
                        parsed_data=p_info["parsed_data"],
                        status="processed"
                    )
                    db.add(doc_record)
                    db.commit()
                    db.refresh(doc_record)
                    saved_docs.append(doc_record)

        except Exception as e:
            db.rollback()
            if os.path.exists(target_path):
                try:
                    os.remove(target_path)
                except Exception:
                    pass
            import traceback
            tb = traceback.format_exc()
            print(f"[TRACE Pipeline Error] Upload processing failed: {tb}")
            raise HTTPException(status_code=500, detail=f"Document pipeline failed on '{upload.filename}': {str(e)}")

    # Stage 6: Transaction linking
    try:
        from app.reconciliation.linker import TransactionLinker
        from app.reconciliation.orchestrator import reconciliation_orchestrator
        from app.models.discrepancy import Discrepancy, Evidence

        print("[TRACE Pipeline] 6. Transaction linking: Grouping documents into canonical transactions...")
        txns = TransactionLinker.link_database_documents(db)
        print(f"[TRACE Pipeline] 6. Transaction linking complete: {len(txns)} transaction cluster(s) active")

        # Stage 7 & 8: Automated Reconciliation and Discrepancy Detection
        for txn in txns:
            docs = txn.documents
            doc_dicts = [
                {
                    "id": d.id,
                    "filename": d.filename,
                    "doc_type": d.doc_type,
                    "original_pdf_id": getattr(d, "original_pdf_id", None),
                    "page_number": getattr(d, "page_number", 1),
                    "parsed_data": d.parsed_data or {},
                    "raw_text": d.raw_text,
                    "page_count": d.page_count
                }
                for d in docs
            ]
            print(f"[TRACE Pipeline] 7. Reconciliation: Evaluating 10 Decimal Rules for {txn.transaction_ref}...")
            result = reconciliation_orchestrator.reconcile_transaction(
                transaction_ref=txn.transaction_ref,
                documents=doc_dicts,
                mode="HYBRID",
                llm_provider_name="offline"
            )

            # Persist discrepancies
            db.query(Discrepancy).filter(Discrepancy.transaction_id == txn.id).delete()
            for disc_data in result.get("discrepancies", []):
                disc_id = f"disc_{uuid.uuid4().hex[:10]}"
                disc_record = Discrepancy(
                    id=disc_id,
                    transaction_id=txn.id,
                    rule_code=disc_data.get("rule_code", "UNKNOWN"),
                    discrepancy_type=disc_data.get("discrepancy_type", "GENERAL"),
                    severity=disc_data.get("severity", "MEDIUM"),
                    confidence=float(disc_data.get("confidence", 0.9)),
                    title=disc_data.get("title", ""),
                    description=disc_data.get("description", ""),
                    difference_amount=float(disc_data.get("difference_amount", 0.0)),
                    expected_value=disc_data.get("expected_value", ""),
                    actual_value=disc_data.get("actual_value", ""),
                    difference_value=disc_data.get("difference_value", ""),
                    llm_explanation=disc_data.get("llm_explanation", ""),
                    status="OPEN"
                )
                db.add(disc_record)
                for ev in disc_data.get("evidences", []):
                    ev_id = f"ev_{uuid.uuid4().hex[:10]}"
                    ev_record = Evidence(
                        id=ev_id,
                        discrepancy_id=disc_id,
                        document_id=ev.get("document_id", "DOC"),
                        document_name=ev.get("document_name", "Document"),
                        page_number=ev.get("page_number", 1),
                        field_name=ev.get("field_name", "Field"),
                        exact_value=str(ev.get("exact_value", "")),
                        snippet=ev.get("snippet", ""),
                        relevance_score=float(ev.get("relevance_score", 1.0))
                    )
                    db.add(ev_record)

            txn.reconciliation_status = result.get("reconciliation_status", "PENDING")
            txn.reconciliation_summary = result.get("ai_grounded_explanation", "")
            db.commit()
            print(f"[TRACE Pipeline] 8. Discrepancy detection: {len(result.get('discrepancies', []))} discrepancy/variances detected for {txn.transaction_ref} (Status: {txn.reconciliation_status})")

    except Exception as e:
        print(f"[TRACE Pipeline Warning] Auto-reconciliation background step encountered error: {e}")

    return saved_docs

@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    skip: int = 0,
    limit: int = 100,
    doc_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Document)
    if doc_type:
        query = query.filter(Document.doc_type == doc_type.upper())
    return query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.post("/seed-demo", response_model=List[DocumentResponse])
def seed_demo_documents(db: Session = Depends(get_db)):
    """
    Seeds realistic sample MSME documents (TXN-001 Clean Match & TXN-002 Multi-Discrepancy)
    and automatically executes transaction linking and rules-based reconciliation.
    """
    sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../sample_data/raw_documents"))
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    saved_docs = []

    if os.path.exists(sample_dir):
        for root, _, files in os.walk(sample_dir):
            for fname in sorted(files):
                if not fname.endswith(".pdf") and not fname.endswith(".txt"):
                    continue
                src_path = os.path.join(root, fname)
                doc_id = f"doc_{uuid.uuid4().hex[:10]}"
                target_path = os.path.join(settings.STORAGE_DIR, f"{doc_id}_{fname}")
                shutil.copyfile(src_path, target_path)

                processed = DocumentProcessingService.process_document(target_path)
                existing_doc = db.query(Document).filter(Document.filename == fname).first()
                if existing_doc:
                    existing_doc.file_path = target_path
                    existing_doc.file_type = "pdf" if fname.endswith(".pdf") else "txt"
                    existing_doc.doc_type = processed["doc_type"]
                    existing_doc.classification_confidence = processed["classification_confidence"]
                    existing_doc.page_count = processed["page_count"]
                    existing_doc.raw_text = processed["raw_text"]
                    existing_doc.parsed_data = processed["parsed_data"]
                    existing_doc.status = "processed"
                    db.commit()
                    db.refresh(existing_doc)
                    saved_docs.append(existing_doc)
                else:
                    doc_record = Document(
                        id=doc_id,
                        original_pdf_id=doc_id,
                        page_number=1,
                        filename=fname,
                        file_path=target_path,
                        file_type="pdf" if fname.endswith(".pdf") else "txt",
                        doc_type=processed["doc_type"],
                        classification_confidence=processed["classification_confidence"],
                        page_count=processed["page_count"],
                        raw_text=processed["raw_text"],
                        parsed_data=processed["parsed_data"],
                        status="processed"
                    )
                    db.add(doc_record)
                    db.commit()
                    db.refresh(doc_record)
                    saved_docs.append(doc_record)

    # Automatically auto-link and reconcile
    from app.reconciliation.linker import TransactionLinker
    from app.reconciliation.orchestrator import reconciliation_orchestrator
    from app.models.discrepancy import Discrepancy, Evidence
    
    txns = TransactionLinker.link_database_documents(db)
    for txn in txns:
        docs = txn.documents
        doc_dicts = [
            {
                "id": d.id,
                "filename": d.filename,
                "doc_type": d.doc_type,
                "parsed_data": d.parsed_data or {},
                "raw_text": d.raw_text,
                "page_count": d.page_count
            }
            for d in docs
        ]
        result = reconciliation_orchestrator.reconcile_transaction(
            transaction_ref=txn.transaction_ref,
            documents=doc_dicts,
            mode="HYBRID",
            llm_provider_name="offline"
        )
        db.query(Discrepancy).filter(Discrepancy.transaction_id == txn.id).delete()
        for disc_data in result.get("discrepancies", []):
            disc_id = f"disc_{uuid.uuid4().hex[:10]}"
            disc_record = Discrepancy(
                id=disc_id,
                transaction_id=txn.id,
                rule_code=disc_data.get("rule_code", "UNKNOWN"),
                discrepancy_type=disc_data.get("discrepancy_type", "GENERAL"),
                severity=disc_data.get("severity", "MEDIUM"),
                confidence=float(disc_data.get("confidence", 0.9)),
                title=disc_data.get("title", ""),
                description=disc_data.get("description", ""),
                difference_amount=float(disc_data.get("difference_amount", 0.0)),
                expected_value=disc_data.get("expected_value", ""),
                actual_value=disc_data.get("actual_value", ""),
                difference_value=disc_data.get("difference_value", ""),
                llm_explanation=disc_data.get("llm_explanation", ""),
                status="OPEN"
            )
            db.add(disc_record)
            for ev in disc_data.get("evidences", []):
                ev_id = f"ev_{uuid.uuid4().hex[:10]}"
                ev_record = Evidence(
                    id=ev_id,
                    discrepancy_id=disc_id,
                    document_id=ev.get("document_id", "DOC"),
                    document_name=ev.get("document_name", "Document"),
                    page_number=ev.get("page_number", 1),
                    field_name=ev.get("field_name", "Field"),
                    exact_value=str(ev.get("exact_value", "")),
                    snippet=ev.get("snippet", ""),
                    relevance_score=float(ev.get("relevance_score", 1.0))
                )
                db.add(ev_record)
        txn.reconciliation_status = result.get("reconciliation_status", "PENDING")
        txn.reconciliation_summary = result.get("ai_grounded_explanation", "")
        db.commit()

    return saved_docs

@router.delete("/{doc_id}")
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass
    db.delete(doc)
    db.commit()
    return {"status": "success", "message": f"Document {doc_id} deleted"}
