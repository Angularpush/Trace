"""
TRACE - Documents & Uploads API Endpoints
Handles multi-file batch uploads, PDF boundary segmentation,
document classification, and structured extraction.
Enforces: FILE != DOCUMENT != TRANSACTION.
"""

import os
import uuid
import shutil
import hashlib
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File as FastApiFile, Form, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.upload import UploadBatch, File
from app.models.document import Document
from app.schemas.document import DocumentResponse, FileResponse, UploadBatchResponse
from app.extraction.extractor_service import DocumentProcessingService
from app.reconciliation.linker import transaction_linker

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".json"}

def compute_checksum(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

@router.post("/upload", response_model=List[DocumentResponse])
async def upload_documents(
    files: List[UploadFile] = FastApiFile(...),
    doc_type: Optional[str] = Form(None),
    uploaded_by: Optional[str] = Form("auditor"),
    db: Session = Depends(get_db)
):
    """
    Handles physical upload of one or multiple files.
    Creates UploadBatch -> File records -> Document segments via boundary detection -> Extracts fields -> Links transactions.
    """
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)

    # 1. Create UploadBatch
    batch_id = f"batch_{uuid.uuid4().hex[:10]}"
    upload_batch = UploadBatch(
        id=batch_id,
        uploaded_by=uploaded_by or "auditor",
        original_filename=files[0].filename if files else "batch",
        number_of_files=len(files),
        processing_status="PROCESSING"
    )
    db.add(upload_batch)
    db.flush()

    all_created_docs = []

    for upload in files:
        ext = os.path.splitext(upload.filename)[1].lower()
        if not ext or ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format '{ext}' for file '{upload.filename}'. Allowed: PDF, PNG, JPG, JPEG, TXT, JSON."
            )

        file_id = f"file_{uuid.uuid4().hex[:10]}"
        storage_filename = f"{file_id}_{upload.filename}"
        target_path = os.path.join(settings.STORAGE_DIR, storage_filename)

        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)

        file_size = os.path.getsize(target_path)
        checksum = compute_checksum(target_path)

        # 2. Create File Entity
        db_file = File(
            id=file_id,
            upload_batch_id=batch_id,
            filename=upload.filename,
            file_type=ext.replace(".", ""),
            file_size=file_size,
            storage_path=target_path,
            checksum=checksum,
            processing_status="PROCESSED"
        )
        db.add(db_file)
        db.flush()

        try:
            # 3. Document Boundary Segmentation & Information Extraction
            segmented_docs = DocumentProcessingService.process_file_segments(
                target_path,
                user_doc_type=doc_type,
                output_dir=settings.STORAGE_DIR
            )

            for seg in segmented_docs:
                doc_id = f"doc_{uuid.uuid4().hex[:10]}"
                p_start = seg.get("page_start", 1)
                p_end = seg.get("page_end", 1)
                p_count = p_end - p_start + 1

                # Construct page-specific filename
                if len(segmented_docs) > 1:
                    doc_fn = f"{os.path.splitext(upload.filename)[0]} (P{p_start}-P{p_end} {seg['document_type']}){ext}"
                else:
                    doc_fn = upload.filename

                db_doc = Document(
                    id=doc_id,
                    file_id=file_id,
                    document_type=seg.get("document_type", "OTHER"),
                    doc_type=seg.get("document_type", "OTHER"),  # backward compat
                    page_start=p_start,
                    page_end=p_end,
                    page_number=p_start,
                    page_count=p_count,
                    document_number=seg.get("document_number"),
                    confidence=seg.get("confidence", 1.0),
                    classification_confidence=seg.get("confidence", 1.0),
                    classification_method=seg.get("classification_method", "ML_CLASSIFIER"),
                    extracted_text=seg.get("raw_text", ""),
                    raw_text=seg.get("raw_text", ""),
                    structured_data=seg.get("parsed_data", {}),
                    parsed_data=seg.get("parsed_data", {}),
                    filename=doc_fn,
                    file_path=seg.get("file_path") or target_path,
                    file_type=ext.replace(".", ""),
                    status="processed"
                )
                db.add(db_doc)
                all_created_docs.append(db_doc)

        except Exception as e:
            upload_batch.processing_status = "ERROR"
            db_file.processing_status = "ERROR"
            db.commit()
            raise HTTPException(status_code=500, detail=f"Segmentation failed for '{upload.filename}': {str(e)}")

    upload_batch.processing_status = "COMPLETED"
    db.commit()

    # 4. Trigger Automatic Multi-Signal Transaction Clustering
    try:
        transaction_linker.link_database_documents(db)
    except Exception as e:
        print(f"[DocumentUpload] Linking step note: {e}")

    for d in all_created_docs:
        db.refresh(d)

    return all_created_docs

@router.get("", response_model=List[DocumentResponse])
@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    skip: int = 0,
    limit: int = 100,
    doc_type: Optional[str] = None,
    file_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns segmented business documents.
    """
    query = db.query(Document)
    if doc_type:
        query = query.filter(
            (Document.document_type == doc_type.upper()) | (Document.doc_type == doc_type.upper())
        )
    if file_id:
        query = query.filter(Document.file_id == file_id)
    return query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")
    return doc

@router.get("/files/{file_id}", response_model=FileResponse)
def get_file_detail(file_id: str, db: Session = Depends(get_db)):
    f = db.query(File).filter(File.id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail=f"File '{file_id}' not found")
    return f

@router.post("/{doc_id}/reclassify", response_model=DocumentResponse)
def reclassify_document(
    doc_id: str,
    target_type: str = Query(..., description="Target document type: PURCHASE_ORDER, INVOICE, DELIVERY_NOTE, PAYMENT_RECEIPT, etc."),
    db: Session = Depends(get_db)
):
    """
    Human-in-the-loop override: reclassifies document and re-parses domain fields.
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    new_type = target_type.upper()
    lines = [l.strip() for l in doc.extracted_text.split("\n") if l.strip()]
    re_parsed = DocumentProcessingService.parse_segment_data(new_type, doc.extracted_text, lines)

    doc.document_type = new_type
    doc.doc_type = new_type
    doc.confidence = 1.0
    doc.classification_method = "USER_CONFIRMED"
    doc.structured_data = re_parsed
    doc.parsed_data = re_parsed
    if re_parsed.get("document_number"):
        doc.document_number = re_parsed.get("document_number")

    db.commit()
    db.refresh(doc)

    # Re-run linking
    transaction_linker.link_database_documents(db)
    return doc

@router.delete("/{doc_id}")
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"status": "deleted", "document_id": doc_id}

@router.post("/seed-demo", response_model=List[DocumentResponse])
def seed_demo_documents(db: Session = Depends(get_db)):
    """
    Seeds demo MSME transactions with Purchase Order, Tax Invoice, Delivery Note, and Payment Receipt.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    sample_dir = os.path.join(base_dir, "sample_data", "raw_documents")
    
    txn_folders = ["TXN-001", "TXN-002"]
    created_docs = []
    
    for tf in txn_folders:
        folder_path = os.path.join(sample_dir, tf)
        if os.path.exists(folder_path):
            for fn in os.listdir(folder_path):
                if fn.lower().endswith(".pdf"):
                    fp = os.path.join(folder_path, fn)
                    try:
                        segments = DocumentProcessingService.process_file_segments(fp)
                        for seg in segments:
                            doc_id = f"doc_{uuid.uuid4().hex[:10]}"
                            db_doc = Document(
                                id=doc_id,
                                document_type=seg.get("document_type", "OTHER"),
                                doc_type=seg.get("document_type", "OTHER"),
                                page_start=seg.get("page_start", 1),
                                page_end=seg.get("page_end", 1),
                                page_number=seg.get("page_start", 1),
                                page_count=seg.get("page_end", 1) - seg.get("page_start", 1) + 1,
                                document_number=seg.get("document_number"),
                                confidence=seg.get("confidence", 1.0),
                                classification_confidence=seg.get("confidence", 1.0),
                                classification_method=seg.get("classification_method", "ML_CLASSIFIER"),
                                extracted_text=seg.get("raw_text", ""),
                                raw_text=seg.get("raw_text", ""),
                                structured_data=seg.get("parsed_data", {}),
                                parsed_data=seg.get("parsed_data", {}),
                                filename=fn,
                                file_path=fp,
                                file_type="pdf",
                                status="processed"
                            )
                            db.add(db_doc)
                            created_docs.append(db_doc)
                    except Exception as e:
                        print(f"Error seeding {fn}: {e}")
                        
    if not created_docs:
        demo_specs = [
            ("PURCHASE_ORDER", "PO-2024-001", "Acme Supplies Ltd", "Bharat Retailers Pvt", 125000.0, "PO-2024-001.pdf"),
            ("INVOICE", "INV-2024-089", "Acme Supplies Ltd", "Bharat Retailers Pvt", 125000.0, "INV-2024-089.pdf"),
            ("DELIVERY_NOTE", "DN-2024-089", "Acme Supplies Ltd", "Bharat Retailers Pvt", 125000.0, "DN-2024-089.pdf"),
            ("PAYMENT_RECEIPT", "PAY-2024-045", "Acme Supplies Ltd", "Bharat Retailers Pvt", 125000.0, "PAY-2024-045.pdf"),
        ]
        for dtype, num, supp, cust, amt, fn in demo_specs:
            doc_id = f"doc_{uuid.uuid4().hex[:10]}"
            mock_data = {
                "document_number": num,
                "po_number": "PO-2024-001",
                "invoice_number": "INV-2024-089" if dtype != "PURCHASE_ORDER" else None,
                "supplier": supp,
                "customer": cust,
                "total_amount": amt,
                "date": "2024-03-01",
                "items": [{"description": "Industrial Fasteners", "quantity": 100, "unit_price": 1250.0, "total": amt}]
            }
            db_doc = Document(
                id=doc_id,
                document_type=dtype,
                doc_type=dtype,
                page_start=1,
                page_end=1,
                page_number=1,
                page_count=1,
                document_number=num,
                confidence=1.0,
                classification_confidence=1.0,
                classification_method="DEMO_SEED",
                extracted_text=f"{dtype} {num}\nSupplier: {supp}\nCustomer: {cust}\nTotal: {amt}",
                raw_text=f"{dtype} {num}\nSupplier: {supp}\nCustomer: {cust}\nTotal: {amt}",
                structured_data=mock_data,
                parsed_data=mock_data,
                filename=fn,
                file_path=fn,
                file_type="pdf",
                status="processed"
            )
            db.add(db_doc)
            created_docs.append(db_doc)

    db.commit()
    transaction_linker.link_database_documents(db)
    for d in created_docs:
        db.refresh(d)
    return created_docs
