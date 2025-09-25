from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings"""
    
    # Database Configuration - REQUIRED FROM ENV
    database_url: str = Field(alias="DATABASE_URL")
    database_echo: bool = Field(alias="DATABASE_ECHO")
    
    # PostgreSQL specific settings - REQUIRED FROM ENV
    postgres_host: str = Field(alias="POSTGRES_HOST")
    postgres_port: int = Field(alias="POSTGRES_PORT")
    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(alias="POSTGRES_DB")
    
    # Security - REQUIRED FROM ENV
    secret_key: str = Field(alias="SECRET_KEY")
    algorithm: str = Field(alias="ALGORITHM")
    access_token_expire_minutes: int = Field(alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # File Storage - REQUIRED FROM ENV
    upload_dir: str = Field(alias="UPLOAD_DIR")
    analysis_dir: str = Field(alias="ANALYSIS_DIR")
    reports_dir: str = Field(alias="REPORTS_DIR")
    max_file_size: int = Field(alias="MAX_FILE_SIZE")
    
    # Encryption - REQUIRED FROM ENV
    encryption_key: str = Field(alias="ENCRYPTION_KEY")
    encryption_algorithm: str = Field(alias="ENCRYPTION_ALGORITHM")
    
    # Logging - REQUIRED FROM ENV
    log_level: str = Field(alias="LOG_LEVEL")
    log_file: str = Field(alias="LOG_FILE")
    
    # API Configuration - REQUIRED FROM ENV
    api_v1_str: str = Field(alias="API_V1_STR")
    project_name: str = Field(alias="PROJECT_NAME")
    version: str = Field(alias="VERSION")
    
    # Development - REQUIRED FROM ENV
    debug: bool = Field(alias="DEBUG")
    cors_origins: List[str] = Field(alias="CORS_ORIGINS")
    
    # Big Data Analytics - REQUIRED FROM ENV
    analytics_batch_size: int = Field(alias="ANALYTICS_BATCH_SIZE")
    hash_algorithms: List[str] = Field(alias="HASH_ALGORITHMS")
    max_analysis_threads: int = Field(alias="MAX_ANALYSIS_THREADS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v):
        if not v or v == "":
            raise ValueError("DATABASE_URL is required and cannot be empty")
        if not v.startswith(('postgresql://', 'sqlite://')):
            raise ValueError("DATABASE_URL must be a valid database URL")
        return v
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        if not v or v == "":
            raise ValueError("SECRET_KEY is required and cannot be empty")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters for security")
        return v
    
    @field_validator('encryption_key')
    @classmethod
    def validate_encryption_key(cls, v):
        if not v or v == "":
            raise ValueError("ENCRYPTION_KEY is required and cannot be empty")
        if len(v) < 32:
            raise ValueError("ENCRYPTION_KEY must be at least 32 characters for security")
        return v
    
    @field_validator('postgres_password')
    @classmethod
    def validate_postgres_password(cls, v):
        if not v or v == "":
            raise ValueError("POSTGRES_PASSWORD is required and cannot be empty")
        if len(v) < 8:
            raise ValueError("POSTGRES_PASSWORD must be at least 8 characters")
        return v


# Create settings instance
settings = Settings()

# Ensure directories exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.analysis_dir, exist_ok=True)
os.makedirs(settings.reports_dir, exist_ok=True)
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)