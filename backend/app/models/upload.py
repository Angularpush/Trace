"""
TRACE - UploadBatch and File Models
Represents physical upload events and files before/during document segmentation.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class UploadBatch(Base):
    __tablename__ = "upload_batches"

    id = Column(String, primary_key=True, index=True)
    uploaded_by = Column(String, default="system")
    upload_time = Column(DateTime, default=datetime.utcnow)
    original_filename = Column(String, nullable=True)
    number_of_files = Column(Integer, default=1)
    processing_status = Column(String, default="PENDING")  # PENDING, PROCESSING, COMPLETED, ERROR

    files = relationship("File", back_populates="upload_batch", cascade="all, delete-orphan")


class File(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, index=True)
    upload_batch_id = Column(String, ForeignKey("upload_batches.id", ondelete="CASCADE"), nullable=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, default="pdf")
    file_size = Column(Integer, default=0)
    storage_path = Column(String, nullable=False)
    checksum = Column(String, nullable=True)
    upload_time = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(String, default="PROCESSED")  # UPLOADED, SEGMENTING, PROCESSED, ERROR

    upload_batch = relationship("UploadBatch", back_populates="files")
    documents = relationship("Document", back_populates="file", cascade="all, delete-orphan")

