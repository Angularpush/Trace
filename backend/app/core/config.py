"""
TRACE - Application Configuration
"""

import os
from decimal import Decimal
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "TRACE"
    PROJECT_DESCRIPTION: str = "Document-Level MSME Transaction Reconciliation & Discrepancy Detection System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Base directories
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    STORAGE_DIR: str = os.environ.get("STORAGE_DIR", os.environ.get("UPLOAD_DIR", os.path.join(os.path.dirname(BASE_DIR), "storage")))
    UPLOAD_DIR: str = os.environ.get("UPLOAD_DIR", os.environ.get("STORAGE_DIR", os.path.join(os.path.dirname(BASE_DIR), "storage")))
    MODELS_DIR: str = os.path.join(os.path.dirname(BASE_DIR), "ml", "models")
    
    # Database
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./trace.db")
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
    # Server & Networking
    PORT: int = int(os.environ.get("PORT", "8000"))
    CORS_ORIGINS: str = os.environ.get("CORS_ORIGINS", "*")
    MAX_UPLOAD_SIZE_MB: int = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "50"))
    
    # AI / LLM Configuration
    DEFAULT_LLM_PROVIDER: str = os.environ.get("DEFAULT_LLM_PROVIDER", "openai")  # "offline", "openai", "anthropic", "gemini"
    LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "openai")
    
    # OpenAI / AgentRouter Configuration
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", os.environ.get("AGENTROUTER_API_KEY", "sk-hUMP80hjBvf6CfEYsM0zOzKPOyi9U48h1L3QEw4uMNcGSSYW"))
    OPENAI_API_BASE: str = os.environ.get("OPENAI_API_BASE", os.environ.get("AGENTROUTER_BASE_URL", "https://agentrouter.org/v1"))
    OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-6-astra")
    
    # Anthropic / Claude Configuration
    ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "sk-hUMP80hjBvf6CfEYsM0zOzKPOyi9U48h1L3QEw4uMNcGSSYW")
    ANTHROPIC_API_BASE: str = os.environ.get("ANTHROPIC_API_BASE", "https://agentrouter.org/v1")
    ANTHROPIC_MODEL: str = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5")
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Reconciliation Thresholds (Deterministic)
    PRICE_TOLERANCE_PERCENT: Decimal = Decimal("0.01")  # 1% tolerance for minor rounding
    QUANTITY_TOLERANCE_PERCENT: Decimal = Decimal("0.00")
    MONETARY_TOLERANCE_AMOUNT: Decimal = Decimal("1.00")  # ₹1.00 minor rounding tolerance
    
    # Semantic Matching Thresholds
    SUPPLIER_MATCH_THRESHOLD: float = 0.72
    ITEM_MATCH_THRESHOLD: float = 0.68
    DOCUMENT_LINK_THRESHOLD: float = 0.65
    
    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
