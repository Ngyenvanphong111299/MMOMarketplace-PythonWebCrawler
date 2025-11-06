"""
Configuration management cho Crawler API
Quản lý environment variables và API key settings
"""
import os
from typing import List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables từ .env file
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Cấu hình ứng dụng"""
    
    # API Key Settings
    API_KEY: str = os.getenv("API_KEY", "XzEcSl7aaW7wfeyxW74IGpGDBcM4noaO")
    API_KEY_HEADER: str = os.getenv("API_KEY_HEADER", "X-API-Key")
    
    # Rate Limiting Settings
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS", 
        "http://localhost:3000,http://localhost:8080,http://localhost:8000"
    ).split(",")
    ALLOWED_METHODS: List[str] = ["GET", "POST", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["Content-Type", "Authorization", "X-API-Key"]
    
    # Security Headers
    SECURITY_HEADERS_ENABLED: bool = os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true"
    
    # Request Settings
    MAX_REQUEST_SIZE: int = int(os.getenv("MAX_REQUEST_SIZE", "10485760"))  # 10MB
    
    # URL Validation
    ALLOWED_DOMAINS: List[str] = os.getenv(
        "ALLOWED_DOMAINS",
        "openai.com,techcrunch.com,anthropic.com,adobe.com"
    ).split(",")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    SECURITY_LOG_ENABLED: bool = os.getenv("SECURITY_LOG_ENABLED", "true").lower() == "true"


# Global settings instance
settings = Settings()
