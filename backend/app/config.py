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
    NORMALIZED_DATA_SUBDIR: str = "normalized"
    METADATA_SUBDIR: str = "metadata"
    MODELS_SUBDIR: str = "models"
    EXPERIMENTS_SUBDIR: str = "experiments"
    FEATURE_STORE_SUBDIR: str = "features"

    # Persistent Storage (S3 / Azure Blob / Local)
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")  # local | s3 | azure_blob
    S3_BUCKET: Optional[str] = os.getenv("S3_BUCKET")
    S3_REGION: Optional[str] = os.getenv("S3_REGION")
    S3_ENDPOINT_URL: Optional[str] = os.getenv("S3_ENDPOINT_URL")
    S3_ACCESS_KEY_ID: Optional[str] = os.getenv("S3_ACCESS_KEY_ID")
    S3_SECRET_ACCESS_KEY: Optional[str] = os.getenv("S3_SECRET_ACCESS_KEY")

    AZURE_BLOB_CONNECTION_STRING: Optional[str] = os.getenv("AZURE_BLOB_CONNECTION_STRING")
    AZURE_BLOB_CONTAINER: Optional[str] = os.getenv("AZURE_BLOB_CONTAINER")

    # Modeling / ML
    TARGET_COLUMN: str = os.getenv("TARGET_COLUMN", "y")
    POSITIVE_CLASS_LABEL: str = os.getenv("POSITIVE_CLASS_LABEL", "yes")
    NEGATIVE_CLASS_LABEL: str = os.getenv("NEGATIVE_CLASS_LABEL", "no")
    TEST_SIZE: float = float(os.getenv("TEST_SIZE", "0.2"))
    RANDOM_STATE: int = int(os.getenv("RANDOM_STATE", "42"))
    CALIBRATION_METHOD: str = os.getenv("CALIBRATION_METHOD", "sigmoid")
    MODEL_REGISTRY_RETENTION: int = int(os.getenv("MODEL_REGISTRY_RETENTION", "5"))

    # Monitoring
    MONITORING_WINDOW_DAYS: int = int(os.getenv("MONITORING_WINDOW_DAYS", "30"))
    DRIFT_THRESHOLD: float = float(os.getenv("DRIFT_THRESHOLD", "0.1"))

    # Explainability
    SHAP_BACKGROUND_SAMPLE_SIZE: int = int(os.getenv("SHAP_BACKGROUND_SAMPLE_SIZE", "200"))
    LIME_NUM_FEATURES: int = int(os.getenv("LIME_NUM_FEATURES", "10"))
    
    # AI Agent (Gemini)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    AI_AGENT_ENABLED: bool = os.getenv("AI_AGENT_ENABLED", "true").lower() == "true"
    
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


