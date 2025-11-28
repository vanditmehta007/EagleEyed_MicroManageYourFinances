import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Eagle Eyed API"
    DEBUG: bool = True
    
    # Supabase Settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    # JWT Settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60 * 24 # 24 hours
    
    # OpenAI Settings (for RAG)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Business Rules
    GST_THRESHOLD: float = 2000000.0 # 20 Lakhs
    TDS_THRESHOLD: float = 30000.0
    CASH_PAYMENT_LIMIT: float = 10000.0
    
    class Config:
        env_file = ".env"

# Global settings instance
settings = Settings()
