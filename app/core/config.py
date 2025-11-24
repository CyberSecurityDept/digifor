from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator
from typing import List
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

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


    ENCRYPTION_KEY: str
    ENCRYPTION_ALGORITHM: str = "AES-256-GCM"

    UPLOAD_DIR: str = "./data/uploads"
    ANALYSIS_DIR: str = "./data/analysis"
    REPORTS_DIR: str = "./data/reports"
    APK_DIR: str = "./data/apks"
    LOGO_PATH: str = "./assets/logo.png"
    MAX_FILE_SIZE: int = 104857600

    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/digital_forensics.log"

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Digital Forensics"
    VERSION: str = "1.0.0"
    
    SERVER_IP: str = ""
    API_BASE_URL: str = "http://172.15.2.105"

    ENV: str = "development"
    DEBUG: bool = True

    CORS_ORIGINS: List[AnyHttpUrl] = []

    ANALYTICS_BATCH_SIZE: int = 1000
    HASH_ALGORITHMS: List[str] = ["md5", "sha1", "sha256"]
    MAX_ANALYSIS_THREADS: int = 4

    MOBSF_URL: str = "http://localhost:5001"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("["):
                return json.loads(v)
            return [i.strip() for i in v.split(",") if i]
        elif isinstance(v, list):
            return v
        return []

    class Config:
        env_file = ".env"
        extra = "ignore"
        case_sensitive = True


settings = Settings()
