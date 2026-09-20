"""
TRACE - Document-Level MSME Transaction Reconciliation & Discrepancy Detection System
FastAPI Application Entry Point
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db
from app.api.router import api_router

# Create database tables and perform migrations
init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure storage and tables exist
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    init_db()
    print(f"[{settings.PROJECT_NAME}] Database initialized. Ready on port 8000.")
    yield
    print(f"[{settings.PROJECT_NAME}] Shutting down gracefully.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local frontend development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static storage for document viewing
app.mount("/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")

# Include API Router (both /api/v1 and /api aliases)
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "description": settings.PROJECT_DESCRIPTION,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
