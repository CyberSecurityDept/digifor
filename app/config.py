"""
Configuration settings for Forenlytic Backend
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Database Configuration
    database_url: str = "sqlite:///./data/forenlytic.db"
    database_echo: bool = False
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # File Storage
    upload_dir: str = "./data/uploads"
    analysis_dir: str = "./data/analysis"
    reports_dir: str = "./data/reports"
    max_file_size: int = 104857600  # 100MB
    
    # Encryption
    encryption_key: str = "your-encryption-key-here-32-chars"
    encryption_algorithm: str = "AES-256-GCM"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/forenlytic.log"
    
    # API Configuration
    api_v1_str: str = "/api/v1"
    project_name: str = "Forenlytic"
    version: str = "1.0.0"
    
    # Development
    debug: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Big Data Analytics
    analytics_batch_size: int = 1000
    hash_algorithms: List[str] = ["md5", "sha1", "sha256"]
    max_analysis_threads: int = 4
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()

# Ensure directories exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.analysis_dir, exist_ok=True)
os.makedirs(settings.reports_dir, exist_ok=True)
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
