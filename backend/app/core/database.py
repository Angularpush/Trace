"""
TRACE - Database Connection and Session Management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# SQLite connection args for multithreaded FastAPI access
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    import app.models  # Ensure all model tables are registered with Base.metadata
    Base.metadata.create_all(bind=engine)
    # Check for SQLite schema migrations
    if settings.DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            try:
                # Check documents table columns
                dres = conn.exec_driver_sql("PRAGMA table_info(documents)").fetchall()
                dcol_names = [row[1] for row in dres]
                if dcol_names:
                    new_doc_cols = {
                        "file_id": "VARCHAR DEFAULT NULL",
                        "document_type": "VARCHAR DEFAULT 'OTHER'",
                        "page_start": "INTEGER DEFAULT 1",
                        "page_end": "INTEGER DEFAULT 1",
                        "document_number": "VARCHAR DEFAULT NULL",
                        "confidence": "FLOAT DEFAULT 1.0",
                        "extracted_text": "TEXT DEFAULT ''",
                        "structured_data": "JSON DEFAULT '{}'",
                        "classification_method": "VARCHAR DEFAULT 'ML_CLASSIFIER'",
                        "original_pdf_id": "VARCHAR DEFAULT NULL",
                        "page_number": "INTEGER DEFAULT 1"
                    }
                    for col, col_type in new_doc_cols.items():
                        if col not in dcol_names:
                            conn.exec_driver_sql(f"ALTER TABLE documents ADD COLUMN {col} {col_type}")

                # Check transactions table columns
                tres = conn.exec_driver_sql("PRAGMA table_info(transactions)").fetchall()
                tcol_names = [row[1] for row in tres]
                if tcol_names:
                    new_txn_cols = {
                        "transaction_reference": "VARCHAR DEFAULT ''",
                        "supplier": "VARCHAR DEFAULT ''",
                        "customer": "VARCHAR DEFAULT ''",
                        "transaction_date": "DATETIME DEFAULT NULL",
                        "currency": "VARCHAR DEFAULT 'INR'",
                        "status": "VARCHAR DEFAULT 'PENDING'"
                    }
                    for col, col_type in new_txn_cols.items():
                        if col not in tcol_names:
                            conn.exec_driver_sql(f"ALTER TABLE transactions ADD COLUMN {col} {col_type}")

                # Check discrepancies table columns
                res = conn.exec_driver_sql("PRAGMA table_info(discrepancies)").fetchall()
                col_names = [row[1] for row in res]
                if col_names:
                    if "expected_value" not in col_names:
                        conn.exec_driver_sql("ALTER TABLE discrepancies ADD COLUMN expected_value VARCHAR DEFAULT ''")
                    if "actual_value" not in col_names:
                        conn.exec_driver_sql("ALTER TABLE discrepancies ADD COLUMN actual_value VARCHAR DEFAULT ''")
                    if "difference_value" not in col_names:
                        conn.exec_driver_sql("ALTER TABLE discrepancies ADD COLUMN difference_value VARCHAR DEFAULT ''")
                conn.commit()
            except Exception:
                pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
