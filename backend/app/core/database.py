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
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)
    # Check for SQLite schema migrations
    if settings.DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            try:
                # Check documents table columns
                dres = conn.exec_driver_sql("PRAGMA table_info(documents)").fetchall()
                dcol_names = [row[1] for row in dres]
                if dcol_names:
                    if "original_pdf_id" not in dcol_names:
                        conn.exec_driver_sql("ALTER TABLE documents ADD COLUMN original_pdf_id VARCHAR DEFAULT NULL")
                    if "page_number" not in dcol_names:
                        conn.exec_driver_sql("ALTER TABLE documents ADD COLUMN page_number INTEGER DEFAULT 1")

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
                conn.commit()
            except Exception:
                pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
