"""Configuration management for the application."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_TITLE: str = "SmartReco API"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Security
    API_KEY: Optional[str] = os.getenv("API_KEY", "demo-api-key-change-in-production")
    
    # Data Configuration
    DATA_DIR: Path = Path("data")
    RULES_CONFIG_PATH: Path = Path("rules_config.yaml")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # Scoring Configuration
    PRIORITY_THRESHOLDS: dict = {
        "high": 50,
        "medium": 25,
        "low": 0
    }
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:80",
        "http://localhost"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


