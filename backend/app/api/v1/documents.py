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
    """
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    saved_docs = []
    
    for upload in files:
        doc_id = f"doc_{uuid.uuid4().hex[:10]}"
        ext = os.path.splitext(upload.filename)[1].lower()
        if not ext or ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format '{ext or 'unknown'}' for file '{upload.filename}'. Allowed formats: PDF, PNG, JPG, JPEG, TXT, JSON."
            )

        file_name = f"{doc_id}_{upload.filename}"
        target_path = os.path.join(settings.STORAGE_DIR, file_name)

        # Save file to storage
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)

        try:
            # Process and extract
            processed = DocumentProcessingService.process_document(target_path, user_doc_type=doc_type)

            doc_record = Document(
                id=doc_id,
                filename=upload.filename,
                file_path=target_path,
                file_type=ext.replace(".", ""),
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
        except Exception as e:
            db.rollback()
            if os.path.exists(target_path):
                try:
                    os.remove(target_path)
                except Exception:
                    pass
            raise HTTPException(status_code=500, detail=f"Failed to process {upload.filename}: {str(e)}")

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
        for fname in sorted(os.listdir(sample_dir)):
            if not fname.endswith(".pdf"):
                continue
            src_path = os.path.join(sample_dir, fname)
            doc_id = f"doc_{uuid.uuid4().hex[:10]}"
            target_path = os.path.join(settings.STORAGE_DIR, f"{doc_id}_{fname}")
            shutil.copyfile(src_path, target_path)

            processed = DocumentProcessingService.process_document(target_path)
            doc_record = Document(
                id=doc_id,
                filename=fname,
                file_path=target_path,
                file_type="pdf",
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
