import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Eagle Eyed API"
    DEBUG: bool = True
    
    # Supabase Settings
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    
    # JWT Settings
    JWT_SECRET_KEY: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60 * 24 # 24 hours

    # Gemini Settings
    GOOGLE_API_KEY: str = "AIzaSyClppt8j7WmnTreF8SftbmdXtZYVNcmGdM"

    # OpenAI Settings (Optional)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Agent Configuration
    AGENT_ID: str = "eagle_ai_agent_001"
    AGENT_NAME: str = "Eagle Eye AI"
    AGENT_DOMAIN: str = "Finance, Taxation & Regulatory Compliance"
    AGENT_SPECIALIZATION: str = "Expert Chartered Accountant & Strategic Financial Advisor"
    AGENT_DESCRIPTION: str = "A dual-role AI engine that assists CAs with technical compliance audits, report generation, and natural language transaction search on client data, while simultaneously acting as a financial advisor for clients by analyzing their uploaded documents to provide key ratios, health summaries, and investment strategies based on RBI guidelines and government schemes."
    AGENT_CAPABILITIES: str = "financial_report_generation,document_summarization,natural_language_transaction_search,compliance_audit_gst_tds,financial_ratio_analysis,investment_advisory_rbi_gov_schemes,regulatory_knowledge_base"
    
    # Server Configuration
    PORT: int = 7000
    PUBLIC_URL: str = "http://localhost:7000"
    
    # Mumbai Hacks Registry
    REGISTRY_URL: str = "https://mumbaihacksindex.chat39.com"

    # LLM Provider (anthropic, openai, or gemini)
    LLM_PROVIDER: str = "gemini"

    # Tunnel Configuration (for public deployment)
    ENABLE_TUNNEL: bool = True
    NGROK_AUTH_TOKEN: str = "367X0QQznHQwbOIlZ4yRJB35Eo7_6oyAoKyCkL9UoYH3dyb2P"

    # Business Rules
    GST_THRESHOLD: float = 2000000.0 # 20 Lakhs
    TDS_THRESHOLD: float = 30000.0
    CASH_PAYMENT_LIMIT: float = 10000.0
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Global settings instance
settings = Settings()
