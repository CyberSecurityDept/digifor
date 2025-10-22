from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator
from typing import List, Optional
import secrets
import json


class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_ECHO: bool = False

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    UPLOAD_DIR: str = "./data/uploads"
    ANALYSIS_DIR: str = "./data/analysis"
    REPORTS_DIR: str = "./data/reports"
    APK_DIR: str = "./data/apks"
    MAX_FILE_SIZE: int = 104857600  # 100MB

    ENCRYPTION_KEY: str
    ENCRYPTION_ALGORITHM: str = "AES-256-GCM"

    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/digital_forensics.log"

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Digital Forensics"
    VERSION: str = "1.0.0"

    ENV: str = "development"
    DEBUG: bool = True
    CORS_ORIGINS: List[AnyHttpUrl] = []
    
    ANALYTICS_BATCH_SIZE: int = 1000
    HASH_ALGORITHMS: List[str] = ["md5", "sha1", "sha256"]
    MAX_ANALYSIS_THREADS: int = 4

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("["):
                return json.loads(v)
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
