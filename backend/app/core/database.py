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
